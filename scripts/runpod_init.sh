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
