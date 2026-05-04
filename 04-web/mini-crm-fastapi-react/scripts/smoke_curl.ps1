# Проверка API из PowerShell (API на localhost:8000)
$BASE = if ($env:CRM_API_URL) { $env:CRM_API_URL.TrimEnd('/') } else { "http://127.0.0.1:8000" }
Write-Host "GET $BASE/health"
Invoke-RestMethod -Uri "$BASE/health" -Method Get | ConvertTo-Json
Write-Host "GET $BASE/clients?limit=5"
Invoke-RestMethod -Uri "$BASE/clients?limit=5" -Method Get | ConvertTo-Json
