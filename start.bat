@echo off
REM Start the Biblioteca project with Docker Compose

echo.
echo ====================================
echo   BIBLIOTECA - Sistema de Inicio
echo ====================================
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker no esta corriendo. Por favor inicia Docker Desktop.
    pause
    exit /b 1
)

echo Iniciando servicios...
echo.

REM Start the project with docker compose
docker compose up --pull always

pause
