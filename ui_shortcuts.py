from __future__ import annotations


_COPY_KEYS = {"c", "с"}
_PASTE_KEYS = {"v", "м"}
_CUT_KEYS = {"x", "ч"}
_SELECT_ALL_KEYS = {"a", "ф"}
_CONTROL_CHAR_ACTIONS = {
    "\x01": "select_all",
    "\x03": "copy",
    "\x16": "paste",
    "\x18": "cut",
}
_KEYCODE_ACTIONS = {
    65: "select_all",
    67: "copy",
    86: "paste",
    88: "cut",
}
_VIRTUAL_SHORTCUT_SEQUENCES = {
    "copy": ("<Control-Insert>",),
    "paste": ("<Shift-Insert>",),
    "cut": ("<Shift-Delete>",),
}


def resolve_control_shortcut(keysym: str = "", char: str = "", keycode: int | None = None) -> str | None:
    action = _KEYCODE_ACTIONS.get(keycode)
    if action is not None:
        return action

    action = _CONTROL_CHAR_ACTIONS.get(char)
    if action is not None:
        return action

    tokens = {keysym.casefold(), char.casefold()}
    if tokens & _COPY_KEYS:
        return "copy"
    if tokens & _PASTE_KEYS:
        return "paste"
    if tokens & _CUT_KEYS:
        return "cut"
    if tokens & _SELECT_ALL_KEYS:
        return "select_all"
    return None


def get_edit_target(widget):
    if widget is None:
        return None
    if hasattr(widget, "tag_add") or _is_entry_widget(widget) or hasattr(widget, "selection_range") or hasattr(widget, "select_range"):
        return widget
    for attr_name in ("_textbox", "_entry"):
        inner = getattr(widget, attr_name, None)
        if inner is not None:
            return inner
    return None


def iter_edit_targets(widget):
    seen = set()
    for candidate in (widget, get_edit_target(widget)):
        if candidate is None:
            continue
        marker = id(candidate)
        if marker in seen:
            continue
        seen.add(marker)
        yield candidate


def iter_virtual_shortcut_sequences():
    for action, sequences in _VIRTUAL_SHORTCUT_SEQUENCES.items():
        for sequence in sequences:
            yield action, sequence


def perform_edit_action(widget, action: str, read_clipboard, write_clipboard) -> bool:
    target = get_edit_target(widget)
    if target is None:
        return False

    if _is_entry_widget(target):
        return _perform_entry_action(target, action, read_clipboard, write_clipboard)
    if hasattr(target, "tag_add"):
        return _perform_text_action(target, action, read_clipboard, write_clipboard)
    return False


def _perform_entry_action(widget, action: str, read_clipboard, write_clipboard) -> bool:
    if action == "select_all":
        if hasattr(widget, "selection_range"):
            widget.selection_range(0, "end")
        else:
            widget.select_range(0, "end")
        widget.icursor("end")
        return True

    start, end = _get_entry_selection(widget)

    if action == "copy":
        if start is not None and end is not None and start != end:
            write_clipboard(widget.get()[start:end])
        return True

    if action == "cut":
        if start is not None and end is not None and start != end:
            write_clipboard(widget.get()[start:end])
            widget.delete(start, end)
            widget.icursor(start)
        return True

    if action == "paste":
        text = read_clipboard()
        if start is not None and end is not None and start != end:
            widget.delete(start, end)
            insert_at = start
        else:
            insert_at = widget.index("insert")
        widget.insert(insert_at, text)
        widget.icursor(insert_at + len(text))
        return True

    return False


def _perform_text_action(widget, action: str, read_clipboard, write_clipboard) -> bool:
    if action == "select_all":
        widget.tag_add("sel", "1.0", "end-1c")
        widget.mark_set("insert", "end-1c")
        widget.see("insert")
        return True

    has_selection = bool(widget.tag_ranges("sel"))

    if action == "copy":
        if has_selection:
            write_clipboard(widget.get("sel.first", "sel.last"))
        return True

    if action == "cut":
        if has_selection:
            write_clipboard(widget.get("sel.first", "sel.last"))
            widget.delete("sel.first", "sel.last")
        return True

    if action == "paste":
        text = read_clipboard()
        if has_selection:
            widget.delete("sel.first", "sel.last")
        widget.insert("insert", text)
        widget.see("insert")
        return True

    return False


def _get_entry_selection(widget):
    try:
        start = widget.index("sel.first")
        end = widget.index("sel.last")
    except Exception:
        return None, None
    return start, end


def _is_entry_widget(widget) -> bool:
    return all(hasattr(widget, attr_name) for attr_name in ("index", "insert", "delete", "get")) and not hasattr(widget, "tag_add")
