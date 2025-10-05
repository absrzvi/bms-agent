#!/bin/bash
# Deploy OpenWebUI Pipelines Server for Document Generation
# Based on research in docs/openwebui-doc-gen.md

set -e

echo "=================================================="
echo "OpenWebUI Pipelines Server Deployment"
echo "=================================================="
echo ""

# Check if Pipelines container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^pipelines$"; then
    echo "⚠️  Pipelines container already exists"
    echo ""
    read -p "Remove existing container and redeploy? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping and removing existing container..."
        docker stop pipelines 2>/dev/null || true
        docker rm pipelines 2>/dev/null || true
    else
        echo "Keeping existing container. Exiting."
        exit 0
    fi
fi

echo "Step 1: Pulling Pipelines Docker image..."
docker pull ghcr.io/open-webui/pipelines:main

echo ""
echo "Step 2: Creating Pipelines volume for persistence..."
docker volume create pipelines 2>/dev/null || echo "Volume already exists"

echo ""
echo "Step 3: Starting Pipelines server..."
docker run -d \
    -p 9099:9099 \
    --add-host=host.docker.internal:host-gateway \
    -v pipelines:/app/pipelines \
    -e PIPELINES_DIR=/app/pipelines \
    --name pipelines \
    --restart always \
    ghcr.io/open-webui/pipelines:main

echo ""
echo "Step 4: Waiting for Pipelines server to start..."
sleep 5

# Check if server is running
if docker ps --format '{{.Names}}' | grep -q "^pipelines$"; then
    echo "✅ Pipelines server started successfully"
    echo ""
    echo "Server Details:"
    echo "  - Container: pipelines"
    echo "  - Port: 9099"
    echo "  - API URL: http://localhost:9099"
    echo "  - Default API Key: 0p3n-w3bu!"
    echo "  - Pipelines Directory: /app/pipelines (inside container)"
    echo "  - Volume: pipelines"
    echo ""
    echo "Step 5: Testing server connectivity..."
    
    # Test health endpoint
    if curl -s http://localhost:9099/health > /dev/null 2>&1; then
        echo "✅ Server health check passed"
    else
        echo "⚠️  Server not responding yet (may need a few more seconds)"
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
    echo "2. Create document generation Pipeline:"
    echo "   - Run: pipelines/create-document-pipeline.sh"
    echo ""
    echo "3. View logs if needed:"
    echo "   - docker logs pipelines -f"
    echo ""
else
    echo "❌ Failed to start Pipelines server"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check logs: docker logs pipelines"
    echo "  - Check port availability: lsof -i :9099"
    echo "  - Verify Docker is running: docker ps"
    exit 1
fi
