# 🎬 Video Transcriber

Видеодан автоматты мәтін алатын desktop қолданба (OpenAI Whisper + CustomTkinter).

## ✨ Мүмкіндіктер

- 🎥 MP4, MKV, AVI, MOV, WEBM форматтарын қолдайды
- 🤖 OpenAI Whisper арқылы дәл транскрипция
- 💾 Нәтижені .txt файлға сақтау
- 🌙 Заманауи dark theme интерфейс

## 📦 Орнату (Arch Linux)

### 1. Қажетті пакеттерді орнат
\`\`\`bash
sudo pacman -S python ffmpeg tk
\`\`\`

### 2. Репозиторийді клондау
\`\`\`bash
git clone https://github.com/asfandiartleuken/video-transcriber.git
cd video-transcriber
\`\`\`

### 3. Виртуал орта жасау
\`\`\`bash
python -m venv venv
source venv/bin/activate.fish  # Fish shell үшін
# немесе
source venv/bin/activate       # Bash үшін
\`\`\`

### 4. Кітапханаларды орнату
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 5. Іске қосу
\`\`\`bash
python main.py
\`\`\`

## 🛠️ Технологиялар

- [OpenAI Whisper](https://github.com/openai/whisper)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Python 3.14
