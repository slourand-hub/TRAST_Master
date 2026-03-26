import threading
import queue
import traceback


class GuiWorker:
    def __init__(self):
        self.thread = None
        self.queue = queue.Queue()
        self.is_running = False

    def start(self, target, *args, **kwargs):
        if self.is_running:
            raise RuntimeError("A task is already running.")

        self.is_running = True

        def runner():
            try:
                result = target(*args, **kwargs)
                self.queue.put(("done", result))
            except Exception as e:
                tb = traceback.format_exc()
                self.queue.put(("error", (e, tb)))
            finally:
                self.is_running = False

        self.thread = threading.Thread(target=runner, daemon=True)
        self.thread.start()