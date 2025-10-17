# BMS Agent Persistence Migration Plan

## 🎯 Goal
Move all critical applications and data to `/workspace` to survive pod reboots on RunPod.

---

## 📊 Current State Analysis

### ✅ Already in /workspace
- `/workspace/001-bms-agent/` - Project code and Python venv
- `/workspace/logs/` - Application logs

### ❌ NOT in /workspace (Will be lost on reboot)
1. **Ollama** - Binary in `/usr/local/bin/` or `/opt/`
2. **Ollama Models** - Large models in `/root/.ollama/` or `/usr/share/ollama/`
3. **OpenWebUI** - Installed in project venv (OK) but data in `/root/.openwebui/`
4. **Qdrant** - Binary location unknown, data in `/root/persistent/qdrant_storage`
5. **System Services** - No systemd services configured

---

## 🔧 Migration Strategy

### Phase 1: Create Workspace Structure
```bash
mkdir -p /workspace/apps/{ollama,qdrant,openwebui}
mkdir -p /workspace/data/{ollama_models,openwebui,qdrant_storage}
mkdir -p /workspace/logs
mkdir -p /workspace/scripts
```

### Phase 2: Migrate Ollama

#### 2.1 Move Ollama Binary
```bash
# Find current location
OLLAMA_BIN=$(which ollama)
echo "Current Ollama: $OLLAMA_BIN"

# Copy to workspace
cp $OLLAMA_BIN /workspace/apps/ollama/ollama
chmod +x /workspace/apps/ollama/ollama

# Create symlink (optional)
sudo ln -sf /workspace/apps/ollama/ollama /usr/local/bin/ollama
```

#### 2.2 Move Ollama Models (LARGE - 15GB+)
```bash
# Find models location
OLLAMA_MODELS_DIR=$(find /root /usr /opt -path "*/ollama/models" -type d 2>/dev/null | head -1)
echo "Current models: $OLLAMA_MODELS_DIR"

# Move models to workspace
if [ -d "$OLLAMA_MODELS_DIR" ]; then
    rsync -av --progress "$OLLAMA_MODELS_DIR/" /workspace/data/ollama_models/
fi

# Set environment variable permanently
echo 'export OLLAMA_MODELS=/workspace/data/ollama_models' >> /workspace/scripts/env.sh
```

### Phase 3: Migrate Qdrant

#### 3.1 Move Qdrant Binary
```bash
# Find Qdrant binary
QDRANT_BIN=$(which qdrant || find /usr /opt -name "qdrant" -type f -executable 2>/dev/null | head -1)
echo "Current Qdrant: $QDRANT_BIN"

# Copy to workspace
cp $QDRANT_BIN /workspace/apps/qdrant/qdrant
chmod +x /workspace/apps/qdrant/qdrant
```

#### 3.2 Move Qdrant Data
```bash
# Stop Qdrant first
pkill qdrant

# Move data
if [ -d "/root/persistent/qdrant_storage" ]; then
    rsync -av --progress /root/persistent/qdrant_storage/ /workspace/data/qdrant_storage/
fi

# Update startup script
sed -i 's|/root/persistent/qdrant_storage|/workspace/data/qdrant_storage|g' /workspace/001-bms-agent/scripts/start_qdrant.sh
```

### Phase 4: Migrate OpenWebUI Data

```bash
# OpenWebUI binary is already in project venv (OK)
# Move data directory
if [ -d "/root/.openwebui" ]; then
    rsync -av --progress /root/.openwebui/ /workspace/data/openwebui/
fi

# Set environment variable
echo 'export OPENWEBUI_DATA_DIR=/workspace/data/openwebui' >> /workspace/scripts/env.sh
```

### Phase 5: Create Startup Scripts

#### 5.1 Master Startup Script
```bash
cat > /workspace/scripts/start_all_services.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting BMS Agent Services..."

# Load environment
source /workspace/scripts/env.sh

# Start Qdrant
echo "Starting Qdrant..."
/workspace/apps/qdrant/qdrant \
    --storage-path /workspace/data/qdrant_storage \
    --log-level INFO \
    > /workspace/logs/qdrant.log 2>&1 &

sleep 3

# Start Ollama
echo "Starting Ollama..."
export OLLAMA_MODELS=/workspace/data/ollama_models
/workspace/apps/ollama/ollama serve > /workspace/logs/ollama.log 2>&1 &

sleep 3

# Start BMS API
echo "Starting BMS API..."
cd /workspace/001-bms-agent
source .venv/bin/activate
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/api.log 2>&1 &

sleep 3

# Start OpenWebUI
echo "Starting OpenWebUI..."
export OPENWEBUI_DATA_DIR=/workspace/data/openwebui
nohup open-webui serve --host 0.0.0.0 --port 3000 > /workspace/logs/openwebui.log 2>&1 &

echo "✅ All services started!"
echo ""
echo "Service URLs:"
echo "  - OpenWebUI: http://localhost:3000"
echo "  - BMS API: http://localhost:8000"
echo "  - Qdrant: http://localhost:6333"
echo "  - Ollama: http://localhost:11434"
EOF

chmod +x /workspace/scripts/start_all_services.sh
```

#### 5.2 Environment Variables
```bash
cat > /workspace/scripts/env.sh << 'EOF'
#!/bin/bash
# BMS Agent Environment Variables

# Paths
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
```

#### 5.3 Health Check Script
```bash
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
ps aux | grep -E "(qdrant|ollama|uvicorn|open-webui)" | grep -v grep | awk '{print "  - " $11}'
EOF

chmod +x /workspace/scripts/health_check.sh
```

### Phase 6: Auto-Start on Boot

#### 6.1 Create Init Script
```bash
cat > /workspace/scripts/init_on_boot.sh << 'EOF'
#!/bin/bash
# Add this to RunPod startup script or crontab

# Wait for system to be ready
sleep 10

# Start all services
/workspace/scripts/start_all_services.sh

# Log startup
echo "$(date): BMS Agent services started" >> /workspace/logs/startup.log
EOF

chmod +x /workspace/scripts/init_on_boot.sh
```

#### 6.2 Add to Crontab
```bash
# Add to crontab for auto-start
(crontab -l 2>/dev/null; echo "@reboot /workspace/scripts/init_on_boot.sh") | crontab -
```

---

## 📋 Migration Checklist

### Pre-Migration
- [ ] Backup current data: `tar -czf /workspace/backup_$(date +%Y%m%d).tar.gz /root/.ollama /root/.openwebui /root/persistent`
- [ ] Check disk space: `df -h /workspace` (need ~50GB for Ollama models)
- [ ] Document current service locations

### Migration Steps
- [ ] Phase 1: Create directory structure
- [ ] Phase 2: Migrate Ollama (binary + models)
- [ ] Phase 3: Migrate Qdrant (binary + data)
- [ ] Phase 4: Migrate OpenWebUI data
- [ ] Phase 5: Create startup scripts
- [ ] Phase 6: Configure auto-start

### Post-Migration
- [ ] Test all services start correctly
- [ ] Verify data integrity (check Qdrant collection count)
- [ ] Test search functionality
- [ ] Test OpenWebUI tool integration
- [ ] Simulate reboot: `sudo reboot` (if safe)
- [ ] Verify auto-start works after reboot

---

## 🎯 Quick Migration Command

Run this to execute the full migration:

```bash
cd /workspace/001-bms-agent
bash << 'MIGRATION'
#!/bin/bash
set -e

echo "🚀 Starting BMS Agent Persistence Migration..."

# Create structure
mkdir -p /workspace/{apps/{ollama,qdrant},data/{ollama_models,qdrant_storage,openwebui},logs,scripts}

# Find and copy binaries
echo "📦 Migrating binaries..."
cp $(which ollama) /workspace/apps/ollama/ollama 2>/dev/null || echo "Ollama not found"
cp $(which qdrant || find /usr /opt -name qdrant -type f -executable 2>/dev/null | head -1) /workspace/apps/qdrant/qdrant 2>/dev/null || echo "Qdrant not found"

# Make executable
chmod +x /workspace/apps/ollama/ollama /workspace/apps/qdrant/qdrant 2>/dev/null

# Copy data (this may take time for Ollama models)
echo "📁 Migrating data..."
[ -d /root/.ollama/models ] && rsync -av /root/.ollama/models/ /workspace/data/ollama_models/
[ -d /root/persistent/qdrant_storage ] && rsync -av /root/persistent/qdrant_storage/ /workspace/data/qdrant_storage/
[ -d /root/.openwebui ] && rsync -av /root/.openwebui/ /workspace/data/openwebui/

echo "✅ Migration complete!"
echo "Next: Create startup scripts using the templates above"
MIGRATION
```

---

## ⚠️ Important Notes

1. **Disk Space**: Ollama models are 15GB+. Ensure `/workspace` has enough space.
2. **Symlinks**: Consider using symlinks instead of copies to save space.
3. **Permissions**: Ensure all files are readable/writable by your user.
4. **Testing**: Test thoroughly before relying on auto-start.
5. **Backup**: Always backup before migration!

---

## 🔍 Verification Commands

```bash
# Check all files are in workspace
find /workspace -type f -name "ollama" -o -name "qdrant" -o -name "open-webui"

# Check data directories
du -sh /workspace/data/*

# Test startup
/workspace/scripts/start_all_services.sh

# Check health
/workspace/scripts/health_check.sh
```

---

## 📞 Rollback Plan

If migration fails:

```bash
# Stop all services
pkill -f "ollama|qdrant|uvicorn|open-webui"

# Restore from backup
tar -xzf /workspace/backup_*.tar.gz -C /

# Restart services normally
# (use original startup methods)
```

---

**Status**: Ready for migration  
**Estimated Time**: 30-60 minutes (depending on model sizes)  
**Risk Level**: Low (with proper backup)
