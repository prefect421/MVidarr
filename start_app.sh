#!/bin/bash
# Simple startup script for MVidarr Enhanced

echo "Starting MVidarr Enhanced..."

# Change to application directory
cd "$(dirname "$0")"

# Kill any existing processes
pkill -f "python.*app.py" || true
pkill -f "mvidarr" || true

# Wait for port to be available
echo "Waiting for port to be available..."
sleep 2

# Start the application in the background
echo "Starting application..."
python3 app.py > data/logs/app.log 2>&1 &

# Get the PID
PID=$!
echo "Application started with PID: $PID"

# Wait a moment to check if it started successfully
sleep 3

if ps -p $PID > /dev/null; then
    echo "✓ MVidarr Enhanced is running successfully"
    echo "✓ Access the application at: http://localhost:5000"
    echo "✓ API documentation at: http://localhost:5000/api/docs"
    echo "✓ Logs are being written to: data/logs/app.log"
    echo "✓ To stop the application, run: pkill -f 'python.*app.py'"
else
    echo "✗ Application failed to start. Check logs in data/logs/app.log"
    exit 1
fi