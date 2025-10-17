#!/bin/bash
#
# BMS Agent Backup Restoration Script
# Restores Qdrant storage and BMS data from backup archives
#

set -euo pipefail

BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-/workspace/backups}"
QDRANT_STORAGE_DIR="${QDRANT_STORAGE_DIR:-/workspace/qdrant_storage}"
BMS_DATA_DIR="${BMS_DATA_DIR:-/workspace/bms_data}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error_exit() {
    echo -e "${RED}ERROR: $1${NC}"
    exit 1
}

list_backups() {
    local backup_type="$1"
    local backup_dir="${BACKUP_BASE_DIR}/${backup_type}"
    
    if [ ! -d "$backup_dir" ]; then
        echo "No backups found"
        return
    fi
    
    local count=1
    for backup in "$backup_dir"/*.tar.gz; do
        [ -e "$backup" ] || continue
        local name=$(basename "$backup")
        local size=$(du -h "$backup" | cut -f1)
        local date=$(stat -c %y "$backup" | cut -d' ' -f1)
        echo "  [$count] $name - $size (created: $date)"
        count=$((count + 1))
    done
}

select_backup() {
    local backup_type="$1"
    local backup_dir="${BACKUP_BASE_DIR}/${backup_type}"
    
    echo -e "\n${YELLOW}Available ${backup_type} backups:${NC}"
    list_backups "$backup_type"
    
    echo -e "\nEnter backup filename (or 'latest' for most recent):"
    read -r selection
    
    if [ "$selection" = "latest" ]; then
        local latest=$(ls -t "$backup_dir"/*.tar.gz 2>/dev/null | head -1)
        if [ -z "$latest" ]; then
            error_exit "No backups found"
        fi
        echo "$latest"
    else
        local backup_file="${backup_dir}/${selection}"
        if [ ! -f "$backup_file" ]; then
            error_exit "Backup file not found: $backup_file"
        fi
        echo "$backup_file"
    fi
}

restore_qdrant() {
    local backup_file="$1"
    
    log "Restoring Qdrant from: $(basename "$backup_file")"
    
    # Verify backup integrity
    if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
        error_exit "Backup file is corrupted"
    fi
    
    # Create backup of current data
    if [ -d "$QDRANT_STORAGE_DIR" ]; then
        local backup_current="${QDRANT_STORAGE_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
        log "Backing up current Qdrant data to: $backup_current"
        mv "$QDRANT_STORAGE_DIR" "$backup_current"
    fi
    
    # Extract backup
    log "Extracting backup..."
    tar -xzf "$backup_file" -C "$(dirname "$QDRANT_STORAGE_DIR")"
    
    if [ $? -eq 0 ]; then
        log "${GREEN}Qdrant restoration completed successfully${NC}"
        return 0
    else
        error_exit "Qdrant restoration failed"
    fi
}

restore_bms_data() {
    local backup_file="$1"
    
    log "Restoring BMS data from: $(basename "$backup_file")"
    
    # Verify backup integrity
    if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
        error_exit "Backup file is corrupted"
    fi
    
    # Create backup of current data
    if [ -d "$BMS_DATA_DIR" ]; then
        local backup_current="${BMS_DATA_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
        log "Backing up current BMS data to: $backup_current"
        mv "$BMS_DATA_DIR" "$backup_current"
    fi
    
    # Extract backup
    log "Extracting backup..."
    tar -xzf "$backup_file" -C "$(dirname "$BMS_DATA_DIR")"
    
    if [ $? -eq 0 ]; then
        log "${GREEN}BMS data restoration completed successfully${NC}"
        return 0
    else
        error_exit "BMS data restoration failed"
    fi
}

main() {
    log "BMS Agent Backup Restoration"
    echo "================================"
    
    if [ $# -eq 0 ]; then
        echo "Usage: $0 [qdrant|bms_data|all]"
        echo ""
        echo "Options:"
        echo "  qdrant    - Restore Qdrant storage only"
        echo "  bms_data  - Restore BMS data only"
        echo "  all       - Restore both Qdrant and BMS data"
        exit 1
    fi
    
    local restore_type="$1"
    
    case "$restore_type" in
        qdrant)
            local backup_file=$(select_backup "qdrant")
            restore_qdrant "$backup_file"
            ;;
        bms_data)
            local backup_file=$(select_backup "bms_data")
            restore_bms_data "$backup_file"
            ;;
        all)
            local qdrant_backup=$(select_backup "qdrant")
            local bms_data_backup=$(select_backup "bms_data")
            restore_qdrant "$qdrant_backup"
            restore_bms_data "$bms_data_backup"
            ;;
        *)
            error_exit "Invalid restore type: $restore_type"
            ;;
    esac
    
    log "================================"
    log "${GREEN}Restoration completed${NC}"
    log "Please restart services for changes to take effect"
}

main "$@"
