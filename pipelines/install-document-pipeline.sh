#!/bin/bash
# Install BMS Document Generator Pipeline
# Copies pipeline to Pipelines server and installs dependencies

set -e

echo "=================================================="
echo "Installing BMS Document Generator Pipeline"
echo "=================================================="
echo ""

# Check if Pipelines container is running
if ! docker ps --format '{{.Names}}' | grep -q "^pipelines$"; then
    echo "❌ Pipelines container not running"
    echo ""
    echo "Start it first with:"
    echo "  bash pipelines/deploy-pipelines-server.sh"
    exit 1
fi

echo "Step 1: Copying pipeline file to container..."
docker cp pipelines/bms_document_generator.py pipelines:/app/pipelines/

echo ""
echo "Step 2: Installing Python dependencies in container..."
docker exec pipelines pip install python-docx>=0.8.11 openpyxl>=3.1.0 python-pptx>=0.6.21

echo ""
echo "Step 3: Creating output directory..."
docker exec pipelines mkdir -p /app/pipelines/output

echo ""
echo "Step 4: Restarting Pipelines server to load new pipeline..."
docker restart pipelines

echo ""
echo "Waiting for server to restart..."
sleep 5

echo ""
echo "Step 5: Verifying pipeline installation..."
if curl -s http://localhost:9099/health > /dev/null 2>&1; then
    echo "✅ Pipelines server is running"
    
    # List available pipelines
    echo ""
    echo "Available pipelines:"
    curl -s http://localhost:9099/pipelines 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  (Could not fetch pipeline list)"
else
    echo "⚠️  Server not responding yet"
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
echo "   - docker exec pipelines ls -lh /app/pipelines/output"
echo ""
echo "Pipeline Files:"
echo "  - Container: /app/pipelines/bms_document_generator.py"
echo "  - Output: /app/pipelines/output/"
echo "  - Logs: docker logs pipelines -f"
echo ""
