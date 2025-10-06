#!/bin/bash
set -e

# MS Teams Bot - Storage Initialization Script
# Creates config files and tests Redis connectivity

echo "=== BMS Teams Bot Storage Initialization ==="

# Create config directory if not exists
CONFIG_DIR="/workspace/002-n8n/config"
mkdir -p "$CONFIG_DIR"

# Initialize whitelist.json if not exists
WHITELIST_FILE="$CONFIG_DIR/whitelist.json"
if [ ! -f "$WHITELIST_FILE" ]; then
    echo "Creating whitelist.json..."
    cat > "$WHITELIST_FILE" <<'EOF'
{
  "admins": [],
  "channels": []
}
EOF
    echo "✓ Whitelist created at $WHITELIST_FILE"
else
    echo "✓ Whitelist already exists at $WHITELIST_FILE"
fi

# Test Redis connectivity
echo ""
echo "Testing Redis connectivity..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis is running and accessible"

        # Test TTL functionality
        redis-cli set test_key "test_value" EX 10 > /dev/null
        TTL=$(redis-cli ttl test_key)
        if [ "$TTL" -gt 0 ] && [ "$TTL" -le 10 ]; then
            echo "✓ Redis TTL functionality verified"
        fi
        redis-cli del test_key > /dev/null
    else
        echo "⚠️  Redis is not responding. Please start Redis:"
        echo "   docker run -d --name bms-bot-redis -v /workspace/redis_data:/data -p 6379:6379 redis:7-alpine redis-server --appendonly yes"
        exit 1
    fi
else
    echo "⚠️  redis-cli not found. Please install Redis or add to PATH"
    echo "   Redis is required for conversation context storage"
    exit 1
fi

# Create Redis data directory
REDIS_DATA_DIR="/workspace/redis_data"
mkdir -p "$REDIS_DATA_DIR"
echo "✓ Redis data directory: $REDIS_DATA_DIR"

echo ""
echo "=== Storage Initialization Complete ==="
echo ""
echo "Next steps:"
echo "1. Add admin users to $WHITELIST_FILE"
echo "2. Configure environment variables (copy config/env.example to .env)"
echo "3. Deploy n8n workflows with scripts/deploy-workflows.sh"
