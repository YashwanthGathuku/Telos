<#
.SYNOPSIS
    Start all TELOS services in the correct order.
.DESCRIPTION
    Launches each TELOS service in a separate PowerShell window.
    Services are started in dependency order — independent services first,
    then the orchestrator, then the desktop shell.
.NOTES
    Run from the repository root: .\scripts\start-all.ps1
    Ensure .env is configured before running (see docs/SETUP.md).
#>

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== TELOS Service Launcher ===" -ForegroundColor Cyan
Write-Host "Repo root: $RepoRoot"
Write-Host ""

# --- 1. UIGraph (C#, port 8083) ---
$uigraph = Join-Path $RepoRoot "uigraph\windows"
if (Test-Path $uigraph) {
    Write-Host "[1/6] Starting UIGraph (port 8083)..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$uigraph'; dotnet run"
} else {
    Write-Host "[1/6] SKIP: UIGraph directory not found at $uigraph" -ForegroundColor Yellow
}

# --- 2. Delta Engine (Rust, port 8084) ---
$deltaEngine = Join-Path $RepoRoot "uigraph\rust_engine"
if (Test-Path $deltaEngine) {
    Write-Host "[2/6] Starting Delta Engine (port 8084)..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$deltaEngine'; cargo run --release"
} else {
    Write-Host "[2/6] SKIP: Delta Engine directory not found at $deltaEngine" -ForegroundColor Yellow
}

# --- 3. Screenshot Engine (Go, port 8085) ---
$captureEngine = Join-Path $RepoRoot "services\capture_engine"
if (Test-Path $captureEngine) {
    Write-Host "[3/6] Starting Screenshot Engine (port 8085)..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$captureEngine'; go run ."
} else {
    Write-Host "[3/6] SKIP: Capture Engine directory not found at $captureEngine" -ForegroundColor Yellow
}

# --- 4. Scheduler (Go, port 8081) ---
$scheduler = Join-Path $RepoRoot "services\scheduler"
if (Test-Path $scheduler) {
    Write-Host "[4/6] Starting Scheduler (port 8081)..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$scheduler'; go run ."
} else {
    Write-Host "[4/6] SKIP: Scheduler directory not found at $scheduler" -ForegroundColor Yellow
}

# Brief pause so downstream services are ready
Start-Sleep -Seconds 2

# --- 5. Orchestrator (Python, port 8080) ---
$orchestrator = Join-Path $RepoRoot "services\orchestrator"
if (Test-Path $orchestrator) {
    Write-Host "[5/6] Starting Orchestrator (port 8080)..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$RepoRoot'; python -m services.orchestrator"
} else {
    Write-Host "[5/6] SKIP: Orchestrator directory not found at $orchestrator" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# --- 6. Desktop Shell (Tauri, dev mode) ---
$desktop = Join-Path $RepoRoot "apps\desktop"
if (Test-Path $desktop) {
    Write-Host "[6/6] Starting Desktop Shell (Tauri dev)..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$desktop'; npm run tauri dev"
} else {
    Write-Host "[6/6] SKIP: Desktop directory not found at $desktop" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== All services launched ===" -ForegroundColor Cyan
Write-Host "Verify health: Invoke-RestMethod http://localhost:8080/system/state" -ForegroundColor Gray
