@echo off
echo Stopping any running instances of the application...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1

echo Waiting for processes to terminate...
timeout /t 2 /nobreak >nul

echo Starting OSINT Comments Application...

echo Starting FastAPI Backend...
start cmd /k "cd api && poetry run python run.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo Starting Vue.js Frontend...
start cmd /k "cd frontend && npm run serve"

echo Application restarted!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:8080
echo.
echo Please wait a moment for the application to fully initialize.
echo You may need to refresh your browser page.
