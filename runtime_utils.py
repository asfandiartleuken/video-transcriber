import io
import sys


class _NullTextIO(io.TextIOBase):
    def write(self, _s: str) -> int:
        return 0

    def flush(self) -> None:
        return None


def ensure_stdio_streams() -> None:
    # On Windows GUI builds (PyInstaller --windowed), stdout/stderr can be None.
    # Some dependencies (e.g., whisper/tqdm) call .write(), so provide safe streams.
    if sys.stdout is None:
        sys.stdout = _NullTextIO()
    if sys.stderr is None:
        sys.stderr = _NullTextIO()
