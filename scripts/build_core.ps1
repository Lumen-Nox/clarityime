# Build standalone ClarityIME Python core (PyInstaller)
# Output: platforms/windows/dist/clarityime-core.exe (+ dist/clarityime/ one-folder)
#
# Prerequisites: Python 3.9+ venv at repo root with project deps installed
#   pip install -r requirements.txt
#   pip install pyinstaller

param(
    [switch]$OneDirOnly,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Venv = Join-Path $RepoRoot ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$Pip = Join-Path $Venv "Scripts\pip.exe"
$PyInstaller = Join-Path $Venv "Scripts\pyinstaller.exe"
$DistDir = Join-Path $RepoRoot "platforms\windows\dist"
$WorkDir = Join-Path $RepoRoot "build\pyinstaller"
$SpecOneFile = Join-Path $RepoRoot "clarityime-onefile.spec"
$SpecOneDir = Join-Path $RepoRoot "clarityime-onedir.spec"

if (-not (Test-Path $Venv)) {
    Write-Host "Creating venv at $Venv ..."
    python -m venv $Venv
}

if (-not $SkipInstall) {
    Write-Host "Installing project + build deps ..."
    & $Pip install -e $RepoRoot -q
    & $Pip install pyinstaller -q
}

if (-not (Test-Path $PyInstaller)) {
    Write-Error @"
PyInstaller not found. Install with:
  $Pip install pyinstaller
Then re-run: scripts\build_core.ps1
"@
}

New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

Write-Host "Building clarityime-core (one-file + one-folder) ..."
Push-Location $RepoRoot
try {
    if ($OneDirOnly) {
        & $PyInstaller $SpecOneDir --noconfirm --clean `
            --distpath (Join-Path $RepoRoot "dist") `
            --workpath $WorkDir
    } else {
        & $PyInstaller $SpecOneFile --noconfirm --clean `
            --distpath $DistDir `
            --workpath $WorkDir
        & $PyInstaller $SpecOneDir --noconfirm `
            --distpath (Join-Path $RepoRoot "dist") `
            --workpath (Join-Path $WorkDir "onedir")
    }
} finally {
    Pop-Location
}

$OneFile = Join-Path $DistDir "clarityime-core.exe"
$OneFolder = Join-Path $RepoRoot "dist\clarityime\clarityime-core.exe"

Write-Host ""
if (Test-Path $OneFile) {
    $sizeMb = [math]::Round((Get-Item $OneFile).Length / 1MB, 1)
    Write-Host "OK  one-file  -> $OneFile  (${sizeMb} MB)"
} else {
    Write-Host "WARN  one-file exe missing: $OneFile"
}

if (Test-Path $OneFolder) {
    Write-Host "OK  one-folder -> $OneFolder"
} else {
    Write-Host "NOTE  one-folder layout: dist\clarityime\ (see PyInstaller COLLECT in clarityime.spec)"
}

Write-Host ""
Write-Host "Smoke test (serve --help via subcommand list):"
if (Test-Path $OneFile) {
    & $OneFile --version
    Write-Host "  clarityime-core.exe serve | capture | contacts list | ..."
} else {
    Write-Host "  (skipped — exe not built)"
}

Write-Host ""
Write-Host "Install with bundled core:"
Write-Host "  .\platforms\windows\install.ps1"
