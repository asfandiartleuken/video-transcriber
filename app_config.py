import json
import logging
import os
import platform
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = (
    ("Видео файлдар", "*.mp4 *.mkv *.avi *.mov *.webm"),
    ("Барлық файлдар", "*.*"),
)
WHISPER_MODELS = ["tiny", "base", "small", "medium"]
DEFAULT_LANGUAGE = "en"


def get_config_path() -> Path:
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        appdata = os.getenv("LOCALAPPDATA")
        if appdata:
            return Path(appdata) / "video-transcriber" / "settings.json"
        return home / "AppData" / "Local" / "video-transcriber" / "settings.json"
    if system == "Darwin":
        return home / "Library" / "Application Support" / "video-transcriber" / "settings.json"
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "video-transcriber" / "settings.json"
    return home / ".config" / "video-transcriber" / "settings.json"


CONFIG_PATH = get_config_path()


def load_settings() -> dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except FileNotFoundError:
        return {"model": "base", "language": DEFAULT_LANGUAGE, "timestamps": False}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Settings read error: %s", exc)
        return {"model": "base", "language": DEFAULT_LANGUAGE, "timestamps": False}

    if not isinstance(data, dict):
        logger.warning("Settings file has invalid format, expected dict.")
        return {"model": "base", "language": DEFAULT_LANGUAGE, "timestamps": False}
    return data


def save_settings(data: dict[str, Any]) -> None:
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as file_handle:
            json.dump(data, file_handle, indent=2, ensure_ascii=False)
    except OSError as exc:
        logger.warning("Settings save error: %s", exc)
