@echo off
REM Lance la routine quotidienne et garde une trace de chaque execution.
REM Appele par la tache planifiee "LumenJuris - Prospection 8h30".
REM Les arguments sont transmis : lancer-routine.bat --verifier fonctionne.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist logs mkdir logs
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set JOUR=%%c-%%b-%%a
echo. >> "logs\routine-%JOUR%.log"
echo ===== %date% %time% ===== >> "logs\routine-%JOUR%.log"
python routine.py %* >> "logs\routine-%JOUR%.log" 2>&1
set CODE=%errorlevel%
type "logs\routine-%JOUR%.log"
exit /b %CODE%
