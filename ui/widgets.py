import customtkinter as ctk

DISPLAY_FONT = "Avenir Next"
BODY_FONT = "Trebuchet MS"

PAGE_BG = "#F3EEE6"
CARD_BG = "#FFFBF5"
CARD_ALT = "#F5EEE3"
BORDER = "#E1D5C6"
TEXT = "#17232D"
TEXT_MUTED = "#6A767D"
HERO_BG = "#15232D"
HERO_PANEL = "#20313D"
HERO_TEXT_MUTED = "#B0C1CF"
ACCENT = "#0A8A78"
ACCENT_HOVER = "#07695D"
ACCENT_SOFT = "#D7EFE9"
SUCCESS = "#2C6B58"
SUCCESS_HOVER = "#1F5143"
AMBER = "#B27A2D"
AMBER_HOVER = "#8F6020"
DANGER = "#B95D45"
DANGER_HOVER = "#954734"
TEXTBOX_BG = "#FBF7F0"


def _font(size: int, *, weight: str = "normal", family: str = BODY_FONT) -> ctk.CTkFont:
    return ctk.CTkFont(family=family, size=size, weight=weight)


def _section_label(parent, text: str, *, text_color: str = TEXT_MUTED) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text,
        font=_font(11, weight="bold"),
        text_color=text_color,
        anchor="w",
    )


def _pill(parent, text: str, *, fg_color: str, text_color: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text,
        fg_color=fg_color,
        text_color=text_color,
        corner_radius=999,
        padx=10,
        pady=4,
        font=_font(11, weight="bold"),
    )


def _card(parent, *, fg_color: str = CARD_BG) -> ctk.CTkFrame:
    return ctk.CTkFrame(
        parent,
        fg_color=fg_color,
        corner_radius=18,
        border_width=1,
        border_color=BORDER,
    )


class HeaderFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=HERO_BG, corner_radius=18)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, padx=20, pady=12, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(content, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_row,
            text="🎙  Видео Транскриптор",
            font=_font(22, weight="bold", family=DISPLAY_FONT),
            text_color="#F8FBFD",
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            content,
            text="Whisper AI көмегімен аудио мен видеоны мәтінге және субтитрге айналдыру",
            font=_font(12),
            text_color=HERO_TEXT_MUTED,
            anchor="w",
        ).grid(row=1, column=0, pady=(2, 0), sticky="w")

        chips = ctk.CTkFrame(self, fg_color="transparent")
        chips.grid(row=0, column=1, padx=(0, 20), pady=12, sticky="e")
        for index, label in enumerate(("Whisper", "Local + URL", "Subtitle (.srt)")):
            _pill(
                chips,
                label,
                fg_color=HERO_PANEL,
                text_color="#ECF4F8",
            ).grid(row=0, column=index, padx=(0, 6), sticky="e")


class FileSelectorFrame(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_file_select,
        on_url_use,
        settings: dict,
    ):
        super().__init__(
            parent,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        self.grid_columnconfigure(0, weight=1)
        self._on_file_select = on_file_select
        self._on_url_use = on_url_use
        self._settings = settings

        header_box = ctk.CTkFrame(self, fg_color="transparent")
        header_box.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        _section_label(header_box, "SOURCE").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header_box,
            text="Медиа көзі",
            font=_font(16, weight="bold", family=DISPLAY_FONT),
            text_color=TEXT,
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

        self._setup_file_row()
        self._setup_url_row()

    def _setup_file_row(self):
        row = _card(self, fg_color=CARD_ALT)
        row.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="ew")
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)

        _section_label(row, "LOCAL FILE", text_color=TEXT_MUTED).grid(
            row=0, column=0, padx=12, pady=(10, 2), sticky="w"
        )
        self._file_label = ctk.CTkLabel(
            row,
            text="Файл таңдалмаған",
            font=_font(13, weight="bold"),
            text_color=TEXT,
            anchor="w",
            justify="left",
            wraplength=230,
        )
        self._file_label.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            row,
            text="Файл таңдау",
            height=36,
            width=120,
            corner_radius=12,
            font=_font(12, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#F6FBFA",
            command=self._on_file_select,
        ).grid(row=0, column=1, rowspan=2, padx=(6, 12), pady=10)

    def _setup_url_row(self):
        row = _card(self, fg_color=CARD_ALT)
        row.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="ew")
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)

        _section_label(row, "DIRECT URL / YOUTUBE", text_color=TEXT_MUTED).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(10, 2), sticky="w"
        )
        self._url_entry = ctk.CTkEntry(
            row,
            height=36,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
            fg_color="#FFFDF8",
            text_color=TEXT,
            placeholder_text="https://example.com/video.mp4",
            placeholder_text_color=TEXT_MUTED,
            font=_font(12),
        )
        self._url_entry.grid(row=1, column=0, padx=(12, 6), pady=(0, 10), sticky="ew")
        ctk.CTkButton(
            row,
            text="URL қолдану",
            height=36,
            width=110,
            corner_radius=12,
            font=_font(12, weight="bold"),
            fg_color="#D9EDE8",
            hover_color="#C9E3DC",
            text_color=TEXT,
            command=self._on_url_use,
        ).grid(row=1, column=1, padx=(0, 12), pady=(0, 10))

    def update_file_label(self, text: str, text_color: str = TEXT) -> None:
        resolved_color = TEXT if text_color == "white" else text_color
        self._file_label.configure(text=text, text_color=resolved_color)

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
        super().__init__(
            parent,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        self._on_transcribe = on_transcribe
        self._on_cancel = on_cancel
        self._settings = settings
        self._model_var = ctk.StringVar(value=settings.get("model", "base"))
        self._ts_var = ctk.BooleanVar(value=settings.get("timestamps", False))

        self._setup_ui()

    def _setup_ui(self):
        from config import DEFAULT_LANGUAGE, WHISPER_MODELS

        self.grid_columnconfigure(0, weight=1)

        header_box = ctk.CTkFrame(self, fg_color="transparent")
        header_box.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        _section_label(header_box, "SETTINGS").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header_box,
            text="Параметрлер",
            font=_font(16, weight="bold", family=DISPLAY_FONT),
            text_color=TEXT,
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="ew")
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)

        # Model card
        model_card = _card(controls, fg_color=CARD_ALT)
        model_card.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        model_card.grid_columnconfigure(0, weight=1)
        _section_label(model_card, "MODEL").grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")
        ctk.CTkOptionMenu(
            model_card,
            values=WHISPER_MODELS,
            variable=self._model_var,
            height=36,
            corner_radius=10,
            fg_color="#DDEEEA",
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            text_color=TEXT,
            dropdown_fg_color="#FFFDF8",
            dropdown_hover_color="#EDF5F3",
            dropdown_text_color=TEXT,
            font=_font(12, weight="bold"),
        ).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Language card
        language_card = _card(controls, fg_color=CARD_ALT)
        language_card.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        language_card.grid_columnconfigure(0, weight=1)
        _section_label(language_card, "LANGUAGE").grid(
            row=0, column=0, padx=10, pady=(8, 2), sticky="w"
        )
        self._lang_entry = ctk.CTkEntry(
            language_card,
            height=36,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            fg_color="#FFFDF8",
            text_color=TEXT,
            placeholder_text="en / ru / kk / auto",
            placeholder_text_color=TEXT_MUTED,
            font=_font(12),
        )
        self._lang_entry.insert(0, self._settings.get("language", DEFAULT_LANGUAGE))
        self._lang_entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Timestamps toggle card
        output_card = _card(self, fg_color=CARD_ALT)
        output_card.grid(row=2, column=0, padx=14, pady=(0, 10), sticky="ew")
        output_card.grid_columnconfigure(0, weight=1)
        ctk.CTkCheckBox(
            output_card,
            text="Timestamp view қосу (уақыт белгілері)",
            variable=self._ts_var,
            font=_font(12, weight="bold"),
            text_color=TEXT,
            border_color=ACCENT,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            checkmark_color="#F7FBFA",
        ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        # Action Buttons
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.grid(row=3, column=0, padx=14, pady=(0, 14), sticky="ew")
        action_bar.grid_columnconfigure(0, weight=1)

        self._transcribe_btn = ctk.CTkButton(
            action_bar,
            text="▶  Транскрипциялау",
            font=_font(14, weight="bold"),
            height=44,
            corner_radius=14,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#F6FBFA",
            command=self._on_transcribe,
        )
        self._transcribe_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self._cancel_btn = ctk.CTkButton(
            action_bar,
            text="Тоқтату",
            height=44,
            width=110,
            corner_radius=14,
            font=_font(12, weight="bold"),
            fg_color="#EEDFD7",
            hover_color="#E3CFC6",
            text_color=DANGER,
            state="disabled",
            command=self._on_cancel,
        )
        self._cancel_btn.grid(row=0, column=1, sticky="e")

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
        super().__init__(parent, fg_color=HERO_BG, corner_radius=18)
        self.grid_columnconfigure(0, weight=1)

        _section_label(self, "STATUS", text_color=HERO_TEXT_MUTED).grid(
            row=0, column=0, padx=16, pady=(12, 2), sticky="w"
        )

        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="ew")
        status_row.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            status_row,
            text="Дайын",
            font=_font(15, weight="bold"),
            text_color="#F8FBFD",
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, sticky="w")

        self._percent_label = _pill(
            status_row,
            "0%",
            fg_color="#28404F",
            text_color="#EAF3F8",
        )
        self._percent_label.grid(row=0, column=1, sticky="e")

        self._progress = ctk.CTkProgressBar(
            self,
            height=12,
            corner_radius=999,
            fg_color="#2A3C47",
            progress_color=ACCENT,
        )
        self._progress.set(0)
        self._progress.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            self,
            text="Транскрипция кезінде терезе ашық қалсын. Нәтиже оң жақта шығады.",
            font=_font(11),
            text_color=HERO_TEXT_MUTED,
            justify="left",
            wraplength=360,
            anchor="w",
        ).grid(row=3, column=0, padx=16, pady=(0, 12), sticky="w")

    def set_progress(self, value: float, status: str) -> None:
        clamped = max(0.0, min(value, 1.0))
        self._progress.set(clamped)
        self._status_label.configure(text=status, text_color=self._status_color(status))
        self._percent_label.configure(text=f"{int(clamped * 100)}%")

    def _status_color(self, status: str) -> str:
        if status.startswith("✅"):
            return "#8CE7C8"
        if status.startswith("❌"):
            return "#FFB4A3"
        if status.startswith("⏹"):
            return "#F3D18C"
        return "#F8FBFD"

    def get_status_text(self) -> str:
        return self._status_label.cget("text")

    def set_status_text(self, text: str) -> None:
        self._status_label.configure(text=text, text_color=self._status_color(text))


class ResultFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        label_stack = ctk.CTkFrame(top_bar, fg_color="transparent")
        label_stack.grid(row=0, column=0, sticky="w")
        _section_label(label_stack, "RESULT").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            label_stack,
            text="Транскрипция нәтижесі",
            font=_font(18, weight="bold", family=DISPLAY_FONT),
            text_color=TEXT,
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

        self._stats_label = _pill(
            top_bar,
            "",
            fg_color=ACCENT_SOFT,
            text_color=ACCENT_HOVER,
        )
        self._stats_label.grid(row=0, column=1, rowspan=2, sticky="e")
        self._stats_label.grid_remove()

        self._text_box = ctk.CTkTextbox(
            self,
            font=_font(14),
            wrap="word",
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
            fg_color=TEXTBOX_BG,
            text_color=TEXT,
            scrollbar_button_color="#D8D1C4",
            scrollbar_button_hover_color="#B8AD9A",
        )
        self._text_box.grid(row=1, column=0, padx=16, pady=(4, 16), sticky="nsew")
        self._text_box.insert(
            "1.0",
            "Нәтиже осы жерде пайда болады. Алдымен сол жақта файлды немесе URL-ді таңдап, «Транскрипциялау» батырмасын басыңыз.",
        )

    def get_text_box(self) -> ctk.CTkTextbox:
        return self._text_box

    def set_stats(self, words: int, chars: int) -> None:
        self._stats_label.configure(text=f"{words} сөз · {chars} таңба")
        self._stats_label.grid()

    def clear_stats(self) -> None:
        self._stats_label.configure(text="")
        self._stats_label.grid_remove()


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

        ctk.CTkLabel(
            self,
            text="Экспорт:",
            font=_font(12, weight="bold"),
            text_color=TEXT_MUTED,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._copy_btn = self._make_button(
            text="📋 Clipboard",
            width=115,
            fg_color="#E8E4DC",
            hover_color="#D8D2C8",
            text_color=TEXT,
            command=on_copy,
        )
        self._copy_btn.grid(row=0, column=1, padx=4)

        self._save_txt_btn = self._make_button(
            text="💾 TXT сақтау",
            width=120,
            fg_color=SUCCESS,
            hover_color=SUCCESS_HOVER,
            text_color="#F5FBF8",
            command=on_save_txt,
        )
        self._save_txt_btn.grid(row=0, column=2, padx=4)

        self._save_srt_btn = self._make_button(
            text="💾 SRT сақтау",
            width=120,
            fg_color=AMBER,
            hover_color=AMBER_HOVER,
            text_color="#FFF8ED",
            command=on_save_srt,
        )
        self._save_srt_btn.grid(row=0, column=3, padx=4)

        self._toggle_view_btn = self._make_button(
            text="👁 TS көру",
            width=110,
            fg_color="#D9EDE8",
            hover_color="#C7E3DC",
            text_color=TEXT,
            command=on_toggle_view,
        )
        self._toggle_view_btn.grid(row=0, column=4, padx=4)

        self._reset_btn = self._make_button(
            text="🗑 Тазалау",
            width=100,
            fg_color="#EADFD8",
            hover_color="#DDCDC4",
            text_color=DANGER,
            command=on_reset,
        )
        self._reset_btn.grid(row=0, column=5, padx=(4, 0))

        self.set_output_buttons_state(False)

    def _make_button(
        self,
        *,
        text: str,
        width: int,
        fg_color: str,
        hover_color: str,
        text_color: str,
        command,
    ) -> ctk.CTkButton:
        return ctk.CTkButton(
            self,
            text=text,
            height=38,
            width=width,
            corner_radius=12,
            font=_font(12, weight="bold"),
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            command=command,
        )

    def set_output_buttons_state(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for button in (
            self._copy_btn,
            self._save_txt_btn,
            self._save_srt_btn,
            self._toggle_view_btn,
        ):
            button.configure(state=state)

    def toggle_view_button(self, show_timestamps: bool) -> None:
        text = "📄 Мәтін көру" if show_timestamps else "👁 TS көру"
        self._toggle_view_btn.configure(text=text)

    def reset_view_button(self) -> None:
        self._toggle_view_btn.configure(state="disabled", text="👁 TS көру")
