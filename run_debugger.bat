@echo off
REM ==============================================================================
REM AI-Based Intelligent Desktop Debugger
REM Launcher script using the project's dedicated virtual environment (.venv)
REM ==============================================================================

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe
    echo Please set up the environment and install dependencies:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Starting AI-Based Intelligent Desktop Debugger...
".venv\Scripts\python.exe" main.py %*

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%.
    pause
)
