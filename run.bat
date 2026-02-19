@echo off

REM Fraud Detection System Runner Script for Windows

REM Create necessary directories
if not exist logs mkdir logs
if not exist uploads mkdir uploads

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

REM Create .env if not exists
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

REM Run the application
echo Starting Fraud Detection System...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
