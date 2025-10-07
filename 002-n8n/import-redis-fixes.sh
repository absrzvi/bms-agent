#!/bin/bash
# Automated workflow import script for Redis fixes

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}n8n Workflow Import - Redis Fixes${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if API key is already set
if [ -z "$N8N_API_KEY" ]; then
    echo -e "${YELLOW}Step 1: Create n8n API Key${NC}"
    echo ""
    echo "To import workflows via API, you need an n8n API key."
    echo ""
    echo "Please follow these steps:"
    echo "  1. Open n8n: http://localhost:5678"
    echo "  2. Click your profile → Settings → API"
    echo "  3. Click 'Create an API key'"
    echo "  4. Name it: mcp-import"
    echo "  5. Copy the generated key"
    echo ""
    echo -n "Paste your n8n API key here: "
    read -r API_KEY
    export N8N_API_KEY="$API_KEY"
    echo ""
    echo -e "${GREEN}✓ API key set${NC}"
else
    echo -e "${GREEN}✓ API key already configured${NC}"
fi

export N8N_API_URL="http://localhost:5678"

# Verify n8n is running
echo ""
echo -e "${BLUE}Step 2: Verifying n8n is running...${NC}"
if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
    echo -e "${GREEN}✓ n8n is running${NC}"
else
    echo -e "${RED}✗ n8n is not running${NC}"
    echo "Please start n8n first"
    exit 1
fi

# Verify API key works
echo ""
echo -e "${BLUE}Step 3: Verifying API key...${NC}"
RESPONSE=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" http://localhost:5678/api/v1/workflows)
if echo "$RESPONSE" | grep -q "data"; then
    WORKFLOW_COUNT=$(echo "$RESPONSE" | jq '.data | length')
    echo -e "${GREEN}✓ API key valid (found $WORKFLOW_COUNT workflows)${NC}"
else
    echo -e "${RED}✗ API key invalid or n8n API not accessible${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

# Import Context Manager
echo ""
echo -e "${BLUE}Step 4: Importing Context Manager workflow...${NC}"
RESULT=$(curl -s -X PUT http://localhost:5678/api/v1/workflows/pC8nfwxrXqHUb3gX \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/workspace/002-n8n/workflows/context-manager.json)

if echo "$RESULT" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Context Manager imported successfully${NC}"
    echo "  ID: $(echo "$RESULT" | jq -r '.id')"
    echo "  Name: $(echo "$RESULT" | jq -r '.name')"
else
    echo -e "${RED}✗ Import failed${NC}"
    echo "Response: $(echo "$RESULT" | jq '.')"
    exit 1
fi

# Import Similar Query Detector
echo ""
echo -e "${BLUE}Step 5: Importing Similar Query Detector workflow...${NC}"
RESULT=$(curl -s -X PUT http://localhost:5678/api/v1/workflows/o9QL7V6zWIGgiWDV \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/workspace/002-n8n/workflows/similar-query-detector.json)

if echo "$RESULT" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Similar Query Detector imported successfully${NC}"
    echo "  ID: $(echo "$RESULT" | jq -r '.id')"
    echo "  Name: $(echo "$RESULT" | jq -r '.name')"
else
    echo -e "${RED}✗ Import failed${NC}"
    echo "Response: $(echo "$RESULT" | jq '.')"
    exit 1
fi

# Success summary
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✓ Import Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT: Manual Step Required${NC}"
echo ""
echo "The workflows have been imported, but you still need to:"
echo "  1. Open n8n: http://localhost:5678"
echo "  2. Open 'Context Manager' workflow"
echo "  3. Click each Redis node (3 total)"
echo "  4. Select 'Redis Local' credentials"
echo "  5. Save workflow"
echo ""
echo "  6. Open 'Similar Query Detector' workflow"
echo "  7. Click each Redis node (2 total)"
echo "  8. Select 'Redis Local' credentials"
echo "  9. Save workflow"
echo ""
echo "This is required because n8n doesn't import credentials for security."
echo ""
echo "After that, run:"
echo "  ./test-redis-fixes.sh"
echo ""
echo -e "${GREEN}Done!${NC}"
