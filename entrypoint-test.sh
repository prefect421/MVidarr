#!/bin/bash

echo "=== MINIMAL TEST ENTRYPOINT ==="
echo "Current time: $(date)"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Shell: $0"
echo "Args: $@"

# Check if bash is available
if command -v bash >/dev/null 2>&1; then
    echo "✅ bash is available"
    bash --version | head -1
else
    echo "❌ bash is not available"
fi

# Check basic commands
echo "Testing basic commands:"
ls --version >/dev/null 2>&1 && echo "✅ ls works" || echo "❌ ls failed"
date >/dev/null 2>&1 && echo "✅ date works" || echo "❌ date failed"
whoami >/dev/null 2>&1 && echo "✅ whoami works" || echo "❌ whoami failed"

echo "=== END TEST ==="

# Keep container running for debugging
sleep 30
echo "Test completed, container will exit now"