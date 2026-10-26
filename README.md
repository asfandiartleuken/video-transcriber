# 🎙 Video Transcriber

CustomTkinter desktop app that downloads media (URL/YouTube or local file), extracts audio with ffmpeg, and transcribes with OpenAI Whisper.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## Requirements
- Python 3.10+
- `ffmpeg` and `ffprobe` (in PATH or placed in `tools/`)
- `yt-dlp` for YouTube URLs (in PATH or placed in `tools/`)

## Local development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # tooling: pytest, ruff, black, pre-commit
pre-commit install                   # optional: run format/lint on each commit
python main.py
```
Tests:
```bash
pytest
```
Logs: written to the platform config dir (e.g., `~/.config/video-transcriber/logs/app.log` on Linux).

## Project layout
- `main.py` — entrypoint, logging/runtime/tool PATH setup
- `ui_app.py` — main CustomTkinter window
- `ui/` — widgets and shortcut handling
- `services/` — download/transcription orchestration
- `utils/` — tool resolution, logging, runtime helpers

## License
MIT License © 2026 [asfandiartleuken](https://github.com/asfandiartleuken)

## Download for Windows and macOS

[Download Video Transcriber 0.1.0 beta 1](https://github.com/asfandiartleuken/video-transcriber/releases/tag/v0.1.0-beta.1)

- Windows x64: `Video-Transcriber-Windows-x64-Setup.exe`
- Mac with Apple Silicon: `Video-Transcriber-macOS-arm64.dmg`
- Mac with Intel: `Video-Transcriber-macOS-x64.dmg`

Python and media tools are included. Whisper runs locally without an API key;
the selected model downloads on first use. These beta packages do not yet have
trusted publisher signatures or Apple notarization. Windows/macOS may warn or
block opening a downloaded package. See [RELEASE.md](RELEASE.md) for details.
