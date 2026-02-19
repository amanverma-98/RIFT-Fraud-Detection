#!/bin/bash

# Fraud Detection System Runner Script

# Create necessary directories
mkdir -p logs uploads

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Run the application
echo "Starting Fraud Detection System..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
