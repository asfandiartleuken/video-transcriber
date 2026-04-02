# Windows Packaging (PyInstaller)

## Prereqs
- Windows 64-bit, Python 3.10+ (same arch as target)
- Visual C++ Build Tools (for torch/whisper dependencies)
- Activate your venv: `python -m venv venv && venv\Scripts\activate`
- Install deps: `pip install -r requirements.txt -r requirements-build.txt`

## Bundle media tools (optional but recommended)
- Place `ffmpeg.exe`, `ffprobe.exe`, `yt-dlp.exe` in `tools/`
- Or run: `powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 -DownloadTools`

## Build (one-folder, recommended)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 -Clean
```
Outputs `dist\VideoTranscriber\VideoTranscriber.exe` with `tools/` included if present.

## Build (one-file, slower startup)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 -Clean -OneFile
```

## Build installer (Inno Setup)
Requires Inno Setup (`choco install innosetup`). After PyInstaller build:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\make_installer.ps1 -Version 1.0.0
```
Outputs `dist\VideoTranscriber-Setup-1.0.0.exe`.

## Icon
- Put an icon at `assets/app.ico` before building; it is bundled automatically when present.

## Smoke test
- From `dist\VideoTranscriber`, run `VideoTranscriber.exe`
- Test: file open dialog, URL download, transcription, cancel, save .srt/.txt

## Release checklist
- [ ] venv active and deps installed
- [ ] `tools/` contains ffmpeg/ffprobe/yt-dlp or system PATH has them
- [ ] Build succeeds
- [ ] Smoke tests pass
- [ ] Zip `dist\VideoTranscriber` for distribution
