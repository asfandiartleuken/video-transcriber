import unittest

from ui_shortcuts import get_edit_target, iter_virtual_shortcut_sequences, resolve_control_shortcut


class EntryLike:
    def select_range(self, _start, _end):
        return None


class TextLike:
    def tag_add(self, _tag, _start, _end):
        return None


class Wrapper:
    def __init__(self, inner_name, inner):
        setattr(self, inner_name, inner)


class TestUiShortcuts(unittest.TestCase):
    def test_resolve_control_shortcut_supports_latin_and_cyrillic_layouts(self):
        self.assertEqual(resolve_control_shortcut("c", "c"), "copy")
        self.assertEqual(resolve_control_shortcut("C", "C"), "copy")
        self.assertEqual(resolve_control_shortcut("с", "с"), "copy")
        self.assertEqual(resolve_control_shortcut("v", "v"), "paste")
        self.assertEqual(resolve_control_shortcut("м", "м"), "paste")
        self.assertEqual(resolve_control_shortcut("x", "x"), "cut")
        self.assertEqual(resolve_control_shortcut("ч", "ч"), "cut")
        self.assertEqual(resolve_control_shortcut("a", "a"), "select_all")
        self.assertEqual(resolve_control_shortcut("ф", "ф"), "select_all")
        self.assertIsNone(resolve_control_shortcut("b", "b"))

    def test_get_edit_target_returns_supported_widget_or_inner_control(self):
        entry = EntryLike()
        text = TextLike()

        self.assertIs(get_edit_target(entry), entry)
        self.assertIs(get_edit_target(text), text)
        self.assertIs(get_edit_target(Wrapper("_entry", entry)), entry)
        self.assertIs(get_edit_target(Wrapper("_textbox", text)), text)
        self.assertIsNone(get_edit_target(object()))

    def test_virtual_shortcut_sequences_cover_windows_clipboard_keys(self):
        sequences = list(iter_virtual_shortcut_sequences())

        self.assertIn(("copy", "<Control-Insert>"), sequences)
        self.assertIn(("paste", "<Shift-Insert>"), sequences)
        self.assertIn(("cut", "<Shift-Delete>"), sequences)


if __name__ == "__main__":
    unittest.main()
