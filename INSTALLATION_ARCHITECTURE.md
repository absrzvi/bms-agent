# BMS Agent Installation Architecture

**Version:** 1.1  
**Date:** 2025-10-04  
**Constitution Reference:** §11 - AI/LLM Architecture  
**Deployment Target:** RunPod Pods (NOT Docker containers)

## Overview

This document defines the installation architecture for the BMS Agent system running in **RunPod pods** (not Docker), ensuring proper persistence and GPU compatibility.

## Critical Context: RunPod Pod Environment

**Important:** This system runs in RunPod pods, NOT Docker containers:
- RunPod pods are virtual machines with GPU access
- Only `/workspace` directory persists across pod restarts
- Everything outside `/workspace` is ephemeral (lost on restart)
- System packages and `/root` are reset on each pod start
- No Docker containerization - direct pod deployment

## Core Principle

**All applications, libraries, and data MUST be installed in `/workspace` (persistent storage) to survive pod restarts, with ONE exception: Ollama binary.**

**Why `/workspace` only?**
- RunPod pods only persist the `/workspace` volume
- All other directories (`/root`, `/usr`, `/opt`, etc.) are ephemeral
- Pod restarts wipe everything except `/workspace`

## Directory Structure

### Persistent Storage (`/workspace`)

```
/workspace/
├── 001-bms-agent/              # Project repository
│   ├── api/                    # FastAPI application
│   ├── bms-agent/              # Document processor
│   ├── scripts/                # Utility scripts
│   ├── requirements.txt        # Python dependencies
│   └── ...
├── bms-api-venv/               # Python virtual environment (CRITICAL)
│   ├── bin/
│   ├── lib/
│   └── ...
├── data/
│   └── ollama_models/          # Ollama model storage (persistent)
├── qdrant_storage/             # Qdrant vector database
├── bms_data/                   # BMS document storage
├── backups/                    # System backups
├── nltk_data/                  # NLTK data (persistent) ✨ NEW
├── config/
│   ├── authorized_keys         # SSH keys
│   └── env.sh                  # Environment variables
└── logs/                       # Application logs
    ├── api.log
    ├── qdrant.log
    ├── ollama.log
    ├── runpod_init.log
    └── startup.log
```

### Non-Persistent Storage (`/root` and system directories)

```
/root/
└── .ollama/                    # Ollama installation (GPU compatibility)
    └── (Ollama binary and runtime - EPHEMERAL, reinstalled on each pod start)

/usr/local/bin/
└── ollama                      # Ollama binary (EPHEMERAL, reinstalled on each pod start)
```

**Critical Notes:**
- **Ollama binary location is ephemeral** - wiped on pod restart
- **Ollama MUST be reinstalled** on each pod start (handled by `runpod_init.sh`)
- **Ollama models are persistent** - stored in `/workspace/data/ollama_models` via `OLLAMA_MODELS` environment variable
- **System packages are ephemeral** - reinstalled on each pod start (jq, etc.)
- **NLTK data is NOW PERSISTENT** ✨ - stored in `/workspace/nltk_data` via `NLTK_DATA` environment variable

## Installation Locations

| Component | Location | Reason | Persistent |
|-----------|----------|--------|------------|
| Python venv | `/workspace/bms-api-venv` | Persist installed packages | ✅ Yes |
| Python packages | `/workspace/bms-api-venv/lib/` | Avoid reinstalling on restart | ✅ Yes |
| **NLTK data** | **`/workspace/nltk_data`** ✨ | **Persist NLTK resources** | **✅ Yes (NEW!)** |
| Qdrant binary | `/workspace/qdrant` | Persist application | ✅ Yes |
| Qdrant data | `/workspace/qdrant_storage` | Persist vector database | ✅ Yes |
| Ollama binary | `/root/.ollama` or `/usr/local/bin/ollama` | GPU compatibility | ❌ No (reinstalled by init script) |
| Ollama models | `/workspace/data/ollama_models` | Persist large model files | ✅ Yes |
| BMS data | `/workspace/bms_data` | Persist documents | ✅ Yes |
| Logs | `/workspace/logs` | Persist logs | ✅ Yes |
| Backups | `/workspace/backups` | Persist backups | ✅ Yes |
| Config | `/workspace/config` | Environment variables, SSH keys | ✅ Yes |

## Why Ollama in `/root`? (RunPod Pod Specific)

**GPU Compatibility Issue in RunPod Pods:**
- Ollama requires specific system integration for GPU access
- Default installation in `/root` ensures proper CUDA/GPU driver binding
- Installing in `/workspace` can cause GPU detection failures
- RunPod pods reset `/root` on each restart, so Ollama must be reinstalled

**Solution for RunPod Pods:**
- Ollama binary: `/root` or `/usr/local/bin` (EPHEMERAL - reinstalled on each pod start)
- Ollama models: `/workspace/data/ollama_models` (PERSISTENT)
- Environment variable: `OLLAMA_MODELS=/workspace/data/ollama_models`
- Initialization script automatically reinstalls Ollama on each pod start
- Models are NOT re-downloaded (already in `/workspace`)

**Trade-off:**
- Small overhead: ~30 seconds to reinstall Ollama on pod start
- Benefit: GPU compatibility maintained
- Models (large files) remain persistent, saving bandwidth and time

## Initialization Process

### RunPod Startup Script (`scripts/runpod_init.sh`)

The initialization script ensures proper setup on every pod start:

#### Phase 1: Directory Structure
```bash
mkdir -p /workspace/logs
mkdir -p /workspace/data/ollama_models
mkdir -p /workspace/qdrant_storage
mkdir -p /workspace/bms_data
mkdir -p /workspace/backups
```

#### Phase 2: Ollama Installation
```bash
# Install in /root for GPU compatibility
if [ ! -f /usr/local/bin/ollama ]; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Configure to use persistent storage for models
export OLLAMA_MODELS=/workspace/data/ollama_models
```

#### Phase 3: Python Environment
```bash
# Create venv in persistent storage
if [ ! -d /workspace/bms-api-venv ]; then
    python3 -m venv /workspace/bms-api-venv
fi

# Install dependencies
source /workspace/bms-api-venv/bin/activate
pip install --upgrade pip
pip install -r /workspace/001-bms-agent/requirements.txt
```

#### Phase 4: NLTK Data
```bash
# Download required NLTK data
python -c "
import nltk
nltk.download('punkt_tab')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
# ... etc
"
```

#### Phase 5: Ollama Models
```bash
# Start Ollama service
ollama serve &

# Pull models if not present
ollama pull nomic-embed-text
ollama pull mistral
```

#### Phase 6: Start Services
```bash
# Start all BMS Agent services
bash /workspace/001-bms-agent/scripts/start_all_services.sh
```

## Dependencies Management

### requirements.txt

All Python dependencies are defined in `requirements.txt`:

```txt
# FastAPI & Web Framework
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6

# Natural Language Processing
nltk>=3.8.1
spacy>=3.5.0
transformers>=4.35.0
sentence-transformers>=2.2.2

# Data Processing
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0

# Document Processing
PyMuPDF>=1.23.0
beautifulsoup4>=4.12.0
Pillow>=10.0.0
python-docx>=0.8.11
python-pptx>=0.6.21
pdfplumber>=0.10.0

# Vector Database & Search
qdrant-client>=1.7.0

# Utilities
tqdm>=4.66.0
python-dotenv>=1.0.0
pyyaml>=6.0
requests>=2.31.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0

# Optional Advanced Features
scikit-learn>=1.3.0
```

### NLTK Data Files

Required NLTK data (downloaded by init script):
- `punkt_tab` - Tokenizer
- `punkt` - Sentence tokenizer
- `wordnet` - Lexical database
- `stopwords` - Stop words list
- `averaged_perceptron_tagger` - POS tagger
- `maxent_ne_chunker` - Named entity chunker
- `words` - Word list

### System Packages

Installed via apt-get:
- `jq` - JSON processor
- (Others as needed)

## Verification

### Check Installation Locations

```bash
# Verify venv location
ls -la /workspace/bms-api-venv/

# Verify packages installed
source /workspace/bms-api-venv/bin/activate
pip list | grep -E "fastapi|nltk|qdrant|pandas"

# Verify Ollama location
which ollama
# Should show: /usr/local/bin/ollama or /root/.ollama/bin/ollama

# Verify Ollama models location
echo $OLLAMA_MODELS
# Should show: /workspace/data/ollama_models

ls -la /workspace/data/ollama_models/

# Verify NLTK data
python -c "import nltk; print(nltk.data.path)"
```

### Check Services

```bash
# Check all services
./scripts/health_check.sh

# Check specific services
pgrep -f "ollama"
pgrep -f "qdrant"
pgrep -f "uvicorn api.main:app"
pgrep -f "open-webui"
```

### Check Logs

```bash
# Initialization log
tail -100 /workspace/logs/runpod_init.log

# Service logs
tail -50 /workspace/logs/api.log
tail -50 /workspace/logs/qdrant.log
tail -50 /workspace/logs/ollama.log
```

## Troubleshooting

### Issue: Packages Not Found After Restart

**Cause:** Virtual environment not in `/workspace`  
**Solution:** Ensure venv is at `/workspace/bms-api-venv`

```bash
# Check venv location
ls -la /workspace/bms-api-venv/

# Recreate if needed
python3 -m venv /workspace/bms-api-venv
source /workspace/bms-api-venv/bin/activate
pip install -r requirements.txt
```

### Issue: Ollama GPU Not Working

**Cause:** Ollama installed in `/workspace` instead of `/root`  
**Solution:** Reinstall Ollama in default location

```bash
# Remove incorrect installation
rm -rf /workspace/ollama

# Reinstall in /root
curl -fsSL https://ollama.com/install.sh | sh

# Configure models directory
export OLLAMA_MODELS=/workspace/data/ollama_models
```

### Issue: NLTK Data Not Found

**Cause:** NLTK data not downloaded  
**Solution:** Download required data

```bash
source /workspace/bms-api-venv/bin/activate
python -c "
import nltk
nltk.download('punkt_tab')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
"
```

### Issue: Models Disappear After Restart

**Cause:** `OLLAMA_MODELS` not set  
**Solution:** Ensure environment variable is set

```bash
# Add to startup script
export OLLAMA_MODELS=/workspace/data/ollama_models

# Verify
echo $OLLAMA_MODELS
ls -la $OLLAMA_MODELS/
```

## Best Practices

### 1. Always Use Virtual Environment
```bash
source /workspace/bms-api-venv/bin/activate
```

### 2. Set OLLAMA_MODELS Before Starting Ollama
```bash
export OLLAMA_MODELS=/workspace/data/ollama_models
ollama serve
```

### 3. Install New Packages in Venv
```bash
source /workspace/bms-api-venv/bin/activate
pip install <package>
pip freeze > requirements.txt
```

### 4. Check Logs Regularly
```bash
tail -f /workspace/logs/runpod_init.log
```

### 5. Backup Critical Data
```bash
./scripts/backup_system.sh
```

## Constitution Compliance

This architecture complies with Constitution §11:

✅ **All applications/libraries in `/workspace`** (persistent)  
✅ **Python venv in `/workspace/bms-api-venv`**  
✅ **All data directories in `/workspace`**  
✅ **Exception: Ollama in `/root`** (for GPU compatibility)  
✅ **Ollama models in `/workspace/data/ollama_models`** (persistent)  
✅ **`requirements.txt` installed via `runpod_init.sh`**

## Summary

**Key Points:**
1. Everything in `/workspace` except Ollama binary
2. Python venv at `/workspace/bms-api-venv`
3. Ollama binary in `/root` for GPU
4. Ollama models in `/workspace/data/ollama_models`
5. All dependencies auto-installed by `runpod_init.sh`
6. NLTK data downloaded automatically
7. Services start automatically on pod boot

**Result:** Complete persistence across pod restarts with full GPU support.

---

**Last Updated:** 2025-10-04  
**Maintained By:** BMS Agent Team
