@echo off
REM Build script for Selfmade Labs Docker images
REM This script builds all lab images with ttyd web terminals

echo ========================================
echo Building Selfmade Labs Docker Images
echo ========================================
echo.

REM Build Ubuntu SSH Lab
echo [1/2] Building Ubuntu SSH Lab...
cd labs\ubuntu-ssh
docker build -t selfmade/ubuntu-ssh:latest .
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build Ubuntu SSH Lab
    exit /b 1
)
cd ..\..
echo ✓ Ubuntu SSH Lab built successfully
echo.

REM Build Kali Linux Lab
echo [2/2] Building Kali Linux Lab...
cd labs\kali-linux
docker build -t selfmade/kali-linux:latest .
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build Kali Linux Lab
    exit /b 1
)
cd ..\..
echo ✓ Kali Linux Lab built successfully
echo.

echo ========================================
echo All lab images built successfully!
echo ========================================
echo.
echo Available images:
docker images | findstr selfmade
echo.
echo To start the platform, run:
echo   uvicorn app.main:app --reload --port 8000
echo.
