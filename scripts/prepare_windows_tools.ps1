param(
    [string]$ToolsDir = "tools"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($env:OS -ne "Windows_NT") {
    throw "Бұл скрипт Windows PowerShell/Pwsh ішінде орындалуы керек."
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$resolvedToolsDir = Join-Path $root $ToolsDir
New-Item -ItemType Directory -Force $resolvedToolsDir | Out-Null

$ytDlpPath = Join-Path $resolvedToolsDir "yt-dlp.exe"
$ffmpegPath = Join-Path $resolvedToolsDir "ffmpeg.exe"
$ffprobePath = Join-Path $resolvedToolsDir "ffprobe.exe"

Write-Host "[tools] yt-dlp жүктелуде..."
Invoke-WebRequest -Uri "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" -OutFile $ytDlpPath

Write-Host "[tools] ffmpeg archive жүктелуде..."
$zipPath = Join-Path $root "ffmpeg.zip"
$extractDir = Join-Path $root "ffmpeg"
Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

$ffmpeg = Get-ChildItem -Path $extractDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
$ffprobe = Get-ChildItem -Path $extractDir -Recurse -Filter "ffprobe.exe" | Select-Object -First 1
if (-not $ffmpeg -or -not $ffprobe) {
    throw "ffmpeg.exe немесе ffprobe.exe archive ішінен табылмады."
}

Copy-Item $ffmpeg.FullName $ffmpegPath -Force
Copy-Item $ffprobe.FullName $ffprobePath -Force

Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
Remove-Item $extractDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "[tools] Дайын: $resolvedToolsDir"
