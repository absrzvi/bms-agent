#!/bin/bash
# Install Ollama with GPU/CUDA Support
# This script installs Ollama with NVIDIA GPU acceleration

set -e

LOG_FILE="/workspace/logs/ollama_gpu_install.log"
mkdir -p /workspace/logs

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Ollama GPU Installation Started"
log "=========================================="

# 1. Check for NVIDIA GPU
log "Step 1: Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    log "✅ NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | while read line; do
        log "   $line"
    done
    GPU_AVAILABLE=true
else
    log "⚠️  WARNING: nvidia-smi not found. GPU acceleration may not work."
    log "   Continuing with installation anyway..."
    GPU_AVAILABLE=false
fi

# 2. Check CUDA installation
log "Step 2: Checking CUDA installation..."
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $5}' | cut -d',' -f1)
    log "✅ CUDA detected: version $CUDA_VERSION"
    log "   CUDA path: $(which nvcc)"
elif [ -d /usr/local/cuda ]; then
    log "✅ CUDA installation found at /usr/local/cuda"
    export PATH=/usr/local/cuda/bin:$PATH
    export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
else
    log "⚠️  WARNING: CUDA not detected. Ollama will attempt to use GPU anyway."
fi

# 3. Check for existing Ollama installation
log "Step 3: Checking for existing Ollama installation..."
if command -v ollama &> /dev/null; then
    EXISTING_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
    log "⚠️  Ollama already installed: $EXISTING_VERSION"
    read -p "Do you want to reinstall? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Installation cancelled by user"
        exit 0
    fi
    log "Removing existing installation..."
    systemctl stop ollama 2>/dev/null || true
    rm -f /usr/local/bin/ollama
    rm -f /etc/systemd/system/ollama.service
    log "✅ Existing installation removed"
fi

# 4. Install Ollama with GPU support
log "Step 4: Installing Ollama..."
log "Downloading and installing Ollama (this may take a few minutes)..."

# Use official install script which automatically detects GPU
curl -fsSL https://ollama.com/install.sh | sh >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
    log "✅ Ollama installed successfully: $OLLAMA_VERSION"
else
    log "❌ ERROR: Ollama installation failed"
    exit 1
fi

# 5. Configure Ollama for GPU
log "Step 5: Configuring Ollama for GPU acceleration..."

# Set environment variables for GPU
export OLLAMA_MODELS=/workspace/data/ollama_models
mkdir -p /workspace/data/ollama_models

# Create systemd override for GPU settings
log "Creating systemd service override..."
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_MODELS=/workspace/data/ollama_models"
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
# GPU settings
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="OLLAMA_NUM_GPU=1"
EOF

log "✅ Systemd override created"

# Reload systemd
systemctl daemon-reload

# 6. Start Ollama service
log "Step 6: Starting Ollama service..."
systemctl stop ollama 2>/dev/null || true
sleep 2

# Start Ollama manually to see GPU detection
log "Starting Ollama with GPU detection..."
export CUDA_VISIBLE_DEVICES=0
OLLAMA_MODELS=/workspace/data/ollama_models ollama serve > /workspace/logs/ollama.log 2>&1 &
OLLAMA_PID=$!
log "Ollama started with PID: $OLLAMA_PID"
log "Environment: OLLAMA_MODELS=/workspace/data/ollama_models CUDA_VISIBLE_DEVICES=0"

# Wait for Ollama to start
log "Waiting for Ollama to initialize..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        log "✅ Ollama service is responding"
        break
    fi
    sleep 1
done

# 7. Verify GPU detection
log "Step 7: Verifying GPU detection..."
sleep 3

# Check Ollama logs for GPU detection
if grep -q "cuda" /workspace/logs/ollama.log 2>/dev/null; then
    log "✅ CUDA detected in Ollama logs"
    grep -i "cuda\|gpu" /workspace/logs/ollama.log | head -5 | while read line; do
        log "   $line"
    done
else
    log "⚠️  No CUDA references found in Ollama logs"
    log "   Ollama may be running in CPU mode"
fi

# 8. Test with a small model
log "Step 8: Testing GPU acceleration with a small model..."
log "Pulling tinyllama model for testing (this may take a minute)..."

ollama pull tinyllama >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "✅ Test model pulled successfully"
    
    # Run a test inference
    log "Running test inference..."
    TEST_START=$(date +%s)
    echo "Say hello in one word" | ollama run tinyllama >> "$LOG_FILE" 2>&1
    TEST_END=$(date +%s)
    TEST_DURATION=$((TEST_END - TEST_START))
    
    log "✅ Test inference completed in ${TEST_DURATION}s"
    
    # Check GPU utilization during inference
    if [ "$GPU_AVAILABLE" = true ]; then
        log "GPU utilization during test:"
        nvidia-smi --query-gpu=utilization.gpu,utilization.memory,temperature.gpu --format=csv,noheader | while read line; do
            log "   $line"
        done
    fi
else
    log "⚠️  Test model pull failed (this is OK, GPU support may still work)"
fi

# 9. Display GPU information
log "Step 9: GPU Information Summary..."
if [ "$GPU_AVAILABLE" = true ]; then
    log "NVIDIA GPU Status:"
    nvidia-smi --query-gpu=index,name,driver_version,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu --format=csv,noheader | while read line; do
        log "   $line"
    done
    
    # Check CUDA libraries
    log "CUDA Libraries:"
    ldconfig -p | grep cuda | head -5 | while read line; do
        log "   $line"
    done
fi

# 10. Create backup
log "Step 10: Creating Ollama installation backup..."
if [ -f /workspace/001-bms-agent/scripts/backup_ollama_install.sh ]; then
    bash /workspace/001-bms-agent/scripts/backup_ollama_install.sh >> "$LOG_FILE" 2>&1
    log "✅ Backup created"
else
    log "⚠️  Backup script not found, skipping backup"
fi

log "=========================================="
log "Ollama GPU Installation Complete!"
log "=========================================="
log ""
log "Installation Summary:"
log "  - Ollama Version: $(ollama --version 2>/dev/null || echo 'unknown')"
log "  - Models Directory: /workspace/data/ollama_models"
log "  - Service Status: Running (PID: $OLLAMA_PID)"
log "  - GPU Support: $([ "$GPU_AVAILABLE" = true ] && echo 'Enabled' || echo 'Unknown')"
log ""
log "Available Commands:"
log "  - List models:     ollama list"
log "  - Pull model:      ollama pull mistral-nemo:12b-instruct"
log "  - Run model:       ollama run mistral-nemo:12b-instruct"
log "  - Check GPU:       nvidia-smi"
log "  - View logs:       tail -f /workspace/logs/ollama.log"
log ""
log "Next Steps:"
log "  1. Pull your required models:"
log "     ollama pull mistral-nemo:12b-instruct"
log "     ollama pull sentence-transformers/all-mpnet-base-v2"
log ""
log "  2. Test GPU acceleration:"
log "     echo 'Write a haiku about AI' | ollama run mistral-nemo:12b-instruct"
log "     # Watch GPU usage in another terminal:"
log "     watch -n 1 nvidia-smi"
log ""
log "  3. Verify models are in persistent storage:"
log "     ls -lh /workspace/data/ollama_models/"
log ""
log "Full installation log: $LOG_FILE"
log "=========================================="

exit 0
