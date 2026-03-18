import threading
import unittest
from unittest.mock import patch

from app_errors import CancelledError
from services.transcription_service import TranscriptionService


class TestTranscriptionService(unittest.TestCase):
    def test_check_cancel_raises(self):
        ev = threading.Event()
        ev.set()
        service = TranscriptionService(ev)
        with self.assertRaises(CancelledError):
            service._check_cancel()

    @patch("services.transcription_service.validate_media_file")
    @patch("services.transcription_service.extract_audio")
    @patch("services.transcription_service.ensure_dependencies")
    @patch.object(TranscriptionService, "_transcribe_audio")
    def test_transcribe_local_file_flow(self, mock_transcribe_audio, _deps, _extract, _validate):
        mock_transcribe_audio.return_value = {
            "text": " Hello world ",
            "segments": [{"start": 0.0, "end": 1.0, "text": " Hello world "}],
        }
        service = TranscriptionService(threading.Event())
        statuses = []

        result = service.transcribe("video.mp4", "base", "en", lambda p, s: statuses.append((p, s)))

        self.assertEqual(result["plain"], "Hello world")
        self.assertIn("srt", result)
        self.assertIn("ts_text", result)
        self.assertTrue(statuses)

    @patch("services.transcription_service.download_youtube_video")
    @patch("services.transcription_service.download_video")
    @patch("services.transcription_service.is_youtube_url", return_value=True)
    @patch("services.transcription_service.is_url", return_value=True)
    @patch("services.transcription_service.validate_media_file")
    @patch("services.transcription_service.extract_audio")
    @patch("services.transcription_service.ensure_dependencies")
    @patch.object(TranscriptionService, "_transcribe_audio")
    def test_transcribe_url_uses_youtube_downloader(
        self,
        mock_transcribe_audio,
        _deps,
        _extract,
        _validate,
        _is_url,
        _is_youtube,
        _download_video,
        mock_download_youtube,
    ):
        mock_transcribe_audio.return_value = {"text": "A", "segments": []}
        service = TranscriptionService(threading.Event())
        result = service.transcribe("https://youtu.be/abc", "base", "en", lambda _p, _s: None)
        self.assertEqual(result["plain"], "A")
        mock_download_youtube.assert_called_once()
        _download_video.assert_not_called()


if __name__ == "__main__":
    unittest.main()
