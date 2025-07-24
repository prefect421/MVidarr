#!/bin/bash
# Test script to check for externally-managed environment
# Make this script executable: chmod +x test_externally_managed.sh

echo "Testing for externally-managed Python environment..."

# Check if pip supports --break-system-packages
if pip install --help | grep -q "break-system-packages" 2>/dev/null; then
    echo "✅ pip supports --break-system-packages flag"
    
    # Test if we hit the externally-managed error
    if pip install --dry-run setuptools 2>&1 | grep -q "externally-managed-environment"; then
        echo "⚠️ DETECTED: externally-managed-environment"
        echo "This system requires special handling for pip installations"
    else
        echo "✅ Standard pip installation should work"
    fi
else
    echo "✅ Legacy pip version - standard installation should work"
fi

# Check for venv availability
if python3 -m venv --help >/dev/null 2>&1; then
    echo "✅ python3 venv is available"
else
    echo "⚠️ python3 venv is not available - may need to install python3-venv"
fi

echo ""
echo "Recommendation:"
if pip install --dry-run setuptools 2>&1 | grep -q "externally-managed-environment"; then
    echo "Use virtual environment installation method"
else
    echo "Standard pip installation should work fine"
fi
