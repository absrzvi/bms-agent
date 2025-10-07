#!/bin/bash
# n8n Startup Script for MS Teams Bot Integration
# Starts n8n with persistent storage in /workspace/n8n

set -e

echo "=== Starting n8n for MS Teams Bot ===="

# Load n8n environment configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../config/n8n.env"

if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "⚠️  Warning: Environment file not found at $ENV_FILE"
    echo "   Using default settings..."
    export N8N_USER_FOLDER=/workspace/n8n
    export N8N_HOST=0.0.0.0
    export N8N_PORT=5678
    export N8N_PROTOCOL=http
    export WEBHOOK_URL=http://localhost:5678/
    export N8N_PUSH_BACKEND=websocket
    export N8N_DIAGNOSTICS_ENABLED=false
fi

echo ""

# Check if n8n is already running
if lsof -Pi :5678 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  n8n is already running on port 5678"
    echo "   Use 'pkill -f n8n' to stop it first"
    exit 1
fi

# Start n8n
echo "Starting n8n..."
echo "Access the UI at: $WEBHOOK_URL"
echo ""
echo "Press Ctrl+C to stop n8n"
echo ""

# Start n8n (will run in foreground)
/workspace/n8n/node_modules/.bin/n8n start
