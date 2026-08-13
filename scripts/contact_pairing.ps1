# ClarityIME contact pairing — export/import via local core API
# Usage:
#   .\scripts\contact_pairing.ps1 export -Name "Sam" -Out sam.json
#   .\scripts\contact_pairing.ps1 import -Path sam.json
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("export", "import")]
    [string]$Action,
    [string]$Name = "",
    [string]$Out = "",
    [string]$Path = "",
    [string]$Core = "http://127.0.0.1:17800"
)

$ErrorActionPreference = "Stop"

if ($Action -eq "export") {
    if (-not $Name) { throw "export requires -Name" }
    $enc = [uri]::EscapeDataString($Name)
    $json = Invoke-RestMethod -Uri "$Core/v1/contacts/export?name=$enc" -Method Get
    $text = $json | ConvertTo-Json -Depth 10
    if ($Out) {
        Set-Content -Path $Out -Value $text -Encoding UTF8
        Write-Host "exported -> $Out"
    } else {
        Write-Output $text
    }
    exit 0
}

if (-not $Path) { throw "import requires -Path" }
$body = Get-Content -Path $Path -Raw -Encoding UTF8
Invoke-RestMethod -Uri "$Core/v1/contacts/import" -Method Post -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) -ContentType "application/json; charset=utf-8" | Out-Null
Write-Host "imported from $Path"
exit 0
