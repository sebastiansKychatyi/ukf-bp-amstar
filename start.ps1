# AmStar Platform - PowerShell Startup Script
# Usage: Right-click -> Run with PowerShell
# OR: powershell -ExecutionPolicy Bypass -File start.ps1

$Host.UI.RawUI.WindowTitle = "AmStar - Startup"

Write-Host ""
Write-Host " ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host " ║         AmStar Football Platform         ║" -ForegroundColor Cyan
Write-Host " ║      FastAPI + Nuxt.js + PostgreSQL      ║" -ForegroundColor Cyan
Write-Host " ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# ── 1. Check Docker ──────────────────────────────────────────────────────────
Write-Host " [CHECK] Verifying Docker is running..." -ForegroundColor Yellow
try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Docker not running" }
    Write-Host " [OK]    Docker Desktop is running" -ForegroundColor Green
} catch {
    Write-Host " [ERROR] Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ── 2. Stop old containers ───────────────────────────────────────────────────
Write-Host " [INFO]  Stopping old containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml down 2>&1 | Out-Null

# ── 3. Start all services ────────────────────────────────────────────────────
Write-Host " [INFO]  Building and starting services (db, redis, backend, frontend)..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host " [ERROR] Failed to start containers. Showing logs:" -ForegroundColor Red
    docker-compose -f docker-compose.local.yml logs --tail=50
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host " [OK]    All containers started" -ForegroundColor Green

# ── 4. Wait for backend health ───────────────────────────────────────────────
Write-Host ""
Write-Host " [INFO]  Waiting for backend to become healthy..." -ForegroundColor Yellow

$attempt = 0
$maxAttempts = 40
$backendOk = $false

while ($attempt -lt $maxAttempts) {
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host " [OK]    Backend is healthy! ($attempt attempts)" -ForegroundColor Green
            $backendOk = $true
            break
        }
    } catch {}

    $dots = "." * ($attempt % 4 + 1)
    Write-Host " [WAIT]  Attempt $attempt/$maxAttempts $dots" -ForegroundColor Gray -NoNewline
    Write-Host "`r" -NoNewline
    Start-Sleep -Seconds 3
}

if (-not $backendOk) {
    Write-Host " [WARN]  Backend not healthy after $($maxAttempts * 3)s - check logs" -ForegroundColor Yellow
}

# ── 5. Wait for frontend ─────────────────────────────────────────────────────
Write-Host " [INFO]  Waiting for frontend (Nuxt.js)..." -ForegroundColor Yellow
$frontendOk = $false
for ($i = 1; $i -le 20; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            Write-Host " [OK]    Frontend is ready!" -ForegroundColor Green
            $frontendOk = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 5
}

if (-not $frontendOk) {
    Write-Host " [WARN]  Frontend still loading (Nuxt install takes 2-5 min first time)" -ForegroundColor Yellow
}

# ── 6. Show status ───────────────────────────────────────────────────────────
Write-Host ""
Write-Host " ╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host " ║            Services Running              ║" -ForegroundColor Green
Write-Host " ╠══════════════════════════════════════════╣" -ForegroundColor Green
Write-Host " ║  Frontend  :  http://localhost:3000      ║" -ForegroundColor Green
Write-Host " ║  Backend   :  http://localhost:8000      ║" -ForegroundColor Green
Write-Host " ║  API Docs  :  http://localhost:8000/docs ║" -ForegroundColor Green
Write-Host " ║  DB Admin  :  localhost:5432             ║" -ForegroundColor Green
Write-Host " ║  Redis     :  localhost:6379             ║" -ForegroundColor Green
Write-Host " ╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Container status table
Write-Host " [INFO]  Container status:" -ForegroundColor Cyan
docker-compose -f docker-compose.local.yml ps
Write-Host ""

# ── 7. Quick API health check ────────────────────────────────────────────────
Write-Host " [INFO]  Quick API health check:" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction Stop
    Write-Host "         /health -> " -NoNewline
    Write-Host "OK" -ForegroundColor Green
    $health | ConvertTo-Json | Write-Host
} catch {
    Write-Host "         /health -> " -NoNewline
    Write-Host "not reachable yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host " [INFO]  Useful commands:" -ForegroundColor Cyan
Write-Host "         Logs:        docker-compose -f docker-compose.local.yml logs -f"
Write-Host "         Stop:        docker-compose -f docker-compose.local.yml down"
Write-Host "         Restart:     docker-compose -f docker-compose.local.yml restart backend"
Write-Host ""

# ── 8. Open browser ──────────────────────────────────────────────────────────
Start-Sleep -Seconds 1
Write-Host " [INFO]  Opening API docs in browser..." -ForegroundColor Yellow
Start-Process "http://localhost:8000/docs"
Start-Sleep -Seconds 2
Write-Host " [INFO]  Opening frontend in browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host " [DONE]  AmStar is running! Press Enter to exit this window." -ForegroundColor Green
Read-Host
