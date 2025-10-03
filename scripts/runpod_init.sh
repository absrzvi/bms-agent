#!/bin/bash
# RunPod Initialization Script
# Place this in RunPod's startup script field

# Wait for system to be ready
sleep 10

# Create logs directory if it doesn't exist
mkdir -p /workspace/logs

# Install Ollama if not present (since /root is not persistent)
if [ ! -f /usr/local/bin/ollama ]; then
    echo "$(date): Ollama not found, installing..." >> /workspace/logs/startup.log
    curl -fsSL https://ollama.com/install.sh | sh >> /workspace/logs/startup.log 2>&1
    echo "$(date): Ollama installed" >> /workspace/logs/startup.log
fi

# Ensure Ollama models directory exists in persistent storage
mkdir -p /workspace/data/ollama_models
export OLLAMA_MODELS=/workspace/data/ollama_models

# Start BMS Agent services
if [ -f /workspace/scripts/start_all_services.sh ]; then
    echo "$(date): Starting BMS Agent services" >> /workspace/logs/startup.log
    /workspace/scripts/start_all_services.sh >> /workspace/logs/startup.log 2>&1
    echo "$(date): BMS Agent services started" >> /workspace/logs/startup.log
fi
