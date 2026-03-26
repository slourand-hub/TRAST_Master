import numpy as np


def parse_int_list(text: str):
    text = text.strip()
    if not text:
        return []
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def build_logspace_pulsewidths_us(state: dict):
    start_exp = float(state["log_pw_start_exp_var"].get())
    end_exp = float(state["log_pw_end_exp_var"].get())
    n_points = int(state["log_pw_num_points_var"].get())

    if n_points < 1:
        raise ValueError("Number of pulse-width points must be >= 1.")
    if start_exp >= end_exp:
        raise ValueError("Start exponent must be smaller than end exponent.")

    pulse_widths_s = np.logspace(start_exp, end_exp, n_points)
    return (pulse_widths_s * 1e6).tolist()


def collect_gui_values(state: dict):
    return {
        "mode": state["mode_var"].get(),
        "analysis_target": state["analysis_target_var"].get(),
        "output_folder": state["output_folder_var"].get(),
        "moku_ip": state["moku_ip_var"].get(),
        "mokucli": state["mokucli_var"].get(),
        "log_pw_start_exp": state["log_pw_start_exp_var"].get(),
        "log_pw_end_exp": state["log_pw_end_exp_var"].get(),
        "log_pw_num_points": state["log_pw_num_points_var"].get(),
        "duty_percent": state["duty_percent_var"].get(),
        "amplitude_vpp": state["amplitude_var"].get(),
        "offset_v": state["offset_var"].get(),
        "num_frames_per_width": state["num_frames_var"].get(),
        "num_periods_to_capture": state["num_periods_var"].get(),
        "settle_time_s": state["settle_time_var"].get(),
        "x_axis": state["xaxis_var"].get(),
        "max_harmonic": state["max_harmonic_var"].get(),
        "main_fft_harmonics": state["main_harmonics_var"].get(),
        "diagnostic_harmonics": state["diagnostic_harmonics_var"].get(),
        "n_spectrum_pw": state["n_spectrum_pw_var"].get(),
        "plot_raw_traces": state["plot_raw_var"].get(),
        "save_csv": state["save_csv_var"].get(),
        "include_ls_trast": state["include_ls_var"].get(),
        "keep_li_files": state["keep_li_var"].get(),
        "keep_npy_files": state["keep_npy_var"].get(),
        "show_advanced": state["show_advanced_var"].get(),
        "timestamped_subfolder": state["timestamped_subfolder_var"].get(),
        "trigger_source": state["trigger_source_var"].get(),
        "trigger_level": state["trigger_level_var"].get(),
        "trigger_edge": state["trigger_edge_var"].get(),
        "acquisition_mode": state["acquisition_mode_var"].get(),
    }


def validate_gui_inputs(values: dict):
    errors = []

    mode = values["mode"].strip()

    try:
        start_exp = float(values["log_pw_start_exp"])
        end_exp = float(values["log_pw_end_exp"])
        if start_exp >= end_exp:
            errors.append("Start exponent must be smaller than end exponent.")
    except Exception:
        errors.append("Invalid logspace exponents.")

    try:
        n_points = int(values["log_pw_num_points"])
        if n_points < 1:
            errors.append("Number of points must be at least 1.")
    except Exception:
        errors.append("Number of points must be an integer.")

    try:
        duty = float(values["duty_percent"])
        if duty <= 0:
            errors.append("Duty percent must be > 0.")
    except Exception:
        errors.append("Duty percent must be numeric.")

    try:
        frames = int(values["num_frames_per_width"])
        if frames < 1:
            errors.append("Frames per width must be at least 1.")
    except Exception:
        errors.append("Frames per width must be an integer.")

    try:
        max_h = int(values["max_harmonic"])
        main_h = parse_int_list(values["main_fft_harmonics"])
        diag_h = parse_int_list(values["diagnostic_harmonics"])

        if max_h < 1:
            errors.append("Max harmonic must be at least 1.")
        if main_h and max(main_h) > max_h:
            errors.append("Main FFT harmonics exceed max harmonic.")
        if diag_h and max(diag_h) > max_h:
            errors.append("Diagnostic harmonics exceed max harmonic.")
    except Exception:
        errors.append("Invalid harmonic settings.")

    if mode in ("acquire", "both"):
        if not values["output_folder"].strip():
            errors.append("Output folder is empty.")

    if mode == "analyze":
        if not values["analysis_target"].strip():
            errors.append("Analysis target is empty.")

    return errors