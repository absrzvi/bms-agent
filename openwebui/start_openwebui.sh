#!/bin/bash
# Start OpenWebUI with BMS Agent integration

echo "🚀 Starting OpenWebUI with BMS Agent Tools"
echo "=========================================="

# Set data directory
export OPEN_WEBUI_DATA_DIR=/workspace/openwebui/data

# Set Ollama connection
export OLLAMA_BASE_URL=http://localhost:11434

# Disable authentication for POC (optional)
export WEBUI_AUTH=False

# Create directories
mkdir -p $OPEN_WEBUI_DATA_DIR/tools

# Copy/link BMS search tool
if [ ! -f "$OPEN_WEBUI_DATA_DIR/tools/bms_search.py" ]; then
    echo "📋 Installing BMS search tool..."
    cp /workspace/001-bms-agent/tools/bms_search.py \
       $OPEN_WEBUI_DATA_DIR/tools/
    echo "✅ BMS search tool installed"
fi

# Activate OpenWebUI virtual environment
cd /workspace/openwebui
source venv/bin/activate

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Ollama is not running on port 11434"
    echo "   OpenWebUI requires Ollama to function"
fi

# Check if BMS API is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ BMS API is running"
else
    echo "⚠️  BMS API is not running on port 8000"
    echo "   Start it with: uvicorn api.main:app --host 0.0.0.0 --port 8000"
fi

echo ""
echo "🌐 Starting OpenWebUI on http://localhost:3000"
echo "   Data directory: $OPEN_WEBUI_DATA_DIR"
echo "   Ollama URL: $OLLAMA_BASE_URL"
echo "   BMS API: http://localhost:8000"
echo "   Auth: $WEBUI_AUTH"
echo ""

# Start OpenWebUI
open-webui serve --host 0.0.0.0 --port 3000
