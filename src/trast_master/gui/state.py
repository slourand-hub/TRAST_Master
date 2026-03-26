import tkinter as tk
from trast_master.gui.worker import GuiWorker

def create_gui_state():
    root = tk.Tk()
    root.title("TRAST Master GUI")
    root.geometry("1200x850")
    root.minsize(950, 700)

    state = {
        "mode_var": tk.StringVar(value="analyze"),

        "analysis_target_var": tk.StringVar(
            value=r"C:\Users\slour\OneDrive\Desktop\Master Thesis\LabMain\20260325_fftTRAST\Test6"
        ),
        "output_folder_var": tk.StringVar(
            value=r"C:\Users\slour\OneDrive\Desktop\Master Thesis\LabMain\20260325_fftTRAST\Test6"
        ),

        "moku_ip_var": tk.StringVar(value="169.254.36.39"),
        "mokucli_var": tk.StringVar(value=r"C:\Program Files\Liquid Instruments\Moku CLI\mokucli.exe"),

        "log_pw_start_exp_var": tk.StringVar(value="-7"),
        "log_pw_end_exp_var": tk.StringVar(value="-3"),
        "log_pw_num_points_var": tk.StringVar(value="30"),
        "logspace_preview_var": tk.StringVar(value=""),

        "duty_percent_var": tk.StringVar(value="1.0"),
        "amplitude_var": tk.StringVar(value="1.0"),
        "offset_var": tk.StringVar(value="0.5"),
        "num_frames_var": tk.StringVar(value="1"),
        "num_periods_var": tk.StringVar(value="20.0"),
        "settle_time_var": tk.StringVar(value="0.1"),

        "trigger_source_var": tk.StringVar(value="ChannelA"),
        "trigger_level_var": tk.StringVar(value="0.2"),
        "trigger_edge_var": tk.StringVar(value="Rising"),
        "acquisition_mode_var": tk.StringVar(value="Normal"),

        "xaxis_var": tk.StringVar(value="pulse_width_us"),
        "max_harmonic_var": tk.StringVar(value="200"),
        "main_harmonics_var": tk.StringVar(value="1,5,10,20"),
        "diagnostic_harmonics_var": tk.StringVar(value="1,2,3,5,10,20"),
        "n_spectrum_pw_var": tk.StringVar(value="5"),

        "plot_raw_var": tk.BooleanVar(value=False),
        "save_csv_var": tk.BooleanVar(value=False),
        "include_ls_var": tk.BooleanVar(value=False),
        "keep_li_var": tk.BooleanVar(value=True),
        "keep_npy_var": tk.BooleanVar(value=True),
        "show_advanced_var": tk.BooleanVar(value=False),
        "timestamped_subfolder_var": tk.BooleanVar(value=True),
        "show_log_var": tk.BooleanVar(value=True),

        "status_var": tk.StringVar(value="Ready."),
        "validation_var": tk.StringVar(value=""),
        "summary_var": tk.StringVar(value=""),
        "acq_error_var": tk.StringVar(value=""),
        "preset_name_var": tk.StringVar(value="Preset: default"),

        "worker": GuiWorker(),
    }

    return root, state