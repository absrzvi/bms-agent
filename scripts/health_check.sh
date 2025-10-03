#!/bin/bash
#
# BMS Agent Comprehensive Health Check Script
# Probes all services and logs results with timestamps
#

set -euo pipefail

# Configuration
LOG_FILE="/workspace/logs/health_check.log"
TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
log_to_file() {
    echo "[$TIMESTAMP] $*" >> "$LOG_FILE"
}

echo "🏥 BMS Agent Health Check"
echo "========================"
echo "Timestamp: $TIMESTAMP"
echo ""

# Initialize counters
TOTAL_CHECKS=0
PASSED_CHECKS=0

check_service() {
    local name=$1
    local url=$2
    local timeout=${3:-5}
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if curl -s --max-time "$timeout" "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name: Running"
        log_to_file "✓ $name: Running ($url)"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $name: Down"
        log_to_file "✗ $name: Down ($url)"
        return 1
    fi
}

check_service_with_details() {
    local name=$1
    local url=$2
    local timeout=${3:-5}
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    local response=$(curl -s --max-time "$timeout" "$url" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $name: Running"
        log_to_file "✓ $name: Running ($url) - Response: ${response:0:100}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $name: Down (timeout or connection error)"
        log_to_file "✗ $name: Down ($url) - Error: $response"
        return 1
    fi
}

# Core Services
echo "Core Services:"
check_service "Qdrant" "http://localhost:6333/healthz" 5
check_service "Ollama" "http://localhost:11434/api/tags" 5

# BMS API
echo ""
echo "BMS API:"
check_service_with_details "API Health" "http://localhost:8000/health" 5
check_service "API Detailed Health" "http://localhost:8000/health/detailed" 10

# Metrics
echo ""
echo "Monitoring:"
check_service "Metrics Endpoint" "http://localhost:8000/metrics/uplink" 5

# OpenWebUI (optional)
echo ""
echo "Optional Services:"
check_service "OpenWebUI" "http://localhost:3000" 5 || echo -e "${YELLOW}  (OpenWebUI is optional)${NC}"

# Process Status
echo ""
echo "📊 Process Status:"
if pgrep -f "qdrant" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Qdrant (PID: $(pgrep -f qdrant))"
else
    echo -e "  ${RED}✗${NC} Qdrant"
fi

if pgrep -f "ollama serve" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Ollama (PID: $(pgrep -f 'ollama serve'))"
else
    echo -e "  ${RED}✗${NC} Ollama"
fi

if pgrep -f "uvicorn api.main:app" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} BMS API (PID: $(pgrep -f 'uvicorn api.main:app'))"
else
    echo -e "  ${RED}✗${NC} BMS API"
fi

if pgrep -f "open-webui serve" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} OpenWebUI (PID: $(pgrep -f 'open-webui serve'))"
else
    echo -e "  ${YELLOW}○${NC} OpenWebUI (optional)"
fi

# Disk Space
echo ""
echo "💾 Disk Space:"
df -h /workspace | tail -1 | awk '{print "  Usage: " $5 " (" $3 " used / " $2 " total)"}'

# Memory
echo ""
echo "🧠 Memory:"
free -h | grep Mem | awk '{print "  Usage: " $3 " / " $2 " (" int($3/$2 * 100) "%)"}'

# Summary
echo ""
echo "========================"
echo "Summary: $PASSED_CHECKS/$TOTAL_CHECKS checks passed"
log_to_file "Summary: $PASSED_CHECKS/$TOTAL_CHECKS checks passed"

if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}✓ All systems operational${NC}"
    log_to_file "✓ All systems operational"
    exit 0
elif [ $PASSED_CHECKS -ge $((TOTAL_CHECKS * 3 / 4)) ]; then
    echo -e "${YELLOW}⚠ Some services degraded${NC}"
    log_to_file "⚠ Some services degraded"
    exit 1
else
    echo -e "${RED}✗ Critical services down${NC}"
    log_to_file "✗ Critical services down"
    exit 2
fi
