#!/bin/bash
#
# BMS Agent Automated Backup System
# Creates timestamped backups of Qdrant storage and BMS data
# Implements retention policies: 30-day logs, 90-day data backups
#

set -euo pipefail

# Configuration
BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-/workspace/backups}"
QDRANT_STORAGE_DIR="${QDRANT_STORAGE_DIR:-/workspace/qdrant_storage}"
BMS_DATA_DIR="${BMS_DATA_DIR:-/workspace/bms_data}"
LOG_DIR="${LOG_DIR:-/workspace/logs}"
BACKUP_LOG="${LOG_DIR}/backup.log"

# Retention policies (days)
LOG_RETENTION_DAYS=30
DATA_RETENTION_DAYS=90

# Minimum free disk space (percentage)
MIN_FREE_SPACE_PERCENT=10

# Timestamp for backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DATE=$(date +%Y-%m-%d)

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$BACKUP_LOG"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check disk space
check_disk_space() {
    local mount_point="$1"
    local usage=$(df "$mount_point" | tail -1 | awk '{print $5}' | sed 's/%//')
    local free_percent=$((100 - usage))
    
    if [ "$free_percent" -lt "$MIN_FREE_SPACE_PERCENT" ]; then
        error_exit "Insufficient disk space: ${free_percent}% free (minimum: ${MIN_FREE_SPACE_PERCENT}%)"
    fi
    
    log "Disk space check passed: ${free_percent}% free"
}

# Create backup directory structure
create_backup_dirs() {
    mkdir -p "${BACKUP_BASE_DIR}/qdrant"
    mkdir -p "${BACKUP_BASE_DIR}/bms_data"
    mkdir -p "${BACKUP_BASE_DIR}/logs"
    mkdir -p "$LOG_DIR"
    
    log "Backup directories created"
}

# Backup Qdrant storage
backup_qdrant() {
    local backup_file="${BACKUP_BASE_DIR}/qdrant/qdrant_${TIMESTAMP}.tar.gz"
    
    if [ ! -d "$QDRANT_STORAGE_DIR" ]; then
        log "WARNING: Qdrant storage directory not found: $QDRANT_STORAGE_DIR"
        return 1
    fi
    
    log "Starting Qdrant backup..."
    
    # Create compressed archive
    tar -czf "$backup_file" -C "$(dirname "$QDRANT_STORAGE_DIR")" "$(basename "$QDRANT_STORAGE_DIR")" 2>&1 | tee -a "$BACKUP_LOG"
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "Qdrant backup completed: $backup_file ($size)"
        return 0
    else
        error_exit "Qdrant backup failed"
    fi
}

# Backup BMS data
backup_bms_data() {
    local backup_file="${BACKUP_BASE_DIR}/bms_data/bms_data_${TIMESTAMP}.tar.gz"
    
    if [ ! -d "$BMS_DATA_DIR" ]; then
        log "WARNING: BMS data directory not found: $BMS_DATA_DIR"
        return 1
    fi
    
    log "Starting BMS data backup..."
    
    # Create compressed archive
    tar -czf "$backup_file" -C "$(dirname "$BMS_DATA_DIR")" "$(basename "$BMS_DATA_DIR")" 2>&1 | tee -a "$BACKUP_LOG"
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "BMS data backup completed: $backup_file ($size)"
        return 0
    else
        error_exit "BMS data backup failed"
    fi
}

# Backup logs
backup_logs() {
    local backup_file="${BACKUP_BASE_DIR}/logs/logs_${TIMESTAMP}.tar.gz"
    
    if [ ! -d "$LOG_DIR" ]; then
        log "WARNING: Log directory not found: $LOG_DIR"
        return 1
    fi
    
    log "Starting logs backup..."
    
    # Create compressed archive (exclude backup.log to avoid recursion)
    tar -czf "$backup_file" -C "$(dirname "$LOG_DIR")" \
        --exclude="backup.log" \
        "$(basename "$LOG_DIR")" 2>&1 | tee -a "$BACKUP_LOG"
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "Logs backup completed: $backup_file ($size)"
        return 0
    else
        log "WARNING: Logs backup failed (non-critical)"
        return 1
    fi
}

# Apply retention policy
apply_retention() {
    local backup_type="$1"
    local retention_days="$2"
    local backup_dir="${BACKUP_BASE_DIR}/${backup_type}"
    
    if [ ! -d "$backup_dir" ]; then
        return 0
    fi
    
    log "Applying ${retention_days}-day retention policy to ${backup_type} backups..."
    
    # Find and delete old backups
    local deleted_count=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        deleted_count=$((deleted_count + 1))
        log "Deleted old backup: $(basename "$file")"
    done < <(find "$backup_dir" -name "*.tar.gz" -type f -mtime +${retention_days} -print0)
    
    if [ $deleted_count -gt 0 ]; then
        log "Retention policy applied: $deleted_count old ${backup_type} backup(s) deleted"
    else
        log "No old ${backup_type} backups to delete"
    fi
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log "WARNING: Backup file not found for verification: $backup_file"
        return 1
    fi
    
    log "Verifying backup integrity: $(basename "$backup_file")"
    
    # Test archive integrity
    if tar -tzf "$backup_file" >/dev/null 2>&1; then
        log "Backup verification passed: $(basename "$backup_file")"
        return 0
    else
        log "ERROR: Backup verification failed: $(basename "$backup_file")"
        return 1
    fi
}

# Generate backup report
generate_report() {
    local qdrant_count=$(find "${BACKUP_BASE_DIR}/qdrant" -name "*.tar.gz" -type f 2>/dev/null | wc -l)
    local bms_data_count=$(find "${BACKUP_BASE_DIR}/bms_data" -name "*.tar.gz" -type f 2>/dev/null | wc -l)
    local logs_count=$(find "${BACKUP_BASE_DIR}/logs" -name "*.tar.gz" -type f 2>/dev/null | wc -l)
    
    local total_size=$(du -sh "$BACKUP_BASE_DIR" 2>/dev/null | cut -f1)
    
    log "=== Backup Report ==="
    log "Date: $BACKUP_DATE"
    log "Qdrant backups: $qdrant_count"
    log "BMS data backups: $bms_data_count"
    log "Log backups: $logs_count"
    log "Total backup size: $total_size"
    log "===================="
}

# Main backup execution
main() {
    log "========================================="
    log "BMS Agent Backup System - Starting"
    log "========================================="
    
    # Pre-flight checks
    check_disk_space "/workspace"
    create_backup_dirs
    
    # Perform backups
    local backup_success=true
    
    if ! backup_qdrant; then
        backup_success=false
    fi
    
    if ! backup_bms_data; then
        backup_success=false
    fi
    
    backup_logs  # Non-critical, don't fail on error
    
    # Verify latest backups
    local latest_qdrant="${BACKUP_BASE_DIR}/qdrant/qdrant_${TIMESTAMP}.tar.gz"
    local latest_bms_data="${BACKUP_BASE_DIR}/bms_data/bms_data_${TIMESTAMP}.tar.gz"
    
    verify_backup "$latest_qdrant"
    verify_backup "$latest_bms_data"
    
    # Apply retention policies
    apply_retention "qdrant" "$DATA_RETENTION_DAYS"
    apply_retention "bms_data" "$DATA_RETENTION_DAYS"
    apply_retention "logs" "$LOG_RETENTION_DAYS"
    
    # Generate report
    generate_report
    
    if [ "$backup_success" = true ]; then
        log "========================================="
        log "BMS Agent Backup System - Completed Successfully"
        log "========================================="
        exit 0
    else
        log "========================================="
        log "BMS Agent Backup System - Completed with Errors"
        log "========================================="
        exit 1
    fi
}

# Run main function
main "$@"
