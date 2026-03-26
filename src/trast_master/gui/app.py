from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from trast_master.gui.state import create_gui_state
from trast_master.gui.tables import clear_treeview, make_treeview_with_scrollbars
from trast_master.gui.logging_utils import append_log, clear_log
from trast_master.gui.callbacks import (
    on_run,
    preview_run,
    refresh_gui_state,
    browse_analysis_file,
    browse_analysis_folder,
    browse_output_folder,
)
from trast_master.gui.presets import save_preset, load_preset


def launch_gui():
    root, state = create_gui_state()
    state["root"] = root

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    outer = ttk.Frame(root, padding=10)
    outer.grid(row=0, column=0, sticky="nsew")
    outer.columnconfigure(0, weight=1)
    outer.rowconfigure(2, weight=1)

    interactive_widgets = []

    def register_widget(widget):
        interactive_widgets.append(widget)
        return widget

    def set_controls_enabled(enabled: bool):
        normal_state = "normal" if enabled else "disabled"
        combo_state = "readonly" if enabled else "disabled"

        for widget in interactive_widgets:
            try:
                if isinstance(widget, ttk.Combobox):
                    widget.configure(state=combo_state)
                else:
                    widget.configure(state=normal_state)
            except Exception:
                pass
    # Header
    header = ttk.LabelFrame(outer, text="TRAST Master", padding=10)
    header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    header.columnconfigure(6, weight=1)

    ttk.Label(header, text="Mode").grid(row=0, column=0, padx=(0, 8), sticky="w")
    mode_combo = register_widget(ttk.Combobox(
        header,
        textvariable=state["mode_var"],
        values=["acquire", "analyze", "both"],
        state="readonly",
        width=16,
    ))
    mode_combo.grid(row=0, column=1, sticky="w")

    ttk.Checkbutton(header, text="Show advanced", variable=state["show_advanced_var"]).grid(
        row=0, column=2, padx=(16, 8), sticky="w"
    )

    save_btn = register_widget(ttk.Button(header, text="Save preset", command=lambda: save_preset(state)))
    save_btn.grid(row=0, column=3, padx=4)

    load_btn = register_widget(ttk.Button(header, text="Load preset", command=lambda: load_preset(state)))
    load_btn.grid(row=0, column=4, padx=4)

    preview_btn = register_widget(ttk.Button(header, text="Preview", command=lambda: preview_run(state)))
    preview_btn.grid(row=0, column=5, padx=4)

    ttk.Label(header, textvariable=state["status_var"]).grid(row=0, column=6, sticky="e", padx=(8, 8))
    ttk.Label(header, textvariable=state["preset_name_var"]).grid(row=1, column=0, columnspan=7, sticky="w", pady=(8, 0))

    # Top content
    top = ttk.Frame(outer)
    top.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    top.columnconfigure(0, weight=1)
    top.columnconfigure(1, weight=1)

    left = ttk.Frame(top)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    left.columnconfigure(0, weight=1)

    right = ttk.Frame(top)
    right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
    right.columnconfigure(0, weight=1)

    # Paths
    paths_frame = ttk.LabelFrame(left, text="Paths", padding=10)
    paths_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    paths_frame.columnconfigure(1, weight=1)

    analysis_target_row = ttk.Frame(paths_frame)
    analysis_target_row.grid(row=0, column=0, columnspan=3, sticky="ew", pady=4)
    analysis_target_row.columnconfigure(1, weight=1)

    ttk.Label(analysis_target_row, text="Analysis target").grid(row=0, column=0, sticky="w", padx=(0, 8))
    ttk.Entry(analysis_target_row, textvariable=state["analysis_target_var"]).grid(row=0, column=1, sticky="ew", padx=(0, 6))
    ttk.Button(analysis_target_row, text="Browse file", command=lambda: browse_analysis_file(state)).grid(row=0, column=2, padx=(0, 4))
    ttk.Button(analysis_target_row, text="Browse folder", command=lambda: browse_analysis_folder(state)).grid(row=0, column=3)

    output_folder_row = ttk.Frame(paths_frame)
    output_folder_row.grid(row=1, column=0, columnspan=3, sticky="ew", pady=4)
    output_folder_row.columnconfigure(1, weight=1)

    ttk.Label(output_folder_row, text="Save folder").grid(row=0, column=0, sticky="w", padx=(0, 8))
    ttk.Entry(output_folder_row, textvariable=state["output_folder_var"]).grid(row=0, column=1, sticky="ew", padx=(0, 6))
    ttk.Button(output_folder_row, text="Browse", command=lambda: browse_output_folder(state)).grid(row=0, column=2)

    timestamp_row = ttk.Frame(paths_frame)
    timestamp_row.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(2, 0))
    ttk.Checkbutton(
        timestamp_row,
        text="Create timestamped subfolder for acquisition",
        variable=state["timestamped_subfolder_var"],
    ).grid(row=0, column=0, sticky="w")

    # Acquisition
    acquisition_frame = ttk.LabelFrame(left, text="Acquisition Settings", padding=10)
    acquisition_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    acquisition_frame.columnconfigure(0, weight=1)

    sweep_frame = ttk.LabelFrame(acquisition_frame, text="Sweep", padding=8)
    sweep_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))

    ttk.Label(sweep_frame, text="Start exp (s)").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Entry(sweep_frame, textvariable=state["log_pw_start_exp_var"], width=10).grid(row=0, column=1, sticky="w", pady=3)

    ttk.Label(sweep_frame, text="End exp (s)").grid(row=0, column=2, sticky="w", padx=(16, 8), pady=3)
    ttk.Entry(sweep_frame, textvariable=state["log_pw_end_exp_var"], width=10).grid(row=0, column=3, sticky="w", pady=3)

    ttk.Label(sweep_frame, text="Points").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Entry(sweep_frame, textvariable=state["log_pw_num_points_var"], width=10).grid(row=1, column=1, sticky="w", pady=3)

    ttk.Label(sweep_frame, text="Frames").grid(row=1, column=2, sticky="w", padx=(16, 8), pady=3)
    ttk.Entry(sweep_frame, textvariable=state["num_frames_var"], width=10).grid(row=1, column=3, sticky="w", pady=3)

    ttk.Label(sweep_frame, text="Periods").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Entry(sweep_frame, textvariable=state["num_periods_var"], width=10).grid(row=2, column=1, sticky="w", pady=3)

    ttk.Label(sweep_frame, text="Settle time (s)").grid(row=2, column=2, sticky="w", padx=(16, 8), pady=3)
    ttk.Entry(sweep_frame, textvariable=state["settle_time_var"], width=10).grid(row=2, column=3, sticky="w", pady=3)

    ttk.Label(sweep_frame, textvariable=state["logspace_preview_var"]).grid(row=3, column=0, columnspan=4, sticky="w", pady=(4, 0))

    wg_frame = ttk.LabelFrame(acquisition_frame, text="Waveform", padding=8)
    wg_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))

    ttk.Label(wg_frame, text="Duty %").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Entry(wg_frame, textvariable=state["duty_percent_var"], width=10).grid(row=0, column=1, sticky="w", pady=3)

    ttk.Label(wg_frame, text="Amplitude Vpp").grid(row=0, column=2, sticky="w", padx=(16, 8), pady=3)
    ttk.Entry(wg_frame, textvariable=state["amplitude_var"], width=10).grid(row=0, column=3, sticky="w", pady=3)

    ttk.Label(wg_frame, text="Offset V").grid(row=0, column=4, sticky="w", padx=(16, 8), pady=3)
    ttk.Entry(wg_frame, textvariable=state["offset_var"], width=10).grid(row=0, column=5, sticky="w", pady=3)

    scope_frame = ttk.LabelFrame(acquisition_frame, text="Oscilloscope", padding=8)
    scope_frame.grid(row=2, column=0, sticky="ew")

    ttk.Label(scope_frame, text="Trigger source").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Combobox(scope_frame, textvariable=state["trigger_source_var"], values=["ChannelA", "ChannelB"], state="readonly", width=12).grid(row=0, column=1, sticky="w", pady=3)

    ttk.Label(scope_frame, text="Trigger level").grid(row=0, column=2, sticky="w", padx=(16, 8), pady=3)
    ttk.Entry(scope_frame, textvariable=state["trigger_level_var"], width=10).grid(row=0, column=3, sticky="w", pady=3)

    ttk.Label(scope_frame, text="Trigger edge").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Combobox(scope_frame, textvariable=state["trigger_edge_var"], values=["Rising", "Falling"], state="readonly", width=12).grid(row=1, column=1, sticky="w", pady=3)

    ttk.Label(scope_frame, text="Acquisition mode").grid(row=1, column=2, sticky="w", padx=(16, 8), pady=3)
    ttk.Combobox(scope_frame, textvariable=state["acquisition_mode_var"], values=["Normal", "Precision"], state="readonly", width=12).grid(row=1, column=3, sticky="w", pady=3)

    ttk.Label(acquisition_frame, textvariable=state["acq_error_var"], foreground="firebrick").grid(row=3, column=0, sticky="w", pady=(6, 0))

    advanced_frame = ttk.LabelFrame(left, text="Advanced", padding=10)
    advanced_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
    advanced_frame.columnconfigure(1, weight=1)

    ttk.Label(advanced_frame, text="Moku IP").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Entry(advanced_frame, textvariable=state["moku_ip_var"]).grid(row=0, column=1, sticky="ew", pady=3)

    ttk.Label(advanced_frame, text="Moku CLI").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Entry(advanced_frame, textvariable=state["mokucli_var"]).grid(row=1, column=1, sticky="ew", pady=3)

    # Analysis
    analysis_frame = ttk.LabelFrame(right, text="Analysis Settings", padding=10)
    analysis_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    analysis_frame.columnconfigure(1, weight=1)

    ttk.Label(analysis_frame, text="X axis").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Combobox(analysis_frame, textvariable=state["xaxis_var"], values=["pulse_width_ns", "pulse_width_us", "pulse_width_ms", "log_pw_s"], state="readonly", width=18).grid(row=0, column=1, sticky="w", pady=3)

    ttk.Label(analysis_frame, text="Max harmonic").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Entry(analysis_frame, textvariable=state["max_harmonic_var"], width=12).grid(row=1, column=1, sticky="w", pady=3)

    ttk.Label(analysis_frame, text="Main FFT harmonics").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Entry(analysis_frame, textvariable=state["main_harmonics_var"]).grid(row=2, column=1, sticky="ew", pady=3)

    ttk.Label(analysis_frame, text="Diagnostic harmonics").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Entry(analysis_frame, textvariable=state["diagnostic_harmonics_var"]).grid(row=3, column=1, sticky="ew", pady=3)

    ttk.Label(analysis_frame, text="Number of spectra").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=3)
    ttk.Entry(analysis_frame, textvariable=state["n_spectrum_pw_var"], width=12).grid(row=4, column=1, sticky="w", pady=3)

    options_frame = ttk.LabelFrame(right, text="Options", padding=10)
    options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    options_frame.columnconfigure(0, weight=1)
    options_frame.columnconfigure(1, weight=1)

    acquisition_options_frame = ttk.Frame(options_frame)
    acquisition_options_frame.grid(row=0, column=0, sticky="nw", padx=(0, 20))

    ttk.Checkbutton(acquisition_options_frame, text="Plot raw traces during acquisition", variable=state["plot_raw_var"]).grid(row=0, column=0, sticky="w", pady=3)
    ttk.Checkbutton(acquisition_options_frame, text="Keep .li files", variable=state["keep_li_var"]).grid(row=1, column=0, sticky="w", pady=3)
    ttk.Checkbutton(acquisition_options_frame, text="Keep .npy files", variable=state["keep_npy_var"]).grid(row=2, column=0, sticky="w", pady=3)

    analysis_options_frame = ttk.Frame(options_frame)
    analysis_options_frame.grid(row=0, column=1, sticky="nw")

    ttk.Checkbutton(analysis_options_frame, text="Save CSV during analysis", variable=state["save_csv_var"]).grid(row=0, column=0, sticky="w", pady=3)
    ttk.Checkbutton(analysis_options_frame, text="Include LS TRAST", variable=state["include_ls_var"]).grid(row=1, column=0, sticky="w", pady=3)

    summary_frame = ttk.LabelFrame(right, text="Run Summary", padding=10)
    summary_frame.grid(row=2, column=0, sticky="ew")
    summary_frame.columnconfigure(0, weight=1)

    ttk.Label(summary_frame, textvariable=state["summary_var"], wraplength=450, justify="left").grid(row=0, column=0, sticky="w")
    ttk.Label(summary_frame, textvariable=state["validation_var"], foreground="firebrick", wraplength=450, justify="left").grid(row=1, column=0, sticky="w", pady=(6, 0))
    ttk.Checkbutton(summary_frame, text="Show run log", variable=state["show_log_var"]).grid(row=2, column=0, sticky="w", pady=(8, 0))

    # Results
    results_frame = ttk.LabelFrame(outer, text="Results", padding=10)
    results_frame.grid(row=2, column=0, sticky="nsew")
    results_frame.columnconfigure(0, weight=1)
    results_frame.rowconfigure(0, weight=1)

    notebook = ttk.Notebook(results_frame)
    notebook.grid(row=0, column=0, sticky="nsew")

    log_tab = ttk.Frame(notebook)
    acq_tab = ttk.Frame(notebook)
    trast_tab = ttk.Frame(notebook)

    notebook.add(acq_tab, text="Acquisition Table")
    notebook.add(trast_tab, text="TRAST Table")
    notebook.add(log_tab, text="Log")

    log_tab.columnconfigure(0, weight=1)
    log_tab.rowconfigure(0, weight=1)
    log_text = ScrolledText(log_tab, height=10, wrap="word", state="disabled")
    log_text.grid(row=0, column=0, sticky="nsew")

    acq_frame, acq_tree = make_treeview_with_scrollbars(acq_tab)
    acq_frame.grid(row=0, column=0, sticky="nsew")
    acq_tab.columnconfigure(0, weight=1)
    acq_tab.rowconfigure(0, weight=1)

    trast_frame, trast_tree = make_treeview_with_scrollbars(trast_tab)
    trast_frame.grid(row=0, column=0, sticky="nsew")
    trast_tab.columnconfigure(0, weight=1)
    trast_tab.rowconfigure(0, weight=1)

    # Actions
    actions = ttk.Frame(outer)
    actions.grid(row=3, column=0, sticky="ew", pady=(8, 0))
    actions.columnconfigure(10, weight=1)


    run_btn = register_widget(ttk.Button(actions, text="Run", command=lambda: on_run(state)))
    run_btn.grid(row=0, column=0, padx=(0, 6))

    preview_btn2 = register_widget(ttk.Button(actions, text="Preview", command=lambda: preview_run(state)))
    preview_btn2.grid(row=0, column=1)

    # Shared runtime refs
    state["append_log"] = lambda msg: append_log(log_text, root, msg)
    state["clear_log"] = lambda: clear_log(log_text)
    state["clear_treeview"] = clear_treeview
    state["acq_tree"] = acq_tree
    state["trast_tree"] = trast_tree
    state["notebook"] = notebook
    state["log_tab"] = log_tab

    state["analysis_target_row"] = analysis_target_row
    state["output_folder_row"] = output_folder_row
    state["timestamp_row"] = timestamp_row
    state["acquisition_frame"] = acquisition_frame
    state["acquisition_options_frame"] = acquisition_options_frame
    state["analysis_options_frame"] = analysis_options_frame
    state["analysis_frame"] = analysis_frame
    state["summary_frame"] = summary_frame
    state["advanced_frame"] = advanced_frame

    state["set_controls_enabled"] = set_controls_enabled
    state["interactive_widgets"] = interactive_widgets

    # Bindings
    def _refresh(*_args):
        refresh_gui_state(state)

    state["mode_var"].trace_add("write", _refresh)
    state["show_advanced_var"].trace_add("write", _refresh)
    state["log_pw_start_exp_var"].trace_add("write", _refresh)
    state["log_pw_end_exp_var"].trace_add("write", _refresh)
    state["log_pw_num_points_var"].trace_add("write", _refresh)
    state["num_frames_var"].trace_add("write", _refresh)
    state["duty_percent_var"].trace_add("write", _refresh)
    state["max_harmonic_var"].trace_add("write", _refresh)
    state["main_harmonics_var"].trace_add("write", _refresh)
    state["diagnostic_harmonics_var"].trace_add("write", _refresh)
    state["output_folder_var"].trace_add("write", _refresh)
    state["analysis_target_var"].trace_add("write", _refresh)
    state["trigger_level_var"].trace_add("write", _refresh)
    state["show_log_var"].trace_add("write", _refresh)

    refresh_gui_state(state)
    root.mainloop()