import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config import get_config_path
from utils.media import get_app_root, get_tool_binary


class TestPackagingRuntime(unittest.TestCase):
    def test_windows_bundled_exe_in_frozen_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            tool = root / "tools" / "ffmpeg.exe"
            tool.touch()
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "_MEIPASS", directory, create=True), patch.object(sys, "platform", "win32"), patch("utils.media.shutil.which", return_value=None):
                self.assertEqual(get_app_root(), root)
                self.assertEqual(get_tool_binary("ffmpeg"), str(tool))

    def test_macos_bundled_tool_in_frozen_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            tool = root / "tools" / "ffprobe"
            tool.touch()
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "_MEIPASS", directory, create=True), patch.object(sys, "platform", "darwin"):
                self.assertEqual(get_tool_binary("ffprobe"), str(tool))

    def test_windows_settings_use_appdata(self):
        with patch("config.platform.system", return_value="Windows"), patch.dict(os.environ, {"APPDATA": "/profiles/user/AppData/Roaming", "XDG_CONFIG_HOME": "/wrong"}):
            self.assertEqual(get_config_path(), Path("/profiles/user/AppData/Roaming/video-transcriber/settings.json"))
