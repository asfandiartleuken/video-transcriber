import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import CONFIG_PATH
from .runtime import ensure_stdio_streams


def configure_logging() -> None:
    ensure_stdio_streams()

    log_dir = CONFIG_PATH.parent / "logs"
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "app.log"
        file_handler = RotatingFileHandler(
            Path(log_path),
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
    except OSError as exc:
        root.warning("File logging disabled: %s", exc)
    else:
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
