#!/bin/bash
# BMS Agent - Restart All Services

print_green() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_info() {
    echo -e "\033[0;36mℹ️  $1\033[0m"
}

echo "============================================"
echo "  Restarting All BMS Agent Services"
echo "============================================"
echo ""

# Stop all services first
bash /workspace/bms-agent/stop_all.sh

# Wait for services to shut down
print_info "Waiting for services to shut down..."
sleep 3

# Start all services
bash /workspace/bms-agent/start_all.sh
