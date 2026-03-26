from tkinter import ttk


def clear_treeview(tree: ttk.Treeview):
    tree.delete(*tree.get_children())


def populate_treeview_from_dataframe(tree: ttk.Treeview, df, max_rows=None):
    clear_treeview(tree)

    if df is None or df.empty:
        tree["columns"] = ()
        tree["show"] = "headings"
        return

    display_df = df.copy()

    for col in display_df.columns:
        try:
            if str(display_df[col].dtype) != "object":
                display_df[col] = display_df[col].round(6)
        except Exception:
            pass

    if max_rows is not None:
        display_df = display_df.head(max_rows)

    columns = [str(c) for c in display_df.columns]
    tree["columns"] = columns
    tree["show"] = "headings"

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=130, anchor="center", stretch=True)

    for _, row in display_df.iterrows():
        tree.insert("", "end", values=[row[col] for col in display_df.columns])


def make_treeview_with_scrollbars(parent):
    frame = ttk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    tree = ttk.Treeview(frame)
    tree.grid(row=0, column=0, sticky="nsew")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    return frame, tree