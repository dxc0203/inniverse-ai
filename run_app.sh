#!/bin/bash
cd "$(dirname "$0")"

if [ -f ".venv/bin/activate" ]; then
    echo "Virtual environment found. Activating..."
    source .venv/bin/activate
else
    echo "Virtual environment not found. Creating..."
    python3 -m venv .venv
    echo "Activating virtual environment..."
    source .venv/bin/activate
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

echo "Starting Inniverse AI..."
streamlit run src/app/main.py