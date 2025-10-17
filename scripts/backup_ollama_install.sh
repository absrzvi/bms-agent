#!/bin/bash
# Backup Ollama Installation Script
# Run this ONCE on a working pod to create the Ollama backup

set -e

BACKUP_DIR="/workspace/backups/ollama_install"
LOG_FILE="/workspace/logs/ollama_backup.log"

mkdir -p /workspace/logs
mkdir -p "$BACKUP_DIR"/{bin,systemd,lib}

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Ollama Installation Backup Started"
log "=========================================="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    log "❌ ERROR: Ollama is not installed on this system"
    log "Please install Ollama first: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
log "Found Ollama: $OLLAMA_VERSION"

# 1. Backup Ollama binary
log "Backing up Ollama binary..."
if [ -f /usr/local/bin/ollama ]; then
    cp /usr/local/bin/ollama "$BACKUP_DIR/bin/"
    chmod +x "$BACKUP_DIR/bin/ollama"
    BINARY_SIZE=$(du -h "$BACKUP_DIR/bin/ollama" | cut -f1)
    log "✅ Binary backed up ($BINARY_SIZE)"
else
    log "❌ ERROR: /usr/local/bin/ollama not found"
    exit 1
fi

# 2. Backup systemd service
log "Backing up systemd service..."
if [ -f /etc/systemd/system/ollama.service ]; then
    cp /etc/systemd/system/ollama.service "$BACKUP_DIR/systemd/"
    log "✅ Systemd service backed up"
else
    log "⚠️  No systemd service found (this is OK)"
fi

# 3. Backup libraries
log "Backing up Ollama libraries..."
if [ -d /usr/local/lib ]; then
    find /usr/local/lib -name "*ollama*" -type f -exec cp {} "$BACKUP_DIR/lib/" \; 2>/dev/null || true
    LIB_COUNT=$(find "$BACKUP_DIR/lib/" -type f | wc -l)
    if [ "$LIB_COUNT" -gt 0 ]; then
        log "✅ Libraries backed up ($LIB_COUNT files)"
    else
        log "⚠️  No Ollama libraries found in /usr/local/lib (this is OK)"
    fi
fi

# 4. Create backup manifest
log "Creating backup manifest..."
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
Ollama Installation Backup
==========================
Created: $(date)
Ollama Version: $OLLAMA_VERSION
Hostname: $(hostname)

Contents:
---------
EOF

find "$BACKUP_DIR" -type f | while read file; do
    SIZE=$(du -h "$file" | cut -f1)
    echo "  - ${file#$BACKUP_DIR/} ($SIZE)" >> "$BACKUP_DIR/MANIFEST.txt"
done

# 5. Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "✅ Backup manifest created"

log "=========================================="
log "Ollama Backup Complete!"
log "=========================================="
log "Location: $BACKUP_DIR"
log "Total Size: $TOTAL_SIZE"
log "Files:"
find "$BACKUP_DIR" -type f | while read file; do
    SIZE=$(du -h "$file" | cut -f1)
    log "  - ${file#$BACKUP_DIR/} ($SIZE)"
done
log "=========================================="
log ""
log "To verify backup, run:"
log "  cat $BACKUP_DIR/MANIFEST.txt"
log ""
log "This backup will be used by runpod_init_v2.sh on pod restarts"

exit 0
