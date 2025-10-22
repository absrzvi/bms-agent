#!/bin/bash
# BMS Agent - Complete Startup Script
# Run this after pod boots to restore full operational status
# Safe to run multiple times (idempotent)

set -e

# ==================== Color Output Functions ====================
print_header() {
    echo ""
    echo "================================================================================"
    echo "  $1"
    echo "================================================================================"
}

print_green() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_yellow() {
    echo -e "\033[1;33m⚠️  $1\033[0m"
}

print_red() {
    echo -e "\033[0;31m❌ $1\033[0m"
}

print_info() {
    echo -e "\033[0;36mℹ️  $1\033[0m"
}

# ==================== Prerequisite Checks ====================
print_header "BMS Agent Complete Startup Script"

if [ ! -d "/workspace/bms-agent" ]; then
    print_red "BMS Agent directory not found at /workspace/bms-agent"
    exit 1
fi

cd /workspace/bms-agent
print_info "Working directory: $(pwd)"

# ==================== Step 1: Install All Dependencies ====================
print_header "Step 1: Installing All Dependencies"

# Main requirements.txt
if [ -f "requirements.txt" ]; then
    print_info "Installing dependencies from requirements.txt..."
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    print_green "Main dependencies installed"
else
    print_yellow "requirements.txt not found, skipping"
fi

# Backend requirements
if [ -f "bms-agent/reqs/requirements_file.txt" ]; then
    print_info "Installing backend dependencies from requirements_file.txt..."
    pip install -r bms-agent/reqs/requirements_file.txt --quiet
    print_green "Backend dependencies installed"
else
    print_yellow "Backend requirements_file.txt not found, skipping"
fi

# Test requirements (optional)
if [ -f "bms-agent/requirements-test.txt" ]; then
    print_info "Installing test dependencies (optional)..."
    pip install -r bms-agent/requirements-test.txt --quiet 2>/dev/null || print_yellow "Test dependencies skipped"
    print_green "Test dependencies installed"
fi

# ==================== Step 2: Download NLP Resources ====================
print_header "Step 2: Downloading NLP Resources"

# NLTK data
print_info "Downloading NLTK data..."
python3 << 'EOF'
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

required_data = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words']
for data in required_data:
    try:
        nltk.download(data, quiet=True)
    except Exception as e:
        print(f"Warning: Failed to download {data}: {e}")
print("NLTK data download complete")
EOF
print_green "NLTK data downloaded"

# spaCy model
print_info "Downloading spaCy English model..."
python3 -m spacy download en_core_web_sm --quiet 2>/dev/null || print_yellow "spaCy model may already exist"
print_green "spaCy model ready"

# ==================== Step 3: Create Required Directories ====================
print_header "Step 3: Creating Required Directories"

mkdir -p /workspace/qdrant-data
mkdir -p /workspace/ollama
mkdir -p /workspace/openwebui
mkdir -p /workspace/logs
mkdir -p /workspace/visual-artifacts/images
mkdir -p /workspace/visual-artifacts/slides
mkdir -p /workspace/visual-artifacts/thumbnails

print_green "All required directories created"

# ==================== Step 4: Start Services ====================
print_header "Step 4: Starting All Services"

# Function to check if service is running
is_running() {
    pgrep -f "$1" > /dev/null
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_wait=30

    for i in $(seq 1 $max_wait); do
        if curl -s "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

# --- Ollama ---
print_info "Checking Ollama service..."
if is_running "ollama serve"; then
    print_yellow "Ollama already running"
else
    print_info "Starting Ollama..."
    nohup env OLLAMA_HOST=0.0.0.0 OLLAMA_MODELS=/workspace/ollama OLLAMA_KEEP_ALIVE=-1 ollama serve > /workspace/logs/ollama.log 2>&1 &
    sleep 3
    if is_running "ollama serve"; then
        print_green "Ollama started (PID: $(pgrep -f 'ollama serve'))"
    else
        print_red "Failed to start Ollama"
    fi
fi

# --- Qdrant ---
print_info "Checking Qdrant service..."
if is_running "qdrant"; then
    print_yellow "Qdrant already running"
else
    if [ -f "./qdrant" ]; then
        print_info "Starting Qdrant..."
        nohup ./qdrant --storage-path /workspace/qdrant-data > /workspace/logs/qdrant.log 2>&1 &
        sleep 2
        if is_running "qdrant"; then
            print_green "Qdrant started (PID: $(pgrep -x qdrant))"
            if wait_for_service "http://localhost:6333/healthz" "Qdrant"; then
                print_green "Qdrant is healthy and ready"
            else
                print_yellow "Qdrant started but health check timed out"
            fi
        else
            print_red "Failed to start Qdrant"
        fi
    else
        print_red "Qdrant binary not found at ./qdrant"
    fi
fi

# --- OpenWebUI ---
print_info "Checking OpenWebUI service..."
if is_running "open-webui"; then
    print_yellow "OpenWebUI already running"
else
    # Generate secret key if needed
    if [ ! -f "/workspace/openwebui/.webui_secret_key" ]; then
        print_info "Generating WebUI secret key..."
        openssl rand -hex 32 > /workspace/openwebui/.webui_secret_key
    fi

    export WEBUI_SECRET_KEY=$(cat /workspace/openwebui/.webui_secret_key)
    export OLLAMA_API_BASE_URL="http://localhost:11434"
    export OPEN_WEBUI_DIR="/workspace/openwebui"
    export DATA_DIR="$OPEN_WEBUI_DIR/data"
    export WEBUI_HOST="0.0.0.0"
    export WEBUI_PORT="8080"

    mkdir -p "$DATA_DIR"

    print_info "Starting OpenWebUI..."
    cd /workspace/openwebui
    nohup open-webui serve > /workspace/logs/webui.log 2>&1 &
    cd /workspace/bms-agent
    sleep 3
    if is_running "open-webui"; then
        print_green "OpenWebUI started (PID: $(pgrep -f 'open-webui'))"
    else
        print_red "Failed to start OpenWebUI"
    fi
fi

# --- FastAPI ---
print_info "Checking FastAPI service..."
if is_running "uvicorn api.main"; then
    print_yellow "FastAPI already running"
else
    print_info "Starting FastAPI..."
    cd /workspace/bms-agent/bms-agent
    export QDRANT_HOST=localhost
    export QDRANT_PORT=6333
    export QDRANT_COLLECTION=nomad_bms_documents
    nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/api.log 2>&1 &
    cd /workspace/bms-agent
    sleep 2
    if is_running "uvicorn api.main"; then
        print_green "FastAPI started (PID: $(pgrep -f 'uvicorn api.main'))"
        if wait_for_service "http://localhost:8000/health" "FastAPI"; then
            print_green "FastAPI is healthy and ready"
        else
            print_yellow "FastAPI started but health check timed out"
        fi
    else
        print_red "Failed to start FastAPI"
    fi
fi

# ==================== Step 5: Service Status Check ====================
print_header "Step 5: Service Status Summary"

echo ""
printf "%-20s %-15s %-15s %-50s\n" "SERVICE" "STATUS" "PID" "URL"
echo "--------------------------------------------------------------------------------"

# Ollama
if is_running "ollama serve"; then
    printf "%-20s %-15s %-15s %-50s\n" "Ollama" "✅ Running" "$(pgrep -f 'ollama serve')" "http://localhost:11434"
else
    printf "%-20s %-15s %-15s %-50s\n" "Ollama" "❌ Stopped" "-" "http://localhost:11434"
fi

# Qdrant
if is_running "qdrant"; then
    printf "%-20s %-15s %-15s %-50s\n" "Qdrant" "✅ Running" "$(pgrep -x qdrant)" "http://localhost:6333/dashboard"
else
    printf "%-20s %-15s %-15s %-50s\n" "Qdrant" "❌ Stopped" "-" "http://localhost:6333/dashboard"
fi

# OpenWebUI
if is_running "open-webui"; then
    printf "%-20s %-15s %-15s %-50s\n" "OpenWebUI" "✅ Running" "$(pgrep -f 'open-webui')" "http://localhost:8080"
else
    printf "%-20s %-15s %-15s %-50s\n" "OpenWebUI" "❌ Stopped" "-" "http://localhost:8080"
fi

# FastAPI
if is_running "uvicorn api.main"; then
    printf "%-20s %-15s %-15s %-50s\n" "FastAPI" "✅ Running" "$(pgrep -f 'uvicorn api.main')" "http://localhost:8000/docs"
else
    printf "%-20s %-15s %-15s %-50s\n" "FastAPI" "❌ Stopped" "-" "http://localhost:8000/docs"
fi

echo ""

# ==================== Step 6: Verification ====================
print_header "Step 6: System Verification"

# Check Qdrant collection
if is_running "qdrant"; then
    print_info "Verifying Qdrant collection..."
    python3 << 'EOF' 2>/dev/null || print_yellow "Collection verification skipped"
import sys
from qdrant_client import QdrantClient

try:
    client = QdrantClient(host="localhost", port=6333)
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if 'nomad_bms_documents' in collection_names:
        info = client.get_collection('nomad_bms_documents')
        print(f"✅ Collection 'nomad_bms_documents' exists with {info.points_count} points")
    else:
        print("⚠️  Collection 'nomad_bms_documents' not found. Run ingestion to create it.")
except Exception as e:
    print(f"⚠️  Qdrant verification failed: {e}")
EOF
else
    print_yellow "Qdrant not running, skipping collection verification"
fi

# Check visual artifacts directory
ARTIFACT_COUNT=$(find /workspace/visual-artifacts -type f -name "*.png" 2>/dev/null | wc -l)
if [ $ARTIFACT_COUNT -gt 0 ]; then
    print_green "Visual artifacts directory: $ARTIFACT_COUNT images found"
else
    print_yellow "Visual artifacts directory: No images found (run ingestion to populate)"
fi

# ==================== Final Summary ====================
print_header "Startup Complete"

echo ""
print_green "BMS Agent is ready for use!"
echo ""
echo "📍 Persistent storage locations:"
echo "   - Qdrant data:      /workspace/qdrant-data/"
echo "   - Ollama models:    /workspace/ollama/"
echo "   - OpenWebUI data:   /workspace/openwebui/"
echo "   - Visual artifacts: /workspace/visual-artifacts/"
echo "   - Logs:             /workspace/logs/"
echo "   - BMS Agent code:   /workspace/bms-agent/"
echo ""
echo "🌐 Service URLs (accessible from browser):"
echo "   - OpenWebUI:  http://localhost:8080"
echo "   - BMS API:    http://localhost:8000/docs"
echo "   - Qdrant:     http://localhost:6333/dashboard"
echo "   - Ollama:     http://localhost:11434"
echo ""
echo "📚 Next steps:"
echo "   1. Upload documents via OpenWebUI or run batch ingestion:"
echo "      python3 batch_ingest_by_department.py --department HR"
echo ""
echo "   2. Search documents via OpenWebUI using the 'BMS Agent Search' tool"
echo ""
echo "   3. View logs:"
echo "      tail -f /workspace/logs/api.log"
echo "      tail -f /workspace/logs/qdrant.log"
echo "      tail -f /workspace/logs/ollama.log"
echo "      tail -f /workspace/logs/webui.log"
echo ""
echo "🔧 Troubleshooting:"
echo "   - Restart all services: bash /workspace/bms-agent/restart_all.sh"
echo "   - Stop all services:    bash /workspace/bms-agent/stop_all.sh"
echo "   - Check service status: bash /workspace/bms-agent/status.sh"
echo ""
