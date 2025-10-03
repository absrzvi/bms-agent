#!/bin/bash
# Save SSH Keys to Persistent Storage
# Run this to backup your current SSH authorized_keys

set -e

CONFIG_DIR="/workspace/config"
LOG_FILE="/workspace/logs/ssh_backup.log"

mkdir -p "$CONFIG_DIR"
mkdir -p /workspace/logs

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "SSH Keys Backup Started"
log "=========================================="

# Check if authorized_keys exists
if [ -f /root/.ssh/authorized_keys ]; then
    cp /root/.ssh/authorized_keys "$CONFIG_DIR/authorized_keys"
    chmod 600 "$CONFIG_DIR/authorized_keys"
    
    KEY_COUNT=$(grep -c "^ssh-" "$CONFIG_DIR/authorized_keys" 2>/dev/null || echo 0)
    log "✅ SSH keys backed up to $CONFIG_DIR/authorized_keys"
    log "   Found $KEY_COUNT SSH key(s)"
    
    # Show key fingerprints (for verification)
    log "Key fingerprints:"
    ssh-keygen -lf "$CONFIG_DIR/authorized_keys" 2>/dev/null | while read line; do
        log "   $line"
    done
else
    log "⚠️  No authorized_keys found in /root/.ssh/"
    log "   Creating empty file for future use"
    touch "$CONFIG_DIR/authorized_keys"
    chmod 600 "$CONFIG_DIR/authorized_keys"
fi

log "=========================================="
log "SSH Keys Backup Complete!"
log "=========================================="
log "Location: $CONFIG_DIR/authorized_keys"
log ""
log "These keys will be restored by runpod_init_v2.sh on pod restarts"

exit 0
