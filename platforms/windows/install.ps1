# Install ClarityIME (Windows) — core service + tray keyboard host + PATH
$ErrorActionPreference = "Stop"
$WindowsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $WindowsDir)
$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\ClarityIME"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# Bundled PyInstaller core (optional — built via scripts/build_core.ps1)
$BundledCore = Join-Path $WindowsDir "dist\clarityime-core.exe"
$UseBundledCore = Test-Path $BundledCore
$InstalledCore = Join-Path $InstallDir "clarityime-core.exe"

# Python venv + editable install (fallback when no bundled exe)
$Venv = Join-Path $RepoRoot ".venv"
$VenvScripts = Join-Path $Venv "Scripts"
$ClarityimeVenvExe = Join-Path $VenvScripts "clarityime.exe"

if ($UseBundledCore) {
    Copy-Item $BundledCore $InstalledCore -Force
    Write-Host "Using bundled core -> $InstalledCore"
} else {
    Write-Host "Bundled core not found ($BundledCore); using Python venv fallback"
    if (-not (Test-Path $Venv)) { python -m venv $Venv }
    & (Join-Path $Venv "Scripts\pip.exe") install -e $RepoRoot -q
}

# Build host if missing
$HostExe = Join-Path $WindowsDir "dist\clarityime-host.exe"
if (-not (Test-Path $HostExe)) {
    & (Join-Path $WindowsDir "build.ps1")
}

Copy-Item $HostExe (Join-Path $InstallDir "clarityime-host.exe") -Force

# CLI wrappers — prefer bundled clarityime-core.exe when present
if ($UseBundledCore) {
    $ClarityimeCmd = @"
@echo off
setlocal
if not defined CLARITYIME_ROOT set "CLARITYIME_ROOT=$RepoRoot"
if not defined CLARITYIME_CORE_EXE set "CLARITYIME_CORE_EXE=%~dp0clarityime-core.exe"
"%CLARITYIME_CORE_EXE%" %*
"@
    $ServeCmd = @"
@echo off
setlocal
if not defined CLARITYIME_ROOT set "CLARITYIME_ROOT=$RepoRoot"
if not defined CLARITYIME_CORE_EXE set "CLARITYIME_CORE_EXE=%~dp0clarityime-core.exe"
cd /d "%CLARITYIME_ROOT%"
start "ClarityIME Core" /MIN "%CLARITYIME_CORE_EXE%" serve
"@
} else {
    $ClarityimeCmd = @"
@echo off
if not defined CLARITYIME_VENV (
  echo Error: CLARITYIME_VENV not set. Re-run install.ps1
  exit /b 1
)
"%CLARITYIME_VENV%\Scripts\clarityime.exe" %*
"@
    $ServeCmd = @"
@echo off
if not defined CLARITYIME_VENV (
  echo Error: CLARITYIME_VENV not set. Re-run install.ps1
  exit /b 1
)
cd /d "%CLARITYIME_ROOT%"
"%CLARITYIME_VENV%\Scripts\clarityime.exe" serve
"@
}
Set-Content -Path (Join-Path $InstallDir "clarityime.cmd") -Value $ClarityimeCmd -Encoding ASCII
Set-Content -Path (Join-Path $InstallDir "clarityime-serve.cmd") -Value $ServeCmd -Encoding ASCII

$StartCmd = @"
@echo off
start "ClarityIME Core" /MIN "%~dp0clarityime-serve.cmd"
timeout /t 2 /nobreak >nul
start "ClarityIME" "%~dp0clarityime-host.exe"
"@
Set-Content -Path (Join-Path $InstallDir "clarityime-start.cmd") -Value $StartCmd -Encoding ASCII

Copy-Item (Join-Path $InstallDir "clarityime-serve.cmd") (Join-Path $InstallDir "clarityime-serve.bat") -Force
Copy-Item (Join-Path $InstallDir "clarityime-start.cmd") (Join-Path $InstallDir "clarityime-start.bat") -Force

# Login: core only (optional)
$TaskName = "ClarityIMECore"
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    if ($UseBundledCore) {
        $Action = New-ScheduledTaskAction -Execute $InstalledCore -Argument "serve" -WorkingDirectory $RepoRoot
    } else {
        $Action = New-ScheduledTaskAction -Execute (Join-Path $InstallDir "clarityime-serve.cmd")
    }
    $Trigger = New-ScheduledTaskTrigger -AtLogOn
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ErrorAction SilentlyContinue
    if ($Settings) {
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -ErrorAction Stop | Out-Null
    } else {
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -ErrorAction Stop | Out-Null
    }
    Write-Host "Scheduled task: ClarityIMECore"
} catch {
    Write-Host "Note: scheduled task skipped (Startup + Settings UI still work)"
}

$Startup = [Environment]::GetFolderPath("Startup")
$Shortcut = Join-Path $Startup "ClarityIME.lnk"
$Wsh = New-Object -ComObject WScript.Shell
$Lnk = $Wsh.CreateShortcut($Shortcut)
$Lnk.TargetPath = Join-Path $InstallDir "clarityime-start.cmd"
$Lnk.WorkingDirectory = $InstallDir
$Lnk.Save()

# Environment + PATH
[Environment]::SetEnvironmentVariable("CLARITYIME_ROOT", $RepoRoot, "User")
[Environment]::SetEnvironmentVariable("CLARITYIME_VENV", $Venv, "User")
[Environment]::SetEnvironmentVariable("CLARITYIME_PYTHON", (Join-Path $VenvScripts "python.exe"), "User")
if ($UseBundledCore) {
    [Environment]::SetEnvironmentVariable("CLARITYIME_CORE_EXE", $InstalledCore, "User")
    # legacy alias — some shells/scripts still read CLARITYIME_CORE for the exe path
    [Environment]::SetEnvironmentVariable("CLARITYIME_CORE", $InstalledCore, "User")
} else {
    [Environment]::SetEnvironmentVariable("CLARITYIME_CORE_EXE", $null, "User")
    [Environment]::SetEnvironmentVariable("CLARITYIME_CORE", $null, "User")
}

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$PathEntries = @($InstallDir)
if (-not $UseBundledCore) { $PathEntries += $VenvScripts }
foreach ($p in $PathEntries) {
    if ($UserPath -notlike "*$p*") { $UserPath = "$UserPath;$p" }
}
[Environment]::SetEnvironmentVariable("Path", $UserPath, "User")
$env:Path = "$env:Path;$InstallDir"
if (-not $UseBundledCore) { $env:Path = "$env:Path;$VenvScripts" }
$env:CLARITYIME_ROOT = $RepoRoot
$env:CLARITYIME_VENV = $Venv
if ($UseBundledCore) {
    $env:CLARITYIME_CORE_EXE = $InstalledCore
    $env:CLARITYIME_CORE = $InstalledCore
    Write-Host "CLARITYIME_CORE_EXE=$InstalledCore"
}

Write-Host ""
Write-Host "Installed -> $InstallDir"
Write-Host ""
if ($UseBundledCore) {
    Write-Host "Core: bundled clarityime-core.exe (no Python required for serve/capture)"
} else {
    Write-Host "Core: Python venv (.venv) — build standalone: scripts\build_core.ps1"
}
Write-Host ""
Write-Host "UI:  clarityime-start"
Write-Host "CLI: clarityime --version   (new terminal after PATH refresh)"
Write-Host "     clarityime serve | clarityime capture | clarityime contacts list"
Write-Host ""
Write-Host "Tray -> Settings for contacts / mode / privacy (no terminal)"
