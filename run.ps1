param(
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root "backend")
$env:OCR_PROVIDER = "tesseract"

Write-Host "Preparing ONE AI Care Continuity..." -ForegroundColor Cyan
py -3 -m app.bootstrap
if ($LASTEXITCODE -ne 0) {
  throw "Database bootstrap failed."
}

Write-Host "Starting the app at http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor DarkGray
py -3 -m uvicorn app.main:app --host 0.0.0.0 --port $Port
