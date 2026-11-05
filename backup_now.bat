@echo off
title PharmaSuite Backup
cd /d "%~dp0"
".venv\Scripts\python.exe" backup_db.py
pause
