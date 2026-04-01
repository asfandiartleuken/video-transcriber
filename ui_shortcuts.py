from __future__ import annotations


_COPY_KEYS = {"c", "с"}
_PASTE_KEYS = {"v", "м"}
_CUT_KEYS = {"x", "ч"}
_SELECT_ALL_KEYS = {"a", "ф"}
_SHORTCUT_SEQUENCES = {
    "copy": ("<Control-c>", "<Control-C>", "<Control-с>", "<Control-С>", "<Control-Insert>"),
    "paste": ("<Control-v>", "<Control-V>", "<Control-м>", "<Control-М>", "<Shift-Insert>"),
    "cut": ("<Control-x>", "<Control-X>", "<Control-ч>", "<Control-Ч>", "<Shift-Delete>"),
    "select_all": ("<Control-a>", "<Control-A>", "<Control-ф>", "<Control-Ф>"),
}


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


def iter_shortcut_sequences():
    for action, sequences in _SHORTCUT_SEQUENCES.items():
        for sequence in sequences:
            yield action, sequence
