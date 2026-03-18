import os
import queue
import threading
import logging
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from app_config import DEFAULT_LANGUAGE, VIDEO_EXTENSIONS, WHISPER_MODELS, load_settings, save_settings
from app_errors import CancelledError, DependencyError, DownloadError
from media_tools import get_video_duration
from services.transcription_service import TranscriptionService
from transcriber_core import is_url

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
logger = logging.getLogger(__name__)


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
        self._display_timestamps = False
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

        self._toggle_view_btn = ctk.CTkButton(
            btn_bar,
            text="🕐  TS көру",
            height=36,
            width=130,
            state="disabled",
            fg_color="#6b5f1a",
            hover_color="#4a4112",
            command=self._toggle_timestamp_view,
        )
        self._toggle_view_btn.grid(row=0, column=4, padx=4)

        self._reset_btn = ctk.CTkButton(
            btn_bar,
            text="♻  Тазалау",
            height=36,
            width=120,
            fg_color="#3f3f3f",
            hover_color="#2a2a2a",
            command=self._reset_output,
        )
        self._reset_btn.grid(row=0, column=5, padx=4)


    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Видео файл таңдаңыз",
            initialdir=self._settings.get("last_dir", os.path.expanduser("~")),
            filetypes=VIDEO_EXTENSIONS,
        )
        if not path:
            return
        try:
            self._video_path = path
            self._url_entry.delete(0, "end")
            name = os.path.basename(path)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            duration = get_video_duration(path)
            self._file_label.configure(text=f"✅  {name}  ({size_mb:.1f} MB · {duration})", text_color="white")
            self._save_current_settings(last_dir=os.path.dirname(path))
        except OSError as exc:
            logger.exception("Failed to read selected file metadata")
            messagebox.showerror("Қате", f"Файл туралы ақпаратты оқу сәтсіз аяқталды: {exc}")

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

        self._save_current_settings()

        self._job_counter += 1
        self._active_job_id = self._job_counter
        self._cancel_event.clear()

        self._transcribe_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal")
        self._save_txt_btn.configure(state="disabled")
        self._save_srt_btn.configure(state="disabled")
        self._toggle_view_btn.configure(state="disabled")
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
        self._display_timestamps = bool(self._ts_var.get())

        self._render_output()

        words = len(self._transcript_text.split())
        chars = len(self._transcript_text)
        self._stats_label.configure(text=f"{words} сөз · {chars} таңба")

        self._set_progress(1.0, "✅  Транскрипция дайын!")
        self._transcribe_btn.configure(state="normal")
        self._cancel_btn.configure(state="disabled")

        if self._transcript_text:
            self._save_txt_btn.configure(state="normal")
            self._save_srt_btn.configure(state="normal")
            self._toggle_view_btn.configure(state="normal")
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
            initialdir=self._settings.get("last_dir", os.path.expanduser("~")),
            filetypes=filetypes,
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as file_handle:
                file_handle.write(content)
            self._save_current_settings(last_dir=os.path.dirname(path))
            messagebox.showinfo("Сақталды", f"Файл сақталды:\n{path}")
        except OSError as exc:
            logger.exception("Save failed for %s", path)
            messagebox.showerror("Сақтау қатесі", str(exc))

    def _render_output(self):
        display = self._segments_to_timestamped_text() if self._display_timestamps else self._transcript_text
        self._text_box.delete("1.0", "end")
        self._text_box.insert("1.0", display or "(Мәтін анықталмады)")

    def _segments_to_timestamped_text(self) -> str:
        lines = []
        for segment in self._segments:
            start = float(segment.get("start", 0.0))
            h, rem = divmod(int(start), 3600)
            m, s = divmod(rem, 60)
            text = str(segment.get("text", "")).strip()
            lines.append(f"[{h:02d}:{m:02d}:{s:02d}]  {text}")
        return "\n".join(lines)

    def _toggle_timestamp_view(self):
        if not self._transcript_text:
            return
        self._display_timestamps = not self._display_timestamps
        self._toggle_view_btn.configure(text="📝  Мәтін көру" if self._display_timestamps else "🕐  TS көру")
        self._render_output()

    def _reset_output(self):
        self._transcript_text = ""
        self._srt_text = ""
        self._segments = []
        self._display_timestamps = False
        self._text_box.delete("1.0", "end")
        self._stats_label.configure(text="")
        self._set_progress(0.0, "Дайын")
        self._save_txt_btn.configure(state="disabled")
        self._save_srt_btn.configure(state="disabled")
        self._copy_btn.configure(state="disabled")
        self._toggle_view_btn.configure(state="disabled", text="🕐  TS көру")

    def _save_current_settings(self, last_dir: str | None = None):
        if last_dir:
            self._settings["last_dir"] = last_dir
        self._settings["model"] = self._model_var.get()
        self._settings["language"] = self._lang_entry.get().strip()
        self._settings["timestamps"] = self._ts_var.get()
        save_settings(self._settings)

    def _set_progress(self, value: float, status: str):
        self._progress.set(value)
        self._status_label.configure(text=status)
