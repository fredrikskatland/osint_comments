@echo off
echo Starting OSINT Comments Application...

echo Starting FastAPI Backend...
start cmd /k "cd api && poetry run python run.py"

echo Starting Vue.js Frontend...
start cmd /k "cd frontend && npm run serve"

echo Application started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:8080
