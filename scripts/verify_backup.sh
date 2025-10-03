#!/bin/bash
#
# BMS Agent Backup Verification Script
# Verifies integrity of backup archives
#

set -euo pipefail

BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-/workspace/backups}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

verify_archive() {
    local archive="$1"
    local name=$(basename "$archive")
    
    if [ ! -f "$archive" ]; then
        echo -e "${RED}✗${NC} $name - File not found"
        return 1
    fi
    
    # Test archive integrity
    if tar -tzf "$archive" >/dev/null 2>&1; then
        local size=$(du -h "$archive" | cut -f1)
        echo -e "${GREEN}✓${NC} $name - OK ($size)"
        return 0
    else
        echo -e "${RED}✗${NC} $name - Corrupted"
        return 1
    fi
}

main() {
    log "BMS Agent Backup Verification"
    echo "================================"
    
    local total=0
    local passed=0
    local failed=0
    
    # Verify Qdrant backups
    echo -e "\n${YELLOW}Qdrant Backups:${NC}"
    shopt -s nullglob
    for backup in "${BACKUP_BASE_DIR}/qdrant"/*.tar.gz; do
        total=$((total + 1))
        if verify_archive "$backup"; then
            passed=$((passed + 1))
        else
            failed=$((failed + 1))
        fi
    done
    
    # Verify BMS data backups
    echo -e "\n${YELLOW}BMS Data Backups:${NC}"
    for backup in "${BACKUP_BASE_DIR}/bms_data"/*.tar.gz; do
        total=$((total + 1))
        if verify_archive "$backup"; then
            passed=$((passed + 1))
        else
            failed=$((failed + 1))
        fi
    done
    
    # Verify log backups
    echo -e "\n${YELLOW}Log Backups:${NC}"
    for backup in "${BACKUP_BASE_DIR}/logs"/*.tar.gz; do
        total=$((total + 1))
        if verify_archive "$backup"; then
            passed=$((passed + 1))
        else
            failed=$((failed + 1))
        fi
    done
    
    # Summary
    echo -e "\n================================"
    echo "Total backups: $total"
    echo -e "${GREEN}Passed: $passed${NC}"
    if [ $failed -gt 0 ]; then
        echo -e "${RED}Failed: $failed${NC}"
        exit 1
    else
        echo "Failed: 0"
        exit 0
    fi
}

main "$@"
