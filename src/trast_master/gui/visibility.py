def update_log_visibility(state: dict):
    notebook = state["notebook"]
    log_tab = state["log_tab"]
    show_log = state["show_log_var"].get()

    tab_ids = notebook.tabs()
    log_tab_id = str(log_tab)

    if show_log:
        if log_tab_id not in tab_ids:
            notebook.add(log_tab, text="Log")
    else:
        if log_tab_id in tab_ids:
            notebook.forget(log_tab)


def _set_tab_visible(notebook, tab, title: str, visible: bool):
    tab_id = str(tab)
    current_tabs = notebook.tabs()

    if visible and tab_id not in current_tabs:
        notebook.add(tab, text=title)
    elif (not visible) and tab_id in current_tabs:
        notebook.forget(tab)


def update_mode_ui(state: dict):
    mode = state["mode_var"].get()
    show_advanced = state["show_advanced_var"].get()

    analysis_target_row = state["analysis_target_row"]
    output_folder_row = state["output_folder_row"]
    timestamp_row = state["timestamp_row"]
    acquisition_frame = state["acquisition_frame"]
    advanced_frame = state["advanced_frame"]

    inspector_notebook = state["inspector_notebook"]
    analysis_tab = state["analysis_tab"]
    run_tab = state["run_tab"]
    hardware_tab = state["hardware_tab"]

    if mode == "acquire":
        state["stage1_title_var"].set("Stage 1 — Acquisition")
        state["stage2_title_var"].set("Stage 2 — Instrument / run diagnostics")

        analysis_target_row.grid_remove()
        output_folder_row.grid()
        timestamp_row.grid()

        acquisition_frame.grid()

        _set_tab_visible(inspector_notebook, analysis_tab, "Analysis", False)
        _set_tab_visible(inspector_notebook, run_tab, "Run", True)
        _set_tab_visible(inspector_notebook, hardware_tab, "Hardware", True)

    elif mode == "analyze":
        state["stage1_title_var"].set("Analysis input")
        state["stage2_title_var"].set("Stage 2 — Analysis")

        analysis_target_row.grid()
        output_folder_row.grid_remove()
        timestamp_row.grid_remove()

        acquisition_frame.grid_remove()

        _set_tab_visible(inspector_notebook, analysis_tab, "Analysis", True)
        _set_tab_visible(inspector_notebook, run_tab, "Run", True)
        _set_tab_visible(inspector_notebook, hardware_tab, "Hardware", False)

    else:  # both
        state["stage1_title_var"].set("Stage 1 — Acquisition")
        state["stage2_title_var"].set("Stage 2 — Automatic analysis")

        analysis_target_row.grid_remove()
        output_folder_row.grid()
        timestamp_row.grid()

        acquisition_frame.grid()

        _set_tab_visible(inspector_notebook, analysis_tab, "Analysis", True)
        _set_tab_visible(inspector_notebook, run_tab, "Run", True)
        _set_tab_visible(inspector_notebook, hardware_tab, "Hardware", True)

    if show_advanced and mode in ("acquire", "both"):
        advanced_frame.grid()
        try:
            inspector_notebook.select(hardware_tab)
        except Exception:
            pass
    else:
        advanced_frame.grid_remove()