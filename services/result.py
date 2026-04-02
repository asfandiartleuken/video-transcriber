from dataclasses import dataclass, field
from typing import Any


@dataclass
class TranscriptionResult:
    text: str
    segments: list[dict[str, Any]]
    srt: str
    ts_text: str
    word_count: int = field(init=False)
    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.word_count = len(self.text.split())
        self.char_count = len(self.text)

    @classmethod
    def from_whisper_result(cls, whisper_result: dict[str, Any]) -> "TranscriptionResult":
        segments = whisper_result.get("segments", [])
        text = whisper_result.get("text", "").strip()
        from utils.formatting import segments_to_srt, segments_to_timestamped

        return cls(
            text=text,
            segments=segments,
            srt=segments_to_srt(segments),
            ts_text=segments_to_timestamped(segments),
        )
