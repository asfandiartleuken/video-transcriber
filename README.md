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

## 📥 Жүктеп алу (орнату керек емес)

Репозиторийдің **[Releases](https://github.com/asfandiartleuken/video-transcriber/releases)** бетінен жүктеп аласың:

| Жүйе | Файл |
|------|------|
| 🍎 macOS | `VideoTranscriber-mac.dmg` |
| 🪟 Windows | `VideoTranscriber-Setup.exe` |

- **macOS**: `.dmg`-ды ашып, `VideoTranscriber.app`-ты `Applications`-қа сүйреп апар
- **Windows**: `VideoTranscriber-Setup.exe`-ді ашып, орнатуды аяқта

> Билдтер GitHub Actions арқылы автоматты жасалады

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
