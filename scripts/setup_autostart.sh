#!/bin/bash
# BMS Agent Auto-Start Setup Script

echo "🔧 Setting up BMS Agent Auto-Start"
echo "===================================="
echo ""

# Method 1: Add to .bashrc (runs on login)
echo "1. Adding to .bashrc..."
if ! grep -q "start_all_services.sh" ~/.bashrc 2>/dev/null; then
    cat >> ~/.bashrc << 'EOF'

# BMS Agent Auto-Start
if [ -f /workspace/scripts/start_all_services.sh ]; then
    # Check if services are already running
    if ! pgrep -f "qdrant" > /dev/null 2>&1; then
        echo "🚀 Starting BMS Agent services..."
        /workspace/scripts/start_all_services.sh
    fi
fi
EOF
    echo "   ✅ Added to .bashrc"
else
    echo "   ℹ️  Already in .bashrc"
fi

# Method 2: Create init script for RunPod
echo ""
echo "2. Creating RunPod init script..."
cat > /workspace/scripts/runpod_init.sh << 'EOF'
#!/bin/bash
# RunPod Initialization Script
# Place this in RunPod's startup script field

# Wait for system to be ready
sleep 10

# Start BMS Agent services
if [ -f /workspace/scripts/start_all_services.sh ]; then
    echo "$(date): Starting BMS Agent services" >> /workspace/logs/startup.log
    /workspace/scripts/start_all_services.sh >> /workspace/logs/startup.log 2>&1
    echo "$(date): BMS Agent services started" >> /workspace/logs/startup.log
fi
EOF
chmod +x /workspace/scripts/runpod_init.sh
echo "   ✅ Created /workspace/scripts/runpod_init.sh"

# Method 3: Create systemd service file (for manual installation)
echo ""
echo "3. Creating systemd service template..."
cat > /workspace/scripts/bms-agent.service << 'EOF'
[Unit]
Description=BMS Agent Services
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory=/workspace
ExecStart=/workspace/scripts/start_all_services.sh
RemainAfterExit=yes
StandardOutput=append:/workspace/logs/startup.log
StandardError=append:/workspace/logs/startup.log

[Install]
WantedBy=multi-user.target
EOF
echo "   ✅ Created systemd service template"

# Method 4: Create cron job template
echo ""
echo "4. Creating cron job template..."
cat > /workspace/scripts/crontab.txt << 'EOF'
# BMS Agent Auto-Start
@reboot /workspace/scripts/start_all_services.sh >> /workspace/logs/startup.log 2>&1
EOF
echo "   ✅ Created cron template"

echo ""
echo "=================================="
echo "✅ Auto-Start Setup Complete!"
echo "=================================="
echo ""
echo "📋 Available Methods:"
echo ""
echo "Method 1: .bashrc (ACTIVE)"
echo "   - Starts on shell login"
echo "   - Already configured"
echo ""
echo "Method 2: RunPod Startup Script"
echo "   - Add this to RunPod's startup script field:"
echo "   - /workspace/scripts/runpod_init.sh"
echo ""
echo "Method 3: Systemd (if available)"
echo "   - sudo cp /workspace/scripts/bms-agent.service /etc/systemd/system/"
echo "   - sudo systemctl daemon-reload"
echo "   - sudo systemctl enable bms-agent.service"
echo ""
echo "Method 4: Cron (if available)"
echo "   - crontab /workspace/scripts/crontab.txt"
echo ""
echo "🧪 Test auto-start:"
echo "   - Logout and login again (tests .bashrc)"
echo "   - Or reboot system (tests RunPod/systemd/cron)"
echo ""
echo "📝 Logs:"
echo "   - /workspace/logs/startup.log"
