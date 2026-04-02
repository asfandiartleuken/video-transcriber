Param(
    [switch]$Clean,
    [switch]$OneFile,
    [switch]$DownloadTools,
    [string]$Version = "dev"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSCommandPath | Split-Path -Parent
Set-Location $repoRoot

Write-Host "==> Using repo root: $repoRoot"

# Ensure venv is active
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    throw "Python not found in PATH. Activate your venv first."
}

# Ensure placeholder icon exists
$iconPath = Join-Path $repoRoot "assets/app.ico"
if (-not (Test-Path $iconPath)) {
    Write-Host "==> Generating placeholder icon"
    python assets/make_icon.py
}

if ($Clean) {
    Write-Host "==> Cleaning build artifacts"
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build,dist,__pycache__
    Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# Optional: download tools into tools/ for bundling
if ($DownloadTools) {
    $toolsDir = Join-Path $repoRoot "tools"
    New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

    $downloads = @(
        @{ Name = "yt-dlp.exe"; Url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" },
        @{ Name = "ffmpeg.zip"; Url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" }
    )

    foreach ($item in $downloads) {
        $outPath = Join-Path $toolsDir $item.Name
        Write-Host "==> Downloading $($item.Name)"
        Invoke-WebRequest -Uri $item.Url -OutFile $outPath -UseBasicParsing
        if ($item.Name -eq "ffmpeg.zip") {
            Write-Host "==> Extracting ffmpeg.zip"
            Expand-Archive -Force $outPath -DestinationPath $toolsDir
            Remove-Item $outPath
            $ffmpegExe = Get-ChildItem -Recurse -Path $toolsDir -Filter "ffmpeg.exe" | Select-Object -First 1
            $ffprobeExe = Get-ChildItem -Recurse -Path $toolsDir -Filter "ffprobe.exe" | Select-Object -First 1
            if ($ffmpegExe) { Copy-Item $ffmpegExe.FullName -Destination (Join-Path $toolsDir "ffmpeg.exe") -Force }
            if ($ffprobeExe) { Copy-Item $ffprobeExe.FullName -Destination (Join-Path $toolsDir "ffprobe.exe") -Force }
            # Clean extracted folders
            Get-ChildItem -Directory $toolsDir | Where-Object { $_.Name -notlike "*.exe" } | Remove-Item -Recurse -Force
        }
    }
}

$pyinstallerArgs = @(
    "VideoTranscriber.spec"
)

if ($OneFile) {
    # Override spec-based COLLECT with onefile build
    $pyinstallerArgs = @(
        "--noconfirm",
        "--noconsole",
        "--name", "VideoTranscriber",
        "--icon", "assets/app.ico",
        "main.py"
    )
}

Write-Host "==> Running PyInstaller"
pyinstaller @pyinstallerArgs

Write-Host "==> Done. Output: dist\VideoTranscriber"
