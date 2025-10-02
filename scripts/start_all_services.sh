#!/bin/bash
set -e

echo "🚀 Starting BMS Agent Services..."

# Load environment
source /workspace/scripts/env.sh 2>/dev/null || true

# Start Qdrant
if [ -f /workspace/apps/qdrant/qdrant ]; then
    echo "Starting Qdrant..."
    cd /workspace/apps/qdrant
    ./qdrant --config-path /workspace/apps/qdrant/config.yaml \
        > /workspace/logs/qdrant.log 2>&1 &
    sleep 3
fi

# Start Ollama
if [ -f /workspace/apps/ollama/ollama ]; then
    echo "Starting Ollama..."
    export OLLAMA_MODELS=/workspace/data/ollama_models
    /workspace/apps/ollama/ollama serve > /workspace/logs/ollama.log 2>&1 &
    sleep 3
fi

# Start BMS API
if [ -d /workspace/001-bms-agent ]; then
    echo "Starting BMS API..."
    cd /workspace/001-bms-agent
    source /workspace/bms-api-venv/bin/activate
    nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/api.log 2>&1 &
    sleep 3
fi

# Start OpenWebUI
if [ -f /workspace/openwebui/venv/bin/open-webui ]; then
    echo "Starting OpenWebUI..."
    cd /workspace/openwebui
    source /workspace/openwebui/venv/bin/activate
    export OPENWEBUI_DATA_DIR=/workspace/data/openwebui
    nohup open-webui serve --host 0.0.0.0 --port 3000 > /workspace/logs/openwebui.log 2>&1 &
    sleep 3
fi

echo "✅ All services started!"
echo ""
echo "Service URLs:"
echo "  - OpenWebUI: http://localhost:3000"
echo "  - BMS API: http://localhost:8000"
echo "  - Qdrant: http://localhost:6333"
echo "  - Ollama: http://localhost:11434"
