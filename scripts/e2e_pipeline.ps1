# End-to-end API pipeline smoke (no microphone) — candidates + feedback bundle + contact export
param(
    [int]$Port = 17897
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Base = "http://127.0.0.1:$Port"
$E2eData = Join-Path $env:TEMP "clarityime_e2e_data"

Set-Location $RepoRoot
$env:PYTHONPATH = $RepoRoot
$env:CLARITYIME_DATA_DIR = $E2eData
if (Test-Path $E2eData) { Remove-Item -Recurse -Force $E2eData -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $E2eData | Out-Null

$launcher = Join-Path $env:TEMP "clarityime_e2e_server.py"
@"
import os, sys
sys.path.insert(0, r"$RepoRoot")
os.environ["CLARITYIME_DATA_DIR"] = r"$E2eData"
from clarityime.server import run_server
run_server(host="127.0.0.1", port=$Port)
"@ | Set-Content -Path $launcher -Encoding UTF8

$core = Start-Process -FilePath "python" -ArgumentList "-u", $launcher `
    -WorkingDirectory $RepoRoot -PassThru -WindowStyle Hidden
try {
    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
        try {
            $h = Invoke-RestMethod -Uri "$Base/v1/health" -TimeoutSec 2
            if ($h.ok) { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 400 }
    }
    if (-not $ready) { throw "core not ready on $Base" }

    $tokenPath = Join-Path $E2eData ".local_api_token"
    if (-not (Test-Path $tokenPath)) { throw "missing API token at $tokenPath" }
    $token = (Get-Content $tokenPath -Raw).Trim()
    $authHeaders = @{ "X-ClarityIME-Token" = $token }

    $sec = Invoke-RestMethod -Uri "$Base/v1/security/status" -TimeoutSec 2
    if (-not $sec.cerome_tags) { throw "security status missing cerome_tags" }

    $raw = "hello um I wanted to ask when the project finishes"
    $nbest = @($raw, "when does the project finish")

    $cBody = (@{ text = $raw; nbest = $nbest; mode = "default" } | ConvertTo-Json -Compress)
    $c = Invoke-RestMethod -Uri "$Base/v1/candidates" -Method Post -Body $cBody -ContentType "application/json; charset=utf-8"
    if (-not $c.candidates -or $c.candidates.Count -lt 1) { throw "candidates empty" }

    $contact = @{
        name = "E2E_Test"
        relationship = "friend"
        style_notes = "brief"
        comprehension_notes = "smoke"
        cerome = @{
            L2 = @{ clarity = 0.8; warmth = 0.5; efficiency = 0.7; precision = 0.5; humor = 0.2 }
            L5 = @{ label = "steady" }
        }
    } | ConvertTo-Json -Depth 6 -Compress
    $saved = Invoke-RestMethod -Uri "$Base/v1/contacts" -Method Post -Body $contact -ContentType "application/json; charset=utf-8" -Headers $authHeaders
    if (-not $saved.name) { throw "contact POST failed" }
    if (-not $saved.cerome) { throw "contact missing cerome tags" }

    $exp = Invoke-RestMethod -Uri "$Base/v1/contacts/export?name=E2E_Test" -Method Get
    if (-not $exp.name) { throw "export missing name" }
    if (-not $exp.cerome) { throw "export missing cerome" }

    $fBody = @{
        raw = $raw
        preferred = '[user_feedback] too formal'
        nbest = $nbest
        mode = "default"
        candidates = $c.candidates
    } | ConvertTo-Json -Depth 5 -Compress
    $f = Invoke-RestMethod -Uri "$Base/v1/feedback" -Method Post -Body $fBody -ContentType "application/json; charset=utf-8" -Headers $authHeaders
    if (-not $f.bundle_url) { throw "feedback missing bundle_url" }

    $bundleId = ($f.bundle_url -split '/')[-1]
    $b = Invoke-RestMethod -Uri "$Base/v1/bundles/$bundleId" -Method Get
    if (-not $b.raw) { throw "bundle GET failed" }

    Write-Host "e2e_pipeline ok: security + cerome + export + feedback on port $Port"
    exit 0
}
finally {
    if ($core -and -not $core.HasExited) { Stop-Process -Id $core.Id -Force -ErrorAction SilentlyContinue }
    Remove-Item $launcher -Force -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $E2eData -ErrorAction SilentlyContinue
}
