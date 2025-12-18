#!/bin/bash
# Run Playwright tests with automatic Django server startup

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

echo "🧪 Running Playwright Tests"
echo "============================"
echo ""
echo "📁 Repository: $REPO_DIR"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Are you in the Django project root?"
    exit 1
fi

if [ ! -d "tests/playwright" ]; then
    echo "❌ Error: tests/playwright directory not found"
    exit 1
fi

echo "✅ Django project found"
echo "✅ Playwright tests found"
echo ""

# Run pytest
# Note: The django_server fixture will automatically start the Django server
echo "🚀 Starting tests (Django server will start automatically)..."
echo ""

pytest tests/playwright/ -v "$@"

echo ""
echo "✅ Tests completed!"



