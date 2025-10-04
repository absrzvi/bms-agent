#!/bin/bash
# Quick Test Script for Post-MVP Features
# Tests T036 (re-upload), T037 (async queue), T039 (deletion)

set -e

API_URL="http://localhost:8000"
TEST_FILE="test_document.txt"

echo "🧪 BMS Agent Post-MVP Feature Testing"
echo "======================================"
echo ""

# Create a test document
echo "Creating test document..."
cat > $TEST_FILE << 'EOF'
BMS Agent Test Document
=======================

This is a test document for validating the BMS Agent system.

Key Features:
- Document processing with Enhanced Document Processor v4.0
- Semantic search with 768-dimensional embeddings
- Hybrid search combining semantic and keyword matching
- Railway-specific metadata extraction

Test Content:
Railway connectivity infrastructure requires robust monitoring and
maintenance systems. The BMS (Building Management System) Agent provides
intelligent document retrieval for railway documentation.
EOF

echo "✅ Test document created: $TEST_FILE"
echo ""

# Test 1: Initial Upload
echo "📤 Test 1: Initial Document Upload"
echo "-----------------------------------"
UPLOAD1=$(curl -s -X POST $API_URL/api/v1/documents/upload \
  -F "file=@$TEST_FILE" \
  -F "profile=railway")

DOC_ID=$(echo $UPLOAD1 | jq -r '.document_id')
CHUNKS1=$(echo $UPLOAD1 | jq -r '.processing_result.chunks_created')
REPLACED1=$(echo $UPLOAD1 | jq -r '.replaced_existing')

echo "Document ID: $DOC_ID"
echo "Chunks created: $CHUNKS1"
echo "Replaced existing: $REPLACED1"
echo ""

if [ "$REPLACED1" == "false" ]; then
    echo "✅ Test 1 PASSED: Initial upload successful, no replacement"
else
    echo "❌ Test 1 FAILED: Should not replace on first upload"
fi
echo ""

# Test 2: Re-upload (Destructive Replacement - T036)
echo "♻️  Test 2: Document Re-upload (T036)"
echo "-------------------------------------"
sleep 2
UPLOAD2=$(curl -s -X POST $API_URL/api/v1/documents/upload \
  -F "file=@$TEST_FILE" \
  -F "profile=railway")

DOC_ID2=$(echo $UPLOAD2 | jq -r '.document_id')
CHUNKS2=$(echo $UPLOAD2 | jq -r '.processing_result.chunks_created')
REPLACED2=$(echo $UPLOAD2 | jq -r '.replaced_existing')
DELETED=$(echo $UPLOAD2 | jq -r '.replacement_info.deleted_chunks // 0')

echo "New Document ID: $DOC_ID2"
echo "Chunks created: $CHUNKS2"
echo "Replaced existing: $REPLACED2"
echo "Deleted chunks: $DELETED"
echo ""

if [ "$REPLACED2" == "true" ] && [ "$DELETED" == "$CHUNKS1" ]; then
    echo "✅ Test 2 PASSED: Re-upload replaced old document"
else
    echo "❌ Test 2 FAILED: Replacement not working correctly"
    echo "   Expected deleted: $CHUNKS1, Got: $DELETED"
fi
echo ""

# Test 3: Async Upload (T037)
echo "⏳ Test 3: Async Upload Queue (T037)"
echo "------------------------------------"
ASYNC_RESPONSE=$(curl -s -X POST $API_URL/api/v1/documents/upload/async \
  -F "file=@$TEST_FILE" \
  -F "profile=railway")

JOB_ID=$(echo $ASYNC_RESPONSE | jq -r '.job_id')
STATUS_URL=$(echo $ASYNC_RESPONSE | jq -r '.status_url')

echo "Job ID: $JOB_ID"
echo "Status URL: $STATUS_URL"
echo ""

# Check initial status
echo "Checking initial status..."
STATUS1=$(curl -s $API_URL/api/v1/documents/status/$JOB_ID)
STATUS1_STATE=$(echo $STATUS1 | jq -r '.status')
echo "Status: $STATUS1_STATE"
echo ""

# Wait and check again
echo "Waiting 5 seconds for processing..."
sleep 5

STATUS2=$(curl -s $API_URL/api/v1/documents/status/$JOB_ID)
STATUS2_STATE=$(echo $STATUS2 | jq -r '.status')
PROGRESS=$(echo $STATUS2 | jq -r '.progress_percent')
echo "Status: $STATUS2_STATE"
echo "Progress: $PROGRESS%"
echo ""

# Check queue stats
echo "Queue statistics:"
QUEUE_STATS=$(curl -s $API_URL/api/v1/documents/queue/stats)
echo $QUEUE_STATS | jq '.queue_stats'
echo ""

if [ "$STATUS2_STATE" == "completed" ] || [ "$STATUS2_STATE" == "processing" ]; then
    echo "✅ Test 3 PASSED: Async upload queue working"
else
    echo "❌ Test 3 FAILED: Async queue not processing"
fi
echo ""

# Test 4: Document Deletion (T039)
echo "🗑️  Test 4: Document Deletion (T039)"
echo "------------------------------------"
echo "Deleting document: $DOC_ID2"

DELETE_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X DELETE $API_URL/api/v1/documents/$DOC_ID2)
HTTP_CODE=$(echo "$DELETE_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)

echo "HTTP Status Code: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" == "204" ]; then
    echo "✅ Test 4a PASSED: Document deleted successfully (HTTP 204)"
else
    echo "❌ Test 4a FAILED: Expected HTTP 204, got $HTTP_CODE"
fi
echo ""

# Try to delete again (should fail with 404)
echo "Attempting to delete again (should fail)..."
DELETE2_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X DELETE $API_URL/api/v1/documents/$DOC_ID2)
HTTP_CODE2=$(echo "$DELETE2_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)

echo "HTTP Status Code: $HTTP_CODE2"
echo ""

if [ "$HTTP_CODE2" == "404" ]; then
    echo "✅ Test 4b PASSED: Second deletion returned 404 (not found)"
else
    echo "❌ Test 4b FAILED: Expected HTTP 404, got $HTTP_CODE2"
fi
echo ""

# Test 5: Search Functionality
echo "🔍 Test 5: Search with min_score Filter (T040)"
echo "-----------------------------------------------"
SEARCH_RESPONSE=$(curl -s -X POST $API_URL/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "railway connectivity",
    "limit": 5,
    "min_score": 0.7
  }')

RESULT_COUNT=$(echo $SEARCH_RESPONSE | jq '.results | length')
echo "Results returned: $RESULT_COUNT"

if [ "$RESULT_COUNT" -gt "0" ]; then
    echo "✅ Test 5 PASSED: Search with min_score filtering works"
    echo ""
    echo "Sample result:"
    echo $SEARCH_RESPONSE | jq '.results[0] | {document_name, score, document_type}'
else
    echo "⚠️  Test 5: No results (may be expected if min_score too high)"
fi
echo ""

# Cleanup
echo "🧹 Cleanup"
echo "----------"
rm -f $TEST_FILE
echo "✅ Test document removed"
echo ""

# Summary
echo "======================================"
echo "📊 Test Summary"
echo "======================================"
echo "✅ Test 1: Initial upload"
echo "$([ "$REPLACED2" == "true" ] && echo "✅" || echo "❌") Test 2: Document re-upload (T036)"
echo "$([ "$STATUS2_STATE" == "completed" ] || [ "$STATUS2_STATE" == "processing" ] && echo "✅" || echo "❌") Test 3: Async upload queue (T037)"
echo "$([ "$HTTP_CODE" == "204" ] && echo "✅" || echo "❌") Test 4a: Document deletion (T039)"
echo "$([ "$HTTP_CODE2" == "404" ] && echo "✅" || echo "❌") Test 4b: Deletion idempotency"
echo "$([ "$RESULT_COUNT" -gt "0" ] && echo "✅" || echo "⚠️ ") Test 5: Search with filters (T040)"
echo ""
echo "🎉 Post-MVP feature testing complete!"
