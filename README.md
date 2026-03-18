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
| ⏹ Тоқтату | Транскрипцияны Cancel ету |
| 📊 Статистика | Сөз / таңба саны |
| 💾 Параметрлер | Автоматты сақталады |
| 🌙 Dark theme | Заманауи CustomTkinter интерфейс |

---

## 🚀 Іске қосу (source)

Бұл жоба қазір тек source-тан іске қосылады (`Releases`/installer жоқ).

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

## 📄 Лицензия

MIT License © 2026 [asfandiartleuken](https://github.com/asfandiartleuken)
