#!/bin/bash
# BMS Agent Initialization Script for RunPod
# This script sets up the environment on pod startup

set -e

# Color output functions
print_green() {
    echo -e "\033[0;32m[BMS Agent Init]:\033[0m $1"
}

print_yellow() {
    echo -e "\033[1;33m[BMS Agent Warning]:\033[0m $1"
}

print_red() {
    echo -e "\033[0;31m[BMS Agent Error]:\033[0m $1"
}

print_green "Starting BMS Agent initialization..."

# Check if we're in the workspace directory
if [ ! -d "/workspace/bms-agent" ]; then
    print_red "BMS Agent directory not found in /workspace!"
    exit 1
fi

cd /workspace/bms-agent

# Step 1: Configure SSH access
print_green "Configuring SSH access..."
SSH_DIR="/root/.ssh"
AUTHORIZED_KEYS="$SSH_DIR/authorized_keys"
SSH_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKp/hbUNKvpaYJb8uhQoIZ9cFFCXse708DnJwUBygr98 runpod-bms-agent"

# Create .ssh directory if it doesn't exist
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

# Add SSH key to authorized_keys if not already present
if [ -f "$AUTHORIZED_KEYS" ]; then
    if grep -qF "runpod-bms-agent" "$AUTHORIZED_KEYS"; then
        print_yellow "SSH key already present in authorized_keys"
    else
        echo "$SSH_KEY" >> "$AUTHORIZED_KEYS"
        chmod 600 "$AUTHORIZED_KEYS"
        print_green "✅ SSH key added to authorized_keys"
    fi
else
    echo "$SSH_KEY" > "$AUTHORIZED_KEYS"
    chmod 600 "$AUTHORIZED_KEYS"
    print_green "✅ SSH key added to authorized_keys"
fi

# Step 2: Install Python dependencies
print_green "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    print_green "✅ Dependencies installed"
else
    print_yellow "requirements.txt not found, skipping dependency installation"
fi

# Step 3: Download NLTK data (required for text processing)
print_green "Downloading NLTK data..."
python3 -c "
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('words', quiet=True)
print('✅ NLTK data downloaded')
" || print_yellow "NLTK download failed (may already exist)"

# Step 4: Download spaCy model (required for NER)
print_green "Downloading spaCy model..."
python3 -m spacy download en_core_web_sm --quiet 2>/dev/null || print_yellow "spaCy model may already exist"

# Step 5: Ensure Qdrant data directory exists
print_green "Setting up Qdrant data directory..."
mkdir -p /workspace/qdrant-data
print_green "✅ Qdrant data directory ready at /workspace/qdrant-data"

# Step 6: Check if Qdrant binary exists
if [ ! -f "./qdrant" ]; then
    print_yellow "Qdrant binary not found in /workspace/bms-agent/"
    print_yellow "Expected location: /workspace/bms-agent/qdrant"
    print_yellow "Please ensure the Qdrant binary is present"
else
    print_green "✅ Qdrant binary found"
fi

# Step 7: Start Qdrant service
print_green "Starting Qdrant service..."
if pgrep -x "qdrant" > /dev/null; then
    print_yellow "Qdrant is already running"
else
    if [ -f "./qdrant" ]; then
        nohup ./qdrant --storage-path /workspace/qdrant-data > /workspace/logs/qdrant.log 2>&1 &
        QDRANT_PID=$!
        print_green "✅ Qdrant started (PID: $QDRANT_PID)"

        # Wait for Qdrant to be ready
        print_green "Waiting for Qdrant to initialize..."
        for i in {1..30}; do
            if curl -s http://localhost:6333/healthz >/dev/null 2>&1; then
                print_green "✅ Qdrant is healthy and ready!"
                break
            fi
            sleep 1
            echo -n "."
        done
        echo ""
    else
        print_red "Cannot start Qdrant: binary not found"
    fi
fi

# Step 8: Verify collection exists
print_green "Verifying Qdrant collection..."
python3 verify_qdrant.py 2>/dev/null || print_yellow "Collection verification skipped (verify_qdrant.py may not exist)"

# Step 9: Display service status
print_green "==================== Service Status ===================="
echo ""
echo "Ollama:     $(pgrep -x 'ollama' > /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "OpenWebUI:  $(pgrep -f 'open-webui' > /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "Qdrant:     $(pgrep -x 'qdrant' > /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo ""
print_green "========================================================"

# Step 10: Display next steps
echo ""
print_green "BMS Agent initialization complete!"
echo ""
echo "📍 Persistent storage locations:"
echo "   - Qdrant data:     /workspace/qdrant-data/"
echo "   - Ollama models:   /workspace/ollama/"
echo "   - OpenWebUI data:  /workspace/openwebui/"
echo "   - Logs:            /workspace/logs/"
echo "   - BMS Agent:       /workspace/bms-agent/"
echo ""
echo "🚀 Next steps:"
echo "   1. Start the FastAPI server:"
echo "      cd /workspace/bms-agent/bms-agent && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "   2. Access services:"
echo "      - OpenWebUI:  http://localhost:8080"
echo "      - BMS API:    http://localhost:8000/docs"
echo "      - Qdrant:     http://localhost:6333/dashboard"
echo ""
echo "   3. Ingest documents:"
echo "      python3 /workspace/bms-agent/batch_ingest_by_department.py --department HR"
echo ""
