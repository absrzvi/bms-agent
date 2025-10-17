#!/bin/bash
# Install BMS Document Generator Pipeline (Pod Environment)
# Copies pipeline and installs dependencies without Docker

set -e

echo "=================================================="
echo "Installing BMS Document Generator Pipeline (Pod)"
echo "=================================================="
echo ""

PIPELINES_DIR="/workspace/001-bms-agent/pipelines"
OUTPUT_DIR="/workspace/001-bms-agent/pipelines/output"

# Check if Pipelines server process is running
if [ ! -f "$PIPELINES_DIR/server.pid" ]; then
    echo "⚠️  Pipelines server PID file not found"
    echo ""
    echo "Start it first with:"
    echo "  bash pipelines/deploy-pipelines-server.sh"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Verifying pipeline file exists..."
if [ ! -f "$PIPELINES_DIR/bms_document_generator.py" ]; then
    echo "❌ Pipeline file not found: $PIPELINES_DIR/bms_document_generator.py"
    exit 1
fi
echo "✅ Pipeline file found"

echo ""
echo "Step 2: Installing Python dependencies..."
pip install python-docx>=0.8.11 openpyxl>=3.1.0 python-pptx>=0.6.21 --quiet

echo "✅ Dependencies installed"

echo ""
echo "Step 3: Creating output directory..."
mkdir -p "$OUTPUT_DIR"
chmod 755 "$OUTPUT_DIR"
echo "✅ Output directory created: $OUTPUT_DIR"

echo ""
echo "Step 4: Verifying dependencies..."
python3 << 'PYCHECK'
import sys
try:
    import docx
    print("  ✅ python-docx installed")
except ImportError:
    print("  ❌ python-docx not available")
    sys.exit(1)

try:
    import openpyxl
    print("  ✅ openpyxl installed")
except ImportError:
    print("  ❌ openpyxl not available")
    sys.exit(1)

try:
    import pptx
    print("  ✅ python-pptx installed")
except ImportError:
    print("  ❌ python-pptx not available")
    sys.exit(1)
PYCHECK

echo ""
echo "Step 5: Restarting Pipelines server to load new pipeline..."
if [ -f "$PIPELINES_DIR/server.pid" ]; then
    OLD_PID=$(cat "$PIPELINES_DIR/server.pid")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Stopping old server (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2
    fi
fi

echo "Starting Pipelines server..."
bash "$PIPELINES_DIR/start-server.sh"

echo ""
echo "Waiting for server to restart..."
sleep 3

echo ""
echo "Step 6: Verifying pipeline installation..."
if curl -s http://localhost:9099/health > /dev/null 2>&1; then
    echo "✅ Pipelines server is running"
    
    # Try to list available pipelines
    echo ""
    echo "Checking available pipelines..."
    PIPELINES_RESPONSE=$(curl -s http://localhost:9099/pipelines 2>/dev/null)
    if [ -n "$PIPELINES_RESPONSE" ]; then
        echo "$PIPELINES_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "  Response: $PIPELINES_RESPONSE"
    fi
else
    echo "⚠️  Server not responding yet (checking logs...)"
    if [ -f "$PIPELINES_DIR/server.log" ]; then
        echo ""
        echo "Last 20 lines of server log:"
        tail -n 20 "$PIPELINES_DIR/server.log"
    fi
fi

echo ""
echo "=================================================="
echo "✅ Installation Complete"
echo "=================================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Connect Pipeline to OpenWebUI:"
echo "   - Open: http://localhost:3000/admin"
echo "   - Go to: Settings → Connections"
echo "   - Click: + Add Connection"
echo "   - API URL: http://localhost:9099"
echo "   - API Key: 0p3n-w3bu!"
echo "   - Click: Save"
echo ""
echo "2. Enable Pipeline for your model:"
echo "   - Go to: Workspace → Models"
echo "   - Select your model → Edit"
echo "   - Scroll to 'Pipelines' section"
echo "   - Enable 'BMS Document Generator'"
echo "   - Click: Save"
echo ""
echo "3. Test document generation:"
echo "   - bash pipelines/test-document-generation.sh"
echo ""
echo "4. View generated documents:"
echo "   - ls -lh $OUTPUT_DIR"
echo ""
echo "Pipeline Files:"
echo "  - Pipeline: $PIPELINES_DIR/bms_document_generator.py"
echo "  - Output: $OUTPUT_DIR"
echo "  - Server Log: $PIPELINES_DIR/server.log"
echo "  - Server PID: $PIPELINES_DIR/server.pid"
echo ""
echo "Commands:"
echo "  - View logs: tail -f $PIPELINES_DIR/server.log"
echo "  - Stop server: kill \$(cat $PIPELINES_DIR/server.pid)"
echo "  - Restart: bash pipelines/install-document-pipeline.sh"
echo ""
