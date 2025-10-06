#!/bin/bash
# Manage Services (T023)
# Start, stop, restart, and check status of all bot services

set -e

REDIS_PORT=6379
N8N_PORT=5678

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if service is running
check_redis() {
  if redis-cli -p "$REDIS_PORT" ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis: Running (port $REDIS_PORT)"
    return 0
  else
    echo -e "${RED}✗${NC} Redis: Not running"
    return 1
  fi
}

check_n8n() {
  if curl -s "http://localhost:$N8N_PORT/healthz" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} n8n: Running (port $N8N_PORT)"
    return 0
  else
    echo -e "${RED}✗${NC} n8n: Not running"
    return 1
  fi
}

check_bms_api() {
  if curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} BMS API: Running (port 8000)"
    return 0
  else
    echo -e "${YELLOW}⚠${NC} BMS API: Not running (external service)"
    return 1
  fi
}

check_ollama() {
  if curl -s "http://localhost:11434/api/tags" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama: Running (port 11434)"
    return 0
  else
    echo -e "${YELLOW}⚠${NC} Ollama: Not running (external service)"
    return 1
  fi
}

# Start services
start_services() {
  echo "=== Starting Services ==="
  echo ""
  
  # Start Redis
  if ! check_redis > /dev/null 2>&1; then
    echo "Starting Redis..."
    if [ -f /workspace/redis/bin/redis-server ]; then
      /workspace/redis/bin/redis-server /workspace/redis/redis.conf --daemonize yes
    elif command -v redis-server > /dev/null 2>&1; then
      redis-server --daemonize yes --dir /workspace/redis_data
    else
      echo -e "${RED}ERROR:${NC} Redis not found"
      exit 1
    fi
    sleep 2
    check_redis
  else
    echo "Redis already running"
  fi
  
  echo ""
  
  # Start n8n
  if ! check_n8n > /dev/null 2>&1; then
    echo "Starting n8n..."
    if [ -f /workspace/002-n8n/scripts/start-n8n.sh ]; then
      /workspace/002-n8n/scripts/start-n8n.sh
    else
      echo -e "${YELLOW}⚠${NC} start-n8n.sh not found, using default"
      N8N_USER_FOLDER=/workspace/n8n nohup n8n start > /workspace/logs/n8n.log 2>&1 &
    fi
    sleep 3
    check_n8n
  else
    echo "n8n already running"
  fi
  
  echo ""
  echo "=== Services Started ==="
}

# Stop services
stop_services() {
  echo "=== Stopping Services ==="
  echo ""
  
  # Stop n8n
  if check_n8n > /dev/null 2>&1; then
    echo "Stopping n8n..."
    pkill -f "n8n start" || true
    sleep 2
  fi
  
  # Stop Redis
  if check_redis > /dev/null 2>&1; then
    echo "Stopping Redis..."
    redis-cli -p "$REDIS_PORT" SHUTDOWN NOSAVE || true
    sleep 2
  fi
  
  echo ""
  echo "=== Services Stopped ==="
}

# Restart services
restart_services() {
  stop_services
  echo ""
  sleep 2
  start_services
}

# Check status
check_status() {
  echo "=== Service Status ==="
  echo ""
  check_redis || true
  check_n8n || true
  check_bms_api || true
  check_ollama || true
  echo ""
}

# Health check with detailed info
health_check() {
  echo "=== Health Check ==="
  echo ""
  
  # Redis
  if check_redis > /dev/null 2>&1; then
    echo "Redis Info:"
    redis-cli -p "$REDIS_PORT" INFO server | grep redis_version
    redis-cli -p "$REDIS_PORT" INFO memory | grep used_memory_human
    echo ""
  fi
  
  # n8n
  if check_n8n > /dev/null 2>&1; then
    echo "n8n Info:"
    curl -s "http://localhost:$N8N_PORT/healthz" | head -1
    echo ""
  fi
  
  # BMS API
  if check_bms_api > /dev/null 2>&1; then
    echo "BMS API Info:"
    curl -s "http://localhost:8000/health" | head -3
    echo ""
  fi
  
  # Check conversation count
  if check_redis > /dev/null 2>&1; then
    conv_count=$(redis-cli -p "$REDIS_PORT" --scan --pattern "conversation:*" | wc -l)
    echo "Active conversations: $conv_count"
  fi
  
  echo ""
}

# Main command handler
case "${1:-status}" in
  start)
    start_services
    ;;
  stop)
    stop_services
    ;;
  restart)
    restart_services
    ;;
  status)
    check_status
    ;;
  health)
    health_check
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|health}"
    echo ""
    echo "Commands:"
    echo "  start   - Start all services"
    echo "  stop    - Stop all services"
    echo "  restart - Restart all services"
    echo "  status  - Check service status"
    echo "  health  - Detailed health check"
    exit 1
    ;;
esac
