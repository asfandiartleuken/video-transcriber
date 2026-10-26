"""Video Transcriber desktop entry point."""
import multiprocessing as mp
import sys

if __name__ == "__main__":
    # Divert frozen multiprocessing workers before importing the GUI or logging.
    mp.freeze_support()

    from utils import add_bundled_tools_to_path, configure_logging, ensure_stdio_streams

    ensure_stdio_streams()
    configure_logging()
    add_bundled_tools_to_path()

    if "--smoke-test" in sys.argv:
        from utils.smoke import run_smoke_test

        run_smoke_test()
    else:
        from ui_app import VideoTranscriberApp

        app = VideoTranscriberApp()
        app.mainloop()
