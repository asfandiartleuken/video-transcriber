from .shortcuts import (
    iter_edit_targets,
    iter_virtual_shortcut_sequences,
    perform_edit_action,
    resolve_control_shortcut,
)

# Widgets depend on optional GUI libraries (e.g., customtkinter). Import them lazily so
# headless environments (like unit tests) can still import shortcut helpers without
# requiring GUI dependencies to be installed.
try:  # noqa: SIM105 – clarity over cleverness
    from .widgets import (
        ButtonBarFrame,
        FileSelectorFrame,
        HeaderFrame,
        OptionsFrame,
        ProgressFrame,
        ResultFrame,
    )
    _WIDGETS_IMPORTED = True
except ImportError:
    _WIDGETS_IMPORTED = False

__all__ = [
    "resolve_control_shortcut",
    "iter_edit_targets",
    "iter_virtual_shortcut_sequences",
    "perform_edit_action",
]

if _WIDGETS_IMPORTED:
    __all__ += [
        "HeaderFrame",
        "FileSelectorFrame",
        "OptionsFrame",
        "ProgressFrame",
        "ResultFrame",
        "ButtonBarFrame",
    ]
