def append_log(log_text, root, msg: str):
    text = str(msg)
    if not text.endswith("\n"):
        text += "\n"

    log_text.configure(state="normal")
    log_text.insert("end", text)
    log_text.see("end")
    log_text.configure(state="disabled")
    root.update_idletasks()


def clear_log(log_text):
    log_text.configure(state="normal")
    log_text.delete("1.0", "end")
    log_text.configure(state="disabled")