#!/bin/bash

echo "🏥 BMS Agent Health Check"
echo "========================"
echo ""

check_service() {
    local name=$1
    local url=$2
    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $name: Running"
        return 0
    else
        echo "❌ $name: Down"
        return 1
    fi
}

check_service "Qdrant" "http://localhost:6333/health"
check_service "Ollama" "http://localhost:11434/api/tags"
check_service "BMS API" "http://localhost:8000/health"
check_service "OpenWebUI" "http://localhost:3000"

echo ""
echo "📊 Process Status:"
ps aux | grep -E "(qdrant|ollama|uvicorn|open-webui)" | grep -v grep | awk '{print "  - " $11}' || echo "  No processes found"
