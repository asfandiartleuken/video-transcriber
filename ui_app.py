import os
import queue
import threading
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from config import VIDEO_EXTENSIONS, load_settings, save_settings
from errors import CancelledError, DependencyError, DownloadError
from services import TranscriptionService
from ui import (
    ButtonBarFrame,
    FileSelectorFrame,
    HeaderFrame,
    OptionsFrame,
    ProgressFrame,
    ResultFrame,
    iter_edit_targets,
    iter_virtual_shortcut_sequences,
    perform_edit_action,
    resolve_control_shortcut,
)
from utils import format_timestamped_text, get_video_duration, is_url

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
        self._ts_text = ""
        self._display_timestamps = False
        self._task_queue: queue.Queue = queue.Queue()
        self._cancel_event = threading.Event()
        self._settings = load_settings()
        self._job_counter = 0
        self._active_job_id = 0

        self._build_ui()
        self._bind_shortcuts()
        self._poll_queue()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self._header = HeaderFrame(self)
        self._header.grid(row=0, column=0, padx=16, pady=(16, 6), sticky="ew")

        self._file_selector = FileSelectorFrame(
            self,
            on_file_select=self._select_file,
            on_url_use=self._use_url,
            settings=self._settings,
        )
        self._file_selector.grid(row=1, column=0, padx=16, pady=6, sticky="ew")

        self._options_frame = OptionsFrame(
            self,
            settings=self._settings,
            on_transcribe=self._start_transcription,
            on_cancel=self._cancel_transcription,
        )
        self._options_frame.grid(row=2, column=0, padx=16, pady=6, sticky="ew")

        self._progress = ProgressFrame(self)
        self._progress.grid(row=3, column=0, padx=16, pady=6, sticky="ew")

        self._result = ResultFrame(self)
        self._result.grid(row=4, column=0, padx=16, pady=6, sticky="nsew")

        self._button_bar = ButtonBarFrame(
            self,
            on_copy=self._copy_to_clipboard,
            on_save_txt=self._save_txt,
            on_save_srt=self._save_srt,
            on_toggle_view=self._toggle_timestamp_view,
            on_reset=self._reset_output,
        )
        self._button_bar.grid(row=5, column=0, padx=16, pady=(0, 16), sticky="ew")

    def _bind_shortcuts(self):
        editable_widgets = (
            self._file_selector._url_entry,
            self._options_frame._lang_entry,
            self._result.get_text_box(),
        )
        for widget in editable_widgets:
            for target in iter_edit_targets(widget):
                target.bind("<Control-KeyPress>", self._handle_control_shortcut)
                for action, sequence in iter_virtual_shortcut_sequences():
                    target.bind(
                        sequence,
                        lambda event, shortcut=action: self._handle_shortcut_action(event, shortcut),
                    )

    def _handle_control_shortcut(self, event):
        action = resolve_control_shortcut(event.keysym, event.char, event.keycode)
        if action is None:
            return None
        return self._handle_shortcut_action(event, action)

    def _handle_shortcut_action(self, event, action: str):
        try:
            handled = perform_edit_action(
                event.widget or self.focus_get(),
                action,
                self.clipboard_get,
                self._write_clipboard_text,
            )
            return "break" if handled else None
        except tk.TclError:
            return "break"

    def _write_clipboard_text(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)

    def _select_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Аудио/видео файл таңдаңыз",
            initialdir=self._settings.get("last_dir", os.path.expanduser("~")),
            filetypes=VIDEO_EXTENSIONS,
        )
        if not path:
            return
        try:
            self._video_path = path
            name = os.path.basename(path)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            duration = get_video_duration(path)
            self._file_selector.update_file_label(f"✅  {name}  ({size_mb:.1f} MB · {duration})", "white")
            self._save_current_settings(last_dir=os.path.dirname(path))
        except OSError as exc:
            logger.exception("Failed to read selected file metadata")
            messagebox.showerror("Қате", f"Файл туралы ақпаратты оқу сәтсіз аяқталды: {exc}", parent=self)

    def _use_url(self):
        url = self._file_selector.get_url()
        if not url:
            messagebox.showwarning("Ескерту", "URL енгізіңіз.", parent=self)
            return
        if not is_url(url):
            messagebox.showwarning("Ескерту", "URL http:// немесе https:// деп басталуы керек.", parent=self)
            return
        self._video_path = url
        short = url.split("/")[-1][:55] or url[:55]
        self._file_selector.update_file_label(f"🔗  {short}", "#5bc8f5")

    def _start_transcription(self):
        self._save_current_settings()
        if not self._video_path:
            messagebox.showwarning(
                "Ескерту", "Алдымен аудио/видео файл таңдаңыз немесе URL енгізіңіз.", parent=self
            )
            return
        self._run_transcription_job(self._video_path, "Дайындалуда…")

    def _cancel_transcription(self):
        self._cancel_event.set()
        self._progress.set_progress(0, "⏹  Тоқтатылды")
        self._options_frame.set_transcribe_state(True)
        self._options_frame.set_cancel_state(False)

    def _run_transcription_job(self, video_path: str, status_text: str):
        if not is_url(video_path) and not os.path.isfile(video_path):
            messagebox.showerror("Қате", "Таңдалған файл табылмады.", parent=self)
            return

        self._job_counter += 1
        self._active_job_id = self._job_counter
        self._cancel_event.clear()
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except queue.Empty:
                break

        self._options_frame.set_transcribe_state(False)
        self._options_frame.set_cancel_state(True)
        self._button_bar.set_output_buttons_state(False)
        self._result.get_text_box().delete("1.0", "end")
        self._result.clear_stats()
        self._progress.set_progress(0.02, status_text)

        language = self._options_frame.get_language()
        job_id = self._active_job_id

        threading.Thread(
            target=self._transcribe_worker,
            args=(job_id, video_path, self._options_frame.get_model(), language),
            daemon=True,
        ).start()

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
                    self._progress.set_progress(*payload)
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
        self._transcript_text = data["text"]
        self._srt_text = data["srt"]
        self._ts_text = data["ts_text"]
        self._display_timestamps = bool(self._options_frame.get_timestamps())

        self._render_output()
        self._result.set_stats(data.get("word_count", 0), data.get("char_count", 0))

        self._progress.set_progress(1.0, "✅  Транскрипция дайын!")
        self._options_frame.set_transcribe_state(True)
        self._options_frame.set_cancel_state(False)

        if self._transcript_text:
            self._button_bar.set_output_buttons_state(True)

    def _on_cancelled(self):
        self._progress.set_progress(0, "⏹  Тоқтатылды")
        self._options_frame.set_transcribe_state(True)
        self._options_frame.set_cancel_state(False)

    def _on_error(self, message: str):
        self._progress.set_progress(0, "❌  Қате шықты")
        self._options_frame.set_transcribe_state(True)
        self._options_frame.set_cancel_state(False)
        messagebox.showerror("Қате", message, parent=self)

    def _copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self._transcript_text)
        self._progress.set_status_text("📋  Clipboard-қа көшірілді!")
        self.after(2000, lambda: self._progress.set_status_text("✅  Транскрипция дайын!"))

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
            messagebox.showinfo("Ақпарат", "Сақтайтын мәтін жоқ.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
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
            messagebox.showinfo("Сақталды", f"Файл сақталды:\n{path}", parent=self)
        except OSError as exc:
            logger.exception("Save failed for %s", path)
            messagebox.showerror("Сақтау қатесі", str(exc), parent=self)

    def _render_output(self):
        text_box = self._result.get_text_box()
        display = self._ts_text if self._display_timestamps else self._transcript_text
        text_box.delete("1.0", "end")
        text_box.insert("1.0", display or "(Мәтін анықталмады)")

    def _toggle_timestamp_view(self):
        if not self._transcript_text:
            return
        self._display_timestamps = not self._display_timestamps
        self._button_bar.toggle_view_button(self._display_timestamps)
        self._render_output()

    def _reset_output(self):
        self._transcript_text = ""
        self._srt_text = ""
        self._ts_text = ""
        self._display_timestamps = False
        self._result.get_text_box().delete("1.0", "end")
        self._result.clear_stats()
        self._progress.set_progress(0.0, "Дайын")
        self._button_bar.set_output_buttons_state(False)
        self._button_bar.reset_view_button()

    def _save_current_settings(self, last_dir: str | None = None):
        if last_dir:
            self._settings["last_dir"] = last_dir
        self._settings["model"] = self._options_frame.get_model()
        self._settings["language"] = self._options_frame._lang_entry.get().strip()
        self._settings["timestamps"] = self._options_frame.get_timestamps()
        save_settings(self._settings)
