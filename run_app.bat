@echo off
REM Change directory to the project root (where this file is located)
cd /d "%~dp0"

REM Check for virtual environment and activate if found
if exist ".venv\Scripts\activate.bat" (
    echo Virtual environment found. Activating...
    call ".venv\Scripts\activate.bat"
) else (
    echo Virtual environment not found. Creating...
    python -m venv .venv
    echo Activating virtual environment...
    call ".venv\Scripts\activate.bat"
)

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo Starting Inniverse AI...
echo Project Root: %CD%
streamlit run src/app/main.py