import os
import time
from pathlib import Path

import numpy as np

from trast_master.config import Config


def validate_acquisition_config(config: Config):
    if not config.output_folder:
        raise ValueError("config.output_folder must be set in acquire mode")
    if not config.pulsewidths_us:
        raise ValueError("config.pulsewidths_us must not be empty")
    if config.num_frames_per_width < 1:
        raise ValueError("config.num_frames_per_width must be at least 1")
    if config.duty_percent <= 0:
        raise ValueError("config.duty_percent must be > 0")
    if config.num_periods_to_capture <= 0:
        raise ValueError("config.num_periods_to_capture must be > 0")


def safe_stop_waveform(logger=print):
    logger("safe_stop_waveform placeholder")


def pulsewidths_seconds_from_config(config: Config):
    return np.asarray(config.pulsewidths_us, dtype=float) * 1e-6


def run_acquisition(config: Config, logger=print, stop_event=None, progress_cb=None):
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    def update_progress(value: float, stage: str, detail: str):
        if progress_cb is not None:
            progress_cb(value, stage, detail)

    validate_acquisition_config(config)

    output_dir = Path(config.output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger("Acquisition started")
    logger(f"Output folder: {output_dir}")

    pulsewidths_s = pulsewidths_seconds_from_config(config)
    total_steps = len(pulsewidths_s) * config.num_frames_per_width
    completed_steps = 0

    update_progress(1, "Preparing acquisition", f"Output folder: {output_dir}")

    for pw_idx, pw_s in enumerate(pulsewidths_s):
        if stopped():
            safe_stop_waveform(logger=logger)
            raise RuntimeError("Run stopped by user.")

        duty_fraction = config.duty_percent / 100.0
        period_s = pw_s / duty_fraction
        f0_hz = 1.0 / period_s
        t_obs_s = config.num_periods_to_capture * period_s

        logger(
            f"Pulse width = {pw_s * 1e6:.3f} us | "
            f"duty = {config.duty_percent:.3f}% | "
            f"f0 = {f0_hz:.3f} Hz | "
            f"Tobs = {t_obs_s:.6f} s"
        )

        for frame_idx in range(config.num_frames_per_width):
            if stopped():
                safe_stop_waveform(logger=logger)
                raise RuntimeError("Run stopped by user.")

            detail = (
                f"Pulse width {pw_idx + 1}/{len(pulsewidths_s)} | "
                f"Frame {frame_idx + 1}/{config.num_frames_per_width} | "
                f"{pw_s * 1e6:.3f} us"
            )
            progress = 5.0 + 70.0 * (completed_steps / max(total_steps, 1))
            update_progress(progress, "Acquiring", detail)

            logger(f"  Frame {frame_idx + 1}/{config.num_frames_per_width}")

            # Placeholder synthetic signal
            fs = max(1000.0, 100.0 * f0_hz)
            dt = 1.0 / fs
            n_samples = max(100, int(round(t_obs_s / dt)))
            time_axis = np.arange(n_samples) * dt

            signal = (
                1.0
                + 0.2 * np.cos(2.0 * np.pi * f0_hz * time_axis)
                + 0.05 * np.cos(2.0 * np.pi * 2.0 * f0_hz * time_axis)
            )

            pw_us = pw_s * 1e6
            save_name = f"trace_pw_{pw_us:.3f}us_frame_{frame_idx + 1}.npz"
            save_path = output_dir / save_name

            np.savez(
                save_path,
                time=time_axis,
                detector=signal,
                pulse_width_us=pw_us,
                duty_percent=config.duty_percent,
                fundamental_frequency_hz=f0_hz,
                num_periods_to_capture=config.num_periods_to_capture,
            )

            logger(f"    Saved: {save_path.name}")

            completed_steps += 1

            if config.settle_time_s > 0:
                time.sleep(config.settle_time_s)

    safe_stop_waveform(logger=logger)
    update_progress(80.0, "Finishing acquisition", "Acquisition loop completed.")
    logger("Acquisition finished")
    return str(output_dir)