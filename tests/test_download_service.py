import ssl
import os
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error

from app_errors import DownloadError
from services.download_service import download_video, validate_response_headers


class _FakeResponse:
    def __init__(self, chunks: list[bytes], headers: dict[str, str]):
        self._chunks = list(chunks)
        self.headers = headers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, _size: int) -> bytes:
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


class TestDownloadService(unittest.TestCase):
    def test_validate_response_headers_rejects_bad_type(self):
        with self.assertRaises(DownloadError):
            validate_response_headers({"Content-Type": "text/html", "Content-Length": "10"})

    def test_download_video_success(self):
        fake = _FakeResponse(
            chunks=[b"hello ", b"world"],
            headers={"Content-Type": "video/mp4", "Content-Length": "11"},
        )
        progress: list[float] = []
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            dest = tmp.name
        try:
            with patch("services.download_service.urllib.request.urlopen", return_value=fake) as mock_urlopen:
                download_video(
                    "https://example.com/video.mp4",
                    dest,
                    threading.Event(),
                    progress_callback=lambda p: progress.append(p),
                )
            _, kwargs = mock_urlopen.call_args
            self.assertIn("context", kwargs)
            self.assertIsNotNone(kwargs["context"])
            with open(dest, "rb") as f:
                self.assertEqual(f.read(), b"hello world")
            self.assertTrue(progress)
        finally:
            if os.path.exists(dest):
                os.unlink(dest)

    def test_download_video_ssl_error_message(self):
        ssl_error = ssl.SSLCertVerificationError("certificate verify failed")
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            dest = tmp.name
        try:
            with patch(
                "services.download_service.urllib.request.urlopen",
                side_effect=urllib.error.URLError(ssl_error),
            ):
                with self.assertRaises(DownloadError) as err:
                    download_video(
                        "https://example.com/video.mp4",
                        dest,
                        threading.Event(),
                    )
            self.assertIn("SSL сертификатын тексеру сәтсіз аяқталды", str(err.exception))
        finally:
            if os.path.exists(dest):
                os.unlink(dest)


if __name__ == "__main__":
    unittest.main()
