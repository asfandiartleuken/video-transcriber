"""Run on the target OS with native tools staged in build/tools."""
import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.0")
    args = parser.parse_args()
    if platform.system() not in ("Windows", "Darwin"):
        parser.error("Build this application on Windows or macOS.")
    os.chdir(ROOT)
    tools = ROOT / "build" / "tools"
    suffix = ".exe" if sys.platform == "win32" else ""
    for name in ("ffmpeg", "ffprobe"):
        binary = tools / (name + suffix)
        if not binary.is_file():
            parser.error(f"Missing {binary}; see RELEASE.md")
        subprocess.run([str(binary), "--version" if name == "yt-dlp" else "-version"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    icon = ROOT / "build" / ("icon.ico" if sys.platform == "win32" else "icon.icns")
    with Image.open(ROOT / "assets" / "icon.png") as image:
        image.convert("RGBA").resize((1024, 1024)).save(icon)
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
               "--onedir", "--windowed", "--name", "Video Transcriber", "--icon", str(icon),
               "--add-data", f"assets{os.pathsep}assets",
               "--add-data", f"build/notices{os.pathsep}notices",
               "--collect-all", "customtkinter", "--collect-all", "whisper",
               "--collect-all", "tiktoken", "--collect-all", "yt_dlp", "--collect-submodules", "tiktoken_ext",
               "--copy-metadata", "openai-whisper", "--copy-metadata", "tiktoken"]
    if sys.platform == "darwin":
        command += ["--osx-bundle-identifier", "com.asfandiartleuken.videotranscriber"]
    for name in ("ffmpeg", "ffprobe"):
        command += ["--add-binary", f"{tools / (name + suffix)}{os.pathsep}tools"]
    command += ["main.py"]
    subprocess.run(command, check=True)
    print(f"Built Video Transcriber {args.version} for {platform.system()} {platform.machine()}")


if __name__ == "__main__":
    main()
