import logging
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from app_errors import CancelledError, DependencyError

logger = logging.getLogger(__name__)


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_tool_binary(tool_name: str) -> str | None:
    app_root = get_app_root()
    candidates = [tool_name]
    if os.name == "nt" and not tool_name.lower().endswith(".exe"):
        candidates.append(f"{tool_name}.exe")

    for candidate in candidates:
        bundled = app_root / "tools" / candidate
        if bundled.is_file():
            return str(bundled)

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def add_bundled_tools_to_path() -> None:
    tools_dir = get_app_root() / "tools"
    if not tools_dir.is_dir():
        return

    current_path = os.environ.get("PATH", "")
    parts = current_path.split(os.pathsep) if current_path else []
    tools_str = str(tools_dir)
    if tools_str not in parts:
        os.environ["PATH"] = tools_str + (os.pathsep + current_path if current_path else "")


def ensure_dependencies() -> None:
    missing = [tool for tool in ("ffmpeg", "ffprobe") if get_tool_binary(tool) is None]
    if not missing:
        return
    tools = ", ".join(missing)
    raise DependencyError(
        f"Қажетті құрал(дар) табылмады: {tools}\n\n"
        "Орнату жолдары:\n"
        "  • Windows: winget install ffmpeg\n"
        "  • Arch Linux: sudo pacman -S ffmpeg\n"
        "  • macOS: brew install ffmpeg"
    )


def get_video_duration(video_path: str) -> str:
    try:
        ffprobe_bin = get_tool_binary("ffprobe")
        if ffprobe_bin is None:
            return "?"
        result = subprocess.run(
            [
                ffprobe_bin,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        seconds = float(result.stdout.strip())
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
    except (subprocess.SubprocessError, ValueError, OSError):
        return "?"


def extract_audio(video_path: str, audio_path: str, cancel_event: threading.Event) -> None:
    ffmpeg_bin = get_tool_binary("ffmpeg")
    if ffmpeg_bin is None:
        raise DependencyError("`ffmpeg` табылмады.")
    cmd = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        audio_path,
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    while process.poll() is None:
        if cancel_event.is_set():
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            raise CancelledError("Операция тоқтатылды.")
        time.sleep(0.1)

    if process.returncode != 0:
        stderr = process.stderr.read() if process.stderr else ""
        cleaned = "\n".join(line.strip() for line in stderr.splitlines() if line.strip())
        raise RuntimeError(f"ffmpeg қатесі:\n{cleaned or 'Аудио шығару сәтсіз аяқталды.'}")


def validate_media_file(video_path: str) -> None:
    ffprobe_bin = get_tool_binary("ffprobe")
    if ffprobe_bin is None:
        raise DependencyError("`ffprobe` табылмады.")
    if not os.path.isfile(video_path):
        raise RuntimeError("Көрсетілген файл табылмады.")

    if os.path.getsize(video_path) == 0:
        raise RuntimeError("Файл бос. Дұрыс видео сілтемесін немесе файлды таңдаңыз.")

    probe = subprocess.run(
        [
            ffprobe_bin,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "csv=p=0",
            video_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if probe.returncode != 0:
        details = "\n".join(line.strip() for line in probe.stderr.splitlines() if line.strip())
        raise RuntimeError(
            "Файл видео ретінде ашылмады. Бұл сілтеме тікелей видео емес немесе файл бүлінген.\n"
            f"{details or 'ffprobe файлды оқи алмады.'}"
        )

    stream_types = {line.strip() for line in probe.stdout.splitlines() if line.strip()}
    if not stream_types.intersection({"video", "audio"}):
        raise RuntimeError("Файлда audio/video ағындары табылмады.")
