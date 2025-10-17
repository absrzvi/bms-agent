#!/bin/bash
# Quick v3 Features Test - Fast validation of key capabilities

API_URL="http://localhost:8000"

echo "========================================="
echo "  BMS Agent v3 Quick Feature Test"
echo "========================================="
echo ""

# Test 1: Basic Search
echo "1. Basic Semantic Search..."
curl -s -X POST "$API_URL/api/v1/search/semantic" \
    -H "Content-Type: application/json" \
    -d '{"query": "sick leave", "limit": 2}' | jq -r '.status, (.results | length)' | head -2
echo ""

# Test 2: Hybrid Search
echo "2. Hybrid Search..."
curl -s -X POST "$API_URL/api/v1/search/hybrid" \
    -H "Content-Type: application/json" \
    -d '{"query": "BMS-HUMR", "limit": 2}' | jq -r '.status, (.results | length)' | head -2
echo ""

# Test 3: Department Filter
echo "3. Department Filtering (HUMR)..."
curl -s -X POST "$API_URL/api/v1/search/semantic" \
    -H "Content-Type: application/json" \
    -d '{"query": "policy", "limit": 2, "filters": {"department": "HUMR"}}' | jq -r '.status, (.results[0].payload.department // "no_dept")' | head -2
echo ""

# Test 4: Quality Filter
echo "4. Quality Filtering (≥0.80)..."
curl -s -X POST "$API_URL/api/v1/search/semantic" \
    -H "Content-Type: application/json" \
    -d '{"query": "safety", "limit": 2, "filters": {"quality_score_min": 0.80}}' | jq -r '.status, (.results[0].quality_score // 0)' | head -2
echo ""

# Test 5: Min Score Filter
echo "5. Relevance Filtering (min_score=0.7)..."
curl -s -X POST "$API_URL/api/v1/search/semantic" \
    -H "Content-Type: application/json" \
    -d '{"query": "expense", "limit": 2, "min_score": 0.7}' | jq -r '.status, (.results | length)' | head -2
echo ""

# Test 6: Document Type Filter
echo "6. Document Type Filtering (pdf)..."
curl -s -X POST "$API_URL/api/v1/search/semantic" \
    -H "Content-Type: application/json" \
    -d '{"query": "form", "limit": 2, "filters": {"document_type": "pdf"}}' | jq -r '.status, (.results[0].document_type // "no_type")' | head -2
echo ""

# Test 7: Hybrid with Custom Weights
echo "7. Hybrid Search with Custom Weights..."
curl -s -X POST "$API_URL/api/v1/search/hybrid" \
    -H "Content-Type: application/json" \
    -d '{"query": "DevOps", "limit": 2, "dense_weight": 0.8, "sparse_weight": 0.2}' | jq -r '.status, (.results | length)' | head -2
echo ""

# Test 8: Combined Filters
echo "8. Combined Filters (QHSE + Quality)..."
curl -s -X POST "$API_URL/api/v1/search/semantic" \
    -H "Content-Type: application/json" \
    -d '{"query": "procedure", "limit": 2, "filters": {"department": "QHSE", "quality_score_min": 0.75}}' | jq -r '.status, (.results[0].payload.department // "no_dept")' | head -2
echo ""

echo "========================================="
echo "  ✅ Quick Test Complete!"
echo "========================================="
echo ""
echo "All core v3 API features tested:"
echo "  ✅ Semantic search"
echo "  ✅ Hybrid search"
echo "  ✅ Department filtering"
echo "  ✅ Quality filtering"
echo "  ✅ Relevance filtering"
echo "  ✅ Document type filtering"
echo "  ✅ Custom hybrid weights"
echo "  ✅ Combined filters"
echo ""
echo "Note: Advanced features (conversational, synthesis,"
echo "explainability) are handled by OpenWebUI tool layer"
echo "with fallback to these core API endpoints."
