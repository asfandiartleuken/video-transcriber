from __future__ import annotations

from typing import Any


def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")


def is_youtube_url(url: str) -> bool:
    from urllib.parse import urlparse

    try:
        netloc = urlparse(url).netloc.lower()
    except ValueError:
        return False
    return any(host in netloc for host in ("youtube.com", "youtu.be", "m.youtube.com", "www.youtube.com"))


def format_srt_time(seconds: float) -> str:
    ms = int((seconds % 1) * 1000)
    total_seconds = int(seconds)
    m, s = divmod(total_seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def segments_to_srt(segments: list[dict[str, Any]]) -> str:
    lines = []
    for index, segment in enumerate(segments, 1):
        start = format_srt_time(segment["start"])
        end = format_srt_time(segment["end"])
        lines.append(f"{index}\n{start} --> {end}\n{segment['text'].strip()}\n")
    return "\n".join(lines)


def segments_to_timestamped(segments: list[dict[str, Any]]) -> str:
    lines = []
    for segment in segments:
        start = format_srt_time(segment["start"]).replace(",", ".")
        lines.append(f"[{start}]  {segment['text'].strip()}")
    return "\n".join(lines)


def format_timestamped_text(segments: list[dict[str, Any]]) -> str:
    lines = []
    for segment in segments:
        start = float(segment.get("start", 0.0))
        h, rem = divmod(int(start), 3600)
        m, s = divmod(rem, 60)
        text = str(segment.get("text", "")).strip()
        lines.append(f"[{h:02d}:{m:02d}:{s:02d}]  {text}")
    return "\n".join(lines)
