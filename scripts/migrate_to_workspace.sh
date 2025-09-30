#!/bin/bash
# BMS Agent Persistence Migration Script
# Moves all critical applications and data to /workspace

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 BMS Agent Persistence Migration"
echo "===================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Running as root. Consider running as regular user.${NC}"
fi

# Check disk space
AVAILABLE=$(df /workspace | tail -1 | awk '{print $4}')
REQUIRED=$((50 * 1024 * 1024)) # 50GB in KB

if [ "$AVAILABLE" -lt "$REQUIRED" ]; then
    echo -e "${RED}❌ Insufficient disk space!${NC}"
    echo "   Available: $(($AVAILABLE / 1024 / 1024))GB"
    echo "   Required: 50GB (for Ollama models)"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create backup
echo "📦 Creating backup..."
BACKUP_FILE="/workspace/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" \
    /root/.ollama 2>/dev/null \
    /root/.openwebui 2>/dev/null \
    /root/persistent 2>/dev/null \
    || echo "Some directories not found (OK)"
echo -e "${GREEN}✅ Backup created: $BACKUP_FILE${NC}"
echo ""

# Create directory structure
echo "📁 Creating workspace structure..."
mkdir -p /workspace/apps/{ollama,qdrant}
mkdir -p /workspace/data/{ollama_models,qdrant_storage,openwebui}
mkdir -p /workspace/logs
mkdir -p /workspace/scripts
echo -e "${GREEN}✅ Directory structure created${NC}"
echo ""

# Migrate Ollama
echo "🦙 Migrating Ollama..."
OLLAMA_BIN=$(which ollama 2>/dev/null || echo "")
if [ -n "$OLLAMA_BIN" ]; then
    cp "$OLLAMA_BIN" /workspace/apps/ollama/ollama
    chmod +x /workspace/apps/ollama/ollama
    echo -e "${GREEN}✅ Ollama binary copied${NC}"
    
    # Find and migrate models
    OLLAMA_MODELS=$(find /root /usr /opt -path "*/ollama/models" -type d 2>/dev/null | head -1)
    if [ -d "$OLLAMA_MODELS" ]; then
        echo "   Copying models (this may take several minutes)..."
        rsync -av --progress "$OLLAMA_MODELS/" /workspace/data/ollama_models/ 2>&1 | \
            grep -E "^(sending|sent|total)" || true
        echo -e "${GREEN}✅ Ollama models migrated${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama models not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Ollama binary not found${NC}"
fi
echo ""

# Migrate Qdrant
echo "🔍 Migrating Qdrant..."
QDRANT_BIN=$(which qdrant 2>/dev/null || find /usr /opt /root -name "qdrant" -type f -executable 2>/dev/null | head -1)
if [ -n "$QDRANT_BIN" ]; then
    cp "$QDRANT_BIN" /workspace/apps/qdrant/qdrant
    chmod +x /workspace/apps/qdrant/qdrant
    echo -e "${GREEN}✅ Qdrant binary copied${NC}"
    
    # Migrate data
    if [ -d "/root/persistent/qdrant_storage" ]; then
        echo "   Stopping Qdrant..."
        pkill qdrant 2>/dev/null || true
        sleep 2
        
        echo "   Copying Qdrant data..."
        rsync -av /root/persistent/qdrant_storage/ /workspace/data/qdrant_storage/
        echo -e "${GREEN}✅ Qdrant data migrated${NC}"
    else
        echo -e "${YELLOW}⚠️  Qdrant data not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Qdrant binary not found${NC}"
fi
echo ""

# Migrate OpenWebUI data
echo "🌐 Migrating OpenWebUI data..."
if [ -d "/root/.openwebui" ]; then
    rsync -av /root/.openwebui/ /workspace/data/openwebui/
    echo -e "${GREEN}✅ OpenWebUI data migrated${NC}"
else
    echo -e "${YELLOW}⚠️  OpenWebUI data not found${NC}"
fi
echo ""

# Create environment file
echo "⚙️  Creating environment configuration..."
cat > /workspace/scripts/env.sh << 'EOF'
#!/bin/bash
# BMS Agent Environment Variables

export WORKSPACE_ROOT=/workspace
export BMS_AGENT_ROOT=/workspace/001-bms-agent

# Ollama
export OLLAMA_MODELS=/workspace/data/ollama_models
export OLLAMA_HOST=http://localhost:11434

# Qdrant
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export QDRANT_STORAGE=/workspace/data/qdrant_storage

# OpenWebUI
export OPENWEBUI_DATA_DIR=/workspace/data/openwebui

# BMS API
export BMS_API_URL=http://localhost:8000

# Add workspace apps to PATH
export PATH=/workspace/apps/ollama:/workspace/apps/qdrant:$PATH
EOF
chmod +x /workspace/scripts/env.sh
echo -e "${GREEN}✅ Environment file created${NC}"
echo ""

# Create startup script
echo "🚀 Creating startup script..."
cat > /workspace/scripts/start_all_services.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting BMS Agent Services..."

# Load environment
source /workspace/scripts/env.sh

# Start Qdrant
if [ -f /workspace/apps/qdrant/qdrant ]; then
    echo "Starting Qdrant..."
    /workspace/apps/qdrant/qdrant \
        --storage-path /workspace/data/qdrant_storage \
        --log-level INFO \
        > /workspace/logs/qdrant.log 2>&1 &
    sleep 3
fi

# Start Ollama
if [ -f /workspace/apps/ollama/ollama ]; then
    echo "Starting Ollama..."
    export OLLAMA_MODELS=/workspace/data/ollama_models
    /workspace/apps/ollama/ollama serve > /workspace/logs/ollama.log 2>&1 &
    sleep 3
fi

# Start BMS API
if [ -d /workspace/001-bms-agent ]; then
    echo "Starting BMS API..."
    cd /workspace/001-bms-agent
    source .venv/bin/activate
    nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/api.log 2>&1 &
    sleep 3
fi

# Start OpenWebUI
if [ -f /workspace/001-bms-agent/.venv/bin/open-webui ]; then
    echo "Starting OpenWebUI..."
    cd /workspace/001-bms-agent
    source .venv/bin/activate
    export OPENWEBUI_DATA_DIR=/workspace/data/openwebui
    nohup open-webui serve --host 0.0.0.0 --port 3000 > /workspace/logs/openwebui.log 2>&1 &
    sleep 3
fi

echo "✅ All services started!"
echo ""
echo "Service URLs:"
echo "  - OpenWebUI: http://localhost:3000"
echo "  - BMS API: http://localhost:8000"
echo "  - Qdrant: http://localhost:6333"
echo "  - Ollama: http://localhost:11434"
EOF
chmod +x /workspace/scripts/start_all_services.sh
echo -e "${GREEN}✅ Startup script created${NC}"
echo ""

# Create health check script
echo "🏥 Creating health check script..."
cat > /workspace/scripts/health_check.sh << 'EOF'
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
EOF
chmod +x /workspace/scripts/health_check.sh
echo -e "${GREEN}✅ Health check script created${NC}"
echo ""

# Update Qdrant startup script if it exists
if [ -f /workspace/001-bms-agent/scripts/start_qdrant.sh ]; then
    echo "🔧 Updating existing Qdrant startup script..."
    sed -i 's|/root/persistent/qdrant_storage|/workspace/data/qdrant_storage|g' /workspace/001-bms-agent/scripts/start_qdrant.sh
    echo -e "${GREEN}✅ Qdrant script updated${NC}"
fi
echo ""

# Summary
echo "=================================="
echo -e "${GREEN}✅ Migration Complete!${NC}"
echo "=================================="
echo ""
echo "📁 New Locations:"
echo "   - Ollama: /workspace/apps/ollama/"
echo "   - Qdrant: /workspace/apps/qdrant/"
echo "   - Models: /workspace/data/ollama_models/"
echo "   - Qdrant Data: /workspace/data/qdrant_storage/"
echo "   - OpenWebUI Data: /workspace/data/openwebui/"
echo ""
echo "🚀 Next Steps:"
echo "   1. Test services: /workspace/scripts/start_all_services.sh"
echo "   2. Check health: /workspace/scripts/health_check.sh"
echo "   3. Add to crontab: (crontab -l; echo '@reboot /workspace/scripts/start_all_services.sh') | crontab -"
echo ""
echo "📦 Backup Location: $BACKUP_FILE"
echo ""
echo -e "${YELLOW}⚠️  Remember to test before rebooting!${NC}"
