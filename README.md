# 🎙 Video Transcriber

Видеодан сөйлеуді автоматты түрде текстке айналдыратын desktop қолданба.
**OpenAI Whisper** + **CustomTkinter** негізінде жасалған.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

---

## ✨ Мүмкіндіктер

| Мүмкіндік | Сипаттама |
|-----------|-----------|
| 🎥 Локал файл | MP4, MKV, AVI, MOV, WEBM форматтары |
| 🔗 URL қолдау | Тікелей MP4 сілтемесінен транскрипция |
| 🤖 Whisper модельдері | tiny · base · small · medium |
| 🕐 Timestamps | Уақыт белгілері бар мәтін |
| 🎞 SRT экспорт | Субтитр файлы жасау |
| 📄 TXT экспорт | Қарапайым мәтін файлы |
| 📋 Clipboard | Бір кликпен мәтінді көшіру |
| 🕐 Көрініс ауыстыру | Қарапайым мәтін / timestamps арасында ауысу |
| ♻ Тазалау | Нәтижені бір батырмамен тазарту |
| ⏹ Тоқтату | Транскрипцияны Cancel ету |
| 📊 Статистика | Сөз / таңба саны |
| 💾 Параметрлер | Автоматты сақталады |
| 🌙 Dark theme | Заманауи CustomTkinter интерфейс |

---

## 🚀 Іске қосу (source)

Алдымен жүйелік тәуелділіктерді орнатыңыз:

- `ffmpeg` (міндетті)
- `yt-dlp` (тек YouTube URL үшін)

Мысал:

- Arch Linux: `sudo pacman -S ffmpeg yt-dlp`
- macOS: `brew install ffmpeg yt-dlp`
- Windows: `winget install ffmpeg yt-dlp`

Содан кейін:

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Тесттер:

```bash
python -m unittest discover -s tests -v
```

---

## 🪟 Windows-қа `.exe` шығару

Жобада Windows build үшін дайын файлдар бар:

- `VideoTranscriber.spec` (PyInstaller config)
- `requirements-build.txt` (build тәуелділігі)
- `scripts/build_windows.ps1` (бір командамен build)
- `.github/installer/VideoTranscriber.iss` (Inno Setup installer)

### 1) Тек `.exe` (portable папка) жасау

PowerShell ішінде:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build_windows.ps1 -Clean
```

Нәтиже:

- `dist\VideoTranscriber\VideoTranscriber.exe`

### 2) Installer (`.exe setup`) жасау

Алдымен Inno Setup орнатыңыз:

```powershell
winget install JRSoftware.InnoSetup
```

Сосын:

```powershell
.\scripts\build_windows.ps1 -Clean -CreateInstaller -Version 1.0.0
```

Нәтиже (repo түбірінде):

- `VideoTranscriber-Setup.exe`

### 3) ffmpeg/ffprobe/yt-dlp

Екі жол бар:

1. Жүйеге орнату:
   - `winget install ffmpeg yt-dlp`
2. Немесе жоба түбірінде `tools\` бумасын жасап, ішіне:
   - `ffmpeg.exe`
   - `ffprobe.exe`
   - `yt-dlp.exe`

Қолданба алдымен `tools\` ішін тексереді, содан кейін ғана жүйелік `PATH`-ты қарайды.

---

## 🐧 Linux-та отырып Windows installer жасау

Егер өзіңіз Linux қолдансаңыз, Windows build-ті GitHub Actions жасайды.

1. Кодты GitHub-қа push етіңіз.
2. GitHub-та `Actions` -> `Build Windows Installer` workflow-ін ашыңыз.
3. `Run workflow` басып, версия енгізіңіз (мысалы `1.0.0`).
4. Build біткен соң `Artifacts` бөлімінен:
   - `VideoTranscriber-Setup-<version>` (installer)
   - `VideoTranscriber-Portable-<version>` (portable build)
5. Егер `v1.0.0` сияқты tag push етсеңіз, installer автоматты түрде Release asset болып жүктеледі.

---

## ⚙️ Whisper модельдері

| Модель | Жылдамдық | Дәлдік | Диск |
|--------|-----------|--------|------|
| `tiny` | ⚡ Өте жылдам | Төмен | ~75 MB |
| `base` | 🚀 Жылдам | Орташа | ~145 MB |
| `small` | 🔄 Орташа | Жақсы | ~465 MB |
| `medium` | 🐢 Баяу | Өте жақсы | ~1.5 GB |

---

## 🛠 Технологиялар

- [OpenAI Whisper](https://github.com/openai/whisper) — сөйлеуді тану
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — GUI
- [ffmpeg](https://ffmpeg.org/) — аудио/видео өңдеу
- Python 3.9+

---

## 🧱 Архитектура

- `main.py` — entrypoint, logging/runtime setup
- `ui_app.py` — CustomTkinter интерфейсі
- `services/transcription_service.py` — транскрипция orchestration
- `services/download_service.py` — URL/YouTube жүктеу
- `media_tools.py` — ffmpeg/ffprobe, media validation
- `transcriber_core.py` — core utility функциялары
- `app_config.py` — settings load/save
- `tests/` — unit тесттер

---

## 🪵 Логтар

- Лог файлы автоматты түрде сақталады: `~/.config/video-transcriber/logs/app.log` (Linux жүйесінде)
- Windows/macOS-та осыған эквивалент app config директориясы қолданылады

---

## 📄 Лицензия

MIT License © 2026 [asfandiartleuken](https://github.com/asfandiartleuken)
