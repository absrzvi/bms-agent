#!/bin/bash
#
# BMS Agent Service Management Script
# Manages Qdrant, Ollama, BMS API, and OpenWebUI services
#

set -euo pipefail

# Configuration
LOG_DIR="/workspace/logs"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ✅ $*"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ❌ $*"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ⚠️  $*"
}

# Service management functions
start_qdrant() {
    log "Starting Qdrant..."
    
    if pgrep -f "qdrant" > /dev/null; then
        log_warn "Qdrant is already running"
        return 0
    fi
    
    if [ -f /workspace/apps/qdrant/qdrant ]; then
        cd /workspace/apps/qdrant
        nohup ./qdrant --config-path /workspace/apps/qdrant/config.yaml \
            > "$LOG_DIR/qdrant.log" 2>&1 &
        sleep 3
        
        if pgrep -f "qdrant" > /dev/null; then
            log_success "Qdrant started (PID: $(pgrep -f qdrant))"
        else
            log_error "Qdrant failed to start"
            return 1
        fi
    else
        log_error "Qdrant binary not found at /workspace/apps/qdrant/qdrant"
        return 1
    fi
}

stop_qdrant() {
    log "Stopping Qdrant..."
    
    if pgrep -f "qdrant" > /dev/null; then
        pkill -f "qdrant"
        sleep 2
        
        if ! pgrep -f "qdrant" > /dev/null; then
            log_success "Qdrant stopped"
        else
            log_warn "Qdrant did not stop gracefully, forcing..."
            pkill -9 -f "qdrant"
            sleep 1
            log_success "Qdrant force stopped"
        fi
    else
        log_warn "Qdrant is not running"
    fi
}

start_ollama() {
    log "Starting Ollama..."
    
    if pgrep -f "ollama serve" > /dev/null; then
        log_warn "Ollama is already running"
        return 0
    fi
    
    if command -v ollama &> /dev/null; then
        OLLAMA_MODELS=/workspace/data/ollama_models nohup ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
        sleep 3
        
        if pgrep -f "ollama serve" > /dev/null; then
            log_success "Ollama started (PID: $(pgrep -f 'ollama serve'))"
        else
            log_error "Ollama failed to start"
            return 1
        fi
    else
        log_error "Ollama not found in system PATH"
        return 1
    fi
}

stop_ollama() {
    log "Stopping Ollama..."
    
    if pgrep -f "ollama serve" > /dev/null; then
        pkill -f "ollama serve"
        sleep 2
        
        if ! pgrep -f "ollama serve" > /dev/null; then
            log_success "Ollama stopped"
        else
            log_warn "Ollama did not stop gracefully, forcing..."
            pkill -9 -f "ollama serve"
            sleep 1
            log_success "Ollama force stopped"
        fi
    else
        log_warn "Ollama is not running"
    fi
}

start_api() {
    log "Starting BMS API..."
    
    if pgrep -f "uvicorn api.main:app" > /dev/null; then
        log_warn "BMS API is already running"
        return 0
    fi
    
    if [ -d /workspace/001-bms-agent ]; then
        cd /workspace/001-bms-agent
        
        # Activate virtual environment
        if [ -f /workspace/001-bms-agent/.venv/bin/activate ]; then
            source /workspace/001-bms-agent/.venv/bin/activate
        elif [ -f /workspace/bms-api-venv/bin/activate ]; then
            source /workspace/bms-api-venv/bin/activate
        else
            log_error "Virtual environment not found"
            return 1
        fi
        
        nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 \
            > "$LOG_DIR/api.log" 2>&1 &
        sleep 3
        
        if pgrep -f "uvicorn api.main:app" > /dev/null; then
            log_success "BMS API started (PID: $(pgrep -f 'uvicorn api.main:app'))"
        else
            log_error "BMS API failed to start"
            return 1
        fi
    else
        log_error "BMS Agent directory not found at /workspace/001-bms-agent"
        return 1
    fi
}

stop_api() {
    log "Stopping BMS API..."
    
    if pgrep -f "uvicorn api.main:app" > /dev/null; then
        pkill -f "uvicorn api.main:app"
        sleep 2
        
        if ! pgrep -f "uvicorn api.main:app" > /dev/null; then
            log_success "BMS API stopped"
        else
            log_warn "BMS API did not stop gracefully, forcing..."
            pkill -9 -f "uvicorn api.main:app"
            sleep 1
            log_success "BMS API force stopped"
        fi
    else
        log_warn "BMS API is not running"
    fi
}

start_openwebui() {
    log "Starting OpenWebUI..."
    
    if pgrep -f "open-webui serve" > /dev/null; then
        log_warn "OpenWebUI is already running"
        return 0
    fi
    
    if [ -f /workspace/openwebui/venv/bin/open-webui ]; then
        cd /workspace/openwebui
        source /workspace/openwebui/venv/bin/activate
        export OPENWEBUI_DATA_DIR=/workspace/data/openwebui
        nohup open-webui serve --host 0.0.0.0 --port 3000 \
            > "$LOG_DIR/openwebui.log" 2>&1 &
        sleep 3
        
        if pgrep -f "open-webui serve" > /dev/null; then
            log_success "OpenWebUI started (PID: $(pgrep -f 'open-webui serve'))"
        else
            log_error "OpenWebUI failed to start"
            return 1
        fi
    else
        log_warn "OpenWebUI not found, skipping..."
    fi
}

stop_openwebui() {
    log "Stopping OpenWebUI..."

    if pgrep -f "open-webui serve" > /dev/null; then
        pkill -f "open-webui serve"
        sleep 2

        if ! pgrep -f "open-webui serve" > /dev/null; then
            log_success "OpenWebUI stopped"
        else
            log_warn "OpenWebUI did not stop gracefully, forcing..."
            pkill -9 -f "open-webui serve"
            sleep 1
            log_success "OpenWebUI force stopped"
        fi
    else
        log_warn "OpenWebUI is not running"
    fi
}

start_n8n() {
    log "Starting n8n..."

    if pgrep -f "n8n start" > /dev/null; then
        log_warn "n8n is already running"
        return 0
    fi

    if command -v n8n &> /dev/null; then
        export N8N_USER_FOLDER=/workspace/n8n
        export N8N_HOST=0.0.0.0
        export N8N_PORT=5678
        export N8N_DIAGNOSTICS_ENABLED=false
        export DB_SQLITE_POOL_SIZE=5
        export N8N_RUNNERS_ENABLED=true
        export N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true
        export N8N_BLOCK_ENV_ACCESS_IN_NODE=false
        export N8N_GIT_NODE_DISABLE_BARE_REPOS=true

        nohup n8n start > "$LOG_DIR/n8n.log" 2>&1 &
        sleep 3

        if pgrep -f "n8n start" > /dev/null; then
            log_success "n8n started (PID: $(pgrep -f 'n8n start'))"
        else
            log_error "n8n failed to start"
            return 1
        fi
    else
        log_error "n8n not found in system PATH"
        return 1
    fi
}

stop_n8n() {
    log "Stopping n8n..."

    if pgrep -f "n8n start" > /dev/null; then
        pkill -f "n8n start"
        sleep 2

        if ! pgrep -f "n8n start" > /dev/null; then
            log_success "n8n stopped"
        else
            log_warn "n8n did not stop gracefully, forcing..."
            pkill -9 -f "n8n start"
            sleep 1
            log_success "n8n force stopped"
        fi
    else
        log_warn "n8n is not running"
    fi
}

status_service() {
    local service_name="$1"
    local process_pattern="$2"
    
    if pgrep -f "$process_pattern" > /dev/null; then
        local pid=$(pgrep -f "$process_pattern")
        echo -e "${GREEN}✓${NC} $service_name is running (PID: $pid)"
        return 0
    else
        echo -e "${RED}✗${NC} $service_name is not running"
        return 1
    fi
}

show_status() {
    echo ""
    echo "=== BMS Agent Service Status ==="
    echo ""

    status_service "Qdrant" "qdrant"
    status_service "Ollama" "ollama serve"
    status_service "BMS API" "uvicorn api.main:app"
    status_service "OpenWebUI" "open-webui serve"
    status_service "n8n" "n8n start"

    echo ""
    echo "Service URLs:"
    echo "  - Qdrant:    http://localhost:6333"
    echo "  - Ollama:    http://localhost:11434"
    echo "  - BMS API:   http://localhost:8000"
    echo "  - OpenWebUI: http://localhost:3000"
    echo "  - n8n:       http://localhost:5678"
    echo ""
}

start_all() {
    log "Starting all BMS Agent services..."
    echo ""
    
    start_qdrant
    start_ollama
    start_api
    start_openwebui
    
    echo ""
    log_success "All services started!"
    show_status
}

stop_all() {
    log "Stopping all BMS Agent services..."
    echo ""
    
    stop_openwebui
    stop_api
    stop_ollama
    stop_qdrant
    
    echo ""
    log_success "All services stopped!"
}

restart_all() {
    log "Restarting all BMS Agent services..."
    stop_all
    sleep 2
    start_all
}

# Main command handler
case "${1:-}" in
    start)
        if [ -n "${2:-}" ]; then
            case "$2" in
                qdrant) start_qdrant ;;
                ollama) start_ollama ;;
                api) start_api ;;
                openwebui) start_openwebui ;;
                *) log_error "Unknown service: $2"; exit 1 ;;
            esac
        else
            start_all
        fi
        ;;
    stop)
        if [ -n "${2:-}" ]; then
            case "$2" in
                qdrant) stop_qdrant ;;
                ollama) stop_ollama ;;
                api) stop_api ;;
                openwebui) stop_openwebui ;;
                *) log_error "Unknown service: $2"; exit 1 ;;
            esac
        else
            stop_all
        fi
        ;;
    restart)
        if [ -n "${2:-}" ]; then
            case "$2" in
                qdrant) stop_qdrant; sleep 2; start_qdrant ;;
                ollama) stop_ollama; sleep 2; start_ollama ;;
                api) stop_api; sleep 2; start_api ;;
                openwebui) stop_openwebui; sleep 2; start_openwebui ;;
                *) log_error "Unknown service: $2"; exit 1 ;;
            esac
        else
            restart_all
        fi
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status} [service]"
        echo ""
        echo "Services: qdrant, ollama, api, openwebui"
        echo ""
        echo "Examples:"
        echo "  $0 start              # Start all services"
        echo "  $0 stop api           # Stop BMS API only"
        echo "  $0 restart qdrant     # Restart Qdrant only"
        echo "  $0 status             # Show status of all services"
        exit 1
        ;;
esac

exit 0
