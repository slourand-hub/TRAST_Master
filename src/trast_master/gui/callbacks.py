import os
import time
from tkinter import filedialog, messagebox

from trast_master.config import Config
from trast_master.main import run_analysis
from trast_master.acquisition.moku_runner import run_acquisition
from trast_master.analysis.loader import find_npz_files, build_acquisition_summary
from trast_master.analysis.trast_metrics import compute_raw_diagnostics
from trast_master.gui.tables import populate_treeview_from_dataframe
from trast_master.gui.validation import (
    parse_int_list,
    validate_gui_inputs,
    collect_gui_values,
    build_logspace_pulsewidths_us,
)
from trast_master.gui.visibility import update_mode_ui, update_log_visibility
from trast_master.gui.presets import save_preset, load_preset

from trast_master.gui.queue_utils import process_worker_queue, make_worker_logger

def browse_analysis_file(state):
    path = filedialog.askopenfilename(
        title="Select .npz file to analyze",
        filetypes=[("NumPy files", "*.npz"), ("All files", "*.*")]
    )
    if path:
        state["analysis_target_var"].set(path)


def browse_analysis_folder(state):
    path = filedialog.askdirectory(title="Select folder to analyze")
    if path:
        state["analysis_target_var"].set(path)


def browse_output_folder(state):
    path = filedialog.askdirectory(title="Select output folder")
    if path:
        state["output_folder_var"].set(path)


def update_logspace_preview(state):
    try:
        pw_us = build_logspace_pulsewidths_us(state)
        if len(pw_us) == 1:
            txt = f"Generated 1 point: {pw_us[0]:.6g} us"
        else:
            txt = f"Generated {len(pw_us)} points: {pw_us[0]:.6g} us → {pw_us[-1]:.6g} us"
        state["logspace_preview_var"].set(txt)
        state["acq_error_var"].set("")
    except Exception as e:
        state["logspace_preview_var"].set("Invalid logspace settings")
        state["acq_error_var"].set(str(e))


def update_summary(state):
    values = collect_gui_values(state)
    try:
        mode = values["mode"].strip()
        if mode in ("acquire", "both"):
            pw_us = build_logspace_pulsewidths_us(state)
            n_pw = len(pw_us)
            n_frames = int(values["num_frames_per_width"])
            total_acq = n_pw * n_frames
            folder = values["output_folder"].strip() or "(none)"
            duty = values["duty_percent"].strip()
            summary = (
                f"Mode: {mode} | Save: {folder} | "
                f"Pulse widths: {n_pw} points ({pw_us[0]:.6g} us → {pw_us[-1]:.6g} us) | "
                f"Frames/width: {n_frames} | Total acquisitions: {total_acq} | Duty: {duty}%"
            )
        else:
            target = values["analysis_target"].strip() or "(none)"
            summary = (
                f"Mode: {mode} | Target: {target} | "
                f"Main FFT harmonics: {values['main_fft_harmonics']}"
            )
        state["summary_var"].set(summary)
    except Exception:
        state["summary_var"].set("Summary unavailable due to invalid inputs.")


def refresh_gui_state(state):
    update_logspace_preview(state)
    update_summary(state)

    errors = validate_gui_inputs(collect_gui_values(state))
    state["validation_var"].set(" | ".join(errors) if errors else "")

    update_mode_ui(state)
    update_log_visibility(state)


def preview_run(state):
    state["clear_log"]()
    state["append_log"]("Preview run")
    state["append_log"]("-" * 40)
    state["append_log"](state["summary_var"].get())
    if state["validation_var"].get():
        state["append_log"]("Validation warnings:")
        state["append_log"](state["validation_var"].get())
    else:
        state["append_log"]("Validation: OK")


def run_task_in_background(state):
    values = collect_gui_values(state)
    mode = values["mode"].strip()

    if mode == "analyze":
        config = Config(
            mode="analyze",
            folder=values["analysis_target"].strip(),
            x_axis=values["x_axis"].strip(),
            default_duty_fraction=0.01,
            max_harmonic=int(values["max_harmonic"]),
            main_fft_max_harmonics=parse_int_list(values["main_fft_harmonics"]),
            diagnostic_harmonics=parse_int_list(values["diagnostic_harmonics"]),
            n_spectrum_pw=int(values["n_spectrum_pw"]),
            save_csv=values["save_csv"],
            include_ls_trast=values["include_ls_trast"],
        )

        state["worker_log"]("Mode: analyze")
        state["worker_log"](f"Target: {config.folder}")

        files = find_npz_files(config.folder)
        state["worker_log"](f"Found {len(files)} file(s).")

        acq_df = build_acquisition_summary(
            files,
            default_duty_fraction=config.default_duty_fraction,
            acquisition_periods=config.num_periods_to_capture,
        )

        df = compute_raw_diagnostics(
            files=files,
            max_h=config.max_harmonic,
            default_duty_fraction=config.default_duty_fraction,
        )

        acq_cols = [
            "pulse_width_ns",
            "duty_cycle_fraction",
            "fundamental_frequency_hz",
            "dt_s",
            "fs_hz",
            "nyquist_hz",
            "n_samples",
            "t_obs_s",
            "modulation_period_s",
            "samples_per_period",
            "periods_observed",
            "periods_expected",
            "expected_t_obs_s",
            "t_obs_vs_expected_relerr",
        ]
        preview_cols = ["pulse_width_ns", "dc_trast_raw_norm"]
        preview_cols += [f"sum{H}_trast_raw_norm" for H in config.main_fft_max_harmonics]

        state["worker"].queue.put(("tables", {
            "acq_df": acq_df[acq_cols],
            "trast_df": df[preview_cols],
        }))

        bad = acq_df["t_obs_vs_expected_relerr"].abs() > 0.05
        if bad.any():
            state["worker_log"]("WARNING: acquisition windows are not comparable across pulse widths.")

        run_analysis(config, logger=state["worker_log"])

    elif mode == "acquire":
        save_folder = values["output_folder"].strip()
        if values["timestamped_subfolder"]:
            stamp = time.strftime("run_%Y%m%d_%H%M%S")
            save_folder = os.path.join(save_folder, stamp)

        config = Config(
            mode="acquire",
            moku_ip=values["moku_ip"].strip(),
            platform_id=4,
            mokucli_exe=values["mokucli"].strip(),
            output_folder=save_folder,
            pulsewidths_us=build_logspace_pulsewidths_us(state),
            duty_percent=float(values["duty_percent"]),
            amplitude_vpp=float(values["amplitude_vpp"]),
            offset_v=float(values["offset_v"]),
            num_frames_per_width=int(values["num_frames_per_width"]),
            num_periods_to_capture=float(values["num_periods_to_capture"]),
            settle_time_s=float(values["settle_time_s"]),
            frontend_channel=3,
            frontend_impedance="50Ohm",
            frontend_coupling="DC",
            frontend_attenuation="0dB",
            output_gain_db="14dB",
            trigger_source=values["trigger_source"].strip(),
            trigger_level_v=float(values["trigger_level"]),
            trigger_edge=values["trigger_edge"].strip(),
            acquisition_mode=values["acquisition_mode"].strip(),
            plot_raw_traces=values["plot_raw_traces"],
            keep_li_files=values["keep_li_files"],
            keep_npy_files=values["keep_npy_files"],
        )

        state["worker_log"]("Mode: acquire")
        state["worker_log"](f"Save folder: {config.output_folder}")
        run_acquisition(config, logger=state["worker_log"])

    elif mode == "both":
        save_folder = values["output_folder"].strip()
        if values["timestamped_subfolder"]:
            stamp = time.strftime("run_%Y%m%d_%H%M%S")
            save_folder = os.path.join(save_folder, stamp)

        config = Config(
            mode="both",
            x_axis=values["x_axis"].strip(),
            default_duty_fraction=0.01,
            max_harmonic=int(values["max_harmonic"]),
            main_fft_max_harmonics=parse_int_list(values["main_fft_harmonics"]),
            diagnostic_harmonics=parse_int_list(values["diagnostic_harmonics"]),
            n_spectrum_pw=int(values["n_spectrum_pw"]),
            save_csv=values["save_csv"],
            include_ls_trast=values["include_ls_trast"],
            moku_ip=values["moku_ip"].strip(),
            platform_id=4,
            mokucli_exe=values["mokucli"].strip(),
            output_folder=save_folder,
            pulsewidths_us=build_logspace_pulsewidths_us(state),
            duty_percent=float(values["duty_percent"]),
            amplitude_vpp=float(values["amplitude_vpp"]),
            offset_v=float(values["offset_v"]),
            num_frames_per_width=int(values["num_frames_per_width"]),
            num_periods_to_capture=float(values["num_periods_to_capture"]),
            settle_time_s=float(values["settle_time_s"]),
            frontend_channel=3,
            frontend_impedance="50Ohm",
            frontend_coupling="DC",
            frontend_attenuation="0dB",
            output_gain_db="14dB",
            trigger_source=values["trigger_source"].strip(),
            trigger_level_v=float(values["trigger_level"]),
            trigger_edge=values["trigger_edge"].strip(),
            acquisition_mode=values["acquisition_mode"].strip(),
            plot_raw_traces=values["plot_raw_traces"],
            keep_li_files=values["keep_li_files"],
            keep_npy_files=values["keep_npy_files"],
        )

        state["worker_log"]("Mode: both")
        acquired_folder = run_acquisition(config, logger=state["worker_log"])
        config.folder = acquired_folder
        run_analysis(config, logger=state["worker_log"])

    else:
        raise ValueError(f"Unsupported mode: {mode}")

def on_run(state):
    try:
        values = collect_gui_values(state)
        errors = validate_gui_inputs(values)
        state["validation_var"].set(" | ".join(errors) if errors else "")

        if errors:
            raise ValueError("Please fix the validation warnings before running.")

        if state["worker"].is_running:
            raise RuntimeError("A task is already running.")

        state["status_var"].set("Running...")
        state["clear_log"]()
        state["clear_treeview"](state["acq_tree"])
        state["clear_treeview"](state["trast_tree"])

        if "set_controls_enabled" in state:
            state["set_controls_enabled"](False)

        state["worker_log"] = make_worker_logger(state)
        state["worker"].start(run_task_in_background, state)
        process_worker_queue(state)

    except Exception as e:
        state["status_var"].set("Error.")
        state["append_log"](f"ERROR: {e}")
        messagebox.showerror("Error", str(e))