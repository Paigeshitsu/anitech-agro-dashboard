@echo off
echo ========================================
echo Starting ANITECH Django Server on localhost
echo ========================================
echo.

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
echo Starting Django server on http://127.0.0.1:8000
echo Open your browser and navigate to: http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver 127.0.0.1:8000
