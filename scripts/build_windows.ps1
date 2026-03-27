param(
    [string]$Version = "1.0.0",
    [switch]$CreateInstaller,
    [switch]$Clean,
    [string]$VenvPath = ".venv-winbuild"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($env:OS -ne "Windows_NT") {
    throw "Бұл скрипт Windows PowerShell/Pwsh ішінде орындалуы керек."
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if ($Clean) {
    Remove-Item -Recurse -Force "$root\\build" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$root\\dist" -ErrorAction SilentlyContinue
}

if (-not (Test-Path $VenvPath)) {
    Write-Host "[1/5] Virtual environment жасалуда..."
    py -m venv $VenvPath
}

$python = Join-Path $VenvPath "Scripts\\python.exe"
$pip = Join-Path $VenvPath "Scripts\\pip.exe"

if (-not (Test-Path $python)) {
    throw "Python executable табылмады: $python"
}

Write-Host "[2/5] Тәуелділіктер орнатылуда..."
& $python -m pip install --upgrade pip
& $pip install -r requirements.txt -r requirements-build.txt

Write-Host "[3/5] PyInstaller build басталды..."
& $python -m PyInstaller --noconfirm VideoTranscriber.spec

$distDir = Join-Path $root "dist\\VideoTranscriber"
if (-not (Test-Path $distDir)) {
    throw "Build сәтсіз: $distDir табылмады."
}

Write-Host "[4/5] Build дайын: $distDir"

$toolsDir = Join-Path $root "tools"
if (-not (Test-Path $toolsDir)) {
    Write-Warning "tools/ бумасы жоқ. ffmpeg/ffprobe/yt-dlp PATH арқылы табылуы керек немесе tools/ ішіне салыңыз."
}

if ($CreateInstaller) {
    Write-Host "[5/5] Inno Setup installer жасалуда..."
    $iscc = Get-Command iscc -ErrorAction SilentlyContinue
    if (-not $iscc) {
        throw "iscc (Inno Setup Compiler) табылмады. Inno Setup орнатыңыз: winget install JRSoftware.InnoSetup"
    }
    & $iscc.Source "/DMyAppVersion=$Version" ".github\\installer\\VideoTranscriber.iss"
    Write-Host "Installer дайын: $root"
} else {
    Write-Host "[5/5] Installer қадамы өткізіліп кетті. Қаласаңыз: .\\scripts\\build_windows.ps1 -CreateInstaller -Version $Version"
}
