import unittest

from transcriber_core import (
    is_url,
    is_youtube_url,
    seconds_to_srt_time,
    segments_to_srt,
    segments_to_timestamped,
)


class TestTranscriberCore(unittest.TestCase):
    def test_is_url(self):
        self.assertTrue(is_url("https://example.com/video.mp4"))
        self.assertTrue(is_url("http://example.com/video.mp4"))
        self.assertFalse(is_url("ftp://example.com/video.mp4"))
        self.assertFalse(is_url("/home/user/video.mp4"))

    def test_is_youtube_url(self):
        self.assertTrue(is_youtube_url("https://www.youtube.com/watch?v=abc"))
        self.assertTrue(is_youtube_url("https://youtu.be/abc"))
        self.assertFalse(is_youtube_url("https://example.com/watch?v=abc"))
        self.assertFalse(is_youtube_url("not-a-url"))

    def test_seconds_to_srt_time(self):
        self.assertEqual(seconds_to_srt_time(0.0), "00:00:00,000")
        self.assertEqual(seconds_to_srt_time(65.321), "00:01:05,320")
        self.assertEqual(seconds_to_srt_time(3661.9), "01:01:01,900")

    def test_segments_to_srt(self):
        segments = [
            {"start": 0.0, "end": 1.5, "text": " Hello "},
            {"start": 2.0, "end": 3.0, "text": "World"},
        ]
        expected = (
            "1\n00:00:00,000 --> 00:00:01,500\nHello\n\n"
            "2\n00:00:02,000 --> 00:00:03,000\nWorld\n"
        )
        self.assertEqual(segments_to_srt(segments), expected)

    def test_segments_to_timestamped(self):
        segments = [
            {"start": 0.0, "end": 1.0, "text": " Hello "},
            {"start": 61.2, "end": 62.0, "text": "World"},
        ]
        expected = "[00:00:00.000]  Hello\n[00:01:01.200]  World"
        self.assertEqual(segments_to_timestamped(segments), expected)


if __name__ == "__main__":
    unittest.main()
