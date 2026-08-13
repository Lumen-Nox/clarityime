# Windows IME integration smoke test (core HTTP + optional host build)
# NOT Typeless — validates clarityime-core / venv + local API only.
param(
    [int]$Port = 17800,
    [int]$StartupWaitSec = 15,
    [switch]$SkipHostBuild
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$WindowsDir = Join-Path $RepoRoot "platforms\windows"
$HostExe = Join-Path $WindowsDir "dist\clarityime-host.exe"
$BundledCore = Join-Path $WindowsDir "dist\clarityime-core.exe"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BaseUrl = "http://127.0.0.1:$Port"

function Write-Step([string]$Msg) { Write-Host "[smoke] $Msg" -ForegroundColor Cyan }
function Fail([string]$Msg) { Write-Host "[smoke] FAIL: $Msg" -ForegroundColor Red; exit 1 }
function Pass([string]$Msg) { Write-Host "[smoke] OK: $Msg" -ForegroundColor Green }

Write-Step "repo=$RepoRoot"

# 1) Build tray host if missing
if (-not $SkipHostBuild -and -not (Test-Path $HostExe)) {
    Write-Step "clarityime-host.exe missing; running platforms\windows\build.ps1"
    & (Join-Path $WindowsDir "build.ps1")
    if (-not (Test-Path $HostExe)) { Fail "host build did not produce $HostExe" }
}
elseif (Test-Path $HostExe) {
    Pass "clarityime-host.exe present"
}
else {
    Write-Step "SkipHostBuild: not checking host exe"
}

# 2) Verify core entrypoint (bundled exe OR python module)
$CoreExe = $null
$CoreArgsPrefix = @()

if (Test-Path $BundledCore) {
    $CoreExe = $BundledCore
    Write-Step "using bundled core: $CoreExe"
    $verOut = & $CoreExe --version 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0 -and $verOut -notmatch '\d') { Fail "clarityime-core.exe --version failed: $verOut" }
    Pass "clarityime-core.exe --version"
}
elseif (Test-Path $VenvPython) {
    $CoreExe = $VenvPython
    $CoreArgsPrefix = @("-m", "clarityime")
    Write-Step "using venv python -m clarityime"
    $verOut = & $CoreExe @CoreArgsPrefix --version 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0 -and $verOut -notmatch 'clarityime|0\.') { Fail "python -m clarityime --version failed: $verOut" }
    Pass "python -m clarityime --version"
}
else {
    Fail "No core: build $BundledCore (scripts\build_core.ps1) or create .venv and pip install -e ."
}

# 3) Start core in background on loopback
$env:CLARITYIME_ROOT = $RepoRoot
if (Test-Path $BundledCore) { $env:CLARITYIME_CORE_EXE = $BundledCore }

$serveArgs = $CoreArgsPrefix + @("serve", "--host", "127.0.0.1", "--port", "$Port")
Write-Step "starting core: $CoreExe $($serveArgs -join ' ')"
$coreProc = Start-Process -FilePath $CoreExe -ArgumentList $serveArgs -WorkingDirectory $RepoRoot -PassThru -WindowStyle Hidden

function Stop-Core {
    if ($null -eq $coreProc -or $coreProc.HasExited) { return }
    Write-Step "stopping core (pid $($coreProc.Id))"
    try { Stop-Process -Id $coreProc.Id -Force -ErrorAction SilentlyContinue } catch {}
}

try {
    $deadline = (Get-Date).AddSeconds($StartupWaitSec)
    $healthy = $false
    while ((Get-Date) -lt $deadline) {
        if ($coreProc.HasExited) { Fail "core exited early (exit $($coreProc.ExitCode))" }
        try {
            $r = Invoke-WebRequest -Uri "$BaseUrl/v1/health" -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { $healthy = $true; break }
        } catch { Start-Sleep -Milliseconds 400 }
    }
    if (-not $healthy) { Fail "GET /v1/health did not respond within ${StartupWaitSec}s" }

    $healthJson = $r.Content | ConvertFrom-Json
    if (-not $healthJson.ok) { Fail "/v1/health ok!=true: $($r.Content)" }
    Pass "GET /v1/health"

    $body = @{ text = "hello smoke test"; mode = "default" } | ConvertTo-Json -Compress
    $cand = Invoke-RestMethod -Uri "$BaseUrl/v1/candidates" -Method Post -Body $body -ContentType "application/json; charset=utf-8" -TimeoutSec 10
    if ($null -eq $cand.candidates -or $cand.candidates.Count -lt 1) {
        Fail "POST /v1/candidates returned no candidates"
    }
    Pass "POST /v1/candidates ($($cand.candidates.Count) candidate(s))"
}
finally {
    Stop-Core
}

Write-Host ""
Write-Host "[smoke] All checks passed." -ForegroundColor Green

Write-Step "running API e2e pipeline (isolated port)"
& (Join-Path $ScriptDir "e2e_pipeline.ps1")
if ($LASTEXITCODE -ne 0) { Fail "e2e_pipeline.ps1 failed" }
Pass "e2e_pipeline.ps1"

exit 0

