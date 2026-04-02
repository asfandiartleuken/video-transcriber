Param(
    [string]$Version = "0.0.0",
    [string]$SourceDir = "dist\VideoTranscriber",
    [string]$Issuer = "VideoTranscriber"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSCommandPath | Split-Path -Parent
Set-Location $repoRoot

if (-not (Get-Command iscc.exe -ErrorAction SilentlyContinue)) {
    throw "iscc.exe (Inno Setup) not found. Install Inno Setup or add it to PATH."
}

$env:APP_VERSION = $Version
Write-Host "==> Building installer version $Version from $SourceDir"

$issPath = Join-Path $repoRoot "installer/VideoTranscriber.iss"
iscc.exe /DAPP_VERSION=$Version /DSOURCEDIR=$SourceDir $issPath

Write-Host "==> Installer done. Check dist/ for output."
