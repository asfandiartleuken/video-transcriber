Міне, толық `README.md`:

```markdown
# 🎙 Видео Транскриптор

Видеодан сөйлеуді автоматты түрде текстке айналдыратын desktop қолданба.  
**OpenAI Whisper** + **CustomTkinter** негізінде жасалған.

---

## ✨ Мүмкіндіктер

- 🎥 MP4, MKV, AVI, MOV, WEBM форматтарын қолдайды
- 🔗 Тікелей URL сілтемесінен транскрипциялау
- 🤖 OpenAI Whisper арқылы дәл транскрипция
- 🕐 Timestamps (уақыт белгілері) режимі
- 🎞 SRT субтитр экспорты
- 📋 Clipboard-қа бір кликпен көшіру
- 💾 Нәтижені `.txt` файлға сақтау
- ⏹ Транскрипцияны тоқтату батырмасы
- 📊 Сөз саны статистикасы
- 🌙 Заманауи Dark theme интерфейс
- ⚙️ Параметрлерді автоматты сақтау

---

## 📋 Жүйе талаптары

- Python 3.9+
- ffmpeg
- Интернет (бірінші рет модель жүктеу үшін)

---

## 🐧 Arch Linux

### 1. Жүйелік пакеттерді орнату
```bash
sudo pacman -S python ffmpeg tk git
```

### 2. Репозиторийді клондау
```bash
git clone https://github.com/asfandiartleuken/video-transcriber.git
cd video-transcriber
```

### 3. Виртуал орта жасау
```bash
python -m venv venv

# Fish shell үшін:
source venv/bin/activate.fish

# Bash үшін:
source venv/bin/activate
```

### 4. Кітапханаларды орнату
```bash
pip install -r requirements.txt
```

### 5. Іске қосу
```bash
python main.py
```

---

## 🐧 Ubuntu / Debian

### 1. Жүйелік пакеттерді орнату
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv ffmpeg python3-tk git
```

### 2. Репозиторийді клондау
```bash
git clone https://github.com/asfandiartleuken/video-transcriber.git
cd video-transcriber
```

### 3. Виртуал орта жасау
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Кітапханаларды орнату
```bash
pip install -r requirements.txt
```

### 5. Іске қосу
```bash
python main.py
```

---

## 🍎 macOS

### 1. Homebrew орнату (жоқ болса)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. ffmpeg орнату
```bash
brew install ffmpeg
```

### 3. Репозиторийді клондау
```bash
git clone https://github.com/asfandiartleuken/video-transcriber.git
cd video-transcriber
```

### 4. Виртуал орта жасау
```bash
python3 -m venv venv
source venv/bin/activate
```

### 5. Кітапханаларды орнату
```bash
pip install -r requirements.txt
```

### 6. Іске қосу
```bash
python main.py
```

---

## 🪟 Windows

### 1. Python орнату
[python.org](https://www.python.org/downloads/) сайтынан жүктеп алыңыз.  
⚠️ Орнату кезінде **"Add Python to PATH"** белгісін қойыңыз.

### 2. ffmpeg орнату
```cmd
winget install ffmpeg
```
Немесе [ffmpeg.org](https://ffmpeg.org/download.html) сайтынан жүктеп, `C:\ffmpeg\bin` жолын PATH-қа қосыңыз.

### 3. Репозиторийді клондау
```cmd
git clone https://github.com/asfandiartleuken/video-transcriber.git
cd video-transcriber
```

### 4. Виртуал орта жасау
```cmd
python -m venv venv
venv\Scripts\activate
```

### 5. Кітапханаларды орнату
```cmd
pip install -r requirements.txt
```

### 6. Іске қосу
```cmd
python main.py
```

---

## ⚙️ Модель өлшемдері

| Модель | Жылдамдық | Дәлдік | Диск |
|--------|-----------|--------|------|
| `tiny` | ⚡ Өте жылдам | Төмен | ~75 MB |
| `base` | 🚀 Жылдам | Орташа | ~145 MB |
| `small` | 🔄 Орташа | Жақсы | ~465 MB |
| `medium` | 🐢 Баяу | Өте жақсы | ~1.5 GB |

---

## 🛠️ Технологиялар

- [OpenAI Whisper](https://github.com/openai/whisper) — сөйлеуді тануу
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — заманауи GUI
- [ffmpeg](https://ffmpeg.org/) — аудио/видео өңдеу
- Python 3.9+

---

