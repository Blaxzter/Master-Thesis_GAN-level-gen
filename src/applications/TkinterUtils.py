
def clear_tab_panes(tab_control, tabs):
    for tab_idx, tab in enumerate(tabs):
        for key, element in tab.items():
            invert_op = getattr(element, "destroy", None)
            if callable(invert_op):
                invert_op()

    for item in tab_control.winfo_children():
        item.destroy()

    return []