#!/bin/bash
# BMS Agent - Service Status Check

# Function to check if service is running
is_running() {
    pgrep -f "$1" > /dev/null
}

# Function to get health status
get_health() {
    local url=$1
    if curl -s "$url" >/dev/null 2>&1; then
        echo "✅ Healthy"
    else
        echo "❌ Unhealthy"
    fi
}

echo "============================================"
echo "  BMS Agent Service Status"
echo "============================================"
echo ""
printf "%-20s %-15s %-15s %-15s %-50s\n" "SERVICE" "STATUS" "PID" "HEALTH" "URL"
echo "-------------------------------------------------------------------------------------------------------------"

# Ollama
if is_running "ollama serve"; then
    PID=$(pgrep -f 'ollama serve')
    HEALTH=$(get_health "http://localhost:11434")
    printf "%-20s %-15s %-15s %-15s %-50s\n" "Ollama" "✅ Running" "$PID" "$HEALTH" "http://localhost:11434"
else
    printf "%-20s %-15s %-15s %-15s %-50s\n" "Ollama" "❌ Stopped" "-" "-" "http://localhost:11434"
fi

# Qdrant
if is_running "qdrant"; then
    PID=$(pgrep -x qdrant)
    HEALTH=$(get_health "http://localhost:6333/healthz")
    printf "%-20s %-15s %-15s %-15s %-50s\n" "Qdrant" "✅ Running" "$PID" "$HEALTH" "http://localhost:6333/dashboard"
else
    printf "%-20s %-15s %-15s %-15s %-50s\n" "Qdrant" "❌ Stopped" "-" "-" "http://localhost:6333/dashboard"
fi

# OpenWebUI
if is_running "open-webui"; then
    PID=$(pgrep -f 'open-webui')
    HEALTH=$(get_health "http://localhost:8080")
    printf "%-20s %-15s %-15s %-15s %-50s\n" "OpenWebUI" "✅ Running" "$PID" "$HEALTH" "http://localhost:8080"
else
    printf "%-20s %-15s %-15s %-15s %-50s\n" "OpenWebUI" "❌ Stopped" "-" "-" "http://localhost:8080"
fi

# FastAPI
if is_running "uvicorn api.main"; then
    PID=$(pgrep -f 'uvicorn api.main')
    HEALTH=$(get_health "http://localhost:8000/health")
    printf "%-20s %-15s %-15s %-15s %-50s\n" "FastAPI" "✅ Running" "$PID" "$HEALTH" "http://localhost:8000/docs"
else
    printf "%-20s %-15s %-15s %-15s %-50s\n" "FastAPI" "❌ Stopped" "-" "-" "http://localhost:8000/docs"
fi

echo ""

# Check Qdrant collection if running
if is_running "qdrant"; then
    echo "Qdrant Collection Status:"
    python3 << 'EOF' 2>/dev/null || echo "  ⚠️  Could not verify collection"
import sys
sys.path.insert(0, '/workspace/bms-agent/bms-agent/scr')
from qdrant_client import QdrantClient

try:
    client = QdrantClient(host="localhost", port=6333)
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if 'nomad_bms_documents' in collection_names:
        info = client.get_collection('nomad_bms_documents')
        print(f"  ✅ Collection 'nomad_bms_documents': {info.points_count:,} points ({info.vectors_count:,} vectors)")
    else:
        print("  ⚠️  Collection 'nomad_bms_documents' not found")

    for collection in collections.collections:
        if collection.name != 'nomad_bms_documents':
            info = client.get_collection(collection.name)
            print(f"  ℹ️  Collection '{collection.name}': {info.points_count:,} points")
except Exception as e:
    print(f"  ❌ Error: {e}")
EOF
    echo ""
fi

# Visual artifacts status
ARTIFACT_COUNT=$(find /workspace/visual-artifacts -type f -name "*.png" 2>/dev/null | wc -l)
echo "Visual Artifacts:"
echo "  📊 Total images: $ARTIFACT_COUNT"
echo ""

# Disk usage
echo "Storage Usage:"
echo "  Qdrant data:      $(du -sh /workspace/qdrant-data 2>/dev/null | cut -f1)"
echo "  Ollama models:    $(du -sh /workspace/ollama 2>/dev/null | cut -f1)"
echo "  Visual artifacts: $(du -sh /workspace/visual-artifacts 2>/dev/null | cut -f1)"
echo "  Logs:             $(du -sh /workspace/logs 2>/dev/null | cut -f1)"
echo ""

# Recent log activity
echo "Recent Activity (last 5 lines from each log):"
echo ""
for log in /workspace/logs/*.log; do
    if [ -f "$log" ]; then
        echo "--- $(basename $log) ---"
        tail -5 "$log" 2>/dev/null || echo "  (empty)"
        echo ""
    fi
done
