#!/bin/bash
# Import BMS AI Agent Simplified Workflow to n8n
# Usage: ./import-workflow.sh

set -e

WORKFLOW_FILE="/workspace/002-n8n/workflows/bms-ai-simple-direct.json"
N8N_API_URL="${N8N_API_URL:-http://localhost:5678}"
N8N_API_KEY="${N8N_API_KEY:-}"

echo "========================================="
echo "BMS AI Agent Workflow Import"
echo "========================================="
echo ""
echo "Workflow: bms-ai-simple-direct.json"
echo "n8n API: $N8N_API_URL"
echo ""

# Check if workflow file exists
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ Error: Workflow file not found: $WORKFLOW_FILE"
    exit 1
fi

echo "✅ Workflow file found"
echo ""

# Check if n8n is running
echo "Checking n8n availability..."
if curl -s -f "$N8N_API_URL/healthz" > /dev/null 2>&1; then
    echo "✅ n8n is running at $N8N_API_URL"
else
    echo "❌ Error: Cannot reach n8n at $N8N_API_URL"
    echo ""
    echo "To start n8n:"
    echo "  cd /workspace/n8n"
    echo "  npm start"
    echo ""
    exit 1
fi

echo ""
echo "========================================="
echo "Import Options"
echo "========================================="
echo ""
echo "Option 1: Import via n8n UI (Recommended)"
echo "  1. Open n8n: $N8N_API_URL"
echo "  2. Click 'Workflows' → 'Import from File'"
echo "  3. Select: $WORKFLOW_FILE"
echo "  4. Click 'Import'"
echo ""
echo "Option 2: Import via API"
if [ -z "$N8N_API_KEY" ]; then
    echo "  ⚠️  N8N_API_KEY not set. Export it first:"
    echo "     export N8N_API_KEY='your-api-key-here'"
    echo ""
    echo "  To get your API key:"
    echo "    1. Open n8n UI: $N8N_API_URL"
    echo "    2. Go to Settings → API"
    echo "    3. Create new API key"
    echo ""
else
    echo "  Running API import..."
    echo ""

    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$N8N_API_URL/api/v1/workflows" \
      -H "Content-Type: application/json" \
      -H "X-N8N-API-KEY: $N8N_API_KEY" \
      --data @"$WORKFLOW_FILE")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
        WORKFLOW_ID=$(echo "$BODY" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        echo "✅ Workflow imported successfully!"
        echo ""
        echo "Workflow ID: $WORKFLOW_ID"
        echo "Workflow URL: $N8N_API_URL/workflow/$WORKFLOW_ID"
        echo "Webhook URL: $N8N_API_URL/webhook-test/bms-ai-direct"
        echo ""
        echo "Next steps:"
        echo "  1. Open the workflow in n8n UI"
        echo "  2. Click 'Activate' toggle"
        echo "  3. Test via Chat button on Chat Trigger node"
        echo ""
    else
        echo "❌ Import failed with HTTP $HTTP_CODE"
        echo ""
        echo "Response:"
        echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
        echo ""
        echo "Try Option 1 (UI import) instead."
        exit 1
    fi
fi

echo "========================================="
echo "Testing the Workflow"
echo "========================================="
echo ""
echo "After activating in n8n UI, test with:"
echo ""
echo "curl -X POST $N8N_API_URL/webhook-test/bms-ai-direct \\\\"
echo "  -H 'Content-Type: application/json' \\\\"
echo "  -d '{"
echo "    \"chatInput\": \"What are emergency brake procedures?\","
echo "    \"sessionId\": \"test-001\""
echo "  }'"
echo ""
echo "========================================="
echo "Prerequisites"
echo "========================================="
echo ""
echo "Ensure BMS API is running:"
echo "  curl http://localhost:8000/health"
echo ""
echo "If not running, start it:"
echo "  cd /workspace/001-bms-agent"
echo "  source /workspace/bms-api-venv/bin/activate"
echo "  uvicorn api.main:app --host 0.0.0.0 --port 8000 &"
echo ""
echo "========================================="

exit 0
