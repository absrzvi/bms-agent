#!/bin/bash
# BMS Agent - Stop All Services

print_green() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_info() {
    echo -e "\033[0;36mℹ️  $1\033[0m"
}

echo "============================================"
echo "  Stopping All BMS Agent Services"
echo "============================================"
echo ""

# Stop FastAPI
print_info "Stopping FastAPI..."
pkill -f "uvicorn api.main" && print_green "FastAPI stopped" || echo "FastAPI not running"

# Stop OpenWebUI
print_info "Stopping OpenWebUI..."
pkill -f "open-webui" && print_green "OpenWebUI stopped" || echo "OpenWebUI not running"

# Stop Qdrant
print_info "Stopping Qdrant..."
pkill -x "qdrant" && print_green "Qdrant stopped" || echo "Qdrant not running"

# Stop Ollama
print_info "Stopping Ollama..."
pkill -f "ollama serve" && print_green "Ollama stopped" || echo "Ollama not running"

echo ""
print_green "All services stopped"
echo ""
echo "To restart, run: bash /workspace/bms-agent/start_all.sh"
echo ""
