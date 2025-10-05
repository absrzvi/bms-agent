#!/bin/bash
# Deploy OpenWebUI Pipelines Server for Document Generation (Pod Environment)
# Based on research in docs/openwebui-doc-gen.md
# Updated for pod environment without Docker

set -e

echo "=================================================="
echo "OpenWebUI Pipelines Server Deployment (Pod)"
echo "=================================================="
echo ""

# Check if running in pod
if [ -z "$RUNPOD_POD_ID" ] && [ -z "$KUBERNETES_SERVICE_HOST" ]; then
    echo "⚠️  Warning: Not detected as pod environment"
    echo "   Proceeding anyway..."
fi

PIPELINES_REPO="/workspace/pipelines-repo"
PIPELINES_DIR="/workspace/001-bms-agent/pipelines"
OUTPUT_DIR="/workspace/001-bms-agent/pipelines/output"
VENV_DIR="/workspace/001-bms-agent/.venv"

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
echo "Step 2: Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

echo ""
echo "Step 3: Installing Pipelines server package..."
# Clone Pipelines repository if not exists
if [ ! -d "$PIPELINES_REPO" ]; then
    echo "Cloning OpenWebUI Pipelines repository to persistent storage..."
    git clone https://github.com/open-webui/pipelines.git "$PIPELINES_REPO"
    echo "✅ Repository cloned"
else
    echo "✅ Repository already exists at $PIPELINES_REPO"
fi

# Validate pipeline file
if [ ! -f "$PIPELINES_DIR/bms_document_generator.py" ]; then
    echo "❌ Pipeline file not found at $PIPELINES_DIR/bms_document_generator.py"
    exit 1
fi
echo "✅ Pipeline file validated"

# Install pipelines package
cd "$PIPELINES_REPO"
pip install -e . --quiet

echo "✅ Pipelines package installed"

echo ""
echo "Step 4: Installing document generation dependencies..."
pip install python-docx>=0.8.11 openpyxl>=3.1.0 python-pptx>=0.6.21

echo "✅ Dependencies installed"

echo ""
echo "Step 5: Creating Pipelines server startup script..."
cat > "$PIPELINES_DIR/start-server.sh" << 'SERVERSCRIPT'
#!/bin/bash
# Start Pipelines server in pod environment

export PIPELINES_DIR="/workspace/001-bms-agent/pipelines"
export PORT=9099
export HOST=0.0.0.0

cd /workspace/001-bms-agent

echo "Starting Pipelines server on port $PORT..."
echo "Pipelines directory: $PIPELINES_DIR"
echo ""

# Start server with nohup for background execution
nohup python3 -m pipelines.main \
    --host $HOST \
    --port $PORT \
    --pipelines-dir $PIPELINES_DIR \
    > pipelines/server.log 2>&1 &

PIPELINES_PID=$!
echo $PIPELINES_PID > pipelines/server.pid

echo "✅ Pipelines server started (PID: $PIPELINES_PID)"
echo ""
echo "Server Details:"
echo "  - Port: $PORT"
echo "  - API URL: http://localhost:$PORT"
echo "  - Default API Key: 0p3n-w3bu!"
echo "  - Pipelines Directory: $PIPELINES_DIR"
echo "  - Log file: pipelines/server.log"
echo "  - PID file: pipelines/server.pid"
echo ""
echo "View logs: tail -f pipelines/server.log"
echo "Stop server: kill $(cat pipelines/server.pid)"
SERVERSCRIPT

chmod +x "$PIPELINES_DIR/start-server.sh"

echo "✅ Startup script created"

echo ""
echo "Step 6: Starting Pipelines server..."
bash "$PIPELINES_DIR/start-server.sh"

echo ""
echo "Step 7: Waiting for server to start..."
sleep 3

# Check if server is running
if curl -s http://localhost:9099/health > /dev/null 2>&1; then
    echo "✅ Server health check passed"
else
    echo "⚠️  Server not responding yet (checking logs...)"
    if [ -f "$PIPELINES_DIR/server.log" ]; then
        echo "Last 10 lines of log:"
        tail -n 10 "$PIPELINES_DIR/server.log"
    fi
fi

echo ""
echo "=================================================="
echo "Next Steps:"
echo "=================================================="
echo "1. Connect to OpenWebUI:"
echo "   - Open: http://localhost:3000/admin"
echo "   - Go to: Settings → Connections"
echo "   - Click: + Add Connection"
echo "   - API URL: http://localhost:9099"
echo "   - API Key: 0p3n-w3bu!"
echo ""
echo "2. Install document generation Pipeline:"
echo "   - bash pipelines/install-document-pipeline.sh"
echo ""
echo "3. View server logs:"
echo "   - tail -f pipelines/server.log"
echo ""
echo "4. Stop server if needed:"
echo "   - kill \$(cat pipelines/server.pid)"
echo ""

echo "Environment:"
echo "  - Pipelines Dir: $PIPELINES_DIR"
echo "  - Output Dir: $OUTPUT_DIR"
echo "  - Server Log: $PIPELINES_DIR/server.log"
echo "  - Server PID: $PIPELINES_DIR/server.pid"
echo ""
