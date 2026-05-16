import logging
import unittest
from unittest.mock import patch

from utils.logging import configure_logging


class TestLoggingConfiguration(unittest.TestCase):
    def setUp(self):
        self._root = logging.getLogger()
        self._old_handlers = list(self._root.handlers)
        self._old_level = self._root.level

    def tearDown(self):
        self._root.handlers.clear()
        for handler in self._old_handlers:
            self._root.addHandler(handler)
        self._root.setLevel(self._old_level)

    def test_configure_logging_falls_back_to_console_when_file_handler_fails(self):
        with patch("utils.logging.RotatingFileHandler", side_effect=OSError("read-only")):
            configure_logging()

        self.assertTrue(self._root.handlers)
        self.assertTrue(any(isinstance(handler, logging.StreamHandler) for handler in self._root.handlers))


if __name__ == "__main__":
    unittest.main()
