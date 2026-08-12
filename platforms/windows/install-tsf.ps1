# Register / unregister ClarityIME TSF Text Input Processor (requires Administrator)
param(
    [switch]$Unregister,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$WinDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TsfDir = Join-Path $WinDir "ClarityIMETSF"
$DistTsf = Join-Path $WinDir "dist-tsf"

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host "ERROR: Run PowerShell as Administrator (TSF TIP registration writes HKLM)." -ForegroundColor Red
    Write-Host "  Right-click PowerShell → Run as administrator"
    Write-Host "  Then: cd `"$WinDir`"; .\install-tsf.ps1"
    exit 1
}

if (-not $SkipBuild) {
    Write-Host "Building ClarityIMETSF..."
    Push-Location $TsfDir
    dotnet publish -c Release -r win-x64 --self-contained false -o $DistTsf
    Pop-Location
}

$Comhost = Join-Path $DistTsf "ClarityIMETSF.comhost.dll"
$Dll = Join-Path $DistTsf "ClarityIMETSF.dll"

if (-not (Test-Path $Comhost)) {
    Write-Host "ERROR: Missing $Comhost — build failed?" -ForegroundColor Red
    exit 1
}

$TipGuid = "{8F3C2A1E-4B5D-6E7F-8091-A2B3C4D5E6F7}"
$CatKeyboard = "{34745C63-B2F0-4784-8B67-5E12C8701A31}"

if ($Unregister) {
    Write-Host "Unregistering ClarityIME TSF TIP..."
    regsvr32 /u /s $Comhost
    Remove-Item -Path "HKLM:\SOFTWARE\Microsoft\CTF\TIP\$TipGuid" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "HKLM:\SOFTWARE\Classes\CLSID\$TipGuid" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Unregistered. Restart apps or sign out for changes to apply."
    exit 0
}

Write-Host "Registering COM host: $Comhost"
$proc = Start-Process -FilePath "regsvr32" -ArgumentList "/s", "`"$Comhost`"" -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    Write-Host "WARN: regsvr32 exit $($proc.ExitCode) — continuing with manual TIP keys"
}

# Manual TIP registry (ComRegisterFunction may not run under regsvr32 for .NET comhost)
$tipBase = "HKLM:\SOFTWARE\Microsoft\CTF\TIP\$TipGuid"
New-Item -Path $tipBase -Force | Out-Null
Set-ItemProperty -Path $tipBase -Name "Description" -Value "ClarityIME Voice Clarify"
Set-ItemProperty -Path $tipBase -Name "IconFile" -Value $Comhost
Set-ItemProperty -Path $tipBase -Name "IconIndex" -Value 0 -Type DWord
Set-ItemProperty -Path $tipBase -Name "Category" -Value $CatKeyboard

foreach ($pair in @(
        @{ Id = "00000409"; Desc = "ClarityIME (English)" },
        @{ Id = "00000804"; Desc = "ClarityIME (中文)" }
    )) {
    $prof = Join-Path $tipBase "LanguageProfile\$($pair.Id)"
    New-Item -Path $prof -Force | Out-Null
    Set-ItemProperty -Path $prof -Name "Description" -Value $pair.Desc
    Set-ItemProperty -Path $prof -Name "IconFile" -Value $Comhost
    Set-ItemProperty -Path $prof -Name "Enable" -Value 1 -Type DWord
}

$clsid = "HKLM:\SOFTWARE\Classes\CLSID\$TipGuid"
New-Item -Path $clsid -Force | Out-Null
Set-ItemProperty -Path $clsid -Name "(default)" -Value "ClarityIME Text Input Processor"
$inproc = Join-Path $clsid "InprocServer32"
New-Item -Path $inproc -Force | Out-Null
Set-ItemProperty -Path $inproc -Name "(default)" -Value $Comhost
Set-ItemProperty -Path $inproc -Name "ThreadingModel" -Value "Apartment"

Write-Host ""
Write-Host "ClarityIME TSF registered." -ForegroundColor Green
Write-Host ""
Write-Host "Enable the input method:"
Write-Host "  Settings → Time & language → Language & region"
Write-Host "  → Preferred languages → Language options → Add a keyboard"
Write-Host "  → ClarityIME (English) or ClarityIME (中文)"
Write-Host ""
Write-Host "Prerequisites:"
Write-Host "  1. clarityime serve  (http://127.0.0.1:17800) — tray host can start this"
Write-Host "  2. Select ClarityIME in the taskbar IME picker"
Write-Host "  3. F9 in a text field → voice clarify (when key sink active)"
Write-Host ""
Write-Host "Debug log: $env:LOCALAPPDATA\ClarityIME\tsf-debug.log"
Write-Host "Tray fallback still works: Ctrl+Shift+Space via clarityime-host"
