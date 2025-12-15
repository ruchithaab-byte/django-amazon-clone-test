#!/bin/bash
# Django Bootstrap Protocol for SDLC Agent Framework
#
# This script properly initializes a Django application for testing by:
# 1. Installing dependencies
# 2. Setting up the database with migrations
# 3. Creating test fixtures
# 4. Starting the development server in background
#
# Usage: ./bootstrap.sh [start|stop|restart|status]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${PROJECT_DIR}/server.pid"
LOG_FILE="${PROJECT_DIR}/server.log"
ERROR_LOG="${PROJECT_DIR}/server_error.log"
REQUIREMENTS_FILE="${PROJECT_DIR}/requirements.txt"

# Django management command
MANAGE_PY="${PROJECT_DIR}/manage.py"
RUNSERVER_CMD="python ${MANAGE_PY} runserver 0.0.0.0:8000"

echo -e "${BLUE}🚀 Django Bootstrap Protocol v1.0${NC}"
echo -e "${BLUE}📁 Project Directory: ${PROJECT_DIR}${NC}"

# Function to check if server is running
is_server_running() {
    if [[ -f "${PID_FILE}" ]]; then
        local pid=$(cat "${PID_FILE}")
        if ps -p "${pid}" > /dev/null 2>&1; then
            return 0  # Server is running
        else
            # Stale PID file
            rm -f "${PID_FILE}"
            return 1  # Server not running
        fi
    else
        return 1  # Server not running
    fi
}

# Function to install dependencies
install_dependencies() {
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"

    if [[ -f "${REQUIREMENTS_FILE}" ]]; then
        pip install -r "${REQUIREMENTS_FILE}"
        echo -e "${GREEN}✅ Dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠️  No requirements.txt found, skipping dependency installation${NC}"
    fi
}

# Function to setup database
setup_database() {
    echo -e "${YELLOW}🗄️  Setting up database...${NC}"

    # Run migrations
    python "${MANAGE_PY}" migrate --noinput
    echo -e "${GREEN}✅ Database migrations completed${NC}"

    # Create superuser if it doesn't exist
    if [[ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
        echo -e "${YELLOW}👤 Creating superuser...${NC}"
        python "${MANAGE_PY}" createsuperuser --noinput \
            --username "${DJANGO_SUPERUSER_USERNAME:-admin}" \
            --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" || true
        echo -e "${GREEN}✅ Superuser setup completed${NC}"
    fi

    # Collect static files
    echo -e "${YELLOW}📁 Collecting static files...${NC}"
    python "${MANAGE_PY}" collectstatic --noinput --clear
    echo -e "${GREEN}✅ Static files collected${NC}"
}

# Function to start the server
start_server() {
    if is_server_running; then
        echo -e "${GREEN}✅ Django server is already running (PID: $(cat "${PID_FILE}"))${NC}"
        return 0
    fi

    echo -e "${YELLOW}🚀 Starting Django development server...${NC}"

    # Start server in background
    nohup ${RUNSERVER_CMD} > "${LOG_FILE}" 2> "${ERROR_LOG}" &
    local server_pid=$!

    # Save PID
    echo "${server_pid}" > "${PID_FILE}"

    # Wait a moment and check if server started successfully
    sleep 2
    if ps -p "${server_pid}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Django server started successfully (PID: ${server_pid})${NC}"
        echo -e "${GREEN}📡 Server available at: http://0.0.0.0:8000${NC}"
        echo -e "${GREEN}📋 Logs: ${LOG_FILE}${NC}"
        echo -e "${GREEN}❌ Errors: ${ERROR_LOG}${NC}"

        # Test server health
        echo -e "${YELLOW}🏥 Testing server health...${NC}"
        sleep 3
        if curl -f -s http://localhost:8000/ > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server health check passed${NC}"
        else
            echo -e "${RED}⚠️  Server health check failed, but server is running${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to start Django server${NC}"
        rm -f "${PID_FILE}"
        return 1
    fi
}

# Function to stop the server
stop_server() {
    if ! is_server_running; then
        echo -e "${YELLOW}⚠️  Django server is not running${NC}"
        return 0
    fi

    local pid=$(cat "${PID_FILE}")
    echo -e "${YELLOW}🛑 Stopping Django server (PID: ${pid})...${NC}"

    # Graceful shutdown
    kill "${pid}" 2>/dev/null || true

    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "${pid}" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Django server stopped gracefully${NC}"
            rm -f "${PID_FILE}"
            return 0
        fi
        sleep 1
    done

    # Force kill if still running
    echo -e "${YELLOW}🔨 Force killing server...${NC}"
    kill -9 "${pid}" 2>/dev/null || true
    rm -f "${PID_FILE}"
    echo -e "${GREEN}✅ Django server stopped${NC}"
}

# Function to show server status
show_status() {
    if is_server_running; then
        local pid=$(cat "${PID_FILE}")
        echo -e "${GREEN}✅ Django server is running (PID: ${pid})${NC}"
        echo -e "${GREEN}📡 Server available at: http://0.0.0.0:8000${NC}"

        # Show recent logs
        if [[ -f "${LOG_FILE}" ]]; then
            echo -e "${BLUE}📋 Recent logs:${NC}"
            tail -n 5 "${LOG_FILE}"
        fi
    else
        echo -e "${RED}❌ Django server is not running${NC}"
    fi
}

# Function to restart server
restart_server() {
    echo -e "${YELLOW}🔄 Restarting Django server...${NC}"
    stop_server
    sleep 1
    start_server
}

# Function to bootstrap (full initialization)
bootstrap() {
    echo -e "${BLUE}🏗️  Starting full Django bootstrap...${NC}"

    # Change to project directory
    cd "${PROJECT_DIR}"

    # Install dependencies
    install_dependencies

    # Setup database
    setup_database

    # Start server
    start_server

    echo -e "${GREEN}🎉 Django bootstrap completed successfully!${NC}"
    echo -e "${GREEN}🌐 Your Django application is ready at: http://0.0.0.0:8000${NC}"
}

# Main script logic
case "${1:-bootstrap}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    bootstrap|"")
        bootstrap
        ;;
    *)
        echo "Usage: $0 {bootstrap|start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  bootstrap  - Full initialization (install deps, migrate DB, start server)"
        echo "  start      - Start the Django server"
        echo "  stop       - Stop the Django server"
        echo "  restart    - Restart the Django server"
        echo "  status     - Show server status"
        exit 1
        ;;
esac