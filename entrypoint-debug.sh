#!/bin/bash

echo "=============================================="
echo "🚀 MVIDARR DEBUG ENTRYPOINT SCRIPT v3.0 🚀"
echo "=============================================="
echo "📅 Start time: $(date)"
echo "👤 User: $(whoami)"
echo "📁 Directory: $(pwd)"
echo "🐧 Hostname: $(hostname)"
echo "=============================================="

echo "🔍 Checking environment variables..."
echo "DB_HOST: ${DB_HOST:-not_set}"
echo "DB_PORT: ${DB_PORT:-not_set}"
echo "DB_USER: ${DB_USER:-not_set}"
echo "DB_NAME: ${DB_NAME:-not_set}"
echo "PYTHONPATH: ${PYTHONPATH:-not_set}"

echo "📁 Checking key files..."
if [ -f app.py ]; then
    echo "✅ app.py found"
else
    echo "❌ app.py missing"
fi

if [ -d src ]; then
    echo "✅ src directory found"
    echo "📝 src contents:"
    ls -la src/ | head -10
else
    echo "❌ src directory missing"
fi

echo "🐍 Testing Python..."
python3 --version || echo "❌ Python3 failed"

echo "🔗 Testing database connectivity..."
echo "Trying to connect to ${DB_HOST:-mariadb}:${DB_PORT:-3306}..."

# Simple netcat test without set -e
if command -v nc >/dev/null 2>&1; then
    echo "✅ netcat available"
    if nc -z "${DB_HOST:-mariadb}" "${DB_PORT:-3306}" 2>/dev/null; then
        echo "✅ Database port is reachable"
    else
        echo "❌ Database port not reachable (this is expected initially)"
    fi
else
    echo "❌ netcat not available"
fi

echo "🚀 Attempting to start application..."
echo "Command: python3 app.py"

# Try starting the app and capture any immediate errors
timeout 10 python3 app.py 2>&1 | head -20 || echo "❌ Application startup failed or timed out"

echo "=============================================="
echo "🏁 Debug script completed: $(date)"
echo "=============================================="