import queue
from tkinter import messagebox
from trast_master.gui.tables import populate_treeview_from_dataframe
from trast_master.analysis.run_analysis_core import render_analysis_plots


def process_worker_queue(state: dict):
    worker = state["worker"]
    should_continue_polling = worker.is_running

    try:
        while True:
            kind, payload = worker.queue.get_nowait()
            should_continue_polling = True

            if kind == "log":
                state["append_log"](payload)

            elif kind == "status":
                state["status_var"].set(str(payload))

            elif kind == "progress":
                state["progress_value_var"].set(float(payload.get("value", 0.0)))
                state["progress_stage_var"].set(str(payload.get("stage", "")))
                state["progress_detail_var"].set(str(payload.get("detail", "")))

            elif kind == "tables":
                acq_df = payload["acq_df"]
                trast_df = payload["trast_df"]
                populate_treeview_from_dataframe(state["acq_tree"], acq_df)
                populate_treeview_from_dataframe(state["trast_tree"], trast_df)

            elif kind == "plots":
                config = payload["config"]
                df = payload["df"]
                render_analysis_plots(config, df)

            elif kind == "done":
                state["status_var"].set("Done.")
                state["append_log"]("Finished successfully.")
                state["progress_value_var"].set(100.0)
                state["progress_stage_var"].set("Done")
                state["progress_detail_var"].set("Run completed successfully.")
                state["run_controls_hint_var"].set("Ready to run.")
                if "set_controls_enabled" in state:
                    state["set_controls_enabled"](True)
                if "stop_btn" in state:
                    state["stop_btn"].configure(state="disabled")
                should_continue_polling = False

            elif kind == "error":
                exc, tb = payload
                state["status_var"].set("Error.")
                state["append_log"](f"ERROR: {exc}")
                state["append_log"](tb)
                state["progress_stage_var"].set("Stopped with error")
                state["progress_detail_var"].set(str(exc))
                state["run_controls_hint_var"].set("Fix the error and run again.")
                if "set_controls_enabled" in state:
                    state["set_controls_enabled"](True)
                if "stop_btn" in state:
                    state["stop_btn"].configure(state="disabled")
                messagebox.showerror("Error", str(exc))
                should_continue_polling = False

    except queue.Empty:
        pass

    if should_continue_polling or worker.is_running or not worker.queue.empty():
        state["root"].after(100, lambda: process_worker_queue(state))


def make_worker_logger(state: dict):
    def worker_log(msg):
        text = str(msg)
        print(text, flush=True)
        state["worker"].queue.put(("log", text))
    return worker_log