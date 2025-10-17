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
    
    # Set environment variables for persistent data
    export OLLAMA_MODELS=/workspace/data/ollama_models
    export NLTK_DATA=/workspace/nltk_data
    
    # Source environment config if exists
    if [ -f /workspace/config/env.sh ]; then
        source /workspace/config/env.sh
    fi
    
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
        log "SSH keys backed up to /workspace/config/authorized_keys"
    fi
fi

# Create necessary directories
mkdir -p /workspace/logs
mkdir -p /workspace/config
mkdir -p /workspace/data/ollama_models
mkdir -p /workspace/n8n
mkdir -p /workspace/data/redis

# Ensure local tooling binaries are discoverable
export PATH=/workspace/n8n/node_modules/.bin:$PATH
mkdir -p /workspace/qdrant_storage
mkdir -p /workspace/bms_data
mkdir -p /workspace/backups
mkdir -p /workspace/nltk_data

# Ensure modern Node.js and npm for n8n
log "Checking Node.js runtime..."
NODE_MAJOR=0
if command -v node >/dev/null 2>&1; then
    NODE_MAJOR=$(node -p "process.versions.node.split('.')[0]")
    log "Detected Node.js version $(node -v)"
fi

if [ "$NODE_MAJOR" -lt 18 ]; then
    log "Installing Node.js 20.x via NodeSource..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >> "$LOGFILE" 2>&1
    apt-get install -y nodejs >> "$LOGFILE" 2>&1
    log "Node.js installed: $(node -v)"
else
    log "Node.js already meets requirements"
fi

log "Upgrading npm to latest stable..."
if npm install -g npm >> "$LOGFILE" 2>&1; then
    log "npm upgraded: $(npm -v)"
else
    log "WARNING: npm upgrade failed"
fi

# Install Redis if necessary and start server
log "Checking Redis installation..."
if ! command -v redis-server >/dev/null 2>&1; then
    log "Installing Redis..."
    apt-get install -y redis-server >> "$LOGFILE" 2>&1
else
    log "Redis already installed"
fi

log "Configuring Redis for persistent workspace storage..."
REDIS_CONF=/workspace/config/redis.conf
if [ ! -f "$REDIS_CONF" ]; then
    cat > "$REDIS_CONF" <<'EOF'
bind 0.0.0.0
port 6379
dir /workspace/data/redis
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000
logfile /workspace/logs/redis-server.log
databases 16
EOF
    log "Redis config created at $REDIS_CONF"
fi

if pgrep -x "redis-server" >/dev/null 2>&1; then
    log "Redis already running"
else
    log "Starting Redis server..."
    nohup redis-server "$REDIS_CONF" >> /workspace/logs/redis-init.log 2>&1 &
    sleep 3
    if pgrep -x "redis-server" >/dev/null 2>&1; then
        log "Redis server started"
    else
        log "ERROR: Redis failed to start"
    fi
fi
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

# Download required NLTK data to /workspace (persistent)
log "Downloading NLTK data to /workspace/nltk_data..."
mkdir -p /workspace/nltk_data
export NLTK_DATA=/workspace/nltk_data

python -c "
import nltk
import sys
import os

# Set NLTK data path to workspace (persistent)
os.environ['NLTK_DATA'] = '/workspace/nltk_data'
nltk.data.path.insert(0, '/workspace/nltk_data')

try:
    nltk.download('punkt_tab', download_dir='/workspace/nltk_data', quiet=True)
    nltk.download('punkt', download_dir='/workspace/nltk_data', quiet=True)
    nltk.download('wordnet', download_dir='/workspace/nltk_data', quiet=True)
    nltk.download('stopwords', download_dir='/workspace/nltk_data', quiet=True)
    nltk.download('averaged_perceptron_tagger', download_dir='/workspace/nltk_data', quiet=True)
    nltk.download('maxent_ne_chunker', download_dir='/workspace/nltk_data', quiet=True)
    nltk.download('words', download_dir='/workspace/nltk_data', quiet=True)
    print('NLTK data downloaded successfully to /workspace/nltk_data')
except Exception as e:
    print(f'Error downloading NLTK data: {e}', file=sys.stderr)
    sys.exit(1)
" >> "$LOGFILE" 2>&1

if [ $? -eq 0 ]; then
    log "✅ NLTK data downloaded successfully to /workspace/nltk_data"
else
    log "WARNING: NLTK data download failed"
fi

# Set NLTK_DATA environment variable for all future sessions
echo "export NLTK_DATA=/workspace/nltk_data" >> /workspace/config/env.sh
log "NLTK_DATA environment variable configured"

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
    OLLAMA_MODELS=/workspace/data/ollama_models nohup ollama serve > /workspace/logs/ollama.log 2>&1 &
    sleep 5
    log "Ollama started with OLLAMA_MODELS=/workspace/data/ollama_models"
else
    log "Ollama already running"
fi

# Pull embedding model if not present
if [ ! -d "$OLLAMA_MODELS/manifests/registry.ollama.ai/library/nomic-embed-text" ]; then
    log "Pulling nomic-embed-text model..."
    OLLAMA_MODELS=/workspace/data/ollama_models ollama pull nomic-embed-text >> "$LOGFILE" 2>&1
    log "nomic-embed-text model pulled"
fi

# Pull LLM model if not present
if [ ! -d "$OLLAMA_MODELS/manifests/registry.ollama.ai/library/mistral" ]; then
    log "Pulling mistral model..."
    OLLAMA_MODELS=/workspace/data/ollama_models ollama pull mistral >> "$LOGFILE" 2>&1
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
