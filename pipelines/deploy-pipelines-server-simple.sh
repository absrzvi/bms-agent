#!/bin/bash
# Simple Pipelines Server Deployment for Pod Environment
# Runs Pipelines server directly from cloned repository

set -e

echo "=================================================="
echo "OpenWebUI Pipelines Server Deployment (Pod)"
echo "=================================================="
echo ""

# Use persistent storage for Pipelines repository (survives pod restarts)
PIPELINES_REPO="/workspace/pipelines-repo"
PIPELINES_DIR="/workspace/001-bms-agent/pipelines"
OUTPUT_DIR="/workspace/001-bms-agent/pipelines/output"

# Stop existing server if running
if [ -f "$PIPELINES_DIR/server.pid" ]; then
    OLD_PID=$(cat "$PIPELINES_DIR/server.pid")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Stopping existing server (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2
        if ps -p $OLD_PID > /dev/null 2>&1; then
            echo "Force killing..."
            kill -9 $OLD_PID
        fi
        echo "✅ Existing server stopped"
    else
        echo "ℹ️  Stale PID file found (process not running)"
        rm -f "$PIPELINES_DIR/server.pid"
    fi
fi

echo ""
echo "Step 1: Creating directories..."
mkdir -p "$PIPELINES_DIR"
mkdir -p "$OUTPUT_DIR"
echo "✅ Directories created"

echo ""
echo "Step 1.5: Cloning Pipelines repository (if needed)..."
if [ ! -d "$PIPELINES_REPO" ]; then
    echo "Cloning OpenWebUI Pipelines repository to persistent storage..."
    git clone https://github.com/open-webui/pipelines.git "$PIPELINES_REPO"
    echo "✅ Repository cloned"
else
    echo "✅ Repository already exists at $PIPELINES_REPO"
fi

echo ""
echo "Step 1.6: Validating pipeline file..."
if [ ! -f "$PIPELINES_DIR/bms_document_generator.py" ]; then
    echo "❌ Pipeline file not found at $PIPELINES_DIR/bms_document_generator.py"
    exit 1
fi
echo "✅ Pipeline file validated"

echo ""
echo "Step 2: Installing minimal Pipelines server requirements..."
cd "$PIPELINES_REPO"
# Install only essential Pipelines dependencies (skip heavy ML/AI libs we don't need)
pip install fastapi uvicorn pydantic python-multipart passlib PyJWT python-socketio aiohttp requests httpx python-dotenv --quiet

echo "✅ Minimal Pipelines dependencies installed"

echo ""
echo "Step 3: Installing document generation dependencies..."
pip install python-docx>=0.8.11 openpyxl>=3.1.0 python-pptx>=0.6.21 --quiet

echo "✅ Document generation dependencies installed"

echo ""
echo "Step 4: Creating startup script..."
cat > "$PIPELINES_DIR/start-server.sh" << 'SERVERSCRIPT'
#!/bin/bash
# Start Pipelines server from cloned repository

export PIPELINES_DIR="/workspace/001-bms-agent/pipelines"
export PORT=9099
export HOST=0.0.0.0

cd /workspace/pipelines-repo

echo "Starting Pipelines server on port $PORT..."
echo "Pipelines directory: $PIPELINES_DIR"
echo ""

# Start server with nohup for background execution
nohup python3 main.py \
    --host $HOST \
    --port $PORT \
    > /workspace/001-bms-agent/pipelines/server.log 2>&1 &

PIPELINES_PID=$!
echo $PIPELINES_PID > /workspace/001-bms-agent/pipelines/server.pid

echo "✅ Pipelines server started (PID: $PIPELINES_PID)"
echo ""
echo "Server Details:"
echo "  - Port: $PORT"
echo "  - API URL: http://localhost:$PORT"
echo "  - Pipelines Directory: $PIPELINES_DIR"
echo "  - Log file: /workspace/001-bms-agent/pipelines/server.log"
echo "  - PID file: /workspace/001-bms-agent/pipelines/server.pid"
echo ""
echo "View logs: tail -f /workspace/001-bms-agent/pipelines/server.log"
echo "Stop server: kill $(cat /workspace/001-bms-agent/pipelines/server.pid)"
SERVERSCRIPT

chmod +x "$PIPELINES_DIR/start-server.sh"

echo "✅ Startup script created"

echo ""
echo "Step 5: Starting Pipelines server..."
bash "$PIPELINES_DIR/start-server.sh"

echo ""
echo "Step 6: Waiting for server to start..."
sleep 5

# Check if server is running
if curl -s http://localhost:9099 > /dev/null 2>&1; then
    echo "✅ Server responding"
else
    echo "⚠️  Server not responding yet (checking logs...)"
    if [ -f "$PIPELINES_DIR/server.log" ]; then
        echo "Last 20 lines of log:"
        tail -n 20 "$PIPELINES_DIR/server.log"
    fi
fi

echo ""
echo "=================================================="
echo "✅ Deployment Complete"
echo "=================================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Verify server is running:"
echo "   curl http://localhost:9099"
echo "   tail -f pipelines/server.log"
echo ""
echo "2. Install document generation Pipeline:"
echo "   bash pipelines/install-document-pipeline.sh"
echo ""
echo "3. Connect to OpenWebUI:"
echo "   - Open: http://localhost:3000/admin"
echo "   - Go to: Settings → Connections"
echo "   - Click: + Add Connection"
echo "   - API URL: http://localhost:9099"
echo "   - API Key: 0p3n-w3bu!"
echo ""
echo "Commands:"
echo "  - View logs: tail -f pipelines/server.log"
echo "  - Stop server: kill \$(cat pipelines/server.pid)"
echo "  - Restart: bash pipelines/deploy-pipelines-server-simple.sh"
echo ""
