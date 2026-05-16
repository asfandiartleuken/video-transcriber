"""
Video Transcriber — CustomTkinter + OpenAI Whisper
Барлық функциялары бар толық нұсқа (URL қолдауымен).
"""

import multiprocessing as mp

from utils import add_bundled_tools_to_path, configure_logging, ensure_stdio_streams
from ui_app import VideoTranscriberApp

ensure_stdio_streams()
configure_logging()
add_bundled_tools_to_path()


if __name__ == "__main__":
    mp.freeze_support()
    app = VideoTranscriberApp()
    app.mainloop()
