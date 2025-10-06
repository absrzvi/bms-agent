#!/bin/bash
# Deploy n8n Workflows (T021)
# Imports all workflow JSON files to n8n instance

set -e

N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_API_KEY="${N8N_API_KEY:-}"
WORKFLOWS_DIR="/workspace/002-n8n/workflows"

echo "=== n8n Workflow Deployment ==="
echo "n8n URL: $N8N_URL"
echo "Workflows directory: $WORKFLOWS_DIR"
echo ""

# Check if n8n is running
if ! curl -s "$N8N_URL/healthz" > /dev/null 2>&1; then
  echo "ERROR: n8n is not running at $N8N_URL"
  echo "Start n8n first: ./scripts/start-n8n.sh"
  exit 1
fi

echo "✓ n8n is running"

# Check if workflows directory exists
if [ ! -d "$WORKFLOWS_DIR" ]; then
  echo "ERROR: Workflows directory not found: $WORKFLOWS_DIR"
  exit 1
fi

# Count workflow files
WORKFLOW_COUNT=$(find "$WORKFLOWS_DIR" -name "*.json" | wc -l)
echo "Found $WORKFLOW_COUNT workflow files"
echo ""

# Deploy each workflow
for workflow_file in "$WORKFLOWS_DIR"/*.json; do
  if [ -f "$workflow_file" ]; then
    workflow_name=$(basename "$workflow_file" .json)
    echo "Deploying: $workflow_name"
    
    # Import workflow using n8n CLI
    if command -v n8n > /dev/null 2>&1; then
      n8n import:workflow --input="$workflow_file" || echo "  ⚠ Import failed (workflow may already exist)"
    else
      echo "  ℹ Manual import required - use n8n UI to import $workflow_file"
    fi
  fi
done

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Open n8n UI: $N8N_URL"
echo "2. Activate each workflow (toggle switch)"
echo "3. Configure credentials if needed"
echo "4. Test webhook endpoint"
echo ""
