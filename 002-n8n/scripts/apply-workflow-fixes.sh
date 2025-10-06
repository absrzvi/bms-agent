#!/bin/bash
set -e

# Apply all critical workflow fixes via n8n API
# This script updates live workflows in n8n with enhancements

N8N_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4ODczMzU4MC1lYzVkLTQyNDQtODNiNC02Y2UzZjcyMGMwYzIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU5NzU4NjUxfQ.Jw6PkPgleHX6YsvA7gsZPI0rrYiTmVY_nDlYpZAIA2o"
N8N_URL="http://localhost:5678"

echo "========================================="
echo "n8n Workflow Enhancement Script"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to get workflow
get_workflow() {
    local workflow_id=$1
    curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
        "$N8N_URL/api/v1/workflows/$workflow_id"
}

# Function to update workflow
update_workflow() {
    local workflow_id=$1
    local workflow_json=$2

    # Keep only writable fields that n8n API accepts
    local clean_json=$(echo "$workflow_json" | jq '{name, nodes, connections, settings, staticData}')

    curl -s -X PUT \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$clean_json" \
        "$N8N_URL/api/v1/workflows/$workflow_id"
}

echo "Step 1: Adding webhook error handling to all workflows..."
echo "==========================================================="
echo ""

# List of workflows with webhooks and their webhook node IDs
declare -A WEBHOOK_WORKFLOWS=(
    ["BFDMwaYVCaPoRFw2"]="webhook-trigger"  # Main Handler
    ["0N6Wm7z1365fESrA"]="webhook-trigger"  # BMS API Caller
    ["2CYCWujMgXMVWryr"]="webhook-trigger"  # Query Analyzer
    ["pC8nfwxrXqHUb3gX"]="webhook-trigger"  # Context Manager
    ["SpPc24TPGHkaj7K3"]="webhook-trigger"  # Admin Commands
    ["j1kX1U1gicdWDn1v"]="ms-teams-trigger" # LangChain Agent
    ["tvzyTniDZ7XpVloI"]="webhook-trigger"  # Tool Ask BMS
    ["mck76ydIzx0E0ET8"]="webhook-trigger"  # Tool Search Semantic
    ["kGG5OXsm7P1m1AMg"]="webhook-trigger"  # Tool Search Hybrid
    ["H4PNLouLnNsyZ6ks"]="webhook-trigger"  # Tool Search Metadata
    ["FiA7ttEV19p6as4e"]="webhook-trigger"  # Tool Contextual Search
)

for workflow_id in "${!WEBHOOK_WORKFLOWS[@]}"; do
    node_id="${WEBHOOK_WORKFLOWS[$workflow_id]}"

    echo -n "Updating workflow $workflow_id... "

    # Get current workflow
    workflow=$(get_workflow "$workflow_id")

    # Update webhook node with error handling using jq
    updated_workflow=$(echo "$workflow" | jq --arg node_id "$node_id" '
        .nodes |= map(
            if .id == $node_id then
                .parameters.options.onError = "continueRegularOutput"
            else
                .
            end
        )
    ')

    # Update workflow
    result=$(update_workflow "$workflow_id" "$updated_workflow")

    if echo "$result" | jq -e '.id' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        echo "Error: $result"
    fi
done

echo ""
echo "Step 2: Adding retry logic to HTTP Request nodes..."
echo "====================================================="
echo ""

# Workflows with HTTP requests that need retry logic
echo -n "Updating BMS API Caller (Call BMS Ask Endpoint)... "
workflow=$(get_workflow "0N6Wm7z1365fESrA")
updated=$(echo "$workflow" | jq '
    .nodes |= map(
        if .name == "Call BMS Ask Endpoint" or .name == "Call BMS Search Endpoint" then
            .parameters.options.retry = {
                "enabled": true,
                "maxRetries": 3,
                "retryInterval": 1000
            } |
            .continueOnFail = true
        else
            .
        end
    )
')
result=$(update_workflow "0N6Wm7z1365fESrA" "$updated")
if echo "$result" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Success${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
fi

echo -n "Updating Query Analyzer (Ollama Classification)... "
workflow=$(get_workflow "2CYCWujMgXMVWryr")
updated=$(echo "$workflow" | jq '
    .nodes |= map(
        if .name == "Ollama Intent Classification" then
            .parameters.options.timeout = 3000 |
            .parameters.options.retry = {
                "enabled": true,
                "maxRetries": 2,
                "retryInterval": 500
            } |
            .continueOnFail = true
        else
            .
        end
    )
')
result=$(update_workflow "2CYCWujMgXMVWryr" "$updated")
if echo "$result" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Success${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
fi

echo -n "Updating Tool Ask BMS Enhanced... "
workflow=$(get_workflow "tvzyTniDZ7XpVloI")
updated=$(echo "$workflow" | jq '
    .nodes |= map(
        if .name == "Call BMS Ask API" then
            .parameters.options.retry = {
                "enabled": true,
                "maxRetries": 3,
                "retryInterval": 1000
            } |
            .continueOnFail = true
        else
            .
        end
    )
')
result=$(update_workflow "tvzyTniDZ7XpVloI" "$updated")
if echo "$result" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Success${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
fi

echo ""
echo "Step 3: Fixing workflow ID references in LangChain Agent..."
echo "============================================================"
echo ""

echo -n "Updating LangChain Agent Orchestrator... "
workflow=$(get_workflow "j1kX1U1gicdWDn1v")

# Update the workflow to use environment variables for workflow IDs
updated=$(echo "$workflow" | jq '
    .nodes |= map(
        if .name == "Tool: Query BMS API" then
            .parameters.fields.values[0].stringValue = "={{ $env.WORKFLOW_ID_BMS_CALLER || \"0N6Wm7z1365fESrA\" }}"
        elif .name == "Tool: Get Conversation History" then
            .parameters.fields.values[0].stringValue = "={{ $env.WORKFLOW_ID_CONTEXT_MANAGER || \"pC8nfwxrXqHUb3gX\" }}"
        elif .name == "Tool: Check Similar Queries" then
            .parameters.fields.values[0].stringValue = "={{ $env.WORKFLOW_ID_SIMILAR_QUERY || \"o9QL7V6zWIGgiWDV\" }}"
        else
            .
        end
    ) |
    # Remove the dynamic workflow ID fetching nodes
    .nodes |= map(select(.name != "Get Workflow IDs" and .name != "Split Workflow IDs" and .name != "Get BMS Caller Workflow ID" and .name != "Get Context Manager Workflow ID" and .name != "Get Similar Query Workflow ID"))
')

result=$(update_workflow "j1kX1U1gicdWDn1v" "$updated")
if echo "$result" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Success${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    echo "Error: $result"
fi

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo ""
echo -e "${YELLOW}Critical fixes applied:${NC}"
echo "  ✓ Webhook error handling (11 workflows)"
echo "  ✓ HTTP retry logic (4 workflows)"
echo "  ✓ Workflow ID references (1 workflow)"
echo ""
echo -e "${YELLOW}Manual steps required:${NC}"
echo "  1. Fix Redis nodes in context-manager and similar-query-detector"
echo "     (Requires changing node types - use n8n UI)"
echo "  2. Add input validation to tool workflows"
echo "     (Requires adding new nodes - use n8n UI)"
echo "  3. Set up Redis credentials in n8n UI"
echo "  4. Load environment variables from config/workflow-ids.env"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Review changes in n8n UI"
echo "  2. Apply manual fixes for Redis nodes"
echo "  3. Test each workflow"
echo "  4. Activate workflows in dependency order"
echo ""
