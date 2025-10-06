#!/bin/bash
# Cleanup Expired Conversations (T022)
# Removes Redis keys for conversations > 7 days old

set -e

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
DRY_RUN="${1:-}"
TTL_SECONDS=604800  # 7 days

echo "=== Redis Conversation Cleanup ==="
echo "Redis: $REDIS_HOST:$REDIS_PORT"
echo "TTL: $TTL_SECONDS seconds (7 days)"
echo ""

# Check if Redis is accessible
if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
  echo "ERROR: Cannot connect to Redis at $REDIS_HOST:$REDIS_PORT"
  exit 1
fi

echo "✓ Redis connection OK"
echo ""

# Function to clean up conversations
cleanup_conversations() {
  echo "Scanning conversation keys..."
  
  redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --scan --pattern "conversation:*" | while read key; do
    # Get TTL
    ttl=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" TTL "$key")
    
    # If TTL is -1 (no expiry set) or expired (0 or negative)
    if [ "$ttl" -eq -1 ] || [ "$ttl" -le 0 ]; then
      if [ "$DRY_RUN" = "--dry-run" ]; then
        echo "  [DRY RUN] Would delete: $key (TTL: $ttl)"
      else
        echo "  Deleting: $key (TTL: $ttl)"
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" DEL "$key" > /dev/null
      fi
    fi
  done
}

# Function to clean up search history
cleanup_history() {
  echo ""
  echo "Scanning search history keys..."
  
  redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --scan --pattern "user:*:history" | while read key; do
    ttl=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" TTL "$key")
    
    if [ "$ttl" -eq -1 ] || [ "$ttl" -le 0 ]; then
      if [ "$DRY_RUN" = "--dry-run" ]; then
        echo "  [DRY RUN] Would delete: $key (TTL: $ttl)"
      else
        echo "  Deleting: $key (TTL: $ttl)"
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" DEL "$key" > /dev/null
      fi
    fi
  done
}

# Function to clean up old upload jobs (30 days)
cleanup_uploads() {
  echo ""
  echo "Scanning upload job keys..."
  
  redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --scan --pattern "upload:*" | while read key; do
    ttl=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" TTL "$key")
    
    # Clean up if expired
    if [ "$ttl" -le 0 ] && [ "$ttl" != -1 ]; then
      if [ "$DRY_RUN" = "--dry-run" ]; then
        echo "  [DRY RUN] Would delete: $key (TTL: $ttl)"
      else
        echo "  Deleting: $key (TTL: $ttl)"
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" DEL "$key" > /dev/null
      fi
    fi
  done
}

# Run cleanup
cleanup_conversations
cleanup_history
cleanup_uploads

echo ""
if [ "$DRY_RUN" = "--dry-run" ]; then
  echo "=== Dry Run Complete ==="
  echo "Run without --dry-run to actually delete keys"
else
  echo "=== Cleanup Complete ==="
fi

# Show Redis memory usage
echo ""
echo "Redis Memory Usage:"
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO memory | grep used_memory_human

echo ""
