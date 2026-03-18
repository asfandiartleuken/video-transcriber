import logging
from pathlib import Path

from app_config import CONFIG_PATH


def configure_logging() -> None:
    log_dir = CONFIG_PATH.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "app.log"

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    file_handler = logging.FileHandler(Path(log_path), encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
