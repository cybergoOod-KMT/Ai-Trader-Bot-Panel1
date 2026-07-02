param()

$ErrorActionPreference = "Stop"

function Write-Info($message) {
  Write-Host "[INFO] $message" -ForegroundColor Cyan
}

function Write-WarnLine($message) {
  Write-Host "[WARN] $message" -ForegroundColor Yellow
}

function Write-Ok($message) {
  Write-Host "[OK] $message" -ForegroundColor Green
}

function Test-PortFree([int]$Port) {
  $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
  return -not $listeners
}

function New-RandomSecret([int]$Bytes = 48) {
  $buffer = New-Object byte[] $Bytes
  [System.Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
  return [Convert]::ToBase64String($buffer)
}

function New-FernetKey() {
  $buffer = New-Object byte[] 32
  [System.Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
  return [Convert]::ToBase64String($buffer).Replace('+', '-').Replace('/', '_')
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Info "Checking Docker Desktop..."
docker info | Out-Null

$envFile = Join-Path $root ".env"
$exampleFile = Join-Path $root ".env.example"

if (-not (Test-Path $envFile)) {
  Copy-Item $exampleFile $envFile
  Write-Ok ".env created from .env.example"
}

$content = Get-Content $envFile
$exampleContent = Get-Content $exampleFile
$map = @{}
$exampleMap = @{}
foreach ($line in $content) {
  if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
  $parts = $line.Split('=', 2)
  $map[$parts[0]] = $parts[1]
}
foreach ($line in $exampleContent) {
  if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
  $parts = $line.Split('=', 2)
  $exampleMap[$parts[0]] = $parts[1]
}

if (-not $map["SECRET_KEY"]) {
  $map["SECRET_KEY"] = New-RandomSecret
  Write-Ok "Generated SECRET_KEY"
}

if (-not $map["FERNET_KEY"]) {
  $map["FERNET_KEY"] = New-FernetKey
  Write-Ok "Generated FERNET_KEY"
}

$panelPort = if ($map["PANEL_PORT"]) { [int]$map["PANEL_PORT"] } else { 3200 }
while (-not (Test-PortFree $panelPort)) {
  $panelPort++
}
$map["PANEL_PORT"] = "$panelPort"

$apiPort = if ($map["API_PORT"]) { [int]$map["API_PORT"] } else { 8000 }
while (-not (Test-PortFree $apiPort)) {
  $apiPort++
}
$map["API_PORT"] = "$apiPort"
$map["NEXT_PUBLIC_API_BASE_URL"] = "http://localhost:$apiPort"

$defaults = @{
  "DRY_RUN_DEFAULT" = "true"
  "RISK_MAX_TOTAL_BUDGET_USDT" = "1000"
  "RISK_PER_ORDER_USDT" = "100"
  "RISK_MIN_USDT_RESERVE" = "50"
  "RISK_MAX_OPEN_POSITIONS" = "5"
  "RISK_MAX_DAILY_LOSS_PCT" = "5"
  "RISK_SYMBOL_COOLDOWN_SECONDS" = "300"
  "REAL_CONFIRM_TOKEN_TTL_SECONDS" = "120"
  "BOT_SCAN_INTERVAL_SECONDS" = "30"
  "WATCH_POLL_INTERVAL_SECONDS" = "15"
  "POSITION_MONITOR_INTERVAL_SECONDS" = "15"
  "BOT_API_ERROR_THRESHOLD" = "3"
}

foreach ($key in $defaults.Keys) {
  if (-not $map.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($map[$key])) {
    if ($exampleMap.ContainsKey($key) -and -not [string]::IsNullOrWhiteSpace($exampleMap[$key])) {
      $map[$key] = $exampleMap[$key]
    } else {
      $map[$key] = $defaults[$key]
    }
  }
}

$orderedKeys = @(
  "APP_ENV",
  "PANEL_PORT",
  "API_PORT",
  "DATABASE_URL",
  "SECRET_KEY",
  "FERNET_KEY",
  "ADMIN_USERNAME",
  "ADMIN_PASSWORD",
  "REAL_TRADING_ENABLED",
  "DRY_RUN_DEFAULT",
  "DEFAULT_QUOTE_ASSET",
  "OPENAI_DEFAULT_MODEL",
  "OPENAI_URL",
  "TABDEAL_BASE_URL",
  "BINANCE_KLINES_URL",
  "RISK_MAX_TOTAL_BUDGET_USDT",
  "RISK_PER_ORDER_USDT",
  "RISK_MIN_USDT_RESERVE",
  "RISK_MAX_OPEN_POSITIONS",
  "RISK_MAX_DAILY_LOSS_PCT",
  "RISK_SYMBOL_COOLDOWN_SECONDS",
  "REAL_CONFIRM_TOKEN_TTL_SECONDS",
  "BOT_SCAN_INTERVAL_SECONDS",
  "WATCH_POLL_INTERVAL_SECONDS",
  "POSITION_MONITOR_INTERVAL_SECONDS",
  "BOT_API_ERROR_THRESHOLD",
  "NEXT_PUBLIC_API_BASE_URL"
)

$newLines = foreach ($key in $orderedKeys) {
  if ($map.ContainsKey($key)) {
    "$key=$($map[$key])"
  }
}
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($envFile, $newLines, $utf8NoBom)

Write-Info "Starting Docker services..."
docker compose up -d --build

Write-Host ""
Write-Ok "Panel URL: http://localhost:$($map["PANEL_PORT"])"
Write-Ok "API URL: http://localhost:$($map["API_PORT"])"
Write-Ok "Default username: $($map["ADMIN_USERNAME"])"
if ($map["ADMIN_PASSWORD"] -eq "change_this_password") {
  Write-WarnLine "Default password is still active. Change it immediately after login."
}
