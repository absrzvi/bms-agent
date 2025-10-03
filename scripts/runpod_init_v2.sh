#!/bin/bash
# RunPod Initialization Script v2.1 (Enhanced for T042)
# Place this in RunPod's startup script field
# This script runs ONCE per pod boot and sets up the environment
# Enhanced with: GPU verification, comprehensive error handling, service readiness checks

set -euo pipefail

INIT_MARKER="/tmp/runpod_init_complete"
LOG_FILE="/workspace/logs/runpod_init.log"
STARTUP_LOG="/workspace/logs/startup.log"

# Create logs directory
mkdir -p /workspace/logs

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE" | tee -a "$STARTUP_LOG"
}

# Function to log errors
error_exit() {
    log "❌ ERROR: $1"
    exit 1
}

# Check if initialization already completed this boot
if [ -f "$INIT_MARKER" ]; then
    log "Initialization already completed this boot. Exiting."
    exit 0
fi

log "=========================================="
log "RunPod Initialization Started"
log "=========================================="

# 1. SSH Key Persistence
log "Step 1: Setting up SSH keys..."
if [ -f /workspace/config/authorized_keys ]; then
    mkdir -p /root/.ssh
    cp /workspace/config/authorized_keys /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
    chmod 700 /root/.ssh
    log "✅ SSH keys restored from /workspace/config/"
else
    log "⚠️  No SSH keys found in /workspace/config/authorized_keys"
fi

# 2. System Packages Installation
log "Step 2: Installing system packages..."
if ! command -v jq &> /dev/null || ! command -v htop &> /dev/null; then
    log "Installing essential packages (jq, htop, tmux, etc.)..."
    apt-get update -qq
    apt-get install -y -qq jq htop tmux vim nano curl wget git net-tools python3-pip >> "$LOG_FILE" 2>&1
    log "✅ System packages installed"
else
    log "✅ System packages already present"
fi

# 3. Python Requirements Installation
log "Step 3: Installing Python requirements..."
if [ -f /workspace/001-bms-agent/requirements.txt ]; then
    log "Found requirements.txt in /workspace/001-bms-agent/"
    
    # Check if virtual environment exists
    if [ ! -d /workspace/001-bms-agent/.venv ]; then
        log "Creating Python virtual environment..."
        cd /workspace/001-bms-agent
        python3 -m venv .venv >> "$LOG_FILE" 2>&1
        log "✅ Virtual environment created"
    fi
    
    # Activate and install requirements
    log "Installing Python packages from requirements.txt..."
    cd /workspace/001-bms-agent
    source .venv/bin/activate
    pip install --upgrade pip >> "$LOG_FILE" 2>&1
    pip install -r requirements.txt >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        log "✅ Python requirements installed successfully"
        INSTALLED_PACKAGES=$(pip list --format=freeze | wc -l)
        log "   Installed packages: $INSTALLED_PACKAGES"
    else
        log "⚠️  Some Python packages may have failed to install"
        log "   Check $LOG_FILE for details"
    fi
else
    log "⚠️  requirements.txt not found in /workspace/001-bms-agent/"
    log "   Python dependencies may need to be installed manually"
fi

# 4. Ollama Installation from Backup
log "Step 4: Restoring Ollama installation..."
if [ -d /workspace/backups/ollama_install ]; then
    log "Found Ollama backup in /workspace/backups/ollama_install"
    
    # Copy Ollama binary
    if [ -f /workspace/backups/ollama_install/bin/ollama ]; then
        cp /workspace/backups/ollama_install/bin/ollama /usr/local/bin/ollama
        chmod +x /usr/local/bin/ollama
        log "✅ Ollama binary restored to /usr/local/bin/"
    fi
    
    # Copy systemd service if exists
    if [ -f /workspace/backups/ollama_install/systemd/ollama.service ]; then
        cp /workspace/backups/ollama_install/systemd/ollama.service /etc/systemd/system/
        log "✅ Ollama systemd service restored"
    fi
    
    # Copy GPU override config if exists
    if [ -f /workspace/backups/ollama_install/systemd.d/override.conf ]; then
        mkdir -p /etc/systemd/system/ollama.service.d
        cp /workspace/backups/ollama_install/systemd.d/override.conf /etc/systemd/system/ollama.service.d/
        log "✅ Ollama GPU override config restored"
    fi
    
    # Copy any additional files
    if [ -d /workspace/backups/ollama_install/lib ]; then
        cp -r /workspace/backups/ollama_install/lib/* /usr/local/lib/ 2>/dev/null || true
        log "✅ Ollama libraries restored"
    fi
    
    log "✅ Ollama restored from backup ($(ollama --version 2>/dev/null || echo 'version check failed'))"
else
    log "⚠️  No Ollama backup found, installing fresh..."
    curl -fsSL https://ollama.com/install.sh | sh >> "$LOG_FILE" 2>&1
    log "✅ Ollama installed fresh"
    
    # Create backup for next boot
    log "Creating Ollama backup for future boots..."
    mkdir -p /workspace/backups/ollama_install/{bin,systemd,lib}
    cp /usr/local/bin/ollama /workspace/backups/ollama_install/bin/ 2>/dev/null || true
    cp /etc/systemd/system/ollama.service /workspace/backups/ollama_install/systemd/ 2>/dev/null || true
    cp -r /usr/local/lib/ollama* /workspace/backups/ollama_install/lib/ 2>/dev/null || true
    log "✅ Ollama backup created in /workspace/backups/ollama_install/"
fi

# 5. GPU Verification
log "Step 5: Verifying GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null || echo "GPU query failed")
    log "✅ GPU detected: $GPU_INFO"
    
    # Verify CUDA environment
    if [ -n "${CUDA_VISIBLE_DEVICES:-}" ]; then
        log "✅ CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
    else
        log "⚠️  CUDA_VISIBLE_DEVICES not set, GPU may not be accessible"
    fi
else
    log "⚠️  nvidia-smi not found - GPU support may not be available"
fi

# 6. Ollama Configuration
log "Step 6: Configuring Ollama..."
mkdir -p /workspace/data/ollama_models

# Start Ollama service with OLLAMA_MODELS environment variable
log "Starting Ollama service..."
OLLAMA_MODELS=/workspace/data/ollama_models ollama serve > /workspace/logs/ollama.log 2>&1 &
OLLAMA_PID=$!

# Wait for Ollama with timeout
log "Waiting for Ollama to start (30s timeout)..."
OLLAMA_READY=false
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        OLLAMA_READY=true
        break
    fi
    sleep 1
done

if [ "$OLLAMA_READY" = true ]; then
    log "✅ Ollama service started successfully (PID: $OLLAMA_PID)"
    log "   Models directory: /workspace/data/ollama_models"
    
    # Verify Ollama version
    OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
    log "   Ollama version: $OLLAMA_VERSION"
else
    log "❌ Ollama service failed to start within 30 seconds"
    log "   Check /workspace/logs/ollama.log for errors"
fi

# 7. Pre-load Ollama Models
log "Step 7: Checking Ollama models..."
# Check if any models exist in the persistent storage
MODEL_COUNT=$(OLLAMA_MODELS=/workspace/data/ollama_models ollama list 2>/dev/null | grep -v "NAME" | wc -l)
if [ "$MODEL_COUNT" -gt 0 ]; then
    log "✅ Found $MODEL_COUNT model(s) in /workspace/data/ollama_models"
    OLLAMA_MODELS=/workspace/data/ollama_models ollama list | grep -v "NAME" | while read line; do
        log "   - $line"
    done
else
    log "⚠️  No models found in /workspace/data/ollama_models"
    log "   Models should be pre-downloaded and stored in persistent storage"
    log "   Skipping automatic model download to avoid delays"
fi

# 8. Start BMS Agent Services
log "Step 8: Starting BMS Agent services..."
if [ -f /workspace/001-bms-agent/scripts/start_all_services.sh ]; then
    log "Executing start_all_services.sh..."
    bash /workspace/001-bms-agent/scripts/start_all_services.sh >> "$LOG_FILE" 2>&1
    log "✅ BMS Agent services started"
elif [ -f /workspace/scripts/start_all_services.sh ]; then
    log "Executing start_all_services.sh from /workspace/scripts..."
    bash /workspace/scripts/start_all_services.sh >> "$LOG_FILE" 2>&1
    log "✅ BMS Agent services started"
else
    log "⚠️  start_all_services.sh not found in /workspace/001-bms-agent/scripts/ or /workspace/scripts/"
fi

# 9. Health Check
log "Step 9: Running comprehensive health checks..."
log "Waiting for services to fully start..."
sleep 10

# Check Qdrant
if curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
    log "✅ Qdrant: healthy"
else
    log "⚠️  Qdrant: not responding"
fi

# Check BMS API (with retries)
BMS_HEALTHY=false
for i in {1..6}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ BMS API: healthy"
        BMS_HEALTHY=true
        break
    fi
    if [ $i -lt 6 ]; then
        log "   Waiting for BMS API... (attempt $i/6)"
        sleep 5
    fi
done
if [ "$BMS_HEALTHY" = false ]; then
    log "⚠️  BMS API: not responding after 6 attempts"
    log "   Check /workspace/logs/api.log for errors"
fi

# Check OpenWebUI (with retries)
WEBUI_HEALTHY=false
for i in {1..6}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        log "✅ OpenWebUI: healthy"
        WEBUI_HEALTHY=true
        break
    fi
    if [ $i -lt 6 ]; then
        log "   Waiting for OpenWebUI... (attempt $i/6)"
        sleep 5
    fi
done
if [ "$WEBUI_HEALTHY" = false ]; then
    log "⚠️  OpenWebUI: not responding after 6 attempts"
    log "   Check /workspace/logs/openwebui.log for errors"
fi

# 10. Final Summary
log "Step 10: Generating initialization summary..."

# Count successful services
SERVICES_UP=0
SERVICES_TOTAL=4

if curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
    SERVICES_UP=$((SERVICES_UP + 1))
fi
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    SERVICES_UP=$((SERVICES_UP + 1))
fi
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    SERVICES_UP=$((SERVICES_UP + 1))
fi
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    SERVICES_UP=$((SERVICES_UP + 1))
fi

# Mark initialization complete
touch "$INIT_MARKER"

log "=========================================="
log "RunPod Initialization Complete!"
log "=========================================="
log "Status: $SERVICES_UP/$SERVICES_TOTAL services operational"
log ""
log "Services:"
log "  - Qdrant:    http://localhost:6333"
log "  - BMS API:   http://localhost:8000"
log "  - OpenWebUI: http://localhost:3000"
log "  - Ollama:    http://localhost:11434"
log ""
log "Logs:"
log "  - Init:      $LOG_FILE"
log "  - Startup:   $STARTUP_LOG"
log "  - API:       /workspace/logs/api.log"
log "  - Qdrant:    /workspace/logs/qdrant.log"
log "  - Ollama:    /workspace/logs/ollama.log"
log ""
if [ "$SERVICES_UP" -eq "$SERVICES_TOTAL" ]; then
    log "✅ All services started successfully!"
else
    log "⚠️  Some services failed to start. Check logs for details."
fi
log "=========================================="

exit 0
