#!/bin/bash

echo "🛡️ Starting Aadhaar DRISHTI Frontend..."
echo "========================================"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start frontend
echo ""
echo "✅ Starting React development server on http://localhost:3000"
echo "========================================"
npm start
