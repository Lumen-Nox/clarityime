# ClarityIME core smoke - start server briefly, hit health + candidates, exit.
$ErrorActionPreference = "Stop"
chcp 65001 | Out-Null
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot
$env:PYTHONPATH = $repoRoot

$port = 17899
$hostAddr = "127.0.0.1"
$base = "http://${hostAddr}:${port}"

$launcher = Join-Path $env:TEMP "clarityime_smoke_server.py"
@'
from clarityime.server import run_server
run_server(host="127.0.0.1", port=17899)
'@ | Set-Content -Path $launcher -Encoding UTF8

$server = Start-Process -FilePath "python" `
    -ArgumentList $launcher `
    -WorkingDirectory $repoRoot `
    -PassThru -WindowStyle Hidden

try {
    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
        try {
            $health = Invoke-RestMethod -Uri "$base/v1/health" -Method Get -TimeoutSec 2
            if ($health.ok) { $ready = $true; break }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    if (-not $ready) { throw "server did not become ready on $base" }

    $body = '{"text":"hello clarityime smoke","nbest":["hello clarityime smoke","hello clarity"],"mode":"default"}'

    $candidates = Invoke-RestMethod -Uri "$base/v1/candidates" `
        -Method Post -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
        -ContentType "application/json; charset=utf-8" `
        -TimeoutSec 10

    if (-not $candidates.candidates -or $candidates.candidates.Count -lt 1) {
        throw "candidates response empty"
    }

    Write-Host "smoke_core ok: health + candidates"
    exit 0
}
finally {
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $launcher -Force -ErrorAction SilentlyContinue
}
