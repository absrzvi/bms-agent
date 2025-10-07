#!/bin/bash
# Test script for verifying Redis node fixes

echo "========================================="
echo "Testing Redis Node Fixes"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Redis is running
echo "1. Checking Redis..."
if redis-cli PING > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${RED}✗ Redis is not running${NC}"
    echo "Start Redis first: redis-server &"
    exit 1
fi

# Check n8n is running
echo ""
echo "2. Checking n8n..."
if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
    echo -e "${GREEN}✓ n8n is running${NC}"
else
    echo -e "${RED}✗ n8n is not running${NC}"
    echo "Start n8n first"
    exit 1
fi

# Test Context Manager - Store
echo ""
echo "3. Testing Context Manager - Store..."
RESPONSE=$(curl -s -X POST http://localhost:5678/webhook/context-manager \
  -H "Content-Type: application/json" \
  -d '{
    "action": "store",
    "conversationId": "test-fix-001",
    "userMessage": "Test message after Redis fix",
    "botResponse": "Test response"
  }')

if echo "$RESPONSE" | grep -q "context"; then
    echo -e "${GREEN}✓ Context Manager store works${NC}"
else
    echo -e "${RED}✗ Context Manager store failed${NC}"
    echo "Response: $RESPONSE"
fi

# Verify in Redis
echo ""
echo "4. Verifying data in Redis..."
REDIS_DATA=$(redis-cli GET "conversation:test-fix-001")
if [ ! -z "$REDIS_DATA" ]; then
    echo -e "${GREEN}✓ Data stored in Redis${NC}"
    echo "Key: conversation:test-fix-001"
    TTL=$(redis-cli TTL "conversation:test-fix-001")
    echo "TTL: $TTL seconds (~$((TTL/86400)) days)"
else
    echo -e "${RED}✗ Data not found in Redis${NC}"
fi

# Test Context Manager - Get
echo ""
echo "5. Testing Context Manager - Get..."
RESPONSE=$(curl -s -X POST http://localhost:5678/webhook/context-manager \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get",
    "conversationId": "test-fix-001"
  }')

if echo "$RESPONSE" | grep -q "Test message after Redis fix"; then
    echo -e "${GREEN}✓ Context Manager get works${NC}"
else
    echo -e "${RED}✗ Context Manager get failed${NC}"
    echo "Response: $RESPONSE"
fi

# Summary
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo ""
echo "If all tests passed (✓), the Redis fixes are working correctly!"
echo ""
echo "Next steps:"
echo "1. Review REDIS_FIXES_COMPLETE.md for details"
echo "2. Test Similar Query Detector if BMS API is running"
echo "3. Apply other fixes from FIXES_APPLIED.md"
echo "4. Activate all workflows in correct order"
echo ""
