#!/bin/bash
# RunPod Initialization Script v2.0
# Place this in RunPod's startup script field
# This script runs ONCE per pod boot and sets up the environment

set -e

INIT_MARKER="/tmp/runpod_init_complete"
LOG_FILE="/workspace/logs/runpod_init.log"

# Create logs directory
mkdir -p /workspace/logs

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
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
    apt-get install -y -qq jq htop tmux vim nano curl wget git net-tools >> "$LOG_FILE" 2>&1
    log "✅ System packages installed"
else
    log "✅ System packages already present"
fi

# 3. Ollama Installation from Backup
log "Step 3: Restoring Ollama installation..."
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

# 4. Ollama Configuration
log "Step 4: Configuring Ollama..."
export OLLAMA_MODELS=/workspace/data/ollama_models
mkdir -p /workspace/data/ollama_models

# Start Ollama service
log "Starting Ollama service..."
ollama serve > /workspace/logs/ollama.log 2>&1 &
OLLAMA_PID=$!
sleep 5

# Verify Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log "✅ Ollama service started successfully (PID: $OLLAMA_PID)"
else
    log "❌ Ollama service failed to start"
fi

# 5. Pre-load Ollama Models
log "Step 5: Checking Ollama models..."
REQUIRED_MODEL="mistral-nemo:12b-instruct"
if ollama list | grep -q "$REQUIRED_MODEL"; then
    log "✅ Model $REQUIRED_MODEL already available"
else
    log "Pulling model $REQUIRED_MODEL (this may take several minutes)..."
    ollama pull "$REQUIRED_MODEL" >> "$LOG_FILE" 2>&1
    log "✅ Model $REQUIRED_MODEL downloaded"
fi

# 6. Start BMS Agent Services
log "Step 6: Starting BMS Agent services..."
if [ -f /workspace/scripts/start_all_services.sh ]; then
    log "Executing start_all_services.sh..."
    bash /workspace/scripts/start_all_services.sh >> "$LOG_FILE" 2>&1
    log "✅ BMS Agent services started"
else
    log "⚠️  /workspace/scripts/start_all_services.sh not found"
fi

# 7. Health Check
log "Step 7: Running health checks..."
sleep 5

# Check Qdrant
if curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
    log "✅ Qdrant: healthy"
else
    log "⚠️  Qdrant: not responding"
fi

# Check BMS API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log "✅ BMS API: healthy"
else
    log "⚠️  BMS API: not responding"
fi

# Check OpenWebUI
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    log "✅ OpenWebUI: healthy"
else
    log "⚠️  OpenWebUI: not responding"
fi

# 8. Mark initialization complete
touch "$INIT_MARKER"
log "=========================================="
log "RunPod Initialization Complete!"
log "=========================================="
log "Services:"
log "  - Qdrant:    http://localhost:6333"
log "  - BMS API:   http://localhost:8000"
log "  - OpenWebUI: http://localhost:3000"
log "  - Ollama:    http://localhost:11434"
log "=========================================="

exit 0
