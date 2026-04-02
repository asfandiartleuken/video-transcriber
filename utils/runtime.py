import io
import sys


class _NullTextIO(io.TextIOBase):
    def write(self, _s: str) -> int:
        return 0

    def flush(self) -> None:
        return None


def ensure_stdio_streams() -> None:
    if sys.stdout is None:
        sys.stdout = _NullTextIO()
    if sys.stderr is None:
        sys.stderr = _NullTextIO()
