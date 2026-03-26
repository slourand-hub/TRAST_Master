import queue
from tkinter import messagebox
from trast_master.gui.tables import populate_treeview_from_dataframe


def process_worker_queue(state: dict):
    worker = state["worker"]
    should_continue_polling = worker.is_running

    try:
        while True:
            kind, payload = worker.queue.get_nowait()
            should_continue_polling = True

            if kind == "log":
                state["append_log"](payload)

            elif kind == "tables":
                acq_df = payload["acq_df"]
                trast_df = payload["trast_df"]

                populate_treeview_from_dataframe(state["acq_tree"], acq_df)
                populate_treeview_from_dataframe(state["trast_tree"], trast_df)

            elif kind == "done":
                state["status_var"].set("Done.")
                state["append_log"]("Finished successfully.")
                if "set_controls_enabled" in state:
                    state["set_controls_enabled"](True)
                should_continue_polling = False

            elif kind == "error":
                exc, tb = payload
                state["status_var"].set("Error.")
                state["append_log"](f"ERROR: {exc}")
                state["append_log"](tb)
                if "set_controls_enabled" in state:
                    state["set_controls_enabled"](True)
                messagebox.showerror("Error", str(exc))
                should_continue_polling = False

    except queue.Empty:
        pass

    # Keep polling while work is active OR there are still queued messages
    # that arrived right after this poll cycle.
    if should_continue_polling or worker.is_running or not worker.queue.empty():
        state["root"].after(100, lambda: process_worker_queue(state))


def make_worker_logger(state: dict):
    def worker_log(msg):
        state["worker"].queue.put(("log", str(msg)))
    return worker_log
