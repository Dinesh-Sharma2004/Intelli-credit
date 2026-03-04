@echo off
REM Intelli-Credit Installation Script for Windows

echo ========================================
echo Intelli-Credit Installation Script
echo ========================================

REM Check for Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Error: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo.
echo Checking prerequisites...
echo ^✓ Docker is installed

REM Create environment file
echo.
echo Setting up environment...
if not exist .env (
    copy .env.example .env
    echo ^✓ Created .env file
) else (
    echo ^✓ .env file already exists
)

REM Build and start services
echo.
echo Building and starting services...
docker-compose build
docker-compose up -d

echo.
echo Waiting for services to start...
timeout /t 10 /nobreak

REM Check service health
echo.
echo Checking service status...
docker-compose ps

echo.
echo ========================================
echo ^✓ Installation completed!
echo ========================================
echo.
echo Access the application:
echo   Frontend:       http://localhost:3000
echo   Backend API:    http://localhost:8000
echo   API Docs:       http://localhost:8000/docs
echo   Vector DB:      http://localhost:8001
echo.
pause
