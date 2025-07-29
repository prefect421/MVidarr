#!/bin/bash

echo "=============================================="
echo "🚀 MVIDARR PRODUCTION ENTRYPOINT v4.0 🚀"
echo "=============================================="
echo "📅 Start time: $(date)"
echo "👤 User: $(whoami)"
echo "📁 Directory: $(pwd)"
echo "🐧 Hostname: $(hostname)"
echo "=============================================="

# Wait for database to be ready
echo "⏳ Waiting for MariaDB to be ready..."
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
echo "🗄️ Checking database initialization..."
if [ ! -f /app/data/database/.initialized ]; then
    echo "🔧 Database not initialized - creating tables..."
    # Use Python to initialize the database through the app's init_db function
    python3 -c "
import sys
sys.path.insert(0, '/app/src')
print('Importing database initialization module...')
try:
    from src.database.init_db import initialize_database
    print('✅ Successfully imported initialize_database')
    result = initialize_database()
    if result:
        print('✅ Database initialized successfully')
    else:
        print('⚠️ Database initialization returned False')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    print('Trying alternative import...')
    try:
        from database.init_db import create_tables
        print('✅ Using create_tables function')
        success = create_tables()
        print(f'Database creation result: {success}')
    except Exception as e2:
        print(f'❌ Alternative import also failed: {e2}')
        exit(1)
except Exception as e:
    print(f'❌ Database initialization error: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
" 
    if [ $? -eq 0 ]; then
        echo "✅ Database initialization completed successfully"
        touch /app/data/database/.initialized
    else
        echo "❌ Database initialization failed - check logs above"
        echo "🔄 Attempting to start application anyway (database may exist)..."
    fi
else
    echo "✅ Database already initialized (marker file exists)"
fi

# Start the application
echo "🚀 Starting MVidarr application..."
echo "📍 Working directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"

# Start application with error output
echo "▶️ Executing: python3 app.py"
exec python3 app.py