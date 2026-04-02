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
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Tests:
```bash
python -m unittest discover -s tests -v
```
Logs: written to the platform config dir (e.g., `%APPDATA%\video-transcriber\logs\app.log`).

## Build Windows executable (PyInstaller)
Artifacts: `VideoTranscriber.spec`, `scripts/build_windows.ps1`, `requirements-build.txt`, `assets/app.ico` (replace with your icon).

Portable (one-folder, recommended):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 -Clean
```
Output: `dist\VideoTranscriber\VideoTranscriber.exe`

One-file (slower startup):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 -Clean -OneFile
```

Optional tool bundling: add `-DownloadTools` or drop `ffmpeg.exe`, `ffprobe.exe`, `yt-dlp.exe` into `tools/` before building.

## Create installer (Inno Setup)
Requires Inno Setup (`choco install innosetup --yes`). After PyInstaller build:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\make_installer.ps1 -Version 1.0.0
```
Output: `dist\VideoTranscriber-Setup-1.0.0.exe`

## Publish a GitHub release
1) Build portable and installer locally (or run the CI workflow below).
2) Tag your release, e.g. `git tag v1.0.0 && git push origin v1.0.0`.
3) Create a GitHub Release for the tag and upload:
   - `dist/VideoTranscriber-portable.zip` (if zipped) or the portable folder
   - `dist/VideoTranscriber-Setup-<version>.exe`
4) Add release notes (highlights, fixes, known issues).

CI helper:
- `.github/workflows/windows-build.yml` (manual dispatch) builds portable + installer, downloads tools, runs a smoke test, and uploads artifacts you can attach to a Release.

## Project layout
- `main.py` — entrypoint, logging/runtime/tool PATH setup
- `ui_app.py` — main CustomTkinter window
- `ui/` — widgets and shortcut handling
- `services/` — download/transcription orchestration
- `utils/` — tool resolution, logging, runtime helpers
- `assets/` — app icon
- `scripts/` — build, installer, smoke-test helpers
- `installer/` — Inno Setup script

## License
MIT License © 2026 [asfandiartleuken](https://github.com/asfandiartleuken)
