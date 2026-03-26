import json
import os
from tkinter import filedialog


from trast_master.gui.validation import collect_gui_values


def apply_gui_state(state: dict, values: dict):
    mapping = {
        "mode": "mode_var",
        "analysis_target": "analysis_target_var",
        "output_folder": "output_folder_var",
        "moku_ip": "moku_ip_var",
        "mokucli": "mokucli_var",
        "log_pw_start_exp": "log_pw_start_exp_var",
        "log_pw_end_exp": "log_pw_end_exp_var",
        "log_pw_num_points": "log_pw_num_points_var",
        "duty_percent": "duty_percent_var",
        "amplitude_vpp": "amplitude_var",
        "offset_v": "offset_var",
        "num_frames_per_width": "num_frames_var",
        "num_periods_to_capture": "num_periods_var",
        "settle_time_s": "settle_time_var",
        "x_axis": "xaxis_var",
        "max_harmonic": "max_harmonic_var",
        "main_fft_harmonics": "main_harmonics_var",
        "diagnostic_harmonics": "diagnostic_harmonics_var",
        "n_spectrum_pw": "n_spectrum_pw_var",
        "plot_raw_traces": "plot_raw_var",
        "save_csv": "save_csv_var",
        "include_ls_trast": "include_ls_var",
        "keep_li_files": "keep_li_var",
        "keep_npy_files": "keep_npy_var",
        "show_advanced": "show_advanced_var",
        "timestamped_subfolder": "timestamped_subfolder_var",
        "trigger_source": "trigger_source_var",
        "trigger_level": "trigger_level_var",
        "trigger_edge": "trigger_edge_var",
        "acquisition_mode": "acquisition_mode_var",
    }

    for key, var_name in mapping.items():
        if key in values:
            state[var_name].set(values[key])


def save_preset(state: dict):
    path = filedialog.asksaveasfilename(
        title="Save preset",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if not path:
        return

    values = collect_gui_values(state)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(values, f, indent=2)

    state["preset_name_var"].set(f"Preset: {os.path.basename(path)}")
    state["append_log"](f"Saved preset: {path}")


def load_preset(state: dict):
    path = filedialog.askopenfilename(
        title="Load preset",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if not path:
        return

    with open(path, "r", encoding="utf-8") as f:
        values = json.load(f)

    apply_gui_state(state, values)
    state["preset_name_var"].set(f"Preset: {os.path.basename(path)}")
    state["append_log"](f"Loaded preset: {path}")