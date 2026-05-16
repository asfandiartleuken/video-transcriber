import unittest

from ui.shortcuts import (
    get_edit_target,
    iter_virtual_shortcut_sequences,
    perform_edit_action,
    resolve_control_shortcut,
)


class EntryLike:
    def __init__(self, text=""):
        self.text = text
        self.selection = None
        self.cursor = len(text)

    def selection_range(self, _start, _end):
        self.selection = (0, len(self.text))

    def icursor(self, index):
        self.cursor = len(self.text) if index == "end" else int(index)

    def index(self, index):
        if index == "insert":
            return self.cursor
        if index == "sel.first":
            if self.selection is None:
                raise ValueError("no selection")
            return self.selection[0]
        if index == "sel.last":
            if self.selection is None:
                raise ValueError("no selection")
            return self.selection[1]
        return int(index)

    def get(self):
        return self.text

    def delete(self, start, end):
        self.text = self.text[:start] + self.text[end:]
        self.selection = None
        self.cursor = start

    def insert(self, index, value):
        self.text = self.text[:index] + value + self.text[index:]
        self.cursor = index + len(value)


class TextLike:
    def __init__(self, text=""):
        self.text = text
        self.selection = None
        self.insert_offset = len(text)

    def tag_add(self, _tag, _start, _end):
        self.selection = (0, len(self.text))

    def tag_ranges(self, tag_name):
        if tag_name != "sel" or self.selection is None:
            return ()
        return ("sel.first", "sel.last")

    def mark_set(self, _mark, index):
        self.insert_offset = self._to_offset(index)

    def see(self, _index):
        return None

    def get(self, start, end):
        return self.text[self._to_offset(start):self._to_offset(end)]

    def delete(self, start, end):
        start_offset = self._to_offset(start)
        end_offset = self._to_offset(end)
        self.text = self.text[:start_offset] + self.text[end_offset:]
        self.selection = None
        self.insert_offset = start_offset

    def insert(self, index, value):
        offset = self._to_offset(index)
        self.text = self.text[:offset] + value + self.text[offset:]
        self.insert_offset = offset + len(value)

    def _to_offset(self, index):
        if index == "sel.first":
            if self.selection is None:
                raise ValueError("no selection")
            return self.selection[0]
        if index == "sel.last":
            if self.selection is None:
                raise ValueError("no selection")
            return self.selection[1]
        if index == "insert":
            return self.insert_offset
        if index in ("1.0", "0"):
            return 0
        if index == "end-1c":
            return len(self.text)
        if index == "end":
            return len(self.text)
        return int(index)


class Wrapper:
    def __init__(self, inner_name, inner):
        setattr(self, inner_name, inner)


class TestUiShortcuts(unittest.TestCase):
    def test_resolve_control_shortcut_supports_latin_and_cyrillic_layouts(self):
        self.assertEqual(resolve_control_shortcut("c", "c"), "copy")
        self.assertEqual(resolve_control_shortcut("C", "C"), "copy")
        self.assertEqual(resolve_control_shortcut("с", "с"), "copy")
        self.assertEqual(resolve_control_shortcut("", "\x03"), "copy")
        self.assertEqual(resolve_control_shortcut("v", "v"), "paste")
        self.assertEqual(resolve_control_shortcut("м", "м"), "paste")
        self.assertEqual(resolve_control_shortcut("", "\x16"), "paste")
        self.assertEqual(resolve_control_shortcut("x", "x"), "cut")
        self.assertEqual(resolve_control_shortcut("ч", "ч"), "cut")
        self.assertEqual(resolve_control_shortcut("", "\x18"), "cut")
        self.assertEqual(resolve_control_shortcut("a", "a"), "select_all")
        self.assertEqual(resolve_control_shortcut("ф", "ф"), "select_all")
        self.assertEqual(resolve_control_shortcut("", "\x01"), "select_all")
        self.assertEqual(resolve_control_shortcut("", "", 67), "copy")
        self.assertEqual(resolve_control_shortcut("", "", 86), "paste")
        self.assertIsNone(resolve_control_shortcut("b", "b"))

    def test_get_edit_target_returns_supported_widget_or_inner_control(self):
        entry = EntryLike()
        text = TextLike()

        self.assertIs(get_edit_target(entry), entry)
        self.assertIs(get_edit_target(text), text)
        self.assertIs(get_edit_target(Wrapper("_entry", entry)), entry)
        self.assertIs(get_edit_target(Wrapper("_textbox", text)), text)
        self.assertIsNone(get_edit_target(object()))

    def test_virtual_shortcut_sequences_cover_clipboard_alternate_keys(self):
        sequences = list(iter_virtual_shortcut_sequences())

        self.assertIn(("copy", "<Control-Insert>"), sequences)
        self.assertIn(("paste", "<Shift-Insert>"), sequences)
        self.assertIn(("cut", "<Shift-Delete>"), sequences)

    def test_perform_edit_action_updates_entry_clipboard_and_content(self):
        entry = EntryLike("hello")
        clipboard = {"text": ""}

        entry.selection = (1, 4)
        self.assertTrue(perform_edit_action(entry, "copy", lambda: clipboard["text"], lambda value: clipboard.__setitem__("text", value)))
        self.assertEqual(clipboard["text"], "ell")

        self.assertTrue(perform_edit_action(entry, "cut", lambda: clipboard["text"], lambda value: clipboard.__setitem__("text", value)))
        self.assertEqual(entry.text, "ho")
        self.assertEqual(clipboard["text"], "ell")

        entry.cursor = 1
        clipboard["text"] = "XYZ"
        self.assertTrue(perform_edit_action(entry, "paste", lambda: clipboard["text"], lambda value: clipboard.__setitem__("text", value)))
        self.assertEqual(entry.text, "hXYZo")

        self.assertTrue(perform_edit_action(entry, "select_all", lambda: clipboard["text"], lambda value: clipboard.__setitem__("text", value)))
        self.assertEqual(entry.selection, (0, len(entry.text)))

    def test_perform_edit_action_updates_text_widget_content(self):
        text = TextLike("hello world")
        clipboard = {"text": ""}

        text.selection = (0, 5)
        self.assertTrue(perform_edit_action(text, "copy", lambda: clipboard["text"], lambda value: clipboard.__setitem__("text", value)))
        self.assertEqual(clipboard["text"], "hello")

        self.assertTrue(perform_edit_action(text, "cut", lambda: clipboard["text"], lambda value: clipboard.__setitem__("text", value)))
        self.assertEqual(text.text, " world")

        text.insert_offset = 0
        clipboard["text"] = "hi"
        self.assertTrue(perform_edit_action(text, "paste", lambda: clipboard["text"], lambda value: clipboard.__setitem__("text", value)))
        self.assertEqual(text.text, "hi world")

        self.assertTrue(perform_edit_action(text, "select_all", lambda: clipboard["text"], lambda value: clipboard.__setitem__("text", value)))
        self.assertEqual(text.selection, (0, len(text.text)))


if __name__ == "__main__":
    unittest.main()
