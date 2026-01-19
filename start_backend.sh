#!/bin/bash

echo "🛡️ Starting Aadhaar DRISHTI Backend..."
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start backend
echo ""
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "========================================"
cd backend && python main.py
