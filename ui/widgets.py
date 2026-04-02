import customtkinter as ctk


class HeaderFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=12)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="🎙  Видео Транскриптор",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(14, 2), sticky="w")
        ctk.CTkLabel(
            self,
            text="Видеодан сөйлеуді автоматты түрде текстке айналдыру",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")


class FileSelectorFrame(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_file_select,
        on_url_use,
        settings: dict,
    ):
        super().__init__(parent, corner_radius=12)
        self.grid_columnconfigure(1, weight=1)
        self._on_file_select = on_file_select
        self._on_url_use = on_url_use
        self._settings = settings

        self._file_label = ctk.CTkLabel(
            self,
            text="Файл таңдалмаған",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self._file_label.grid(row=0, column=1, padx=4, pady=14, sticky="ew")

        self._setup_file_row()
        self._setup_url_row()

    def _setup_file_row(self):
        ctk.CTkLabel(
            self,
            text="Локал файл:",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=100,
        ).grid(row=0, column=0, padx=(16, 8), pady=14)
        ctk.CTkButton(
            self,
            text="📂  Файл таңдау",
            width=140,
            command=self._on_file_select,
        ).grid(row=0, column=2, padx=(4, 16), pady=14)

    def _setup_url_row(self):
        row = ctk.CTkFrame(self, corner_radius=12)
        row.grid(row=1, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="ew")
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row,
            text="URL:",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=100,
        ).grid(row=0, column=0, padx=(0, 8), pady=12)
        self._url_entry = ctk.CTkEntry(
            row,
            placeholder_text="https://example.com/video.mp4",
            font=ctk.CTkFont(size=12),
        )
        self._url_entry.grid(row=0, column=1, padx=(0, 8), pady=12, sticky="ew")
        ctk.CTkButton(
            row,
            text="🔗  URL қолдану",
            width=140,
            command=self._on_url_use,
        ).grid(row=0, column=2, padx=(0, 0), pady=12)

    def update_file_label(self, text: str, text_color: str = "white") -> None:
        self._file_label.configure(text=text, text_color=text_color)

    def get_url(self) -> str:
        return self._url_entry.get().strip()


class OptionsFrame(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        settings: dict,
        on_transcribe,
        on_cancel,
    ):
        super().__init__(parent, corner_radius=12)
        self._on_transcribe = on_transcribe
        self._on_cancel = on_cancel
        self._settings = settings
        self._model_var = ctk.StringVar(value=settings.get("model", "base"))
        self._ts_var = ctk.BooleanVar(value=settings.get("timestamps", False))

        self._setup_ui()

    def _setup_ui(self):
        from config import WHISPER_MODELS

        ctk.CTkLabel(self, text="Модель:", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, padx=(16, 6), pady=14
        )
        ctk.CTkOptionMenu(self, values=WHISPER_MODELS, variable=self._model_var, width=120).grid(
            row=0, column=1, padx=(0, 16), pady=14, sticky="w"
        )

        ctk.CTkLabel(self, text="Тіл коды:", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=2, padx=(0, 6), pady=14
        )
        from config import DEFAULT_LANGUAGE

        self._lang_entry = ctk.CTkEntry(self, placeholder_text="en / ru / kk / auto", width=110)
        self._lang_entry.insert(0, self._settings.get("language", DEFAULT_LANGUAGE))
        self._lang_entry.grid(row=0, column=3, padx=(0, 16), pady=14, sticky="w")

        ctk.CTkCheckBox(
            self,
            text="Timestamps",
            variable=self._ts_var,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=4, padx=(0, 16), pady=14)

        self._transcribe_btn = ctk.CTkButton(
            self,
            text="▶  Транскрипциялау",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self._on_transcribe,
        )
        self._transcribe_btn.grid(row=0, column=5, padx=(0, 8), pady=14)

        self._cancel_btn = ctk.CTkButton(
            self,
            text="⏹  Тоқтату",
            height=38,
            width=110,
            fg_color="#8B0000",
            hover_color="#5a0000",
            state="disabled",
            command=self._on_cancel,
        )
        self._cancel_btn.grid(row=0, column=6, padx=(0, 16), pady=14)

    def get_model(self) -> str:
        return self._model_var.get()

    def get_language(self) -> str | None:
        lang_raw = self._lang_entry.get().strip().lower()
        return None if lang_raw in ("", "auto") else lang_raw

    def get_timestamps(self) -> bool:
        return self._ts_var.get()

    def set_transcribe_state(self, enabled: bool) -> None:
        self._transcribe_btn.configure(state="normal" if enabled else "disabled")

    def set_cancel_state(self, enabled: bool) -> None:
        self._cancel_btn.configure(state="normal" if enabled else "disabled")


class ProgressFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=12)
        self.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            self,
            text="Дайын",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, padx=16, pady=(10, 4), sticky="ew")

        self._progress = ctk.CTkProgressBar(self)
        self._progress.set(0)
        self._progress.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")

    def set_progress(self, value: float, status: str) -> None:
        self._progress.set(value)
        self._status_label.configure(text=status)

    def get_status_text(self) -> str:
        return self._status_label.cget("text")

    def set_status_text(self, text: str) -> None:
        self._status_label.configure(text=text)


class ResultFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=12)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=12, pady=(12, 0), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_bar,
            text="Транскрипция нәтижесі",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._stats_label = ctk.CTkLabel(
            top_bar,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="e",
        )
        self._stats_label.grid(row=0, column=1, sticky="e")

        self._text_box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(size=13),
            wrap="word",
            corner_radius=8,
        )
        self._text_box.grid(row=1, column=0, padx=12, pady=(6, 12), sticky="nsew")

    def get_text_box(self) -> ctk.CTkTextbox:
        return self._text_box

    def set_stats(self, words: int, chars: int) -> None:
        self._stats_label.configure(text=f"{words} сөз · {chars} таңба")

    def clear_stats(self) -> None:
        self._stats_label.configure(text="")


class ButtonBarFrame(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_copy,
        on_save_txt,
        on_save_srt,
        on_toggle_view,
        on_reset,
    ):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self._on_toggle_view = on_toggle_view

        self._copy_btn = ctk.CTkButton(
            self,
            text="📋  Clipboard",
            height=36,
            width=130,
            state="disabled",
            command=on_copy,
        )
        self._copy_btn.grid(row=0, column=1, padx=4)

        self._save_txt_btn = ctk.CTkButton(
            self,
            text="💾  .txt сақтау",
            height=36,
            width=140,
            state="disabled",
            fg_color="#2d6a2d",
            hover_color="#1a3d1a",
            command=on_save_txt,
        )
        self._save_txt_btn.grid(row=0, column=2, padx=4)

        self._save_srt_btn = ctk.CTkButton(
            self,
            text="🎞  .srt сақтау",
            height=36,
            width=140,
            state="disabled",
            fg_color="#4a3080",
            hover_color="#2e1d55",
            command=on_save_srt,
        )
        self._save_srt_btn.grid(row=0, column=3, padx=4)

        self._toggle_view_btn = ctk.CTkButton(
            self,
            text="🕐  TS көру",
            height=36,
            width=130,
            state="disabled",
            fg_color="#6b5f1a",
            hover_color="#4a4112",
            command=on_toggle_view,
        )
        self._toggle_view_btn.grid(row=0, column=4, padx=4)

        self._reset_btn = ctk.CTkButton(
            self,
            text="♻  Тазалау",
            height=36,
            width=120,
            fg_color="#3f3f3f",
            hover_color="#2a2a2a",
            command=on_reset,
        )
        self._reset_btn.grid(row=0, column=5, padx=4)

    def set_output_buttons_state(self, enabled: bool) -> None:
        for btn in (self._copy_btn, self._save_txt_btn, self._save_srt_btn, self._toggle_view_btn):
            btn.configure(state="normal" if enabled else "disabled")

    def toggle_view_button(self, show_timestamps: bool) -> None:
        text = "📝  Мәтін көру" if show_timestamps else "🕐  TS көру"
        self._toggle_view_btn.configure(text=text)

    def reset_view_button(self) -> None:
        self._toggle_view_btn.configure(state="disabled", text="🕐  TS көру")
