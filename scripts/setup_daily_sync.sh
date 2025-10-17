#!/bin/bash
"""
Setup Daily SharePoint Sync

This script sets up automated daily synchronization using cron or systemd timer.
"""

set -e

PROJECT_DIR="/workspace/001-bms-agent"
SCRIPT_PATH="$PROJECT_DIR/scripts/sharepoint_sync_manager.py"
LOG_DIR="/workspace/logs"
VENV_PATH="$PROJECT_DIR/.venv"

echo "🔧 Setting up Daily SharePoint Sync"
echo "=" | tr -s '=' | head -c 70; echo

# Create log directory
mkdir -p "$LOG_DIR"
echo "✅ Log directory: $LOG_DIR"

# Make script executable
chmod +x "$SCRIPT_PATH"
echo "✅ Script executable: $SCRIPT_PATH"

# Method 1: Cron Job (Recommended for simplicity)
echo ""
echo "📅 Method 1: Cron Job"
echo "─────────────────────────────────────────────────────────────────"

CRON_CMD="0 2 * * * cd $PROJECT_DIR && $VENV_PATH/bin/python $SCRIPT_PATH >> $LOG_DIR/sharepoint_sync_cron.log 2>&1"

echo "Add this line to your crontab:"
echo ""
echo "$CRON_CMD"
echo ""
echo "To install:"
echo "  crontab -e"
echo "  # Add the line above"
echo "  # Save and exit"
echo ""
echo "This will run daily at 2:00 AM"

# Method 2: Systemd Timer (More robust)
echo ""
echo "📅 Method 2: Systemd Timer"
echo "─────────────────────────────────────────────────────────────────"

# Create systemd service file
SERVICE_FILE="/tmp/sharepoint-sync.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=SharePoint Document Sync
After=network.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_PATH/bin/python $SCRIPT_PATH
StandardOutput=append:$LOG_DIR/sharepoint_sync.log
StandardError=append:$LOG_DIR/sharepoint_sync_error.log

[Install]
WantedBy=multi-user.target
EOF

# Create systemd timer file
TIMER_FILE="/tmp/sharepoint-sync.timer"
cat > "$TIMER_FILE" << EOF
[Unit]
Description=Daily SharePoint Document Sync
Requires=sharepoint-sync.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "Created systemd files:"
echo "  Service: $SERVICE_FILE"
echo "  Timer: $TIMER_FILE"
echo ""
echo "To install:"
echo "  sudo cp $SERVICE_FILE /etc/systemd/system/"
echo "  sudo cp $TIMER_FILE /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable sharepoint-sync.timer"
echo "  sudo systemctl start sharepoint-sync.timer"
echo ""
echo "To check status:"
echo "  sudo systemctl status sharepoint-sync.timer"
echo "  sudo systemctl list-timers"

# Method 3: Simple wrapper script for manual/testing
echo ""
echo "📅 Method 3: Manual/Testing Script"
echo "─────────────────────────────────────────────────────────────────"

WRAPPER_SCRIPT="$PROJECT_DIR/scripts/run_sync.sh"
cat > "$WRAPPER_SCRIPT" << 'EOF'
#!/bin/bash
# Quick wrapper to run sync manually

cd /workspace/001-bms-agent
source .venv/bin/activate
python scripts/sharepoint_sync_manager.py "$@"
EOF

chmod +x "$WRAPPER_SCRIPT"
echo "Created wrapper script: $WRAPPER_SCRIPT"
echo ""
echo "Usage:"
echo "  ./scripts/run_sync.sh                    # Daily sync"
echo "  ./scripts/run_sync.sh --lookback-days 7  # Last 7 days"
echo "  ./scripts/run_sync.sh --download-only    # Download only"

# Summary
echo ""
echo "=" | tr -s '=' | head -c 70; echo
echo "✅ Setup Complete!"
echo "=" | tr -s '=' | head -c 70; echo
echo ""
echo "📝 Next Steps:"
echo "  1. Export SharePoint cookies (if not done)"
echo "  2. Choose a scheduling method above"
echo "  3. Test manually first: ./scripts/run_sync.sh --download-only"
echo "  4. Check logs: tail -f $LOG_DIR/sharepoint_sync.log"
echo ""
echo "📁 Directory Structure:"
echo "  /workspace/bms_data/"
echo "  ├── incoming/     # Downloaded files (by type)"
echo "  ├── processing/   # Currently being processed"
echo "  ├── processed/    # Successfully processed (archive)"
echo "  └── failed/       # Failed documents (with error logs)"
echo ""
