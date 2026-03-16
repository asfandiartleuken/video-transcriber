"""
Video Transcriber — CustomTkinter + OpenAI Whisper
Видео файлдан сөйлеуді текстке айналдыратын desktop қолданба.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import queue
import os
import sys
import subprocess
import tempfile


# ─── Тақырып ──────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ─── Константалар ─────────────────────────────────────────────────────────────
VIDEO_EXTENSIONS = (
    ("Видео файлдар", "*.mp4 *.mkv *.avi *.mov *.webm"),
    ("Барлық файлдар", "*.*"),
)
WHISPER_MODELS = ["tiny", "base", "small", "medium"]
DEFAULT_LANGUAGE = "en"   # өзгерту оңай: "kk", "ru", "auto" (None) т.б.


def check_ffmpeg() -> bool:
    """ffmpeg орнатылғанын тексеру."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def extract_audio(video_path: str, audio_path: str) -> None:
    """ffmpeg арқылы видеодан аудио алу (wav форматы)."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg қатесі:\n{result.stderr.decode('utf-8', errors='ignore')}"
        )


# ─── Негізгі класс ────────────────────────────────────────────────────────────
class VideoTranscriberApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🎙 Видео Транскриптор")
        self.geometry("820x700")
        self.minsize(700, 580)

        # Ішкі күй
        self._video_path: str = ""
        self._transcript_text: str = ""
        self._task_queue: queue.Queue = queue.Queue()

        self._build_ui()
        self._poll_queue()   # GUI жаңарту циклін бастау

    # ── UI құрастыру ──────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # ── 1. Тақырып ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, corner_radius=12)
        header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="🎙  Видео Транскриптор",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(14, 2), sticky="w")

        ctk.CTkLabel(
            header,
            text="Видеодан сөйлеуді автоматты түрде текстке айналдыру",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

        # ── 2. Файл таңдау ────────────────────────────────────────────────────
        file_frame = ctk.CTkFrame(self, corner_radius=12)
        file_frame.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            file_frame,
            text="Видео файл:",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=90,
        ).grid(row=0, column=0, padx=(16, 8), pady=14)

        self._file_label = ctk.CTkLabel(
            file_frame,
            text="Файл таңдалмаған",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self._file_label.grid(row=0, column=1, padx=4, pady=14, sticky="ew")

        ctk.CTkButton(
            file_frame,
            text="📂  Файл таңдау",
            width=140,
            command=self._select_file,
        ).grid(row=0, column=2, padx=(4, 16), pady=14)

        # ── 3. Параметрлер ────────────────────────────────────────────────────
        opts_frame = ctk.CTkFrame(self, corner_radius=12)
        opts_frame.grid(row=2, column=0, padx=16, pady=8, sticky="ew")
        opts_frame.grid_columnconfigure((1, 3), weight=1)

        # Модель
        ctk.CTkLabel(
            opts_frame,
            text="Модель:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(16, 8), pady=14)

        self._model_var = ctk.StringVar(value="base")
        self._model_menu = ctk.CTkOptionMenu(
            opts_frame,
            values=WHISPER_MODELS,
            variable=self._model_var,
            width=130,
        )
        self._model_menu.grid(row=0, column=1, padx=(0, 24), pady=14, sticky="w")

        # Тіл
        ctk.CTkLabel(
            opts_frame,
            text="Тіл коды:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=2, padx=(0, 8), pady=14)

        self._lang_entry = ctk.CTkEntry(
            opts_frame,
            placeholder_text="en / ru / kk / auto",
            width=120,
        )
        self._lang_entry.insert(0, DEFAULT_LANGUAGE)
        self._lang_entry.grid(row=0, column=3, padx=(0, 16), pady=14, sticky="w")

        # Транскрипциялау батырмасы
        self._transcribe_btn = ctk.CTkButton(
            opts_frame,
            text="▶  Транскрипциялау",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            command=self._start_transcription,
        )
        self._transcribe_btn.grid(
            row=0, column=4, padx=(8, 16), pady=14
        )

        # ── 4. Прогресс / статус ──────────────────────────────────────────────
        prog_frame = ctk.CTkFrame(self, corner_radius=12)
        prog_frame.grid(row=3, column=0, padx=16, pady=8, sticky="ew")
        prog_frame.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            prog_frame,
            text="Дайын",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, padx=16, pady=(10, 4), sticky="ew")

        self._progress = ctk.CTkProgressBar(prog_frame)
        self._progress.set(0)
        self._progress.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")

        # ── 5. Нәтиже мәтін ──────────────────────────────────────────────────
        result_frame = ctk.CTkFrame(self, corner_radius=12)
        result_frame.grid(row=4, column=0, padx=16, pady=8, sticky="nsew")
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            result_frame,
            text="Транскрипция нәтижесі",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self._text_box = ctk.CTkTextbox(
            result_frame,
            font=ctk.CTkFont(size=13),
            wrap="word",
            corner_radius=8,
        )
        self._text_box.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        # ── 6. Сақтау батырмасы ───────────────────────────────────────────────
        self._save_btn = ctk.CTkButton(
            self,
            text="💾  Мәтінді сақтау (.txt)",
            height=38,
            state="disabled",
            command=self._save_transcript,
        )
        self._save_btn.grid(row=5, column=0, padx=16, pady=(4, 16), sticky="e")

    # ── Файл таңдау ───────────────────────────────────────────────────────────
    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Видео файл таңдаңыз",
            filetypes=VIDEO_EXTENSIONS,
        )
        if path:
            self._video_path = path
            short = os.path.basename(path)
            self._file_label.configure(text=short, text_color="white")

    # ── Транскрипция іске қосу ────────────────────────────────────────────────
    def _start_transcription(self):
        if not self._video_path:
            messagebox.showwarning("Ескерту", "Алдымен видео файл таңдаңыз.")
            return

        if not os.path.isfile(self._video_path):
            messagebox.showerror("Қате", "Таңдалған файл табылмады.")
            return

        # Батырмаларды өшіру
        self._transcribe_btn.configure(state="disabled")
        self._save_btn.configure(state="disabled")
        self._text_box.delete("1.0", "end")
        self._set_progress(0.05, "Жүктеліп жатыр…")

        lang_raw = self._lang_entry.get().strip().lower()
        language = None if lang_raw in ("", "auto") else lang_raw
        model_name = self._model_var.get()

        # Жеке thread-та іске қосу
        thread = threading.Thread(
            target=self._transcribe_worker,
            args=(self._video_path, model_name, language),
            daemon=True,
        )
        thread.start()

    # ── Жұмыс thread-і ───────────────────────────────────────────────────────
    def _transcribe_worker(self, video_path: str, model_name: str, language):
        """Бұл функция GUI-дан тыс жеке thread-та орындалады."""
        tmp_audio = None
        try:
            # ffmpeg тексеру
            if not check_ffmpeg():
                self._task_queue.put(("error",
                    "ffmpeg табылмады.\n\n"
                    "Орнату жолы:\n"
                    "  1) https://ffmpeg.org/download.html сайтына кіріңіз\n"
                    "  2) Жүктеп алыңыз және PATH-қа қосыңыз\n"
                    "  3) Немесе: winget install ffmpeg"
                ))
                return

            # Аудио алу
            self._task_queue.put(("status", (0.2, "Аудио шығарылуда…")))
            tmp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_audio.close()
            extract_audio(video_path, tmp_audio.name)

            # Whisper модельін жүктеу
            self._task_queue.put(("status", (0.4, f"'{model_name}' моделі жүктелуде…")))
            import whisper  # импорт мұнда — баяу import'ты GUI-дан жасырамыз
            model = whisper.load_model(model_name)

            # Транскрипция
            self._task_queue.put(("status", (0.7, "Транскрипциялануда… Күте тұрыңыз")))
            options = {}
            if language:
                options["language"] = language

            result = model.transcribe(tmp_audio.name, **options)
            text = result.get("text", "").strip()

            self._task_queue.put(("done", text))

        except Exception as exc:
            self._task_queue.put(("error", str(exc)))

        finally:
            # Уақытша файлды жою
            if tmp_audio and os.path.exists(tmp_audio.name):
                try:
                    os.unlink(tmp_audio.name)
                except OSError:
                    pass

    # ── Queue polling — thread-safe GUI жаңарту ───────────────────────────────
    def _poll_queue(self):
        """GUI main loop арқылы queue-ды тексереді — thread-safe тәсіл."""
        try:
            while True:
                event, payload = self._task_queue.get_nowait()
                if event == "status":
                    progress_val, msg = payload
                    self._set_progress(progress_val, msg)
                elif event == "done":
                    self._on_transcription_done(payload)
                elif event == "error":
                    self._on_transcription_error(payload)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)  # 100мс кейін қайта тексер

    # ── Нәтиже өңдеу ─────────────────────────────────────────────────────────
    def _on_transcription_done(self, text: str):
        self._transcript_text = text
        self._text_box.delete("1.0", "end")
        self._text_box.insert("1.0", text if text else "(Мәтін анықталмады)")
        self._set_progress(1.0, "✅  Транскрипция дайын!")
        self._transcribe_btn.configure(state="normal")
        if text:
            self._save_btn.configure(state="normal")

    def _on_transcription_error(self, message: str):
        self._set_progress(0, "❌  Қате шықты")
        self._transcribe_btn.configure(state="normal")
        messagebox.showerror("Қате", message)

    # ── Сақтау ───────────────────────────────────────────────────────────────
    def _save_transcript(self):
        if not self._transcript_text:
            messagebox.showinfo("Ақпарат", "Сақтайтын мәтін жоқ.")
            return

        path = filedialog.asksaveasfilename(
            title="Мәтінді сақтау",
            defaultextension=".txt",
            initialfile="transcript.txt",
            filetypes=[("Мәтін файлдар", "*.txt"), ("Барлық файлдар", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._transcript_text)
            messagebox.showinfo("Сақталды", f"Файл сақталды:\n{path}")
        except OSError as exc:
            messagebox.showerror("Сақтау қатесі", str(exc))

    # ── Көмекші ───────────────────────────────────────────────────────────────
    def _set_progress(self, value: float, status: str):
        self._progress.set(value)
        self._status_label.configure(text=status)


# ─── Негізгі нүкте ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = VideoTranscriberApp()
    app.mainloop()
if __name__ == "__main__":
    try:
        app = VideoTranscriberApp()
        app.mainloop()
    except KeyboardInterrupt:
        pass