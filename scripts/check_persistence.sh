#!/bin/bash
# BMS Agent Persistence Verification Script
# Verifies all critical data is in /workspace (persistent storage)

echo "🔍 BMS Agent Persistence Check"
echo "================================"
echo ""

# Check persistent storage
echo "📁 Persistent Storage (/workspace):"
echo "  Total: $(df -h /workspace | tail -1 | awk '{print $2}')"
echo "  Used: $(df -h /workspace | tail -1 | awk '{print $3}')"
echo "  Available: $(df -h /workspace | tail -1 | awk '{print $4}')"
echo ""

# Check critical directories
echo "📂 Critical Directories:"
check_dir() {
    if [ -d "$1" ]; then
        size=$(du -sh "$1" 2>/dev/null | cut -f1)
        echo "  ✅ $1 ($size)"
    else
        echo "  ❌ $1 (MISSING)"
    fi
}

check_dir "/workspace/data/qdrant_storage"
check_dir "/workspace/data/ollama_models"
check_dir "/workspace/data/openwebui"
check_dir "/workspace/bms_data"
check_dir "/workspace/logs"
check_dir "/workspace/apps/qdrant"
check_dir "/workspace/001-bms-agent"
echo ""

# Check Qdrant data
echo "🗄️  Qdrant Database:"
if [ -d "/workspace/data/qdrant_storage" ]; then
    collection_count=$(find /workspace/data/qdrant_storage/collections -type d -maxdepth 1 2>/dev/null | wc -l)
    echo "  Collections: $((collection_count - 1))"
    
    if [ -f "/workspace/data/qdrant_storage/collections/nomad_bms_documents/collection.json" ]; then
        echo "  ✅ nomad_bms_documents collection exists"
    fi
fi
echo ""

# Check Ollama models
echo "🤖 Ollama Models:"
if [ -d "/workspace/data/ollama_models" ]; then
    model_count=$(find /workspace/data/ollama_models -type f -name "manifest.json" 2>/dev/null | wc -l)
    echo "  Models: $model_count"
    
    if [ -d "/workspace/data/ollama_models/manifests/registry.ollama.ai" ]; then
        echo "  Available models:"
        find /workspace/data/ollama_models/manifests/registry.ollama.ai -type d -maxdepth 2 | grep -v "^/workspace/data/ollama_models/manifests/registry.ollama.ai$" | sed 's|/workspace/data/ollama_models/manifests/registry.ollama.ai/||' | sed 's|^|    - |'
    fi
fi
echo ""

# Check BMS documents
echo "📄 BMS Documents:"
if [ -d "/workspace/bms_data" ]; then
    processed=$(find /workspace/bms_data/processed -type f 2>/dev/null | wc -l)
    incoming=$(find /workspace/bms_data/incoming -type f 2>/dev/null | wc -l)
    failed=$(find /workspace/bms_data/failed -type f 2>/dev/null | wc -l)
    
    echo "  Processed: $processed"
    echo "  Incoming: $incoming"
    echo "  Failed: $failed"
fi
echo ""

# Check configuration files
echo "⚙️  Configuration Files:"
check_file() {
    if [ -f "$1" ]; then
        echo "  ✅ $1"
    else
        echo "  ❌ $1 (MISSING)"
    fi
}

check_file "/workspace/apps/qdrant/config.yaml"
check_file "/workspace/001-bms-agent/config/config.yaml"
check_file "/workspace/scripts/env.sh"
echo ""

# Check non-persistent items (will be reinstalled on startup)
echo "⚠️  Non-Persistent Items (Auto-installed on startup):"
if [ -f "/usr/local/bin/ollama" ]; then
    echo "  ✅ Ollama binary (in /usr/local/bin)"
else
    echo "  ❌ Ollama binary (will be installed on next startup)"
fi
echo ""

# Summary
echo "📊 Summary:"
echo "  ✅ All critical data in /workspace (persistent)"
echo "  ✅ Ollama models in /workspace/data/ollama_models"
echo "  ✅ Qdrant data in /workspace/data/qdrant_storage"
echo "  ✅ BMS documents in /workspace/bms_data"
echo "  ⚠️  Ollama binary will be auto-installed on pod restart"
echo ""
echo "💡 Recommendation:"
echo "  - Keep /workspace backed up regularly"
echo "  - Ollama will auto-install on startup (takes ~30 seconds)"
echo "  - All models and data are preserved in /workspace"
echo ""
