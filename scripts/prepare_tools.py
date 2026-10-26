"""Stage target-native media tools and their redistribution notices."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "build" / "tools"
NOTICES = ROOT / "build" / "notices"


def fetch(url, dest):
    request = urllib.request.Request(url, headers={"User-Agent": "VideoTranscriber-build"})
    with urllib.request.urlopen(request, timeout=120) as response:
        dest.write_bytes(response.read())


def main():
    TOOLS.mkdir(parents=True, exist_ok=True)
    NOTICES.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        archive = ROOT / "build" / "ffmpeg.zip"
        fetch(url, archive)
        checksum = archive.with_suffix(".sha256")
        fetch(url + ".sha256", checksum)
        expected = checksum.read_text().split()[0].lower()
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise RuntimeError("FFmpeg checksum mismatch")
        with zipfile.ZipFile(archive) as bundle:
            for tool in ("ffmpeg", "ffprobe"):
                entry = next(n for n in bundle.namelist() if n.endswith(f"/bin/{tool}.exe"))
                (TOOLS / f"{tool}.exe").write_bytes(bundle.read(entry))
            for name in bundle.namelist():
                if not name.endswith("/") and any(word in Path(name).name.lower() for word in ("license", "copying", "readme")):
                    (NOTICES / ("ffmpeg-" + Path(name).name)).write_bytes(bundle.read(name))
        ffmpeg_source = "https://www.gyan.dev/ffmpeg/builds/"
    elif sys.platform == "darwin":
        # PyInstaller collects the Homebrew executables' linked libraries too.
        for tool in ("ffmpeg", "ffprobe"):
            source = shutil.which(tool)
            if not source:
                raise RuntimeError("Run brew install ffmpeg first")
            shutil.copy2(source, TOOLS / tool)
        ffmpeg_source = "https://formulae.brew.sh/formula/ffmpeg"
        fetch("https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/COPYING.GPLv3", NOTICES / "ffmpeg-COPYING.GPLv3")
        result = subprocess.run(["brew", "info", "--json=v2", "--installed"], check=True, capture_output=True, text=True)
        (NOTICES / "homebrew-formulae.json").write_text(result.stdout, encoding="utf-8")
        for formula in json.loads(result.stdout)["formulae"]:
            opt = Path(subprocess.check_output(["brew", "--prefix", formula["name"]], text=True).strip())
            for item in opt.iterdir():
                if item.is_file() and any(word in item.name.lower() for word in ("license", "copying", "notice")):
                    shutil.copy2(item, NOTICES / (formula["name"] + "-" + item.name))
    else:
        raise RuntimeError("Use a Windows or macOS runner")
    version = next(line.split("==")[1].strip() for line in (ROOT / "requirements.txt").read_text().splitlines() if line.startswith("yt-dlp=="))
    # PyPI normalizes 2026.03.17 to 2026.3.17; GitHub tags retain zeroes.
    year, month, day = map(int, version.split("."))
    version = f"{year:04d}.{month:02d}.{day:02d}"
    base = f"https://github.com/yt-dlp/yt-dlp/releases/download/{version}"
    asset = "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp_macos"
    dest = TOOLS / ("yt-dlp.exe" if sys.platform == "win32" else "yt-dlp")
    fetch(f"{base}/{asset}", dest)
    checksums = ROOT / "build" / "yt-dlp-SHA2-256SUMS"
    fetch(f"{base}/SHA2-256SUMS", checksums)
    expected = next(line.split()[0] for line in checksums.read_text().splitlines() if line.split()[-1].lstrip("*") == asset)
    if hashlib.sha256(dest.read_bytes()).hexdigest() != expected:
        raise RuntimeError("yt-dlp checksum mismatch")
    dest.chmod(0o755)
    fetch(f"https://raw.githubusercontent.com/yt-dlp/yt-dlp/{version}/LICENSE", NOTICES / "yt-dlp-LICENSE")
    fetch(f"https://raw.githubusercontent.com/yt-dlp/yt-dlp/{version}/THIRD_PARTY_LICENSES.txt", NOTICES / "yt-dlp-THIRD_PARTY_LICENSES.txt")
    report = subprocess.check_output([sys.executable, "-X", "utf8", "-m", "piplicenses", "--with-license-file", "--format=plain-vertical"], text=True, encoding="utf-8")
    (NOTICES / "python-dependencies.txt").write_text(report, encoding="utf-8")
    versions = {tool: subprocess.check_output([str(TOOLS / (tool + (".exe" if sys.platform == "win32" else ""))), "-version"], text=True).splitlines()[0] for tool in ("ffmpeg", "ffprobe")}
    (NOTICES / "sources.txt").write_text(f"FFmpeg binary source: {ffmpeg_source}\nFFmpeg upstream source: https://ffmpeg.org/download.html\nyt-dlp binary source: {base}\n{versions}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
