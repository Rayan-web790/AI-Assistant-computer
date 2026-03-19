@echo off
TITLE AI Jarvis Assistant
cd /d "%~dp0"

echo Checking for virtual environment...
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] .venv not found. Attempting to run with system Python...
)

echo Starting AI Jarvis...
python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] The program crashed or failed to start.
    pause
)
