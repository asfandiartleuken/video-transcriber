import queue
import threading
import unittest
from unittest.mock import patch

from ui_app import VideoTranscriberApp


class _OptionsFrameStub:
    def __init__(self):
        self.transcribe_state = None
        self.cancel_state = None

    def set_transcribe_state(self, enabled: bool):
        self.transcribe_state = enabled

    def set_cancel_state(self, enabled: bool):
        self.cancel_state = enabled

    def get_language(self):
        return "en"

    def get_model(self):
        return "base"


class _ButtonBarStub:
    def __init__(self):
        self.enabled = None

    def set_output_buttons_state(self, enabled: bool):
        self.enabled = enabled


class _TextBoxStub:
    def __init__(self):
        self.deleted = []

    def delete(self, start, end):
        self.deleted.append((start, end))


class _ResultStub:
    def __init__(self):
        self._text_box = _TextBoxStub()
        self.cleared = False

    def get_text_box(self):
        return self._text_box

    def clear_stats(self):
        self.cleared = True


class _ProgressStub:
    def __init__(self):
        self.values = []

    def set_progress(self, value: float, status: str):
        self.values.append((value, status))


class _ThreadStub:
    instances = []

    def __init__(self, target, args, daemon):
        self.target = target
        self.args = args
        self.daemon = daemon
        self.started = False
        self.__class__.instances.append(self)

    def start(self):
        self.started = True


class TestVideoTranscriberApp(unittest.TestCase):
    def setUp(self):
        _ThreadStub.instances.clear()

    def test_run_transcription_job_uses_fresh_cancel_event(self):
        app = VideoTranscriberApp.__new__(VideoTranscriberApp)
        app._job_counter = 0
        app._active_job_id = 0
        app._task_queue = queue.Queue()
        app._options_frame = _OptionsFrameStub()
        app._button_bar = _ButtonBarStub()
        app._result = _ResultStub()
        app._progress = _ProgressStub()

        old_event = threading.Event()
        old_event.set()
        app._cancel_event = old_event

        with patch("ui_app.threading.Thread", _ThreadStub):
            VideoTranscriberApp._run_transcription_job(
                app,
                "https://example.com/audio.mp3",
                "Дайындалуда…",
            )

        self.assertIsNot(app._cancel_event, old_event)
        self.assertFalse(app._cancel_event.is_set())
        self.assertTrue(_ThreadStub.instances[-1].started)
        self.assertIs(_ThreadStub.instances[-1].args[1], app._cancel_event)
        self.assertEqual(app._options_frame.transcribe_state, False)
        self.assertEqual(app._options_frame.cancel_state, True)

    def test_transcribe_worker_reports_unexpected_errors(self):
        app = VideoTranscriberApp.__new__(VideoTranscriberApp)
        app._task_queue = queue.Queue()
        cancel_event = threading.Event()

        with patch("ui_app.TranscriptionService") as mock_service_cls, patch(
            "ui_app.logger.exception"
        ):
            mock_service_cls.return_value.transcribe.side_effect = ValueError("bad header")

            VideoTranscriberApp._transcribe_worker(
                app,
                7,
                cancel_event,
                "https://example.com/audio.mp3",
                "base",
                "en",
            )

        job_id, event, payload = app._task_queue.get_nowait()
        self.assertEqual(job_id, 7)
        self.assertEqual(event, "error")
        self.assertIn("bad header", payload)


if __name__ == "__main__":
    unittest.main()
