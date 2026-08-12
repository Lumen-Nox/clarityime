# Build ClarityIME Windows host (self-contained exe) and optional TSF IME
param(
    [switch]$IncludeTsf
)

$ErrorActionPreference = "Stop"
$HostDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Building ClarityIMEHost..."
Push-Location (Join-Path $HostDir "ClarityIMEHost")
dotnet publish -c Release -r win-x64 --self-contained false -o (Join-Path $HostDir "dist")
Pop-Location
Write-Host "Built → platforms/windows/dist/clarityime-host.exe"

if ($IncludeTsf) {
    Write-Host "Building ClarityIMETSF..."
    Push-Location (Join-Path $HostDir "ClarityIMETSF")
    dotnet publish -c Release -r win-x64 --self-contained false -o (Join-Path $HostDir "dist-tsf")
    Pop-Location
    Write-Host "Built → platforms/windows/dist-tsf/ClarityIMETSF.comhost.dll"
}

# Always build TSF in Release for dotnet build verification
Write-Host "Building ClarityIMETSF (Release)..."
Push-Location (Join-Path $HostDir "ClarityIMETSF")
dotnet build -c Release
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Pop-Location
Write-Host "TSF build OK"
