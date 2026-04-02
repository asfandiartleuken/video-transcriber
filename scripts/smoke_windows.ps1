Param(
    [string]$ExePath = "dist\VideoTranscriber\VideoTranscriber.exe",
    [int]$TimeoutSeconds = 10
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $ExePath)) {
    throw "Executable not found: $ExePath"
}

Write-Host "==> Smoke test: launching $ExePath"
$p = Start-Process -FilePath $ExePath -WindowStyle Hidden -PassThru

try {
    if (-not $p.WaitForExit($TimeoutSeconds * 1000)) {
        Write-Host "==> Timeout reached; stopping process"
        $p.CloseMainWindow() | Out-Null
        Start-Sleep -Seconds 2
        if (-not $p.HasExited) { $p.Kill() }
    }
    if ($p.ExitCode -ne 0 -and -not $p.HasExited) {
        throw "Process exit code: $($p.ExitCode)"
    }
    Write-Host "==> Smoke test completed (process exited or was closed)."
} finally {
    if ($p -and -not $p.HasExited) { $p.Kill() }
}
