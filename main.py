import customtkinter as ctk
import whisper
import threading
import warnings
import os
warnings.filterwarnings("ignore")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VideoTranscriber(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎬 Video Transcriber")
        self.geometry("750x580")
        self.resizable(True, True)
        self.video_path = None

        # ── Тақырып ──
        ctk.CTkLabel(
            self, text="🎬 Video Transcriber",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self, text="Видеодан мәтін алу",
            font=ctk.CTkFont(size=13), text_color="gray"
        ).pack(pady=(0, 15))

        # ── Файл таңдау ──
        file_frame = ctk.CTkFrame(self, corner_radius=12)
        file_frame.pack(padx=20, pady=5, fill="x")

        self.file_label = ctk.CTkLabel(
            file_frame,
            text="📁  Файл таңдалмаған",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            anchor="w"
        )
        self.file_label.pack(side="left", padx=15, pady=12, fill="x", expand=True)

        ctk.CTkButton(
            file_frame, text="Таңдау",
            width=100, corner_radius=8,
            command=self.browse_file
        ).pack(side="right", padx=10, pady=8)

        # ── Модель таңдау ──
        model_frame = ctk.CTkFrame(self, corner_radius=12)
        model_frame.pack(padx=20, pady=5, fill="x")

        ctk.CTkLabel(
            model_frame, text="Модель:",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=15, pady=12)

        self.model_var = ctk.StringVar(value="base")
        ctk.CTkSegmentedButton(
            model_frame,
            values=["tiny", "base", "small", "medium"],
            variable=self.model_var,
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=10, pady=10)

        # ── Транскрипция батырмасы ──
        self.start_btn = ctk.CTkButton(
            self, text="▶   Транскрипциялау",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45, corner_radius=12,
            fg_color="#1f6aa5", hover_color="#144870",
            command=self.start_transcription
        )
        self.start_btn.pack(padx=20, pady=12, fill="x")

        # ── Прогресс ──
        self.progress = ctk.CTkProgressBar(self, corner_radius=8, height=12)
        self.progress.pack(padx=20, pady=(0, 4), fill="x")
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            self, text="Дайын",
            font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.status_label.pack()

        # ── Мәтін аймағы ──
        self.textbox = ctk.CTkTextbox(
            self, corner_radius=12,
            font=ctk.CTkFont(size=13), wrap="word"
        )
        self.textbox.pack(padx=20, pady=10, fill="both", expand=True)

        # ── Сақтау батырмасы ──
        self.save_btn = ctk.CTkButton(
            self, text="💾   Файлға сақтау",
            font=ctk.CTkFont(size=14),
            height=40, corner_radius=12,
            fg_color="#2d6a2d", hover_color="#1a3d1a",
            command=self.save_text
        )
        self.save_btn.pack(padx=20, pady=(0, 20), fill="x")

    # ── Файл таңдауыш (CTkFileDialog) ──
    def browse_file(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Видео таңдау")
        dialog.geometry("520x400")
        dialog.update()  # ← осыны қос
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="Видео файлдың толық жолын жаз:",
            font=ctk.CTkFont(size=13)
        ).pack(pady=(20, 8), padx=20)

        path_entry = ctk.CTkEntry(
            dialog, width=460, height=38,
            placeholder_text="/home/asfandiar/video.mp4",
            font=ctk.CTkFont(size=12)
        )
        path_entry.pack(padx=20, pady=5)

        ctk.CTkLabel(
            dialog,
            text="Қолдайтын форматтар: mp4 · mkv · avi · mov · webm",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(pady=5)

        def confirm():
            path = path_entry.get().strip()
            if path and os.path.exists(path):
                self.video_path = path
                self.file_label.configure(
                    text=f"✅  {os.path.basename(path)}",
                    text_color="white"
                )
                dialog.destroy()
            else:
                ctk.CTkLabel(
                    dialog, text="⚠️ Файл табылмады!",
                    text_color="red", font=ctk.CTkFont(size=12)
                ).pack()

        ctk.CTkButton(
            dialog, text="✅ Растау",
            height=38, corner_radius=10,
            command=confirm
        ).pack(pady=15, padx=20, fill="x")

    # ── Сақтау диалогы ──
    def save_text(self):
        text = self.textbox.get("0.0", "end").strip()
        if not text:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Сақтау")
        dialog.geometry("520x220")
        dialog.update()  # ← осыны қос
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="Файл атын жаз (.txt):",
            font=ctk.CTkFont(size=13)
        ).pack(pady=(20, 8), padx=20)

        name_entry = ctk.CTkEntry(
            dialog, width=460, height=38,
            placeholder_text="transcript.txt",
            font=ctk.CTkFont(size=12)
        )
        name_entry.pack(padx=20, pady=5)

        def save():
            name = name_entry.get().strip() or "transcript.txt"
            if not name.endswith(".txt"):
                name += ".txt"
            save_path = os.path.join(
                os.path.expanduser("~"), "Documents", name
            )
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_label.configure(
                text=f"✅ Сақталды: {save_path}", text_color="lightgreen"
            )
            dialog.destroy()

        ctk.CTkButton(
            dialog, text="💾 Сақтау",
            height=38, corner_radius=10,
            fg_color="#2d6a2d", hover_color="#1a3d1a",
            command=save
        ).pack(pady=15, padx=20, fill="x")

    def start_transcription(self):
        if not self.video_path:
            self.status_label.configure(
                text="⚠️ Алдымен видео таңдаңыз!", text_color="orange"
            )
            return
        threading.Thread(target=self.transcribe).start()

    def transcribe(self):
        self.start_btn.configure(state="disabled")
        self.status_label.configure(text="⏳ Модель жүктелуде...", text_color="gray")
        self.progress.set(0.2)

        model = whisper.load_model(self.model_var.get())
        self.status_label.configure(text="🔄 Транскрипциялануда...", text_color="gray")
        self.progress.set(0.6)

        result = model.transcribe(self.video_path, language="en")

        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", result["text"])

        self.progress.set(1.0)
        self.status_label.configure(text="✅ Дайын!", text_color="lightgreen")
        self.start_btn.configure(state="normal")


if __name__ == "__main__":
    app = VideoTranscriber()
    app.mainloop()
