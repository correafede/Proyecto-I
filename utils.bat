@echo off
REM Biblioteca - Command shortcuts

:menu
cls
echo.
echo ====================================
echo   BIBLIOTECA - Utilidades
echo ====================================
echo.
echo 1. Iniciar proyecto completo
echo 2. Ver logs en tiempo real
echo 3. Detener servicios
echo 4. Ver estado de contenedores
echo 5. Reiniciar base de datos
echo 6. Acceder a base de datos (psql)
echo 7. Salir
echo.
set /p choice="Selecciona una opcion (1-7): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto logs
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto status
if "%choice%"=="5" goto restart_db
if "%choice%"=="6" goto psql
if "%choice%"=="7" goto exit
goto menu

:start
echo Iniciando Biblioteca...
docker compose up --pull always
goto menu

:logs
echo Mostrando logs en tiempo real...
docker compose logs -f
goto menu

:stop
echo Deteniendo servicios...
docker compose down
pause
goto menu

:status
echo Estado de contenedores:
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
pause
goto menu

:restart_db
echo Deteniendo base de datos...
docker compose down postgres
echo Limpiando volumen de datos...
docker volume rm biblioteca_postgres_data 2>nul
echo Reiniciando base de datos...
docker compose up postgres -d
timeout /t 5
docker compose up api
goto menu

:psql
echo Conectando a PostgreSQL...
docker exec -it pg-biblioteca psql -U federico -d biblioteca_seguridad
goto menu

:exit
echo Hasta luego!
exit /b 0
