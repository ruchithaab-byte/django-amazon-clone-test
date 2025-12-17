# Automatic Django Server Startup for Playwright Tests

## Overview

Playwright tests now **automatically start and stop the Django server** - no manual setup required!

## How It Works

### Before (Manual Setup Required)
```bash
# Terminal 1: Start server manually
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Run tests
pytest tests/playwright/ -v
```

**Problem**: If server wasn't running → `ERR_CONNECTION_REFUSED` → All tests fail

### After (Automatic)
```bash
# Just run tests - server starts automatically!
pytest tests/playwright/ -v
```

**Solution**: `django_server` fixture automatically:
1. ✅ Checks if server is already running (reuses it)
2. ✅ Starts Django server if not running
3. ✅ Waits for server to be ready (max 30 seconds)
4. ✅ Provides `server_url` fixture to tests
5. ✅ Stops server after all tests complete

## Implementation

### Fixture: `django_server`
- **Scope**: `session` (starts once for all tests)
- **Location**: `tests/playwright/conftest.py`
- **Behavior**:
  - Finds Django project root (where `manage.py` is)
  - Checks if port 8000 is already in use
  - Starts server in background subprocess if needed
  - Waits for server to respond
  - Yields server URL: `http://localhost:8000`
  - Cleans up server on teardown

### Using in Tests

**Option 1: Use `server_url` fixture**
```python
def test_example(page: Page, server_url):
    page.goto(f"{server_url}/some/path/")
```

**Option 2: Hardcoded (still works, but less flexible)**
```python
def test_example(page: Page):
    page.goto("http://localhost:8000/some/path/")
```

## Benefits

1. **Zero Manual Setup**: Just run `pytest` - server starts automatically
2. **Reuses Existing Server**: If server is already running, it's reused
3. **Clean Shutdown**: Server stops automatically after tests
4. **CI/CD Friendly**: Works in Docker/CI without manual server management
5. **Error Handling**: Clear errors if server fails to start

## Example Test

```python
@pytest.mark.kualitee_id("AGENTIC-136")
def test_product_edit_shows_last_updated_timestamp(self, page: Page, server_url):
    """Test that product edit page displays last updated timestamp"""
    # Server is automatically started by django_server fixture
    page.goto(f"{server_url}/admindashboard/product_edit/1")
    
    # Test continues...
    expect(page.locator("h4")).to_contain_text("Product Edit")
```

## Troubleshooting

### Server Already Running
If you have a server running on port 8000, the fixture will detect and reuse it:
```
✅ Django server already running on port 8000 - reusing it
```

### Server Fails to Start
If server fails to start, you'll see:
```
RuntimeError: Django server failed to start: [error details]
```

Common causes:
- Port 8000 already in use by another process
- Django settings misconfigured
- Database migration issues

### Manual Override
To manually start server (for debugging):
```bash
# Start server manually
python manage.py runserver 0.0.0.0:8000

# Run tests (fixture will detect and reuse existing server)
pytest tests/playwright/ -v
```

## Architecture

```
┌─────────────────┐
│   pytest run    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ django_server    │ ← Session fixture (runs once)
│   fixture        │
└────────┬────────┘
         │
         ├─→ Check port 8000
         │
         ├─→ Server running? → Reuse it ✅
         │
         └─→ Not running? → Start server ✅
         │
         ▼
┌─────────────────┐
│  Test Execution │
│  (uses server)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Server Cleanup │ ← Automatic teardown
└─────────────────┘
```

## Summary

**Question**: "If the Django server is not up, how do the Playwright tests work?"

**Answer**: **They work automatically!** The `django_server` fixture:
- ✅ Detects if server is running
- ✅ Starts server if needed
- ✅ Provides server URL to tests
- ✅ Stops server after tests complete

**No manual server management required!** 🎉


