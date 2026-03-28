import os
import socket
import subprocess
import sys
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
from trast_master.analysis.run_analysis_core import compute_analysis_results

def update_hardware_status_preview(state):
    values = collect_gui_values(state)

    ip = values["moku_ip"].strip() or "(none)"
    trig_src = values["trigger_source"].strip() or "(none)"
    trig_level = values["trigger_level"].strip() or "(none)"
    trig_edge = values["trigger_edge"].strip() or "(none)"
    acq_mode = values["acquisition_mode"].strip() or "(none)"
    duty = values["duty_percent"].strip() or "(none)"
    amp = values["amplitude_vpp"].strip() or "(none)"
    offset = values["offset_v"].strip() or "(none)"

    state["hw_connection_var"].set(f"Moku IP: {ip} | Connection: not tested")
    state["hw_trigger_var"].set(f"Trigger: {trig_src}, {trig_edge}, level = {trig_level} V")
    state["hw_acquisition_var"].set(f"Acquisition mode: {acq_mode}")
    state["hw_output_var"].set(f"Waveform: duty = {duty}% | amplitude = {amp} Vpp | offset = {offset} V")


def on_test_connection(state):
    ip = state["moku_ip_var"].get().strip()
    if not ip:
        messagebox.showerror("Connection test", "Moku IP is empty.")
        return

    state["status_var"].set("Testing connection...")
    state["hw_connection_var"].set(f"Moku IP: {ip} | Connection: testing...")

    try:
        # Cross-platform single ping
        if sys.platform.startswith("win"):
            cmd = ["ping", "-n", "1", "-w", "1200", ip]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", ip]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            state["hw_connection_var"].set(f"Moku IP: {ip} | Connection: reachable")
            state["status_var"].set("Connection test OK.")
        else:
            state["hw_connection_var"].set(f"Moku IP: {ip} | Connection: unreachable")
            state["status_var"].set("Connection test failed.")
    except Exception as e:
        state["hw_connection_var"].set(f"Moku IP: {ip} | Connection test error: {e}")
        state["status_var"].set("Connection test error.")

def _set_worker_status(state, text: str):
    state["worker"].queue.put(("status", str(text)))


def _set_worker_progress(state, value: float, stage: str, detail: str):
    state["worker"].queue.put(("progress", {
        "value": float(value),
        "stage": str(stage),
        "detail": str(detail),
    }))


def on_stop_request(state):
    if not state["worker"].is_running:
        return

    state["worker"].request_stop()
    state["append_log"]("Stop requested by user. Waiting for safe stop point...")
    state["status_var"].set("Stopping...")
    state["progress_stage_var"].set("Stopping")
    state["progress_detail_var"].set("Waiting for acquisition/analysis loop to stop safely.")
    state["run_controls_hint_var"].set("Stop requested. Please wait.")

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
    update_hardware_status_preview(state)

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

def _build_acquisition_config(state, values, mode: str, save_folder: str) -> Config:
    return Config(
        mode=mode,
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
def run_task_in_background(state):
    values = collect_gui_values(state)
    mode = values["mode"].strip()

    def check_stop():
        if state["worker"].stop_requested:
            raise RuntimeError("Run stopped by user.")

    if mode == "analyze":
        _set_worker_status(state, "Running analysis...")
        _set_worker_progress(state, 5, "Preparing analysis", "Validating analysis inputs.")
        check_stop()

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
        _set_worker_progress(state, 20, "Scanning data", "Finding NPZ files and summarizing acquisitions.")
        check_stop()

        results = compute_analysis_results(config, logger=state["worker_log"])
        _set_worker_progress(state, 75, "Preparing outputs", "Sending tables and plots to GUI.")
        check_stop()

        acq_cols = [
            "filename",
            "pulse_width_ns",
            "f0_hz",
            "n_samples",
            "dt_mean_s",
            "T_obs_s",
            "T_expected_s",
            "t_obs_vs_expected_relerr",
        ]
        acq_cols = [c for c in acq_cols if c in results["acq_df"].columns]

        state["worker"].queue.put(("tables", {
            "acq_df": results["acq_df"][acq_cols],
            "trast_df": results["preview_df"],
        }))

        if config.save_csv:
            out_csv = os.path.join(config.folder, "trast_output_raw.csv")
            results["df"].to_csv(out_csv, index=False)
            state["worker_log"](f"Saved CSV: {out_csv}")

            out_csv_acq = os.path.join(config.folder, "acquisition_summary.csv")
            results["acq_df"].to_csv(out_csv_acq, index=False)
            state["worker_log"](f"Saved CSV: {out_csv_acq}")

        state["worker"].queue.put(("plots", {
            "config": config,
            "df": results["df"],
        }))

        _set_worker_progress(state, 100, "Done", "Analysis completed.")

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

        _set_worker_status(state, "Running acquisition...")
        _set_worker_progress(state, 2, "Preparing acquisition", "Connecting and preparing instruments.")
        check_stop()

        state["worker_log"]("Mode: both")
        acquired_folder = run_acquisition(
            config,
            logger=state["worker_log"],
            stop_event=state["worker"].stop_event,
            progress_cb=lambda value, stage, detail: _set_worker_progress(state, value, stage, detail),
        )

        check_stop()

        config.folder = acquired_folder
        _set_worker_status(state, "Running analysis...")
        _set_worker_progress(state, 82, "Analyzing acquired data", f"Folder: {acquired_folder}")
        state["worker_log"]("Plot rendering is disabled during background GUI analysis for stability.")

        run_analysis(
            config,
            logger=state["worker_log"],
            block_on_plots=False,
            generate_plots=False,
        )

        _set_worker_progress(state, 100, "Done", "Acquisition and analysis completed.")

    elif mode == "acquire":
        save_folder = values["output_folder"].strip()
        if values["timestamped_subfolder"]:
            stamp = time.strftime("run_%Y%m%d_%H%M%S")
            save_folder = os.path.join(save_folder, stamp)

        config = Config(
            mode="acquire",
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

        _set_worker_status(state, "Running acquisition...")
        _set_worker_progress(state, 2, "Preparing acquisition", "Connecting and preparing instruments.")

        run_acquisition(
            config,
            logger=state["worker_log"],
            stop_event=state["worker"].stop_event,
            progress_cb=lambda value, stage, detail: _set_worker_progress(state, value, stage, detail),
        )

        _set_worker_progress(state, 100, "Done", "Acquisition completed.")

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

        state["progress_value_var"].set(0.0)
        state["progress_stage_var"].set("Starting")
        state["progress_detail_var"].set("Launching worker thread.")
        state["run_controls_hint_var"].set("Use Stop to request a safe stop.")

        if "set_controls_enabled" in state:
            state["set_controls_enabled"](False)

        if "stop_btn" in state:
            state["stop_btn"].configure(state="normal")

        state["worker_log"] = make_worker_logger(state)
        state["worker"].start(run_task_in_background, state)
        process_worker_queue(state)

    except Exception as e:
        state["status_var"].set("Error.")
        state["append_log"](f"ERROR: {e}")
        messagebox.showerror("Error", str(e))
