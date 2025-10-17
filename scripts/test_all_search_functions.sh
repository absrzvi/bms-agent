#!/bin/bash
# Test All 13 Operational Search Functions
# Run before demo recording to verify all endpoints work

echo "=================================================="
echo "BMS Agent - Testing All Search Functions"
echo "=================================================="
echo ""

API_BASE="http://localhost:8000/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0

test_endpoint() {
    local name=$1
    local endpoint=$2
    local payload=$3
    
    echo -e "${BLUE}Testing: $name${NC}"
    echo -n "  Endpoint: $endpoint... "
    
    RESPONSE=$(curl -s -X POST "$API_BASE$endpoint" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    if echo "$RESPONSE" | grep -q '"results"'; then
        COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('results', [])))" 2>/dev/null)
        echo -e "${GREEN}✓ PASS${NC} ($COUNT results)"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Response: $(echo "$RESPONSE" | head -c 100)"
        FAIL=$((FAIL + 1))
    fi
    echo ""
}

# ==================== CORE SEARCH FUNCTIONS ====================
echo "=== CORE SEARCH FUNCTIONS ==="
echo ""

test_endpoint \
    "1. search_semantic()" \
    "/search/semantic" \
    '{"query": "GDPR compliance documents", "limit": 3}'

test_endpoint \
    "2. search_hybrid()" \
    "/search/hybrid" \
    '{"query": "business continuity planning railway", "limit": 3}'

# Note: search_smart() is client-side (uses hybrid endpoint)
echo -e "${BLUE}Testing: 3. search_smart()${NC}"
echo "  Note: Client-side logic, uses /search/hybrid"
echo -e "  ${GREEN}✓ N/A${NC} (tool-side implementation)"
echo ""

# ==================== ADVANCED SEARCH (T036) ====================
echo "=== ADVANCED SEARCH (T036 - NEW) ==="
echo ""

test_endpoint \
    "4. search_contextual()" \
    "/search/contextual" \
    '{"query": "safety assessment requirements", "limit": 3, "include_context": true, "expand_parents": true}'

test_endpoint \
    "5. search_rerank()" \
    "/search/rerank" \
    '{"query": "vendor approval process", "limit": 3, "rerank_top_k": 20}'

# ==================== FILTERED SEARCH FUNCTIONS ====================
echo "=== FILTERED SEARCH FUNCTIONS ==="
echo ""

test_endpoint \
    "6. search_by_department()" \
    "/search/hybrid" \
    '{"query": "training procedures", "limit": 3, "filters": {"department": "HUMR"}}'

test_endpoint \
    "7. search_by_document_type()" \
    "/search/semantic" \
    '{"query": "procurement templates", "limit": 3, "filters": {"document_type": "xlsx"}}'

test_endpoint \
    "8. search_by_fleet_type()" \
    "/search/hybrid" \
    '{"query": "maintenance procedures", "limit": 3, "filters": {"fleet_type": "Railjet"}}'

test_endpoint \
    "9. search_by_standard()" \
    "/search/hybrid" \
    '{"query": "electronic equipment requirements", "limit": 3, "filters": {"standard_compliance": "EN50155"}}'

test_endpoint \
    "10. search_with_context()" \
    "/search/hybrid" \
    '{"query": "project risk management", "limit": 3, "filters": {"has_context": true}}'

test_endpoint \
    "11. search_high_quality()" \
    "/search/hybrid" \
    '{"query": "procurement compliance requirements", "limit": 3, "filters": {"quality_score_min": 0.85}}'

test_endpoint \
    "12. search_by_train_id()" \
    "/search/hybrid" \
    '{"query": "technical specifications", "limit": 3, "filters": {"train_id": "RJ-4001"}}'

test_endpoint \
    "13. search_by_component()" \
    "/search/hybrid" \
    '{"query": "maintenance schedule", "limit": 3, "filters": {"network_component": "HVAC"}}'

# ==================== SUMMARY ====================
echo "=================================================="
echo "Test Summary"
echo "=================================================="
echo -e "Passed: ${GREEN}$PASS${NC} / 12 (search_smart excluded)"
echo -e "Failed: ${RED}$FAIL${NC}"
echo ""

TESTED=$((PASS + FAIL))
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ ALL SEARCH FUNCTIONS WORKING${NC}"
    echo ""
    echo "You can now:"
    echo "1. Record comprehensive demo (10-15 min)"
    echo "2. Follow: docs/COMPREHENSIVE_DEMO_GUIDE.md"
    echo "3. Showcase all 13 operational functions"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SOME FUNCTIONS FAILED${NC}"
    echo ""
    echo "Failed endpoints may indicate:"
    echo "- API not fully started"
    echo "- Qdrant not ready"
    echo "- Missing metadata in corpus"
    echo ""
    echo "Review errors above and fix before demo recording."
    exit 1
fi
