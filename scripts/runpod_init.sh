#!/bin/bash
# RunPod Initialization Script
# Place this in RunPod's startup script field
# Ensures all dependencies are installed in /workspace (persistent storage)
# Exception: Ollama installed in /root for GPU compatibility

set -e  # Exit on error

LOGFILE="/workspace/logs/runpod_init.log"
PROJECT_DIR="/workspace/001-bms-agent"
VENV_DIR="/workspace/bms-api-venv"
INIT_MARKER="/workspace/.runpod_init_complete"

# Function for logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOGFILE"
}

# Check if initialization already completed
if [ -f "$INIT_MARKER" ]; then
    log "Initialization already completed. Skipping full init."
    log "Starting services only..."
    
    # Restore SSH keys
    if [ -f /workspace/config/authorized_keys ]; then
        log "Restoring SSH keys..."
        mkdir -p /root/.ssh
        chmod 700 /root/.ssh
        
        # Append workspace keys to root authorized_keys (avoid duplicates)
        if [ -f /root/.ssh/authorized_keys ]; then
            # Backup existing keys
            cp /root/.ssh/authorized_keys /root/.ssh/authorized_keys.backup
            # Append new keys, removing duplicates
            cat /workspace/config/authorized_keys /root/.ssh/authorized_keys | sort -u > /root/.ssh/authorized_keys.tmp
            mv /root/.ssh/authorized_keys.tmp /root/.ssh/authorized_keys
        else
            cp /workspace/config/authorized_keys /root/.ssh/authorized_keys
        fi
        
        chmod 600 /root/.ssh/authorized_keys
        log "SSH keys restored"
    fi
    
    # Set Ollama models directory
    export OLLAMA_MODELS=/workspace/data/ollama_models
    
    # Start services
    if [ -f "$PROJECT_DIR/scripts/start_all_services.sh" ]; then
        cd "$PROJECT_DIR"
        bash scripts/start_all_services.sh >> "$LOGFILE" 2>&1
        log "Services started"
    fi
    
    exit 0
fi

log "=== RunPod Initialization Started ==="

# Wait for system to be ready
sleep 10

# Restore SSH keys FIRST (before anything else)
if [ -f /workspace/config/authorized_keys ]; then
    log "Restoring SSH keys from /workspace/config/authorized_keys..."
    mkdir -p /root/.ssh
    chmod 700 /root/.ssh
    
    # Append workspace keys to root authorized_keys (avoid duplicates)
    if [ -f /root/.ssh/authorized_keys ]; then
        log "Existing SSH keys found, merging..."
        # Backup existing keys
        cp /root/.ssh/authorized_keys /root/.ssh/authorized_keys.backup
        # Append new keys, removing duplicates
        cat /workspace/config/authorized_keys /root/.ssh/authorized_keys | sort -u > /root/.ssh/authorized_keys.tmp
        mv /root/.ssh/authorized_keys.tmp /root/.ssh/authorized_keys
        log "SSH keys merged (duplicates removed)"
    else
        log "No existing SSH keys, copying from workspace..."
        cp /workspace/config/authorized_keys /root/.ssh/authorized_keys
    fi
    
    chmod 600 /root/.ssh/authorized_keys
    log "✅ SSH keys restored successfully"
    
    # Also save to workspace for backup
    cp /root/.ssh/authorized_keys /workspace/config/authorized_keys.backup
else
    log "⚠️  No SSH keys found at /workspace/config/authorized_keys"
    log "Creating directory for future use..."
    mkdir -p /workspace/config
    
    # If root has keys, copy them to workspace
    if [ -f /root/.ssh/authorized_keys ]; then
        log "Backing up existing root SSH keys to workspace..."
        cp /root/.ssh/authorized_keys /workspace/config/authorized_keys
        log "SSH keys backed up to /workspace/config/authorized_keys"
    fi
fi

# Create necessary directories
log "Creating directory structure..."
mkdir -p /workspace/logs
mkdir -p /workspace/data/ollama_models
mkdir -p /workspace/qdrant_storage
mkdir -p /workspace/bms_data
mkdir -p /workspace/backups

# Install Ollama if not present (installed in /root for GPU compatibility)
if [ ! -f /usr/local/bin/ollama ]; then
    log "Ollama not found, installing in /root (for GPU support)..."
    curl -fsSL https://ollama.com/install.sh | sh >> "$LOGFILE" 2>&1
    log "Ollama installed successfully"
else
    log "Ollama already installed"
fi

# Configure Ollama to use persistent storage for models
export OLLAMA_MODELS=/workspace/data/ollama_models
log "Ollama models directory: $OLLAMA_MODELS"

# Create/update Python virtual environment in /workspace
if [ ! -d "$VENV_DIR" ]; then
    log "Creating Python virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR" >> "$LOGFILE" 2>&1
    log "Virtual environment created"
else
    log "Virtual environment already exists"
fi

# Activate virtual environment and install/upgrade dependencies
log "Installing Python dependencies from requirements.txt..."
cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"

# Upgrade pip
pip install --upgrade pip >> "$LOGFILE" 2>&1

# Install requirements
if [ -f "requirements.txt" ]; then
    log "Installing requirements from requirements.txt..."
    pip install -r requirements.txt >> "$LOGFILE" 2>&1
    log "Requirements installed successfully"
else
    log "WARNING: requirements.txt not found!"
fi

# Download required NLTK data
log "Downloading NLTK data..."
python -c "
import nltk
import sys
try:
    nltk.download('punkt_tab', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
    print('NLTK data downloaded successfully')
except Exception as e:
    print(f'Error downloading NLTK data: {e}', file=sys.stderr)
    sys.exit(1)
" >> "$LOGFILE" 2>&1

if [ $? -eq 0 ]; then
    log "NLTK data downloaded successfully"
else
    log "WARNING: NLTK data download failed"
fi

deactivate

# Install system dependencies if needed
log "Checking system dependencies..."
if ! command -v jq &> /dev/null; then
    log "Installing jq..."
    apt-get update >> "$LOGFILE" 2>&1
    apt-get install -y jq >> "$LOGFILE" 2>&1
    log "jq installed"
fi

# Pull required Ollama models
log "Checking Ollama models..."
export OLLAMA_MODELS=/workspace/data/ollama_models

# Start Ollama service first
if ! pgrep -x "ollama" > /dev/null; then
    log "Starting Ollama service..."
    nohup ollama serve > /workspace/logs/ollama.log 2>&1 &
    sleep 5
fi

# Pull embedding model if not present
if [ ! -d "$OLLAMA_MODELS/manifests/registry.ollama.ai/library/nomic-embed-text" ]; then
    log "Pulling nomic-embed-text model..."
    ollama pull nomic-embed-text >> "$LOGFILE" 2>&1
    log "nomic-embed-text model pulled"
fi

# Pull LLM model if not present
if [ ! -d "$OLLAMA_MODELS/manifests/registry.ollama.ai/library/mistral" ]; then
    log "Pulling mistral model..."
    ollama pull mistral >> "$LOGFILE" 2>&1
    log "mistral model pulled"
fi

# Start BMS Agent services
if [ -f "$PROJECT_DIR/scripts/start_all_services.sh" ]; then
    log "Starting BMS Agent services..."
    cd "$PROJECT_DIR"
    bash scripts/start_all_services.sh >> "$LOGFILE" 2>&1
    log "BMS Agent services started"
else
    log "WARNING: start_all_services.sh not found!"
fi

# Final status check
log "Initialization complete. Checking service status..."
sleep 5

if pgrep -x "ollama" > /dev/null; then
    log "✅ Ollama: Running"
else
    log "❌ Ollama: Not running"
fi

if pgrep -f "qdrant" > /dev/null; then
    log "✅ Qdrant: Running"
else
    log "❌ Qdrant: Not running"
fi

if pgrep -f "uvicorn api.main:app" > /dev/null; then
    log "✅ BMS API: Running"
else
    log "❌ BMS API: Not running"
fi

if pgrep -f "open-webui" > /dev/null; then
    log "✅ OpenWebUI: Running"
else
    log "❌ OpenWebUI: Not running"
fi

log "RunPod initialization script completed"
log "Check logs at: /workspace/logs/"

# Mark initialization as complete to prevent re-running on restart
touch "$INIT_MARKER"
log "✅ Initialization marker created: $INIT_MARKER"
log "=== Full initialization will be skipped on next restart ==="
