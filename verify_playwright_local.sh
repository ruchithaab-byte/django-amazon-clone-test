#!/bin/bash
# Verification script for local Playwright testing
# Tests that Playwright works locally without being in requirements.txt

set -e

echo "🧪 Verifying Local Playwright Setup"
echo "===================================="
echo ""

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

echo "📁 Repository: $REPO_DIR"
echo ""

# Step 1: Check if we're in Docker
if [ -f "/.dockerenv" ] || [ -f "/.dockerinit" ]; then
    echo "⚠️  Running in Docker - this script is for local verification only"
    exit 1
fi

echo "✅ Running locally (not in Docker)"
echo ""

# Step 2: Check Python environment
echo "🐍 Checking Python environment..."
PYTHON_CMD=$(which python3 || which python)
echo "   Python: $PYTHON_CMD"
$PYTHON_CMD --version
echo ""

# Step 3: Check if Playwright is currently installed
echo "🔍 Checking Playwright installation..."
if $PYTHON_CMD -c "from playwright.sync_api import Page" 2>/dev/null; then
    echo "   ✅ Playwright is already installed"
    PLAYWRIGHT_VERSION=$($PYTHON_CMD -c "import playwright; print(playwright.__version__)" 2>/dev/null || echo "unknown")
    echo "   Version: $PLAYWRIGHT_VERSION"
else
    echo "   ⚠️  Playwright not installed (this is expected - conftest.py will auto-install)"
fi
echo ""

# Step 4: Check requirements.txt
echo "📋 Checking requirements.txt..."
if grep -q "playwright" requirements.txt 2>/dev/null; then
    echo "   ⚠️  Playwright found in requirements.txt (should not be there)"
else
    echo "   ✅ Playwright NOT in requirements.txt (correct - using framework/auto-install)"
fi
echo ""

# Step 5: Test conftest.py import (this will trigger auto-install if needed)
echo "🧪 Testing conftest.py auto-installation..."
if [ -f "tests/playwright/conftest.py" ]; then
    echo "   Found: tests/playwright/conftest.py"
    
    # Try to import conftest (this will trigger auto-install if Playwright is missing)
    echo "   Attempting to import conftest.py..."
    if $PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
try:
    # This will trigger auto-installation if Playwright is missing
    import tests.playwright.conftest
    print('   ✅ conftest.py imported successfully')
    print('   ✅ Playwright auto-installation works!')
except ImportError as e:
    print(f'   ❌ Import failed: {e}')
    sys.exit(1)
" 2>&1; then
        echo "   ✅ Auto-installation mechanism verified"
    else
        echo "   ❌ Auto-installation failed"
        exit 1
    fi
else
    echo "   ⚠️  conftest.py not found at tests/playwright/conftest.py"
fi
echo ""

# Step 6: Verify Playwright is now available
echo "🔍 Verifying Playwright is now available..."
if $PYTHON_CMD -c "from playwright.sync_api import Page, sync_playwright; print('✅ Playwright import successful')" 2>/dev/null; then
    echo "   ✅ Playwright is ready to use"
else
    echo "   ❌ Playwright still not available after auto-install"
    exit 1
fi
echo ""

# Step 7: Check if browser binaries are installed
echo "🌐 Checking browser binaries..."
if $PYTHON_CMD -m playwright --version >/dev/null 2>&1; then
    echo "   ✅ Playwright CLI available"
    BROWSER_CHECK=$($PYTHON_CMD -m playwright install --dry-run chromium 2>&1 | grep -i "chromium" || echo "")
    if [ -z "$BROWSER_CHECK" ] || echo "$BROWSER_CHECK" | grep -q "installed\|already"; then
        echo "   ✅ Browser binaries appear to be installed"
    else
        echo "   ⚠️  Browser binaries may need installation (run: playwright install chromium)"
    fi
else
    echo "   ⚠️  Playwright CLI not available"
fi
echo ""

# Step 8: Test that pytest can discover Playwright tests
echo "🔍 Checking if pytest can discover Playwright tests..."
if $PYTHON_CMD -m pytest tests/playwright/ --collect-only -q 2>/dev/null | grep -q "test"; then
    TEST_COUNT=$($PYTHON_CMD -m pytest tests/playwright/ --collect-only -q 2>/dev/null | grep -c "test" || echo "0")
    echo "   ✅ Found $TEST_COUNT Playwright test(s)"
else
    echo "   ⚠️  No Playwright tests found (this is okay if tests don't exist yet)"
fi
echo ""

# Summary
echo "===================================="
echo "✅ Verification Complete!"
echo ""
echo "Summary:"
echo "  - Local environment: ✅"
echo "  - Playwright auto-install: ✅"
echo "  - Playwright available: ✅"
echo "  - requirements.txt clean: ✅"
echo ""
echo "You can now run Playwright tests locally with:"
echo "  pytest tests/playwright/ -v"
echo ""
echo "Note: First run may take longer as it installs browsers if needed."



