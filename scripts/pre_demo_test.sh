#!/bin/bash
# Pre-Demo System Test Script
# Run 30 minutes before recording to verify system readiness

echo "=================================================="
echo "BMS Agent Pre-Demo System Test"
echo "=================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

# Test 1: BMS API Health
echo "Test 1: BMS API Health"
echo -n "  Checking http://localhost:8000/health... "
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASS=$((PASS + 1))
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null | head -5
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  BMS API is not responding!"
    FAIL=$((FAIL + 1))
fi
echo ""

# Test 2: Qdrant Connection
echo "Test 2: Qdrant Vector Database"
echo -n "  Checking Qdrant collections... "
QDRANT_RESPONSE=$(curl -s http://localhost:6333/collections/nomad_bms_documents)
if echo "$QDRANT_RESPONSE" | grep -q '"status":"green"'; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASS=$((PASS + 1))
    POINTS=$(echo "$QDRANT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result']['points_count'])" 2>/dev/null)
    VECTORS=$(echo "$QDRANT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result']['vectors_count'])" 2>/dev/null)
    echo "  Points: $POINTS chunks"
    echo "  Vectors: $VECTORS embeddings"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Qdrant collection not healthy!"
    FAIL=$((FAIL + 1))
fi
echo ""

# Test 3: OpenWebUI Accessibility
echo "Test 3: OpenWebUI Interface"
echo -n "  Checking http://localhost:3000... "
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASS=$((PASS + 1))
    echo "  OpenWebUI is accessible"
else
    echo -e "${YELLOW}⚠ WARNING${NC}"
    echo "  OpenWebUI not accessible at localhost:3000"
    echo "  Make sure OpenWebUI is running before demo"
fi
echo ""

# Test 4: BMS Search Endpoint
echo "Test 4: Search API Endpoint"
echo -n "  Testing semantic search... "
SEARCH_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/search/semantic" \
    -H "Content-Type: application/json" \
    -d '{"query": "GDPR", "limit": 2}')
if echo "$SEARCH_RESPONSE" | grep -q '"results"'; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASS=$((PASS + 1))
    RESULT_COUNT=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['results']))" 2>/dev/null)
    echo "  Search returned $RESULT_COUNT results"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Search endpoint not working!"
    FAIL=$((FAIL + 1))
fi
echo ""

# Test 5: Performance Check
echo "Test 5: Response Time Check"
echo -n "  Measuring search latency... "
START_TIME=$(date +%s%N)
curl -s -X POST "http://localhost:8000/api/v1/search/hybrid" \
    -H "Content-Type: application/json" \
    -d '{"query": "procurement forms", "limit": 5}' > /dev/null
END_TIME=$(date +%s%N)
DURATION=$(( (END_TIME - START_TIME) / 1000000 ))
if [ $DURATION -lt 10000 ]; then
    echo -e "${GREEN}✓ PASS${NC} (${DURATION}ms)"
    PASS=$((PASS + 1))
    echo "  Response time acceptable for demo"
else
    echo -e "${YELLOW}⚠ SLOW${NC} (${DURATION}ms)"
    echo "  Response time >10s may be slow for demo"
fi
echo ""

# Summary
echo "=================================================="
echo "Test Summary"
echo "=================================================="
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ SYSTEM READY FOR DEMO RECORDING${NC}"
    echo ""
    echo "Next Steps:"
    echo "1. Open OpenWebUI at http://localhost:3000"
    echo "2. Verify BMS Agent Search tool is loaded"
    echo "3. Clear any existing chat history"
    echo "4. Follow demo script in docs/DEMO_RECORDING_GUIDE.md"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SYSTEM NOT READY${NC}"
    echo ""
    echo "Issues Found:"
    if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "  - BMS API not running (start with: bash scripts/start_api.sh)"
    fi
    if ! echo "$QDRANT_RESPONSE" | grep -q '"status":"green"'; then
        echo "  - Qdrant not healthy (check: curl http://localhost:6333/collections)"
    fi
    echo ""
    echo "Fix issues and run this test again before recording."
    exit 1
fi
