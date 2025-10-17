#!/bin/bash
#
# Setup automated backup cron job
# Configures daily backups at 2 AM
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup_system.sh"
CRON_FILE="/etc/cron.d/bms-backup"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (for cron configuration)"
    echo "Run: sudo $0"
    exit 1
fi

# Verify backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "ERROR: Backup script not found: $BACKUP_SCRIPT"
    exit 1
fi

# Create cron job
cat > "$CRON_FILE" << EOF
# BMS Agent Automated Backup
# Runs daily at 2:00 AM
# Logs to /workspace/logs/backup.log

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Daily backup at 2 AM
0 2 * * * root ${BACKUP_SCRIPT} >> /workspace/logs/backup.log 2>&1

EOF

# Set proper permissions
chmod 0644 "$CRON_FILE"

echo "✓ Cron job configured: $CRON_FILE"
echo "✓ Daily backups scheduled for 2:00 AM"
echo ""
echo "To verify cron job:"
echo "  cat $CRON_FILE"
echo ""
echo "To test backup manually:"
echo "  $BACKUP_SCRIPT"
echo ""
echo "To verify backups:"
echo "  ${SCRIPT_DIR}/verify_backup.sh"

exit 0
