"""
Playwright-Kualitee Integration Configuration
Implements the Push Model for real-time test result reporting
"""

import pytest
import asyncio 
import os 
import sys 
import subprocess
import time
import signal
import socket
import threading
import concurrent.futures
from pathlib import Path
from typing import Any
from playwright.sync_api import Page

# Smart path resolution: Find framework root whether running from framework or injected repo
def find_framework_root():
    """Find the sdlc-agent-framework root directory."""
    current = Path(__file__).resolve().parent
    
    # Strategy 1: Check if we're in the framework (has src/mcp_servers/kualitee_server.py)
    for _ in range(5):  # Walk up max 5 levels
        framework_root = current
        kualitee_path = framework_root / "src" / "mcp_servers" / "kualitee_server.py"
        if kualitee_path.exists():
            return str(framework_root)
        if current.parent == current:  # Reached filesystem root
            break
        current = current.parent
    
    # Strategy 2: If injected, look for framework in common locations
    # When injected into repos/django-amazon-clone-test/tests/playwright/
    # Framework should be at ../../sdlc-agent-framework
    injected_path = Path(__file__).resolve().parent
    if "repos" in str(injected_path):
        # We're in a repos/*/tests/playwright structure
        repos_dir = injected_path
        while repos_dir.name != "repos" and repos_dir.parent != repos_dir:
            repos_dir = repos_dir.parent
        if repos_dir.name == "repos":
            framework_candidate = repos_dir.parent / "sdlc-agent-framework"
            if (framework_candidate / "src" / "mcp_servers" / "kualitee_server.py").exists():
                return str(framework_candidate)
    
    # Fallback: Use environment variable if set
    env_framework = os.getenv("SDLC_FRAMEWORK_ROOT")
    if env_framework and Path(env_framework).exists():
        return env_framework
    
    # Last resort: raise error with helpful message
    raise ImportError(
        f"Could not find sdlc-agent-framework root. "
        f"Tried: {Path(__file__).resolve().parent} and parent directories. "
        f"Set SDLC_FRAMEWORK_ROOT environment variable to framework root path."
    )

# Add framework root to Python path
framework_root = find_framework_root()
sys.path.insert(0, framework_root)

from src.mcp_servers.kualitee_server import KualiteeMCPServer


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "kualitee_id(id): mark test to sync with Kualitee test case ID"
    )


@pytest.fixture(scope="session")
def kualitee_server():
    """Initialize Kualitee server for test reporting"""
    return KualiteeMCPServer()


def pytest_runtest_makereport(item, call):
    """
    Hook that fires after each test to report results to Kualitee
    Implements the Push Model pattern from the integration documentation
    """
    if call.when == "call":  # Only run after test execution, not setup/teardown
        # Check if test has Kualitee ID marker
        kualitee_marker = item.get_closest_marker("kualitee_id")
        if not kualitee_marker:
            return  # Skip tests without Kualitee mapping

        # Extract test case ID and determine result
        test_case_id = kualitee_marker.args[0]
        status = "Passed" if call.excinfo is None else "Failed"

        # Build evidence from test info
        evidence = f"Automated Playwright test: {item.nodeid}"
        if call.excinfo:
            evidence += f" | Error: {str(call.excinfo.value)}"

        # Report to Kualitee (handle event loop conflicts with Playwright)
        try:
            # Check if event loop is already running (Playwright scenario)
            try:
                loop = asyncio.get_running_loop()
                # Event loop is running - schedule coroutine on existing loop using run_coroutine_threadsafe
                import concurrent.futures
                future = asyncio.run_coroutine_threadsafe(
                    _report_to_kualitee(test_case_id, status, evidence),
                    loop
                )
                # Wait for completion (non-blocking, max 5 seconds)
                try:
                    future.result(timeout=5)
                except concurrent.futures.TimeoutError:
                    print(f"⚠️  Kualitee reporting timed out for {test_case_id}")
                except Exception as e:
                    print(f"⚠️  Kualitee reporting error: {e}")
                
            except RuntimeError:
                # No event loop running - safe to use run_until_complete
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Still running somehow - use thread pool
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            _report_to_kualitee(test_case_id, status, evidence)
                        )
                        future.result(timeout=5)
                else:
                    loop.run_until_complete(_report_to_kualitee(test_case_id, status, evidence))
        except Exception as e:
            print(f"⚠️  Failed to report to Kualitee: {e}")


async def _report_to_kualitee(test_case_id: str, status: str, evidence: str):
    """Async helper to report test results to Kualitee"""
    try:
        server = KualiteeMCPServer()
        result = await server.report_execution(
            project_id="20317",  # Django Amazon Clone project
            issue_key=test_case_id,
            status=status,
            evidence=evidence
        )

        if result.get("success"):
            print(f"✅ [Kualitee] Reported {status} for {test_case_id}")
        else:
            print(f"❌ [Kualitee] Failed to report {test_case_id}: {result.get('error')}")

    except Exception as e:
        print(f"❌ [Kualitee] Exception reporting {test_case_id}: {e}")

    return True  # Always return something to satisfy run_until_complete


@pytest.fixture(scope="session")
def django_server():
    """
    Automatically start Django server for Playwright tests.
    Server starts before tests and stops after all tests complete.
    
    If server is already running on port 8000, it will be reused.
    """
    # Find Django project root (where manage.py is)
    current = Path(__file__).resolve().parent
    django_root = None
    
    # Walk up to find manage.py
    for _ in range(5):
        manage_py = current / "manage.py"
        if manage_py.exists():
            django_root = current
            break
        if current.parent == current:
            break
        current = current.parent
    
    # Alternative: look for DjangoEcommerce directory
    if not django_root:
        current = Path(__file__).resolve().parent
        for _ in range(5):
            django_ecommerce = current / "DjangoEcommerce"
            manage_py = current / "manage.py"
            if django_ecommerce.exists() and manage_py.exists():
                django_root = current
                break
            if current.parent == current:
                break
            current = current.parent
    
    if not django_root:
        pytest.skip("Could not find Django project root (manage.py)")
    
    server_url = "http://localhost:8000"
    server_process = None
    original_cwd = os.getcwd()
    
    try:
        # Check if server is already running
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            # Server already running - use it
            print("✅ Django server already running on port 8000 - reusing it")
            yield server_url
            return
        
        # Start Django server
        print("🚀 Starting Django server for Playwright tests...")
        os.chdir(django_root)
        
        # Start server in background
        server_process = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=django_root
        )
        
        # Wait for server to be ready (max 30 seconds)
        max_wait = 30
        wait_interval = 0.5
        waited = 0
        
        while waited < max_wait:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 8000))
                sock.close()
                if result == 0:
                    print(f"✅ Django server started successfully (waited {waited:.1f}s)")
                    break
            except:
                pass
            
            time.sleep(wait_interval)
            waited += wait_interval
            
            # Check if process died
            if server_process.poll() is not None:
                stderr = server_process.stderr.read().decode() if server_process.stderr else "Unknown error"
                raise RuntimeError(f"Django server failed to start: {stderr}")
        
        if waited >= max_wait:
            raise RuntimeError("Django server failed to start within 30 seconds")
        
        yield server_url
        
    finally:
        # Restore original directory
        os.chdir(original_cwd)
        
        # Stop server
        if server_process:
            print("🛑 Stopping Django server...")
            try:
                server_process.terminate()
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            except Exception as e:
                print(f"⚠️  Error stopping server: {e}")


@pytest.fixture
def server_url(django_server):
    """Provide server URL to tests"""
    return django_server


@pytest.fixture
def enhanced_page(page: Page, server_url):
    """
    Enhanced page fixture with common setup and server URL.
    Use this fixture instead of 'page' if you need server_url.
    Or use 'page' and 'server_url' fixtures separately.
    """
    # Set viewport and timeout defaults
    page.set_viewport_size({"width": 1280, "height": 720})
    page.set_default_timeout(10000)  # 10 second timeout

    yield page

    # Cleanup after test
    try:
        page.close()
    except:
        pass  # Page might already be closed