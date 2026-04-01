from __future__ import annotations


_COPY_KEYS = {"c", "с"}
_PASTE_KEYS = {"v", "м"}
_CUT_KEYS = {"x", "ч"}
_SELECT_ALL_KEYS = {"a", "ф"}


def resolve_control_shortcut(keysym: str = "", char: str = "") -> str | None:
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
    if hasattr(widget, "tag_add") or hasattr(widget, "select_range"):
        return widget
    for attr_name in ("_textbox", "_entry"):
        inner = getattr(widget, attr_name, None)
        if inner is not None:
            return inner
    return None
