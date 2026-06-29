@echo off
REM ============================================================
REM RPA-Ponto-SantCec — Launcher para Windows Task Scheduler
REM ============================================================

cd /d "%~dp0"

REM Ativa venv se existir
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python main.py

REM Captura exit code para o Task Scheduler
exit /b %ERRORLEVEL%
