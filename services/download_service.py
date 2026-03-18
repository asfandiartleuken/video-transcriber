import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
from typing import Any

from app_errors import CancelledError, DependencyError, DownloadError
from media_tools import get_tool_binary

DOWNLOAD_TIMEOUT_SECONDS = 30
DOWNLOAD_RETRIES = 2
DOWNLOAD_CHUNK_SIZE = 1024 * 64
MAX_DOWNLOAD_SIZE_MB = 1024
ALLOWED_CONTENT_PREFIXES = ("video/",)
ALLOWED_CONTENT_TYPES = {"application/octet-stream"}


def validate_response_headers(headers: Any) -> int:
    total_size = int(headers.get("Content-Length", 0) or 0)
    max_bytes = MAX_DOWNLOAD_SIZE_MB * 1024 * 1024
    if total_size > 0 and total_size > max_bytes:
        raise DownloadError(f"Видео тым үлкен: {total_size // (1024 * 1024)} MB (лимит {MAX_DOWNLOAD_SIZE_MB} MB)")

    content_type = (headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if content_type:
        is_allowed_type = content_type in ALLOWED_CONTENT_TYPES or any(
            content_type.startswith(prefix) for prefix in ALLOWED_CONTENT_PREFIXES
        )
        if not is_allowed_type:
            raise DownloadError(f"Қолдау жоқ Content-Type: {content_type}")
    return total_size


def download_video(
    url: str,
    dest_path: str,
    cancel_event: threading.Event,
    progress_callback=None,
) -> None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (VideoTranscriber/1.0)"},
    )
    max_bytes = MAX_DOWNLOAD_SIZE_MB * 1024 * 1024
    last_error: Exception | None = None

    for attempt in range(DOWNLOAD_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                total_size = validate_response_headers(response.headers)
                downloaded = 0

                with open(dest_path, "wb") as file_handle:
                    while True:
                        if cancel_event.is_set():
                            raise CancelledError("Операция тоқтатылды.")
                        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        file_handle.write(chunk)
                        downloaded += len(chunk)
                        if downloaded > max_bytes:
                            raise DownloadError(f"Видео лимиттен асты ({MAX_DOWNLOAD_SIZE_MB} MB).")
                        if progress_callback and total_size > 0:
                            progress_callback(min(downloaded / total_size, 1.0))
                if downloaded == 0:
                    raise DownloadError("Сілтеме бос файл қайтарды. Тікелей видео URL қолданыңыз.")
            return
        except CancelledError:
            raise
        except (urllib.error.URLError, TimeoutError, OSError, DownloadError) as exc:
            last_error = exc
            if attempt >= DOWNLOAD_RETRIES:
                break
            time.sleep(1.0 + attempt * 0.8)

    raise DownloadError(f"Видеоны жүктеу сәтсіз аяқталды: {last_error}")


def download_youtube_video(
    url: str,
    dest_path: str,
    cancel_event: threading.Event,
    progress_callback=None,
) -> None:
    yt_dlp_bin = get_tool_binary("yt-dlp")
    if yt_dlp_bin is None:
        raise DependencyError(
            "YouTube сілтемесі үшін `yt-dlp` керек.\n\n"
            "Орнату:\n"
            "  • Windows: winget install yt-dlp\n"
            "  • Arch Linux: sudo pacman -S yt-dlp\n"
            "  • macOS: brew install yt-dlp"
        )

    cmd = [
        yt_dlp_bin,
        "--no-playlist",
        "--newline",
        "--no-warnings",
        "--force-overwrites",
        "--progress",
        "-f",
        "best[ext=mp4]/best",
        "-o",
        dest_path,
        url,
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    percent_pattern = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")

    while True:
        if cancel_event.is_set():
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            raise CancelledError("Операция тоқтатылды.")

        line = process.stdout.readline() if process.stdout else ""
        if not line:
            if process.poll() is not None:
                break
            time.sleep(0.05)
            continue

        if progress_callback:
            match = percent_pattern.search(line)
            if match:
                try:
                    percent = float(match.group(1)) / 100.0
                except ValueError:
                    percent = 0.0
                progress_callback(min(max(percent, 0.0), 1.0))

    return_code = process.wait()
    if return_code != 0:
        raise DownloadError("YouTube видеосын жүктеу сәтсіз аяқталды. Сілтемені тексеріңіз.")
