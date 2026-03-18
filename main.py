"""
Video Transcriber — CustomTkinter + OpenAI Whisper
Барлық функциялары бар толық нұсқа (URL қолдауымен).
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox

import json
import logging
import multiprocessing as mp
import os
import platform
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = (
    ("Видео файлдар", "*.mp4 *.mkv *.avi *.mov *.webm"),
    ("Барлық файлдар", "*.*"),
)
WHISPER_MODELS = ["tiny", "base", "small", "medium"]
DEFAULT_LANGUAGE = "en"

DOWNLOAD_TIMEOUT_SECONDS = 30
DOWNLOAD_RETRIES = 2
DOWNLOAD_CHUNK_SIZE = 1024 * 64
MAX_DOWNLOAD_SIZE_MB = 1024
ALLOWED_CONTENT_PREFIXES = ("video/",)
ALLOWED_CONTENT_TYPES = {"application/octet-stream"}

MP_CTX = mp.get_context("spawn")


def get_config_path() -> Path:
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        appdata = os.getenv("LOCALAPPDATA")
        if appdata:
            return Path(appdata) / "video-transcriber" / "settings.json"
        return home / "AppData" / "Local" / "video-transcriber" / "settings.json"
    if system == "Darwin":
        return home / "Library" / "Application Support" / "video-transcriber" / "settings.json"
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "video-transcriber" / "settings.json"
    return home / ".config" / "video-transcriber" / "settings.json"


CONFIG_PATH = get_config_path()


class CancelledError(Exception):
    pass


class DependencyError(RuntimeError):
    pass


class DownloadError(RuntimeError):
    pass


def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")


def is_youtube_url(url: str) -> bool:
    try:
        netloc = urlparse(url).netloc.lower()
    except ValueError:
        return False
    return any(host in netloc for host in ("youtube.com", "youtu.be", "m.youtube.com", "www.youtube.com"))


def ensure_dependencies() -> None:
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
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
        result = subprocess.run(
            [
                "ffprobe",
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
    cmd = [
        "ffmpeg",
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
    if not os.path.isfile(video_path):
        raise RuntimeError("Көрсетілген файл табылмады.")

    if os.path.getsize(video_path) == 0:
        raise RuntimeError("Файл бос. Дұрыс видео сілтемесін немесе файлды таңдаңыз.")

    probe = subprocess.run(
        [
            "ffprobe",
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
    yt_dlp_bin = shutil.which("yt-dlp")
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


def seconds_to_srt_time(seconds: float) -> str:
    ms = int((seconds % 1) * 1000)
    total_seconds = int(seconds)
    m, s = divmod(total_seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def segments_to_srt(segments: list[dict[str, Any]]) -> str:
    lines = []
    for index, segment in enumerate(segments, 1):
        start = seconds_to_srt_time(segment["start"])
        end = seconds_to_srt_time(segment["end"])
        lines.append(f"{index}\n{start} --> {end}\n{segment['text'].strip()}\n")
    return "\n".join(lines)


def segments_to_timestamped(segments: list[dict[str, Any]]) -> str:
    lines = []
    for segment in segments:
        start = seconds_to_srt_time(segment["start"]).replace(",", ".")
        lines.append(f"[{start}]  {segment['text'].strip()}")
    return "\n".join(lines)


def load_settings() -> dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except FileNotFoundError:
        return {"model": "base", "language": DEFAULT_LANGUAGE, "timestamps": False}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Settings read error: %s", exc)
        return {"model": "base", "language": DEFAULT_LANGUAGE, "timestamps": False}

    if not isinstance(data, dict):
        logger.warning("Settings file has invalid format, expected dict.")
        return {"model": "base", "language": DEFAULT_LANGUAGE, "timestamps": False}
    return data


def save_settings(data: dict[str, Any]) -> None:
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as file_handle:
            json.dump(data, file_handle, indent=2, ensure_ascii=False)
    except OSError as exc:
        logger.warning("Settings save error: %s", exc)


def _transcribe_audio_process(
    audio_path: str,
    model_name: str,
    language: str | None,
    result_queue,
) -> None:
    try:
        import whisper

        model = whisper.load_model(model_name)
        options = {}
        if language:
            options["language"] = language
        result = model.transcribe(audio_path, **options)
        result_queue.put(("ok", result))
    except Exception as exc:  # noqa: BLE001
        result_queue.put(("error", str(exc)))


class TranscriptionService:
    def __init__(self, cancel_event: threading.Event):
        self._cancel_event = cancel_event

    def _check_cancel(self) -> None:
        if self._cancel_event.is_set():
            raise CancelledError("Операция тоқтатылды.")

    def _transcribe_audio(
        self,
        audio_path: str,
        model_name: str,
        language: str | None,
        status_callback,
    ) -> dict[str, Any]:
        status_callback(0.45, f"'{model_name}' моделі жүктелуде…")
        result_queue = MP_CTX.Queue()
        process = MP_CTX.Process(
            target=_transcribe_audio_process,
            args=(audio_path, model_name, language, result_queue),
            daemon=True,
        )
        process.start()

        status_callback(0.70, "Транскрипциялануда… Күте тұрыңыз")
        while process.is_alive():
            if self._cancel_event.is_set():
                process.terminate()
                process.join(timeout=2)
                raise CancelledError("Операция тоқтатылды.")
            process.join(timeout=0.2)

        if self._cancel_event.is_set():
            raise CancelledError("Операция тоқтатылды.")

        try:
            status, payload = result_queue.get(timeout=1)
        except queue.Empty as exc:
            raise RuntimeError("Whisper процесі нәтиже бермеді.") from exc
        if status == "error":
            raise RuntimeError(payload)
        return payload

    def transcribe(
        self,
        video_path: str,
        model_name: str,
        language: str | None,
        status_callback,
    ) -> dict[str, Any]:
        tmp_audio_path: str | None = None
        tmp_video_path: str | None = None
        try:
            ensure_dependencies()
            self._check_cancel()

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                tmp_audio_path = temp_audio.name

            actual_path = video_path
            if is_url(video_path):
                status_callback(0.05, "Видео жүктелуде…")
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                    tmp_video_path = temp_video.name
                # yt-dlp can skip download when target already exists; remove placeholder temp file first.
                try:
                    os.unlink(tmp_video_path)
                except OSError:
                    pass

                def on_download_progress(percent: float) -> None:
                    status_callback(0.05 + percent * 0.15, f"Жүктелуде… {int(percent * 100)}%")

                if is_youtube_url(video_path):
                    download_youtube_video(video_path, tmp_video_path, self._cancel_event, on_download_progress)
                else:
                    download_video(video_path, tmp_video_path, self._cancel_event, on_download_progress)
                actual_path = tmp_video_path

            self._check_cancel()
            validate_media_file(actual_path)
            self._check_cancel()
            status_callback(0.25, "Аудио шығарылуда…")
            extract_audio(actual_path, tmp_audio_path, self._cancel_event)
            self._check_cancel()

            whisper_result = self._transcribe_audio(tmp_audio_path, model_name, language, status_callback)
            segments = whisper_result.get("segments", [])
            plain = whisper_result.get("text", "").strip()
            return {
                "plain": plain,
                "segments": segments,
                "srt": segments_to_srt(segments),
                "ts_text": segments_to_timestamped(segments),
            }
        finally:
            for path in (tmp_audio_path, tmp_video_path):
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError:
                        logger.warning("Failed to remove temp file: %s", path)


class VideoTranscriberApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎙 Видео Транскриптор")
        self.geometry("900x740")
        self.minsize(750, 600)

        self._video_path = ""
        self._transcript_text = ""
        self._srt_text = ""
        self._segments: list[dict[str, Any]] = []
        self._task_queue: queue.Queue = queue.Queue()
        self._cancel_event = threading.Event()
        self._settings = load_settings()
        self._job_counter = 0
        self._active_job_id = 0

        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        header = ctk.CTkFrame(self, corner_radius=12)
        header.grid(row=0, column=0, padx=16, pady=(16, 6), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="🎙  Видео Транскриптор", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(14, 2), sticky="w"
        )
        ctk.CTkLabel(
            header,
            text="Видеодан сөйлеуді автоматты түрде текстке айналдыру",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

        file_frame = ctk.CTkFrame(self, corner_radius=12)
        file_frame.grid(row=1, column=0, padx=16, pady=6, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(file_frame, text="Локал файл:", font=ctk.CTkFont(size=13, weight="bold"), width=100).grid(
            row=0, column=0, padx=(16, 8), pady=14
        )
        self._file_label = ctk.CTkLabel(
            file_frame,
            text="Файл таңдалмаған",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self._file_label.grid(row=0, column=1, padx=4, pady=14, sticky="ew")
        ctk.CTkButton(file_frame, text="📂  Файл таңдау", width=140, command=self._select_file).grid(
            row=0, column=2, padx=(4, 16), pady=14
        )

        url_frame = ctk.CTkFrame(self, corner_radius=12)
        url_frame.grid(row=2, column=0, padx=16, pady=6, sticky="ew")
        url_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(url_frame, text="немесе URL:", font=ctk.CTkFont(size=13, weight="bold"), width=100).grid(
            row=0, column=0, padx=(16, 8), pady=14
        )
        self._url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://example.com/video.mp4",
            font=ctk.CTkFont(size=12),
        )
        self._url_entry.grid(row=0, column=1, padx=4, pady=14, sticky="ew")
        ctk.CTkButton(url_frame, text="🔗  URL қолдану", width=140, command=self._use_url).grid(
            row=0, column=2, padx=(4, 16), pady=14
        )

        opts = ctk.CTkFrame(self, corner_radius=12)
        opts.grid(row=3, column=0, padx=16, pady=6, sticky="ew")
        ctk.CTkLabel(opts, text="Модель:", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, padx=(16, 6), pady=14
        )

        self._model_var = ctk.StringVar(value=self._settings.get("model", "base"))
        ctk.CTkOptionMenu(opts, values=WHISPER_MODELS, variable=self._model_var, width=120).grid(
            row=0, column=1, padx=(0, 16), pady=14, sticky="w"
        )

        ctk.CTkLabel(opts, text="Тіл коды:", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=2, padx=(0, 6), pady=14
        )
        self._lang_entry = ctk.CTkEntry(opts, placeholder_text="en / ru / kk / auto", width=110)
        self._lang_entry.insert(0, self._settings.get("language", DEFAULT_LANGUAGE))
        self._lang_entry.grid(row=0, column=3, padx=(0, 16), pady=14, sticky="w")

        self._ts_var = ctk.BooleanVar(value=self._settings.get("timestamps", False))
        ctk.CTkCheckBox(opts, text="Timestamps", variable=self._ts_var, font=ctk.CTkFont(size=12)).grid(
            row=0, column=4, padx=(0, 16), pady=14
        )

        self._transcribe_btn = ctk.CTkButton(
            opts,
            text="▶  Транскрипциялау",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self._start_transcription,
        )
        self._transcribe_btn.grid(row=0, column=5, padx=(0, 8), pady=14)

        self._cancel_btn = ctk.CTkButton(
            opts,
            text="⏹  Тоқтату",
            height=38,
            width=110,
            fg_color="#8B0000",
            hover_color="#5a0000",
            state="disabled",
            command=self._cancel_transcription,
        )
        self._cancel_btn.grid(row=0, column=6, padx=(0, 16), pady=14)

        prog = ctk.CTkFrame(self, corner_radius=12)
        prog.grid(row=4, column=0, padx=16, pady=6, sticky="ew")
        prog.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            prog,
            text="Дайын",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, padx=16, pady=(10, 4), sticky="ew")

        self._progress = ctk.CTkProgressBar(prog)
        self._progress.set(0)
        self._progress.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")

        result_frame = ctk.CTkFrame(self, corner_radius=12)
        result_frame.grid(row=5, column=0, padx=16, pady=6, sticky="nsew")
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(result_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=12, pady=(12, 0), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top_bar, text="Транскрипция нәтижесі", font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(
            row=0, column=0, sticky="w"
        )

        self._stats_label = ctk.CTkLabel(top_bar, text="", font=ctk.CTkFont(size=11), text_color="gray", anchor="e")
        self._stats_label.grid(row=0, column=1, sticky="e")

        self._text_box = ctk.CTkTextbox(result_frame, font=ctk.CTkFont(size=13), wrap="word", corner_radius=8)
        self._text_box.grid(row=1, column=0, padx=12, pady=(6, 12), sticky="nsew")

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.grid(row=6, column=0, padx=16, pady=(0, 16), sticky="ew")
        btn_bar.grid_columnconfigure(0, weight=1)

        self._copy_btn = ctk.CTkButton(
            btn_bar,
            text="📋  Clipboard",
            height=36,
            width=130,
            state="disabled",
            command=self._copy_to_clipboard,
        )
        self._copy_btn.grid(row=0, column=1, padx=4)

        self._save_txt_btn = ctk.CTkButton(
            btn_bar,
            text="💾  .txt сақтау",
            height=36,
            width=140,
            state="disabled",
            fg_color="#2d6a2d",
            hover_color="#1a3d1a",
            command=self._save_txt,
        )
        self._save_txt_btn.grid(row=0, column=2, padx=4)

        self._save_srt_btn = ctk.CTkButton(
            btn_bar,
            text="🎞  .srt сақтау",
            height=36,
            width=140,
            state="disabled",
            fg_color="#4a3080",
            hover_color="#2e1d55",
            command=self._save_srt,
        )
        self._save_srt_btn.grid(row=0, column=3, padx=4)

    def _select_file(self):
        path = filedialog.askopenfilename(title="Видео файл таңдаңыз", filetypes=VIDEO_EXTENSIONS)
        if not path:
            return
        self._video_path = path
        self._url_entry.delete(0, "end")
        name = os.path.basename(path)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        duration = get_video_duration(path)
        self._file_label.configure(text=f"✅  {name}  ({size_mb:.1f} MB · {duration})", text_color="white")

    def _use_url(self):
        url = self._url_entry.get().strip()
        if not url:
            messagebox.showwarning("Ескерту", "URL енгізіңіз.")
            return
        if not is_url(url):
            messagebox.showwarning("Ескерту", "URL http:// немесе https:// деп басталуы керек.")
            return
        self._video_path = url
        short = url.split("/")[-1][:55] or url[:55]
        self._file_label.configure(text=f"🔗  {short}", text_color="#5bc8f5")

    def _start_transcription(self):
        if not self._video_path:
            messagebox.showwarning("Ескерту", "Алдымен видео файл таңдаңыз немесе URL енгізіңіз.")
            return
        if not is_url(self._video_path) and not os.path.isfile(self._video_path):
            messagebox.showerror("Қате", "Таңдалған файл табылмады.")
            return

        save_settings(
            {
                "model": self._model_var.get(),
                "language": self._lang_entry.get().strip(),
                "timestamps": self._ts_var.get(),
            }
        )

        self._job_counter += 1
        self._active_job_id = self._job_counter
        self._cancel_event.clear()

        self._transcribe_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal")
        self._save_txt_btn.configure(state="disabled")
        self._save_srt_btn.configure(state="disabled")
        self._copy_btn.configure(state="disabled")
        self._text_box.delete("1.0", "end")
        self._stats_label.configure(text="")
        self._set_progress(0.02, "Дайындалуда…")

        lang_raw = self._lang_entry.get().strip().lower()
        language = None if lang_raw in ("", "auto") else lang_raw
        job_id = self._active_job_id

        threading.Thread(
            target=self._transcribe_worker,
            args=(job_id, self._video_path, self._model_var.get(), language),
            daemon=True,
        ).start()

    def _cancel_transcription(self):
        self._cancel_event.set()
        self._set_progress(0, "⏹  Тоқтатылды")
        self._transcribe_btn.configure(state="normal")
        self._cancel_btn.configure(state="disabled")

    def _transcribe_worker(self, job_id: int, video_path: str, model_name: str, language: str | None):
        service = TranscriptionService(self._cancel_event)
        try:
            result = service.transcribe(video_path, model_name, language, lambda p, s: self._push_status(job_id, p, s))
            if self._cancel_event.is_set():
                self._task_queue.put((job_id, "cancelled", None))
                return
            self._task_queue.put((job_id, "done", result))
        except CancelledError:
            self._task_queue.put((job_id, "cancelled", None))
        except DependencyError as exc:
            self._task_queue.put((job_id, "error", str(exc)))
        except DownloadError as exc:
            self._task_queue.put((job_id, "error", str(exc)))
        except RuntimeError as exc:
            self._task_queue.put((job_id, "error", str(exc)))
        except OSError as exc:
            self._task_queue.put((job_id, "error", f"I/O қатесі: {exc}"))

    def _push_status(self, job_id: int, progress: float, text: str):
        self._task_queue.put((job_id, "status", (progress, text)))

    def _poll_queue(self):
        try:
            while True:
                job_id, event, payload = self._task_queue.get_nowait()
                if job_id != self._active_job_id:
                    continue
                if event == "status":
                    self._set_progress(*payload)
                elif event == "done":
                    self._on_done(payload)
                elif event == "error":
                    self._on_error(payload)
                elif event == "cancelled":
                    self._on_cancelled()
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)

    def _on_done(self, data: dict[str, Any]):
        self._segments = data["segments"]
        self._transcript_text = data["plain"]
        self._srt_text = data["srt"]

        display = data["ts_text"] if self._ts_var.get() else data["plain"]
        self._text_box.delete("1.0", "end")
        self._text_box.insert("1.0", display or "(Мәтін анықталмады)")

        words = len(self._transcript_text.split())
        chars = len(self._transcript_text)
        self._stats_label.configure(text=f"{words} сөз · {chars} таңба")

        self._set_progress(1.0, "✅  Транскрипция дайын!")
        self._transcribe_btn.configure(state="normal")
        self._cancel_btn.configure(state="disabled")

        if self._transcript_text:
            self._save_txt_btn.configure(state="normal")
            self._save_srt_btn.configure(state="normal")
            self._copy_btn.configure(state="normal")

    def _on_cancelled(self):
        self._set_progress(0, "⏹  Тоқтатылды")
        self._transcribe_btn.configure(state="normal")
        self._cancel_btn.configure(state="disabled")

    def _on_error(self, message: str):
        self._set_progress(0, "❌  Қате шықты")
        self._transcribe_btn.configure(state="normal")
        self._cancel_btn.configure(state="disabled")
        messagebox.showerror("Қате", message)

    def _copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self._transcript_text)
        self._status_label.configure(text="📋  Clipboard-қа көшірілді!")
        self.after(2000, lambda: self._status_label.configure(text="✅  Транскрипция дайын!"))

    def _save_txt(self):
        self._save_file(
            title="Мәтінді сақтау (.txt)",
            default_ext=".txt",
            default_name="transcript.txt",
            filetypes=[("Мәтін файлдар", "*.txt"), ("Барлық файлдар", "*.*")],
            content=self._transcript_text,
        )

    def _save_srt(self):
        self._save_file(
            title="Субтитрді сақтау (.srt)",
            default_ext=".srt",
            default_name="transcript.srt",
            filetypes=[("SRT субтитр", "*.srt"), ("Барлық файлдар", "*.*")],
            content=self._srt_text,
        )

    def _save_file(self, title: str, default_ext: str, default_name: str, filetypes: list[tuple[str, str]], content: str):
        if not content:
            messagebox.showinfo("Ақпарат", "Сақтайтын мәтін жоқ.")
            return
        path = filedialog.asksaveasfilename(
            title=title,
            defaultextension=default_ext,
            initialfile=default_name,
            filetypes=filetypes,
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as file_handle:
                file_handle.write(content)
            messagebox.showinfo("Сақталды", f"Файл сақталды:\n{path}")
        except OSError as exc:
            messagebox.showerror("Сақтау қатесі", str(exc))

    def _set_progress(self, value: float, status: str):
        self._progress.set(value)
        self._status_label.configure(text=status)


if __name__ == "__main__":
    mp.freeze_support()
    app = VideoTranscriberApp()
    app.mainloop()
