@echo off
REM Lance la routine quotidienne et conserve une trace de chaque execution.
REM Appele par la tache planifiee « LumenJuris - Prospection 8h30 ».
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist logs mkdir logs
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set JOUR=%%c-%%b-%%a
python routine.py >> "logs\routine-%JOUR%.log" 2>&1
exit /b %errorlevel%
