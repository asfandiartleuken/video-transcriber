import json
import logging
import multiprocessing as mp
import os
import queue
import tempfile
import threading
from typing import Any

from app_errors import CancelledError
from media_tools import ensure_dependencies, extract_audio, validate_media_file
from services.download_service import download_video, download_youtube_video
from transcriber_core import is_url, is_youtube_url, segments_to_srt, segments_to_timestamped

logger = logging.getLogger(__name__)
MP_CTX = mp.get_context("spawn")


def _transcribe_audio_process(
    audio_path: str,
    model_name: str,
    language: str | None,
    result_queue,
    result_json_path: str,
) -> None:
    try:
        import whisper

        model = whisper.load_model(model_name)
        options = {}
        if language:
            options["language"] = language
        options["verbose"] = False
        result = model.transcribe(audio_path, **options)
        with open(result_json_path, "w", encoding="utf-8") as file_handle:
            json.dump(result, file_handle, ensure_ascii=False)
        result_queue.put(("ok", "ready"))
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
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_json:
            result_json_path = temp_json.name
        process = MP_CTX.Process(
            target=_transcribe_audio_process,
            args=(audio_path, model_name, language, result_queue, result_json_path),
            daemon=True,
        )
        process.start()

        status_callback(0.70, "Транскрипциялануда… Күте тұрыңыз")
        try:
            while process.is_alive():
                if self._cancel_event.is_set():
                    process.terminate()
                    process.join(timeout=2)
                    raise CancelledError("Операция тоқтатылды.")
                try:
                    status, payload = result_queue.get_nowait()
                    break
                except queue.Empty:
                    process.join(timeout=0.2)
            else:
                try:
                    status, payload = result_queue.get(timeout=2)
                except queue.Empty as exc:
                    raise RuntimeError("Whisper процесі нәтиже бермеді.") from exc

            if self._cancel_event.is_set():
                raise CancelledError("Операция тоқтатылды.")
            if status == "error":
                raise RuntimeError(payload)

            try:
                with open(result_json_path, "r", encoding="utf-8") as file_handle:
                    return json.load(file_handle)
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError("Whisper нәтижесін оқу сәтсіз аяқталды.") from exc
        finally:
            if os.path.exists(result_json_path):
                try:
                    os.unlink(result_json_path)
                except OSError:
                    logger.warning("Failed to remove temp file: %s", result_json_path)

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
