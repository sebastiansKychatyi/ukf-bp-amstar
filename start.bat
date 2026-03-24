@echo off
chcp 65001 >nul
title AmStar - Startup

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║         AmStar Football Platform         ║
echo  ║      FastAPI + Nuxt.js + PostgreSQL      ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Check Docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)
echo  [OK] Docker is running

:: Go to project directory
cd /d "%~dp0"

:: Stop old containers if running
echo  [INFO] Stopping old containers...
docker-compose -f docker-compose.local.yml down >nul 2>&1

:: Build and start
echo  [INFO] Starting all services (db, redis, backend, frontend)...
docker-compose -f docker-compose.local.yml up -d --build

if %errorlevel% neq 0 (
    echo  [ERROR] Failed to start containers.
    docker-compose -f docker-compose.local.yml logs
    pause
    exit /b 1
)

echo.
echo  [INFO] Waiting for backend to be healthy...

set /a attempt=0
:wait_loop
set /a attempt+=1
if %attempt% gtr 30 (
    echo  [WARN] Backend not healthy after 90s - check logs below
    goto :show_info
)

:: Check backend health
curl -s -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] Backend is healthy!
    goto :show_info
)

timeout /t 3 /nobreak >nul
echo  [INFO] Attempt %attempt%/30 - waiting...
goto :wait_loop

:show_info
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║            Services Running              ║
echo  ╠══════════════════════════════════════════╣
echo  ║  Frontend  :  http://localhost:3000      ║
echo  ║  Backend   :  http://localhost:8000      ║
echo  ║  API Docs  :  http://localhost:8000/docs ║
echo  ║  Database  :  localhost:5432             ║
echo  ║  Redis     :  localhost:6379             ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Show container status
echo  [INFO] Container status:
docker-compose -f docker-compose.local.yml ps
echo.

:: Open browser
echo  [INFO] Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:8000/docs
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo  [INFO] To view logs:  docker-compose -f docker-compose.local.yml logs -f
echo  [INFO] To stop:       docker-compose -f docker-compose.local.yml down
echo.
pause
