from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from trast_master.gui.state import create_gui_state
from trast_master.gui.tables import clear_treeview, make_treeview_with_scrollbars
from trast_master.gui.logging_utils import append_log, clear_log
from trast_master.gui.callbacks import (
    on_run,
    on_stop_request,
    on_test_connection,
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
    outer.rowconfigure(1, weight=1)

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

        if "stop_btn" in state:
            state["stop_btn"].configure(state="normal" if not enabled else "disabled")

    # =========================================================
    # Header / command bar
    # =========================================================
    header = ttk.LabelFrame(outer, text="TRAST Master", padding=10)
    header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    header.columnconfigure(11, weight=1)

    ttk.Label(header, text="Mode").grid(row=0, column=0, padx=(0, 8), sticky="w")
    mode_combo = register_widget(ttk.Combobox(
        header,
        textvariable=state["mode_var"],
        values=["acquire", "analyze", "both"],
        state="readonly",
        width=14,
    ))
    mode_combo.grid(row=0, column=1, sticky="w")

    show_advanced_cb = register_widget(ttk.Checkbutton(
        header,
        text="Show advanced",
        variable=state["show_advanced_var"],
    ))
    show_advanced_cb.grid(row=0, column=2, padx=(16, 8), sticky="w")

    save_btn = register_widget(ttk.Button(header, text="Save preset", command=lambda: save_preset(state)))
    save_btn.grid(row=0, column=3, padx=4)

    load_btn = register_widget(ttk.Button(header, text="Load preset", command=lambda: load_preset(state)))
    load_btn.grid(row=0, column=4, padx=4)

    preview_btn = register_widget(ttk.Button(header, text="Preview", command=lambda: preview_run(state)))
    preview_btn.grid(row=0, column=5, padx=4)

    run_btn = ttk.Button(header, text="Run", command=lambda: on_run(state))
    run_btn.grid(row=0, column=6, padx=(16, 4))

    stop_btn = ttk.Button(header, text="Stop", command=lambda: on_stop_request(state), state="disabled")
    stop_btn.grid(row=0, column=7, padx=4)

    test_btn = ttk.Button(header, text="Test connection", command=lambda: on_test_connection(state))
    test_btn.grid(row=0, column=8, padx=(4, 8))

    more_results_btn = ttk.Button(header, text="More results", command=lambda: state["set_results_ratio"](0.45))
    more_results_btn.grid(row=0, column=9, padx=4)

    more_controls_btn = ttk.Button(header, text="More controls", command=lambda: state["set_results_ratio"](0.28))
    more_controls_btn.grid(row=0, column=10, padx=4)

    ttk.Label(header, textvariable=state["status_var"]).grid(row=0, column=11, sticky="e")
    ttk.Label(header, textvariable=state["preset_name_var"]).grid(row=1, column=0, columnspan=11, sticky="w", pady=(8, 0))

    state["stop_btn"] = stop_btn

    # =========================================================
    # Vertical splitter: top controls + bottom results
    # =========================================================
    content_pane = ttk.Panedwindow(outer, orient="vertical")
    content_pane.grid(row=1, column=0, sticky="nsew")

    top_frame = ttk.Frame(content_pane)
    top_frame.columnconfigure(0, weight=1)
    top_frame.columnconfigure(1, weight=1)

    results_frame = ttk.LabelFrame(content_pane, text="Results", padding=10)
    results_frame.columnconfigure(0, weight=1)
    results_frame.rowconfigure(1, weight=1)

    content_pane.add(top_frame, weight=4)
    content_pane.add(results_frame, weight=2)

    def set_results_ratio(ratio: float):
        root.update_idletasks()
        total_h = content_pane.winfo_height()
        if total_h <= 1:
            return

        min_top_h = 470
        min_results_h = 280

        requested_results_h = int(total_h * ratio)
        results_h = max(min_results_h, requested_results_h)

        max_results_h = max(min_results_h, total_h - min_top_h)
        results_h = min(results_h, max_results_h)

        top_h = total_h - results_h
        top_h = max(min_top_h, top_h)

        try:
            content_pane.sashpos(0, top_h)
        except Exception:
            pass

    # =========================================================
    # Top content: left workflow + right inspector tabs
    # =========================================================
    left = ttk.Frame(top_frame)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    left.columnconfigure(0, weight=1)

    right = ttk.Frame(top_frame)
    right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
    right.columnconfigure(0, weight=1)

    stage1_header = ttk.Label(left, textvariable=state["stage1_title_var"], font=("", 10, "bold"))
    stage1_header.grid(row=0, column=0, sticky="w", pady=(0, 6))

    stage2_header = ttk.Label(right, textvariable=state["stage2_title_var"], font=("", 10, "bold"))
    stage2_header.grid(row=0, column=0, sticky="w", pady=(0, 6))

    # =========================================================
    # Left side: acquisition workflow
    # =========================================================
    paths_frame = ttk.LabelFrame(left, text="Paths", padding=10)
    paths_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    paths_frame.columnconfigure(0, weight=1)

    analysis_target_row = ttk.Frame(paths_frame)
    analysis_target_row.grid(row=0, column=0, sticky="ew", pady=4)
    analysis_target_row.columnconfigure(1, weight=1)

    ttk.Label(analysis_target_row, text="Analysis target").grid(row=0, column=0, sticky="w", padx=(0, 8))
    analysis_target_entry = register_widget(ttk.Entry(analysis_target_row, textvariable=state["analysis_target_var"]))
    analysis_target_entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))
    browse_file_btn = register_widget(ttk.Button(analysis_target_row, text="Browse file", command=lambda: browse_analysis_file(state)))
    browse_file_btn.grid(row=0, column=2, padx=(0, 4))
    browse_folder_btn = register_widget(ttk.Button(analysis_target_row, text="Browse folder", command=lambda: browse_analysis_folder(state)))
    browse_folder_btn.grid(row=0, column=3)

    output_folder_row = ttk.Frame(paths_frame)
    output_folder_row.grid(row=1, column=0, sticky="ew", pady=4)
    output_folder_row.columnconfigure(1, weight=1)

    ttk.Label(output_folder_row, text="Output folder").grid(row=0, column=0, sticky="w", padx=(0, 8))
    output_folder_entry = register_widget(ttk.Entry(output_folder_row, textvariable=state["output_folder_var"]))
    output_folder_entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))
    browse_output_btn = register_widget(ttk.Button(output_folder_row, text="Browse", command=lambda: browse_output_folder(state)))
    browse_output_btn.grid(row=0, column=2)

    timestamp_row = ttk.Frame(paths_frame)
    timestamp_row.grid(row=2, column=0, sticky="ew", pady=(2, 0))
    timestamp_cb = register_widget(ttk.Checkbutton(
        timestamp_row,
        text="Create timestamped subfolder for acquisition",
        variable=state["timestamped_subfolder_var"],
    ))
    timestamp_cb.grid(row=0, column=0, sticky="w")

    acquisition_frame = ttk.LabelFrame(left, text="Acquisition Settings", padding=10)
    acquisition_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
    acquisition_frame.columnconfigure(0, weight=1)

    acq_notebook = ttk.Notebook(acquisition_frame)
    acq_notebook.grid(row=0, column=0, sticky="ew")

    sweep_tab = ttk.Frame(acq_notebook)
    waveform_tab = ttk.Frame(acq_notebook)
    oscilloscope_tab = ttk.Frame(acq_notebook)

    acq_notebook.add(sweep_tab, text="Sweep")
    acq_notebook.add(waveform_tab, text="Waveform")
    acq_notebook.add(oscilloscope_tab, text="Oscilloscope")

    # -------------------------
    # Sweep tab
    # -------------------------
    sweep_tab.columnconfigure(0, weight=1)
    sweep_frame = ttk.Frame(sweep_tab, padding=8)
    sweep_frame.grid(row=0, column=0, sticky="ew")

    ttk.Label(sweep_frame, text="Log10 start pulse width [s]").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
    pw_start_entry = register_widget(ttk.Entry(sweep_frame, textvariable=state["log_pw_start_exp_var"], width=10))
    pw_start_entry.grid(row=0, column=1, sticky="w", pady=3)

    ttk.Label(sweep_frame, text="Log10 end pulse width [s]").grid(row=0, column=2, sticky="w", padx=(16, 8), pady=3)
    pw_end_entry = register_widget(ttk.Entry(sweep_frame, textvariable=state["log_pw_end_exp_var"], width=10))
    pw_end_entry.grid(row=0, column=3, sticky="w", pady=3)

    ttk.Label(sweep_frame, text="Number of pulse widths").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
    pw_points_entry = register_widget(ttk.Entry(sweep_frame, textvariable=state["log_pw_num_points_var"], width=10))
    pw_points_entry.grid(row=1, column=1, sticky="w", pady=3)

    ttk.Label(sweep_frame, text="Frames per pulse width").grid(row=1, column=2, sticky="w", padx=(16, 8), pady=3)
    frames_entry = register_widget(ttk.Entry(sweep_frame, textvariable=state["num_frames_var"], width=10))
    frames_entry.grid(row=1, column=3, sticky="w", pady=3)

    ttk.Label(sweep_frame, text="Periods to capture").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=3)
    periods_entry = register_widget(ttk.Entry(sweep_frame, textvariable=state["num_periods_var"], width=10))
    periods_entry.grid(row=2, column=1, sticky="w", pady=3)

    ttk.Label(sweep_frame, text="Settle time (s)").grid(row=2, column=2, sticky="w", padx=(16, 8), pady=3)
    settle_entry = register_widget(ttk.Entry(sweep_frame, textvariable=state["settle_time_var"], width=10))
    settle_entry.grid(row=2, column=3, sticky="w", pady=3)

    ttk.Label(sweep_frame, textvariable=state["logspace_preview_var"]).grid(
        row=3, column=0, columnspan=4, sticky="w", pady=(6, 0)
    )

    # -------------------------
    # Waveform tab
    # -------------------------
    waveform_tab.columnconfigure(0, weight=1)
    wg_frame = ttk.Frame(waveform_tab, padding=8)
    wg_frame.grid(row=0, column=0, sticky="ew")

    ttk.Label(wg_frame, text="Duty %").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
    duty_entry = register_widget(ttk.Entry(wg_frame, textvariable=state["duty_percent_var"], width=10))
    duty_entry.grid(row=0, column=1, sticky="w", pady=3)

    ttk.Label(wg_frame, text="Amplitude Vpp").grid(row=0, column=2, sticky="w", padx=(16, 8), pady=3)
    amp_entry = register_widget(ttk.Entry(wg_frame, textvariable=state["amplitude_var"], width=10))
    amp_entry.grid(row=0, column=3, sticky="w", pady=3)

    ttk.Label(wg_frame, text="Offset V").grid(row=0, column=4, sticky="w", padx=(16, 8), pady=3)
    offset_entry = register_widget(ttk.Entry(wg_frame, textvariable=state["offset_var"], width=10))
    offset_entry.grid(row=0, column=5, sticky="w", pady=3)

    # -------------------------
    # Oscilloscope tab
    # -------------------------
    oscilloscope_tab.columnconfigure(0, weight=1)
    scope_frame = ttk.Frame(oscilloscope_tab, padding=8)
    scope_frame.grid(row=0, column=0, sticky="ew")

    ttk.Label(scope_frame, text="Trigger source").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
    trig_src_combo = register_widget(ttk.Combobox(
        scope_frame,
        textvariable=state["trigger_source_var"],
        values=["ChannelA", "ChannelB"],
        state="readonly",
        width=12,
    ))
    trig_src_combo.grid(row=0, column=1, sticky="w", pady=3)

    ttk.Label(scope_frame, text="Trigger level").grid(row=0, column=2, sticky="w", padx=(16, 8), pady=3)
    trig_level_entry = register_widget(ttk.Entry(scope_frame, textvariable=state["trigger_level_var"], width=10))
    trig_level_entry.grid(row=0, column=3, sticky="w", pady=3)

    ttk.Label(scope_frame, text="Trigger edge").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
    trig_edge_combo = register_widget(ttk.Combobox(
        scope_frame,
        textvariable=state["trigger_edge_var"],
        values=["Rising", "Falling"],
        state="readonly",
        width=12,
    ))
    trig_edge_combo.grid(row=1, column=1, sticky="w", pady=3)

    ttk.Label(scope_frame, text="Acquisition mode").grid(row=1, column=2, sticky="w", padx=(16, 8), pady=3)
    acq_mode_combo = register_widget(ttk.Combobox(
        scope_frame,
        textvariable=state["acquisition_mode_var"],
        values=["Normal", "Precision"],
        state="readonly",
        width=12,
    ))
    acq_mode_combo.grid(row=1, column=3, sticky="w", pady=3)

    ttk.Label(acquisition_frame, textvariable=state["acq_error_var"], foreground="firebrick").grid(
        row=1, column=0, sticky="w", pady=(6, 0)
    )



    # =========================================================
    # Right side: tabs
    # =========================================================
    inspector_notebook = ttk.Notebook(right)
    inspector_notebook.grid(row=1, column=0, sticky="nsew")

    analysis_tab = ttk.Frame(inspector_notebook)
    run_tab = ttk.Frame(inspector_notebook)
    hardware_tab = ttk.Frame(inspector_notebook)

    inspector_notebook.add(analysis_tab, text="Analysis")
    inspector_notebook.add(run_tab, text="Run")
    inspector_notebook.add(hardware_tab, text="Hardware")

    # Analysis tab
    analysis_tab.columnconfigure(0, weight=1)

    analysis_frame = ttk.LabelFrame(analysis_tab, text="Analysis Settings", padding=10)
    analysis_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    analysis_frame.columnconfigure(1, weight=1)

    ttk.Label(analysis_frame, text="X axis").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
    xaxis_combo = register_widget(ttk.Combobox(
        analysis_frame,
        textvariable=state["xaxis_var"],
        values=["pulse_width_ns", "pulse_width_us", "pulse_width_ms", "log_pw_s"],
        state="readonly",
        width=18,
    ))
    xaxis_combo.grid(row=0, column=1, sticky="w", pady=3)

    ttk.Label(analysis_frame, text="Max harmonic").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
    max_harm_entry = register_widget(ttk.Entry(analysis_frame, textvariable=state["max_harmonic_var"], width=12))
    max_harm_entry.grid(row=1, column=1, sticky="w", pady=3)

    ttk.Label(analysis_frame, text="Main FFT harmonics").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=3)
    main_harm_entry = register_widget(ttk.Entry(analysis_frame, textvariable=state["main_harmonics_var"]))
    main_harm_entry.grid(row=2, column=1, sticky="ew", pady=3)

    ttk.Label(analysis_frame, text="Diagnostic harmonics").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=3)
    diag_harm_entry = register_widget(ttk.Entry(analysis_frame, textvariable=state["diagnostic_harmonics_var"]))
    diag_harm_entry.grid(row=3, column=1, sticky="ew", pady=3)

    ttk.Label(analysis_frame, text="Number of spectra").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=3)
    n_spec_entry = register_widget(ttk.Entry(analysis_frame, textvariable=state["n_spectrum_pw_var"], width=12))
    n_spec_entry.grid(row=4, column=1, sticky="w", pady=3)

    options_frame = ttk.LabelFrame(analysis_tab, text="Options", padding=10)
    options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    options_frame.columnconfigure(0, weight=1)
    options_frame.columnconfigure(1, weight=1)

    acquisition_options_frame = ttk.Frame(options_frame)
    acquisition_options_frame.grid(row=0, column=0, sticky="nw", padx=(0, 20))

    plot_raw_cb = register_widget(ttk.Checkbutton(acquisition_options_frame, text="Plot raw traces during acquisition", variable=state["plot_raw_var"]))
    plot_raw_cb.grid(row=0, column=0, sticky="w", pady=3)

    keep_li_cb = register_widget(ttk.Checkbutton(acquisition_options_frame, text="Keep .li files", variable=state["keep_li_var"]))
    keep_li_cb.grid(row=1, column=0, sticky="w", pady=3)

    keep_npy_cb = register_widget(ttk.Checkbutton(acquisition_options_frame, text="Keep .npy files", variable=state["keep_npy_var"]))
    keep_npy_cb.grid(row=2, column=0, sticky="w", pady=3)

    analysis_options_frame = ttk.Frame(options_frame)
    analysis_options_frame.grid(row=0, column=1, sticky="nw")

    save_csv_cb = register_widget(ttk.Checkbutton(analysis_options_frame, text="Save CSV during analysis", variable=state["save_csv_var"]))
    save_csv_cb.grid(row=0, column=0, sticky="w", pady=3)

    include_ls_cb = register_widget(ttk.Checkbutton(analysis_options_frame, text="Include LS TRAST", variable=state["include_ls_var"]))
    include_ls_cb.grid(row=1, column=0, sticky="w", pady=3)

    # Run tab
    run_tab.columnconfigure(0, weight=1)

    summary_frame = ttk.LabelFrame(run_tab, text="Run Summary", padding=10)
    summary_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    summary_frame.columnconfigure(0, weight=1)

    ttk.Label(summary_frame, textvariable=state["summary_var"], wraplength=450, justify="left").grid(row=0, column=0, sticky="w")
    ttk.Label(summary_frame, textvariable=state["validation_var"], foreground="firebrick", wraplength=450, justify="left").grid(row=1, column=0, sticky="w", pady=(6, 0))
    show_log_cb = register_widget(ttk.Checkbutton(summary_frame, text="Show run log", variable=state["show_log_var"]))
    show_log_cb.grid(row=2, column=0, sticky="w", pady=(8, 0))

    progress_frame = ttk.LabelFrame(run_tab, text="Run Progress", padding=10)
    progress_frame.grid(row=1, column=0, sticky="ew")
    progress_frame.columnconfigure(0, weight=1)

    ttk.Label(progress_frame, textvariable=state["progress_stage_var"]).grid(row=0, column=0, sticky="w")
    ttk.Label(progress_frame, textvariable=state["progress_detail_var"], wraplength=450, justify="left").grid(row=1, column=0, sticky="w", pady=(4, 6))

    progress_bar = ttk.Progressbar(
        progress_frame,
        orient="horizontal",
        mode="determinate",
        maximum=100.0,
        variable=state["progress_value_var"],
    )
    progress_bar.grid(row=2, column=0, sticky="ew")

    ttk.Label(progress_frame, textvariable=state["run_controls_hint_var"]).grid(row=3, column=0, sticky="w", pady=(6, 0))

    # Hardware tab
    hardware_tab.columnconfigure(0, weight=1)

    hardware_frame = ttk.LabelFrame(hardware_tab, text="Hardware Status", padding=10)
    hardware_frame.grid(row=0, column=0, sticky="ew")
    hardware_frame.columnconfigure(0, weight=1)

    ttk.Label(hardware_frame, textvariable=state["hw_connection_var"], wraplength=450, justify="left").grid(row=0, column=0, sticky="w")
    ttk.Label(hardware_frame, textvariable=state["hw_trigger_var"], wraplength=450, justify="left").grid(row=1, column=0, sticky="w", pady=(4, 0))
    ttk.Label(hardware_frame, textvariable=state["hw_acquisition_var"], wraplength=450, justify="left").grid(row=2, column=0, sticky="w", pady=(4, 0))
    ttk.Label(hardware_frame, textvariable=state["hw_output_var"], wraplength=450, justify="left").grid(row=3, column=0, sticky="w", pady=(4, 8))

    test_connection_btn2 = ttk.Button(hardware_frame, text="Test connection", command=lambda: on_test_connection(state))
    test_connection_btn2.grid(row=4, column=0, sticky="w")

    advanced_frame = ttk.LabelFrame(hardware_tab, text="Advanced connection settings", padding=10)
    advanced_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
    advanced_frame.columnconfigure(1, weight=1)

    ttk.Label(advanced_frame, text="Moku IP").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
    moku_ip_entry = register_widget(ttk.Entry(advanced_frame, textvariable=state["moku_ip_var"]))
    moku_ip_entry.grid(row=0, column=1, sticky="ew", pady=3)

    ttk.Label(advanced_frame, text="Moku CLI").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
    mokucli_entry = register_widget(ttk.Entry(advanced_frame, textvariable=state["mokucli_var"]))
    mokucli_entry.grid(row=1, column=1, sticky="ew", pady=3)

    # =========================================================
    # Bottom results dock
    # =========================================================
    results_toolbar = ttk.Frame(results_frame)
    results_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    results_toolbar.columnconfigure(3, weight=1)

    ttk.Button(
        results_toolbar,
        text="More results",
        command=lambda: state["set_results_ratio"](0.45),
    ).grid(row=0, column=0, padx=(0, 6))

    ttk.Button(
        results_toolbar,
        text="Balanced",
        command=lambda: state["set_results_ratio"](0.40),
    ).grid(row=0, column=1, padx=(0, 6))

    ttk.Button(
        results_toolbar,
        text="More controls",
        command=lambda: state["set_results_ratio"](0.28),
    ).grid(row=0, column=2, padx=(0, 12))

    ttk.Label(
        results_toolbar,
        text="Use the tabs below for acquisition summary, TRAST metrics, and the run log.",
    ).grid(row=0, column=3, sticky="e")

    notebook = ttk.Notebook(results_frame)
    notebook.grid(row=1, column=0, sticky="nsew")

    acq_tab = ttk.Frame(notebook)
    trast_tab = ttk.Frame(notebook)
    log_tab = ttk.Frame(notebook)

    notebook.add(acq_tab, text="Acquisition")
    notebook.add(trast_tab, text="TRAST")
    notebook.add(log_tab, text="Run Log")

    acq_tab.columnconfigure(0, weight=1)
    acq_tab.rowconfigure(0, weight=1)

    trast_tab.columnconfigure(0, weight=1)
    trast_tab.rowconfigure(0, weight=1)

    log_tab.columnconfigure(0, weight=1)
    log_tab.rowconfigure(0, weight=1)

    acq_frame, acq_tree = make_treeview_with_scrollbars(acq_tab)
    acq_frame.grid(row=0, column=0, sticky="nsew")

    trast_frame, trast_tree = make_treeview_with_scrollbars(trast_tab)
    trast_frame.grid(row=0, column=0, sticky="nsew")

    log_text = ScrolledText(log_tab, height=16, wrap="word", state="disabled")
    log_text.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    # =========================================================
    # Shared runtime refs
    # =========================================================
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
    state["hardware_frame"] = hardware_frame
    state["acq_notebook"] = acq_notebook

    state["stage1_header"] = stage1_header
    state["stage2_header"] = stage2_header

    state["inspector_notebook"] = inspector_notebook
    state["analysis_tab"] = analysis_tab
    state["run_tab"] = run_tab
    state["hardware_tab"] = hardware_tab

    state["set_controls_enabled"] = set_controls_enabled
    state["interactive_widgets"] = interactive_widgets
    state["set_results_ratio"] = set_results_ratio

    # Initial sash placement
    def _place_sash():
        state["set_results_ratio"](0.40)

    root.after(150, _place_sash)

    # Bindings
    def _refresh(*_args):
        refresh_gui_state(state)

    state["mode_var"].trace_add("write", _refresh)
    state["show_advanced_var"].trace_add("write", _refresh)
    state["log_pw_start_exp_var"].trace_add("write", _refresh)
    state["log_pw_end_exp_var"].trace_add("write", _refresh)
    state["log_pw_num_points_var"].trace_add("write", _refresh)
    state["num_frames_var"].trace_add("write", _refresh)
    state["num_periods_var"].trace_add("write", _refresh)
    state["duty_percent_var"].trace_add("write", _refresh)
    state["max_harmonic_var"].trace_add("write", _refresh)
    state["main_harmonics_var"].trace_add("write", _refresh)
    state["diagnostic_harmonics_var"].trace_add("write", _refresh)
    state["output_folder_var"].trace_add("write", _refresh)
    state["analysis_target_var"].trace_add("write", _refresh)
    state["trigger_source_var"].trace_add("write", _refresh)
    state["trigger_level_var"].trace_add("write", _refresh)
    state["trigger_edge_var"].trace_add("write", _refresh)
    state["acquisition_mode_var"].trace_add("write", _refresh)
    state["amplitude_var"].trace_add("write", _refresh)
    state["offset_var"].trace_add("write", _refresh)
    state["show_log_var"].trace_add("write", _refresh)

    refresh_gui_state(state)

    try:
        acq_notebook.select(0)
    except Exception:
        pass

    try:
        notebook.select(log_tab)
    except Exception:
        pass

    root.mainloop()