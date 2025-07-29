#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for MariaDB to be ready..."
echo "Connection details - Host: ${DB_HOST:-mariadb}, Port: ${DB_PORT:-3306}, User: ${DB_USER:-mvidarr}"

# Simple wait for port availability with timeout
timeout=180
count=0
while [ $count -lt $timeout ]; do
    if nc -z "${DB_HOST:-mariadb}" "${DB_PORT:-3306}" 2>/dev/null; then
        echo "MariaDB port is reachable, waiting for database to be fully ready..."
        sleep 5
        echo "MariaDB is ready - starting application"
        break
    else
        echo "MariaDB port ${DB_PORT:-3306} not reachable on ${DB_HOST:-mariadb}, waiting... ($count/$timeout seconds)"
    fi
    sleep 3
    count=$((count + 3))
done

if [ $count -ge $timeout ]; then
    echo "MariaDB failed to start within timeout ($timeout seconds)"
    echo "Checking MariaDB connection details:"
    echo "Host: ${DB_HOST:-mariadb}"
    echo "Port: ${DB_PORT:-3306}"
    echo "User: ${DB_USER:-mvidarr}"
    echo "Database: ${DB_NAME:-mvidarr}"
    echo "Testing basic connectivity..."
    nc -z "${DB_HOST:-mariadb}" "${DB_PORT:-3306}" && echo "Port is reachable" || echo "Port is not reachable"
    exit 1
fi

# Initialize database if needed
if [ ! -f /app/data/database/.initialized ]; then
    echo "Initializing database..."
    # Use Python to initialize the database through the app's init_db function
    python3 -c "
import sys
sys.path.insert(0, '/app/src')
from database.init_db import create_tables
try:
    success = create_tables()
    if success:
        print('Database initialized successfully')
    else:
        print('Database initialization failed')
except Exception as e:
    print(f'Database initialization failed: {e}')
    # Don't exit on database init failure in case it already exists
" || echo "Database initialization failed or already exists"
    touch /app/data/database/.initialized
fi

# Start the application
echo "Starting MVidarr application..."
echo "Python path: $PYTHONPATH"
echo "Working directory: $(pwd)"
echo "App.py exists: $(test -f app.py && echo 'yes' || echo 'no')"

# Start with better error handling
if ! python3 app.py; then
    echo "Application failed to start. Checking for common issues..."
    echo "Directory contents:"
    ls -la /app/
    echo "Python modules in src:"
    ls -la /app/src/ || echo "src directory not found"
    echo "Python version: $(python3 --version)"
    exit 1
fi