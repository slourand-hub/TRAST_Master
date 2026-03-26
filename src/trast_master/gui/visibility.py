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


def update_mode_ui(state: dict):
    mode = state["mode_var"].get()
    show_advanced = state["show_advanced_var"].get()

    analysis_target_row = state["analysis_target_row"]
    output_folder_row = state["output_folder_row"]
    timestamp_row = state["timestamp_row"]
    acquisition_frame = state["acquisition_frame"]
    acquisition_options_frame = state["acquisition_options_frame"]
    analysis_options_frame = state["analysis_options_frame"]
    analysis_frame = state["analysis_frame"]
    summary_frame = state["summary_frame"]
    advanced_frame = state["advanced_frame"]

    if mode == "acquire":
        analysis_target_row.grid_remove()
        output_folder_row.grid()
        timestamp_row.grid()
        acquisition_frame.grid()
        acquisition_options_frame.grid()
        analysis_options_frame.grid_remove()
        analysis_frame.grid_remove()
        summary_frame.grid()

    elif mode == "analyze":
        analysis_target_row.grid()
        output_folder_row.grid_remove()
        timestamp_row.grid_remove()
        acquisition_frame.grid_remove()
        acquisition_options_frame.grid_remove()
        analysis_options_frame.grid()
        analysis_frame.grid()
        summary_frame.grid()

    else:
        analysis_target_row.grid_remove()
        output_folder_row.grid()
        timestamp_row.grid()
        acquisition_frame.grid()
        acquisition_options_frame.grid()
        analysis_options_frame.grid()
        analysis_frame.grid()
        summary_frame.grid()

    if show_advanced and mode in ("acquire", "both"):
        advanced_frame.grid()
    else:
        advanced_frame.grid_remove()