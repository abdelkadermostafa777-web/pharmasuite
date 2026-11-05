@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" build_elements.py
pause
