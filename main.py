"""
Video Transcriber — CustomTkinter + OpenAI Whisper
Барлық функциялары бар толық нұсқа (URL қолдауымен).
"""

import logging
import multiprocessing as mp

from media_tools import add_bundled_tools_to_path
from runtime_utils import ensure_stdio_streams
from ui_app import VideoTranscriberApp

logging.basicConfig(level=logging.INFO)

ensure_stdio_streams()
add_bundled_tools_to_path()


if __name__ == "__main__":
    mp.freeze_support()
    app = VideoTranscriberApp()
    app.mainloop()
