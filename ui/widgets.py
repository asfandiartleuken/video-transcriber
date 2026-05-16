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
        padx=12,
        pady=6,
        font=_font(11, weight="bold"),
    )


def _card(parent, *, fg_color: str = CARD_BG) -> ctk.CTkFrame:
    return ctk.CTkFrame(
        parent,
        fg_color=fg_color,
        corner_radius=24,
        border_width=1,
        border_color=BORDER,
    )


class HeaderFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=HERO_BG, corner_radius=30)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, padx=(26, 18), pady=26, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        _section_label(content, "WHISPER WORKSPACE", text_color=HERO_TEXT_MUTED).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(
            content,
            text="Видео Транскриптор",
            font=_font(34, weight="bold", family=DISPLAY_FONT),
            text_color="#F8FBFD",
            anchor="w",
        ).grid(row=1, column=0, pady=(6, 10), sticky="w")
        ctk.CTkLabel(
            content,
            text=(
                "Локал файлды немесе URL-ді жүктеп, мәтін мен SRT нәтижесін бір "
                "жұмыс кеңістігінде алыңыз."
            ),
            font=_font(14),
            text_color=HERO_TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=640,
        ).grid(row=2, column=0, sticky="w")

        chips = ctk.CTkFrame(content, fg_color="transparent")
        chips.grid(row=3, column=0, pady=(18, 0), sticky="w")
        for index, label in enumerate(("Whisper", "Subtitle-ready", "Local + URL")):
            _pill(
                chips,
                label,
                fg_color=HERO_PANEL,
                text_color="#ECF4F8",
            ).grid(row=0, column=index, padx=(0, 8), sticky="w")

        aside = ctk.CTkFrame(self, fg_color=HERO_PANEL, corner_radius=24)
        aside.grid(row=0, column=1, padx=(0, 24), pady=24, sticky="ns")

        _section_label(aside, "FLOW", text_color=HERO_TEXT_MUTED).grid(
            row=0, column=0, padx=18, pady=(18, 6), sticky="w"
        )
        ctk.CTkLabel(
            aside,
            text="1. Source\n2. Settings\n3. Export",
            font=_font(15, weight="bold"),
            text_color="#F8FBFD",
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, padx=18, pady=(0, 4), sticky="w")
        ctk.CTkLabel(
            aside,
            text="Таза мәтін, timestamp view және .srt бірден қолжетімді болады.",
            font=_font(12),
            text_color=HERO_TEXT_MUTED,
            justify="left",
            wraplength=220,
            anchor="w",
        ).grid(row=2, column=0, padx=18, pady=(0, 18), sticky="w")


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
            corner_radius=24,
            border_width=1,
            border_color=BORDER,
        )
        self.grid_columnconfigure(0, weight=1)
        self._on_file_select = on_file_select
        self._on_url_use = on_url_use
        self._settings = settings

        _section_label(self, "SOURCE").grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")
        ctk.CTkLabel(
            self,
            text="Медиа көзін таңдаңыз",
            font=_font(21, weight="bold", family=DISPLAY_FONT),
            text_color=TEXT,
            anchor="w",
        ).grid(row=1, column=0, padx=20, sticky="w")
        ctk.CTkLabel(
            self,
            text="Локал файлды ашыңыз немесе тікелей видео/YouTube URL қолданыңыз.",
            font=_font(12),
            text_color=TEXT_MUTED,
            anchor="w",
        ).grid(row=2, column=0, padx=20, pady=(4, 16), sticky="w")

        self._setup_file_row()
        self._setup_url_row()

    def _setup_file_row(self):
        row = _card(self, fg_color=CARD_ALT)
        row.grid(row=3, column=0, padx=18, pady=(0, 12), sticky="ew")
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)

        _section_label(row, "LOCAL FILE", text_color=TEXT_MUTED).grid(
            row=0, column=0, padx=16, pady=(14, 4), sticky="w"
        )
        self._file_label = ctk.CTkLabel(
            row,
            text="Файл таңдалмаған",
            font=_font(14, weight="bold"),
            text_color=TEXT,
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self._file_label.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")

        ctk.CTkButton(
            row,
            text="Файл таңдау",
            height=44,
            width=150,
            corner_radius=16,
            font=_font(13, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#F6FBFA",
            command=self._on_file_select,
        ).grid(row=0, column=1, rowspan=2, padx=(10, 16), pady=16)

    def _setup_url_row(self):
        row = _card(self, fg_color=CARD_ALT)
        row.grid(row=4, column=0, padx=18, pady=(0, 18), sticky="ew")
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)

        _section_label(row, "DIRECT URL", text_color=TEXT_MUTED).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 4), sticky="w"
        )
        self._url_entry = ctk.CTkEntry(
            row,
            height=44,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
            fg_color="#FFFDF8",
            text_color=TEXT,
            placeholder_text="https://example.com/video.mp4",
            placeholder_text_color=TEXT_MUTED,
            font=_font(13),
        )
        self._url_entry.grid(row=1, column=0, padx=(16, 10), pady=(0, 16), sticky="ew")
        ctk.CTkButton(
            row,
            text="URL қолдану",
            height=44,
            width=150,
            corner_radius=16,
            font=_font(13, weight="bold"),
            fg_color="#D9EDE8",
            hover_color="#C9E3DC",
            text_color=TEXT,
            command=self._on_url_use,
        ).grid(row=1, column=1, padx=(0, 16), pady=(0, 16))

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
            corner_radius=24,
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

        _section_label(self, "SETTINGS").grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")
        ctk.CTkLabel(
            self,
            text="Транскрипция параметрлері",
            font=_font(21, weight="bold", family=DISPLAY_FONT),
            text_color=TEXT,
            anchor="w",
        ).grid(row=1, column=0, padx=20, sticky="w")
        ctk.CTkLabel(
            self,
            text="Модельді, тілді және timestamp көрінісін бір жерден басқарыңыз.",
            font=_font(12),
            text_color=TEXT_MUTED,
            anchor="w",
        ).grid(row=2, column=0, padx=20, pady=(4, 16), sticky="w")

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=3, column=0, padx=18, pady=(0, 10), sticky="ew")
        controls.grid_columnconfigure((0, 1, 2), weight=1)

        model_card = _card(controls, fg_color=CARD_ALT)
        model_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        _section_label(model_card, "MODEL").grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")
        ctk.CTkOptionMenu(
            model_card,
            values=WHISPER_MODELS,
            variable=self._model_var,
            height=42,
            corner_radius=14,
            fg_color="#DDEEEA",
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            text_color=TEXT,
            dropdown_fg_color="#FFFDF8",
            dropdown_hover_color="#EDF5F3",
            dropdown_text_color=TEXT,
            font=_font(13, weight="bold"),
        ).grid(row=1, column=0, padx=14, pady=(0, 14), sticky="ew")

        language_card = _card(controls, fg_color=CARD_ALT)
        language_card.grid(row=0, column=1, padx=5, sticky="nsew")
        _section_label(language_card, "LANGUAGE").grid(
            row=0, column=0, padx=14, pady=(12, 4), sticky="w"
        )
        self._lang_entry = ctk.CTkEntry(
            language_card,
            height=42,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
            fg_color="#FFFDF8",
            text_color=TEXT,
            placeholder_text="en / ru / kk / auto",
            placeholder_text_color=TEXT_MUTED,
            font=_font(13),
        )
        self._lang_entry.insert(0, self._settings.get("language", DEFAULT_LANGUAGE))
        self._lang_entry.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="ew")

        output_card = _card(controls, fg_color=CARD_ALT)
        output_card.grid(row=0, column=2, padx=(10, 0), sticky="nsew")
        _section_label(output_card, "OUTPUT").grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")
        ctk.CTkCheckBox(
            output_card,
            text="Timestamp view қосу",
            variable=self._ts_var,
            font=_font(13, weight="bold"),
            text_color=TEXT,
            border_color=ACCENT,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            checkmark_color="#F7FBFA",
        ).grid(row=1, column=0, padx=14, pady=(2, 10), sticky="w")
        ctk.CTkLabel(
            output_card,
            text="Нәтижені мәтін немесе уақыт белгілерімен ауыстырып көруге болады.",
            font=_font(11),
            text_color=TEXT_MUTED,
            justify="left",
            wraplength=220,
            anchor="w",
        ).grid(row=2, column=0, padx=14, pady=(0, 14), sticky="w")

        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.grid(row=4, column=0, padx=18, pady=(0, 18), sticky="ew")
        action_bar.grid_columnconfigure(0, weight=1)

        self._transcribe_btn = ctk.CTkButton(
            action_bar,
            text="Транскрипциялау",
            font=_font(14, weight="bold"),
            height=48,
            corner_radius=18,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#F6FBFA",
            command=self._on_transcribe,
        )
        self._transcribe_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self._cancel_btn = ctk.CTkButton(
            action_bar,
            text="Тоқтату",
            height=48,
            width=140,
            corner_radius=18,
            font=_font(13, weight="bold"),
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
        super().__init__(parent, fg_color=HERO_BG, corner_radius=24)
        self.grid_columnconfigure(0, weight=1)

        _section_label(self, "STATUS", text_color=HERO_TEXT_MUTED).grid(
            row=0, column=0, padx=18, pady=(18, 4), sticky="w"
        )
        ctk.CTkLabel(
            self,
            text="Жұмыс барысы",
            font=_font(21, weight="bold", family=DISPLAY_FONT),
            text_color="#F8FBFD",
            anchor="w",
        ).grid(row=1, column=0, padx=18, sticky="w")

        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.grid(row=2, column=0, padx=18, pady=(14, 8), sticky="ew")
        status_row.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            status_row,
            text="Дайын",
            font=_font(18, weight="bold"),
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
            height=16,
            corner_radius=999,
            fg_color="#2A3C47",
            progress_color=ACCENT,
        )
        self._progress.set(0)
        self._progress.grid(row=3, column=0, padx=18, pady=(0, 16), sticky="ew")

        ctk.CTkLabel(
            self,
            text=(
                "Транскрипция кезінде терезе ашық қалсын. Процесс аяқталған соң TXT "
                "пен SRT экспорт батырмалары белсенді болады."
            ),
            font=_font(12),
            text_color=HERO_TEXT_MUTED,
            justify="left",
            wraplength=300,
            anchor="w",
        ).grid(row=4, column=0, padx=18, pady=(0, 18), sticky="w")

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
            corner_radius=24,
            border_width=1,
            border_color=BORDER,
        )
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=18, pady=(18, 0), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        label_stack = ctk.CTkFrame(top_bar, fg_color="transparent")
        label_stack.grid(row=0, column=0, sticky="w")
        _section_label(label_stack, "RESULT").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            label_stack,
            text="Транскрипция нәтижесі",
            font=_font(21, weight="bold", family=DISPLAY_FONT),
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
            corner_radius=18,
            border_width=0,
            fg_color=TEXTBOX_BG,
            text_color=TEXT,
            scrollbar_button_color="#D8D1C4",
            scrollbar_button_hover_color="#B8AD9A",
        )
        self._text_box.grid(row=1, column=0, padx=18, pady=(14, 18), sticky="nsew")
        self._text_box.insert(
            "1.0",
            "Нәтиже осы жерде пайда болады. Алдымен файлды немесе URL-ді таңдаңыз.",
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
            text="Экспорт және жылдам әрекеттер",
            font=_font(12, weight="bold"),
            text_color=TEXT_MUTED,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._copy_btn = self._make_button(
            text="Clipboard",
            width=130,
            fg_color="#E8E4DC",
            hover_color="#D8D2C8",
            text_color=TEXT,
            command=on_copy,
        )
        self._copy_btn.grid(row=0, column=1, padx=6)

        self._save_txt_btn = self._make_button(
            text="TXT сақтау",
            width=136,
            fg_color=SUCCESS,
            hover_color=SUCCESS_HOVER,
            text_color="#F5FBF8",
            command=on_save_txt,
        )
        self._save_txt_btn.grid(row=0, column=2, padx=6)

        self._save_srt_btn = self._make_button(
            text="SRT сақтау",
            width=136,
            fg_color=AMBER,
            hover_color=AMBER_HOVER,
            text_color="#FFF8ED",
            command=on_save_srt,
        )
        self._save_srt_btn.grid(row=0, column=3, padx=6)

        self._toggle_view_btn = self._make_button(
            text="TS көру",
            width=128,
            fg_color="#D9EDE8",
            hover_color="#C7E3DC",
            text_color=TEXT,
            command=on_toggle_view,
        )
        self._toggle_view_btn.grid(row=0, column=4, padx=6)

        self._reset_btn = self._make_button(
            text="Тазалау",
            width=124,
            fg_color="#EADFD8",
            hover_color="#DDCDC4",
            text_color=DANGER,
            command=on_reset,
        )
        self._reset_btn.grid(row=0, column=5, padx=(6, 0))

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
            height=44,
            width=width,
            corner_radius=16,
            font=_font(13, weight="bold"),
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
        text = "Мәтін көру" if show_timestamps else "TS көру"
        self._toggle_view_btn.configure(text=text)

    def reset_view_button(self) -> None:
        self._toggle_view_btn.configure(state="disabled", text="TS көру")
