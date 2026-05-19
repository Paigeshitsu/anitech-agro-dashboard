@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"

echo ========================================
echo Starting ANITECH Django Server on localhost
echo ========================================
echo.

if not exist "%VENV_PYTHON%" (
    echo ERROR: Project virtual environment not found at:
    echo %VENV_PYTHON%
    echo.
    echo Create it and install dependencies first.
    pause
    exit /b 1
)

REM Check if port 8000 is in use
netstat -ano | findstr :8000 > nul
if %errorlevel%==0 (
    echo WARNING: Port 8000 appears to be in use!
    echo Trying to find what is using it...
    netstat -ano | findstr :8000
    echo.
    echo Please close the other application or use a different port.
    echo To use a different port, run: python manage.py runserver 8001
    echo.
    pause
    exit /b 1
)

REM Start the Django development server on 127.0.0.1:8000
echo Syncing Bantay Presyo data for Legazpi and Naga...
"%VENV_PYTHON%" bantay_presyo_region_v_collector.py
if %errorlevel% neq 0 (
    echo WARNING: Bantay Presyo sync failed. Starting server with existing local data.
    echo.
)

echo Starting Django server on http://127.0.0.1:8000
echo Open your browser and navigate to: http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Always use the project's own virtual environment
"%VENV_PYTHON%" manage.py runserver 127.0.0.1:8000
