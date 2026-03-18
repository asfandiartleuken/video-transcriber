"""
Video Transcriber — CustomTkinter + OpenAI Whisper
Барлық функциялары бар толық нұсқа (URL қолдауымен).
"""

import multiprocessing as mp

from logging_utils import configure_logging
from media_tools import add_bundled_tools_to_path
from runtime_utils import ensure_stdio_streams
from ui_app import VideoTranscriberApp

configure_logging()

ensure_stdio_streams()
add_bundled_tools_to_path()


if __name__ == "__main__":
    mp.freeze_support()
    app = VideoTranscriberApp()
    app.mainloop()
