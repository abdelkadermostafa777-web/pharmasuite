@echo off
title PharmaSuite Pro - Web
cd /d "%~dp0"

rem Open the browser after the server has time to start
start "" cmd /c "timeout /t 4 /nobreak >nul && start http://127.0.0.1:8000"

rem Run the web app (closing this window stops the server)
".venv\Scripts\python.exe" -m uvicorn app.main:app --port 8000
if errorlevel 1 pause
