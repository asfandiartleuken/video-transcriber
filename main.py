"""
Video Transcriber — CustomTkinter + OpenAI Whisper
Барлық функциялары бар толық нұсқа (URL қолдауымен).
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import queue
import os
import subprocess
import tempfile
import json
import urllib.request
from pathlib import Path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

VIDEO_EXTENSIONS = (
    ("Видео файлдар", "*.mp4 *.mkv *.avi *.mov *.webm"),
    ("Барлық файлдар", "*.*"),
)
WHISPER_MODELS   = ["tiny", "base", "small", "medium"]
DEFAULT_LANGUAGE = "en"
CONFIG_PATH      = Path.home() / ".config" / "video-transcriber" / "settings.json"


# ─── Утилиттер ────────────────────────────────────────────────────────────────

def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")


def check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def get_video_duration(video_path: str) -> str:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             video_path],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        seconds = float(result.stdout.decode().strip())
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
    except Exception:
        return "?"


def extract_audio(video_path: str, audio_path: str) -> None:
    cmd = ["ffmpeg", "-y", "-i", video_path,
           "-vn", "-acodec", "pcm_s16le",
           "-ar", "16000", "-ac", "1", audio_path]
    result = subprocess.run(cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg қатесі:\n{result.stderr.decode('utf-8', errors='ignore')}"
        )


def download_video(url: str, dest_path: str, progress_callback=None) -> None:
    def _reporthook(block_num, block_size, total_size):
        if progress_callback and total_size > 0:
            percent = min(block_num * block_size / total_size, 1.0)
            progress_callback(percent)
    urllib.request.urlretrieve(url, dest_path, reporthook=_reporthook)


def seconds_to_srt_time(s: float) -> str:
    ms = int((s % 1) * 1000)
    s  = int(s)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def segments_to_srt(segments: list) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        start = seconds_to_srt_time(seg["start"])
        end   = seconds_to_srt_time(seg["end"])
        lines.append(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n")
    return "\n".join(lines)


def segments_to_timestamped(segments: list) -> str:
    lines = []
    for seg in segments:
        start = seconds_to_srt_time(seg["start"]).replace(",", ".")
        lines.append(f"[{start}]  {seg['text'].strip()}")
    return "\n".join(lines)


# ─── Параметрлер ─────────────────────────────────────────────────────────────

def load_settings() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"model": "base", "language": DEFAULT_LANGUAGE, "timestamps": False}


def save_settings(data: dict) -> None:
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ─── Негізгі қолданба ─────────────────────────────────────────────────────────

class VideoTranscriberApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎙 Видео Транскриптор")
        self.geometry("900x740")
        self.minsize(750, 600)

        self._video_path: str         = ""
        self._transcript_text: str    = ""
        self._srt_text: str           = ""
        self._segments: list          = []
        self._task_queue: queue.Queue = queue.Queue()
        self._cancel_event            = threading.Event()
        self._settings                = load_settings()

        self._build_ui()
        self._poll_queue()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # ── Тақырып ──────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, corner_radius=12)
        header.grid(row=0, column=0, padx=16, pady=(16, 6), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header,
                     text="🎙  Видео Транскриптор",
                     font=ctk.CTkFont(size=22, weight="bold")
                     ).grid(row=0, column=0, padx=20, pady=(14, 2), sticky="w")

        ctk.CTkLabel(header,
                     text="Видеодан сөйлеуді автоматты түрде текстке айналдыру",
                     font=ctk.CTkFont(size=13), text_color="gray"
                     ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

        # ── Файл таңдау ───────────────────────────────────────────────────────
        file_frame = ctk.CTkFrame(self, corner_radius=12)
        file_frame.grid(row=1, column=0, padx=16, pady=6, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(file_frame, text="Локал файл:",
                     font=ctk.CTkFont(size=13, weight="bold"), width=100
                     ).grid(row=0, column=0, padx=(16, 8), pady=14)

        self._file_label = ctk.CTkLabel(
            file_frame, text="Файл таңдалмаған",
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w"
        )
        self._file_label.grid(row=0, column=1, padx=4, pady=14, sticky="ew")

        ctk.CTkButton(file_frame, text="📂  Файл таңдау",
                      width=140, command=self._select_file
                      ).grid(row=0, column=2, padx=(4, 16), pady=14)

        # ── URL енгізу ────────────────────────────────────────────────────────
        url_frame = ctk.CTkFrame(self, corner_radius=12)
        url_frame.grid(row=2, column=0, padx=16, pady=6, sticky="ew")
        url_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(url_frame, text="немесе URL:",
                     font=ctk.CTkFont(size=13, weight="bold"), width=100
                     ).grid(row=0, column=0, padx=(16, 8), pady=14)

        self._url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://example.com/video.mp4",
            font=ctk.CTkFont(size=12)
        )
        self._url_entry.grid(row=0, column=1, padx=4, pady=14, sticky="ew")

        ctk.CTkButton(url_frame, text="🔗  URL қолдану",
                      width=140, command=self._use_url
                      ).grid(row=0, column=2, padx=(4, 16), pady=14)

        # ── Параметрлер ───────────────────────────────────────────────────────
        opts = ctk.CTkFrame(self, corner_radius=12)
        opts.grid(row=3, column=0, padx=16, pady=6, sticky="ew")

        ctk.CTkLabel(opts, text="Модель:",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=0, padx=(16, 6), pady=14)

        self._model_var = ctk.StringVar(value=self._settings.get("model", "base"))
        ctk.CTkOptionMenu(opts, values=WHISPER_MODELS,
                          variable=self._model_var, width=120
                          ).grid(row=0, column=1, padx=(0, 16), pady=14, sticky="w")

        ctk.CTkLabel(opts, text="Тіл коды:",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=2, padx=(0, 6), pady=14)

        self._lang_entry = ctk.CTkEntry(opts,
                                        placeholder_text="en / ru / kk / auto",
                                        width=110)
        self._lang_entry.insert(0, self._settings.get("language", DEFAULT_LANGUAGE))
        self._lang_entry.grid(row=0, column=3, padx=(0, 16), pady=14, sticky="w")

        self._ts_var = ctk.BooleanVar(value=self._settings.get("timestamps", False))
        ctk.CTkCheckBox(opts, text="Timestamps",
                        variable=self._ts_var,
                        font=ctk.CTkFont(size=12)
                        ).grid(row=0, column=4, padx=(0, 16), pady=14)

        self._transcribe_btn = ctk.CTkButton(
            opts, text="▶  Транскрипциялау",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38, fg_color="#1f6aa5", hover_color="#144870",
            command=self._start_transcription
        )
        self._transcribe_btn.grid(row=0, column=5, padx=(0, 8), pady=14)

        self._cancel_btn = ctk.CTkButton(
            opts, text="⏹  Тоқтату",
            height=38, width=110,
            fg_color="#8B0000", hover_color="#5a0000",
            state="disabled", command=self._cancel_transcription
        )
        self._cancel_btn.grid(row=0, column=6, padx=(0, 16), pady=14)

        # ── Прогресс ──────────────────────────────────────────────────────────
        prog = ctk.CTkFrame(self, corner_radius=12)
        prog.grid(row=4, column=0, padx=16, pady=6, sticky="ew")
        prog.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            prog, text="Дайын",
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w"
        )
        self._status_label.grid(row=0, column=0, padx=16, pady=(10, 4), sticky="ew")

        self._progress = ctk.CTkProgressBar(prog)
        self._progress.set(0)
        self._progress.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")

        # ── Нәтиже мәтін ──────────────────────────────────────────────────────
        result_frame = ctk.CTkFrame(self, corner_radius=12)
        result_frame.grid(row=5, column=0, padx=16, pady=6, sticky="nsew")
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(result_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=12, pady=(12, 0), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top_bar, text="Транскрипция нәтижесі",
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
                     ).grid(row=0, column=0, sticky="w")

        self._stats_label = ctk.CTkLabel(
            top_bar, text="",
            font=ctk.CTkFont(size=11), text_color="gray", anchor="e"
        )
        self._stats_label.grid(row=0, column=1, sticky="e")

        self._text_box = ctk.CTkTextbox(
            result_frame, font=ctk.CTkFont(size=13),
            wrap="word", corner_radius=8
        )
        self._text_box.grid(row=1, column=0, padx=12, pady=(6, 12), sticky="nsew")

        # ── Батырмалар панелі ─────────────────────────────────────────────────
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.grid(row=6, column=0, padx=16, pady=(0, 16), sticky="ew")
        btn_bar.grid_columnconfigure(0, weight=1)

        self._copy_btn = ctk.CTkButton(
            btn_bar, text="📋  Clipboard",
            height=36, width=130, state="disabled",
            command=self._copy_to_clipboard
        )
        self._copy_btn.grid(row=0, column=1, padx=4)

        self._save_txt_btn = ctk.CTkButton(
            btn_bar, text="💾  .txt сақтау",
            height=36, width=140, state="disabled",
            fg_color="#2d6a2d", hover_color="#1a3d1a",
            command=self._save_txt
        )
        self._save_txt_btn.grid(row=0, column=2, padx=4)

        self._save_srt_btn = ctk.CTkButton(
            btn_bar, text="🎞  .srt сақтау",
            height=36, width=140, state="disabled",
            fg_color="#4a3080", hover_color="#2e1d55",
            command=self._save_srt
        )
        self._save_srt_btn.grid(row=0, column=3, padx=4)

    # ── Файл / URL таңдау ─────────────────────────────────────────────────────

    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Видео файл таңдаңыз",
            filetypes=VIDEO_EXTENSIONS
        )
        if not path:
            return
        self._video_path = path
        self._url_entry.delete(0, "end")
        name     = os.path.basename(path)
        size     = os.path.getsize(path) / (1024 * 1024)
        duration = get_video_duration(path)
        self._file_label.configure(
            text=f"✅  {name}  ({size:.1f} MB · {duration})",
            text_color="white"
        )

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
        self._file_label.configure(
            text=f"🔗  {short}",
            text_color="#5bc8f5"
        )

    # ── Транскрипция іске қосу ────────────────────────────────────────────────

    def _start_transcription(self):
        if not self._video_path:
            messagebox.showwarning("Ескерту", "Алдымен видео файл таңдаңыз немесе URL енгізіңіз.")
            return
        if not is_url(self._video_path) and not os.path.isfile(self._video_path):
            messagebox.showerror("Қате", "Таңдалған файл табылмады.")
            return

        save_settings({
            "model":      self._model_var.get(),
            "language":   self._lang_entry.get().strip(),
            "timestamps": self._ts_var.get(),
        })

        self._cancel_event.clear()
        self._transcribe_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal")
        self._save_txt_btn.configure(state="disabled")
        self._save_srt_btn.configure(state="disabled")
        self._copy_btn.configure(state="disabled")
        self._text_box.delete("1.0", "end")
        self._stats_label.configure(text="")
        self._set_progress(0.05, "Жүктеліп жатыр…")

        lang_raw = self._lang_entry.get().strip().lower()
        language = None if lang_raw in ("", "auto") else lang_raw

        threading.Thread(
            target=self._transcribe_worker,
            args=(self._video_path, self._model_var.get(), language),
            daemon=True
        ).start()

    def _cancel_transcription(self):
        self._cancel_event.set()
        self._set_progress(0, "⏹  Тоқтатылды")
        self._transcribe_btn.configure(state="normal")
        self._cancel_btn.configure(state="disabled")

    # ── Worker thread ─────────────────────────────────────────────────────────

    def _transcribe_worker(self, video_path, model_name, language):
        tmp_audio = None
        tmp_video = None
        try:
            if not check_ffmpeg():
                self._task_queue.put(("error",
                    "ffmpeg табылмады.\n\n"
                    "Орнату жолдары:\n"
                    "  • Arch Linux:  sudo pacman -S ffmpeg\n"
                    "  • Ubuntu:      sudo apt install ffmpeg\n"
                    "  • Windows:     winget install ffmpeg\n"
                    "  • macOS:       brew install ffmpeg"
                ))
                return

            # URL болса — жүктеу
            actual_path = video_path
            if is_url(video_path):
                self._task_queue.put(("status", (0.05, "Видео жүктелуде…")))
                tmp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                tmp_video.close()

                def _dl_progress(percent):
                    self._task_queue.put(("status", (
                        0.05 + percent * 0.15,
                        f"Жүктелуде… {int(percent * 100)}%"
                    )))

                download_video(video_path, tmp_video.name, _dl_progress)
                actual_path = tmp_video.name

            if self._cancel_event.is_set():
                return

            # Аудио алу
            self._task_queue.put(("status", (0.25, "Аудио шығарылуда…")))
            tmp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_audio.close()
            extract_audio(actual_path, tmp_audio.name)

            if self._cancel_event.is_set():
                return

            # Модель жүктеу
            self._task_queue.put(("status", (0.45, f"'{model_name}' моделі жүктелуде…")))
            import whisper
            model = whisper.load_model(model_name)

            if self._cancel_event.is_set():
                return

            # Транскрипция
            self._task_queue.put(("status", (0.70, "Транскрипциялануда… Күте тұрыңыз")))
            opts = {}
            if language:
                opts["language"] = language

            result   = model.transcribe(tmp_audio.name, **opts)
            segments = result.get("segments", [])
            plain    = result.get("text", "").strip()

            self._task_queue.put(("done", {
                "plain":    plain,
                "segments": segments,
                "srt":      segments_to_srt(segments),
                "ts_text":  segments_to_timestamped(segments),
            }))

        except Exception as exc:
            self._task_queue.put(("error", str(exc)))
        finally:
            for tmp in (tmp_audio, tmp_video):
                if tmp and os.path.exists(tmp.name):
                    try:
                        os.unlink(tmp.name)
                    except OSError:
                        pass

    # ── Queue polling ──────────────────────────────────────────────────────────

    def _poll_queue(self):
        try:
            while True:
                event, payload = self._task_queue.get_nowait()
                if event == "status":
                    self._set_progress(*payload)
                elif event == "done":
                    self._on_done(payload)
                elif event == "error":
                    self._on_error(payload)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)

    # ── Нәтиже ────────────────────────────────────────────────────────────────

    def _on_done(self, data: dict):
        self._segments        = data["segments"]
        self._transcript_text = data["plain"]
        self._srt_text        = data["srt"]

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

    def _on_error(self, message: str):
        self._set_progress(0, "❌  Қате шықты")
        self._transcribe_btn.configure(state="normal")
        self._cancel_btn.configure(state="disabled")
        messagebox.showerror("Қате", message)

    # ── Clipboard ─────────────────────────────────────────────────────────────

    def _copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self._transcript_text)
        self._status_label.configure(text="📋  Clipboard-қа көшірілді!")
        self.after(2000, lambda: self._status_label.configure(text="✅  Транскрипция дайын!"))

    # ── Сақтау ────────────────────────────────────────────────────────────────

    def _save_txt(self):
        self._save_file(
            title="Мәтінді сақтау (.txt)",
            default_ext=".txt", default_name="transcript.txt",
            filetypes=[("Мәтін файлдар", "*.txt"), ("Барлық файлдар", "*.*")],
            content=self._transcript_text,
        )

    def _save_srt(self):
        self._save_file(
            title="Субтитрді сақтау (.srt)",
            default_ext=".srt", default_name="transcript.srt",
            filetypes=[("SRT субтитр", "*.srt"), ("Барлық файлдар", "*.*")],
            content=self._srt_text,
        )

    def _save_file(self, title, default_ext, default_name, filetypes, content):
        if not content:
            messagebox.showinfo("Ақпарат", "Сақтайтын мәтін жоқ.")
            return
        path = filedialog.asksaveasfilename(
            title=title, defaultextension=default_ext,
            initialfile=default_name, filetypes=filetypes
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Сақталды", f"Файл сақталды:\n{path}")
        except OSError as exc:
            messagebox.showerror("Сақтау қатесі", str(exc))

    def _set_progress(self, value: float, status: str):
        self._progress.set(value)
        self._status_label.configure(text=status)


# ─── Іске қосу ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = VideoTranscriberApp()
    app.mainloop()
