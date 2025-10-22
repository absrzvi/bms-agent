# BMS Agent Startup Scripts

Complete guide for managing BMS Agent services on RunPod pods.

## Quick Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `start_all.sh` | **Complete startup** - Install all dependencies and start all services | `bash start_all.sh` |
| `stop_all.sh` | Stop all services | `bash stop_all.sh` |
| `restart_all.sh` | Restart all services | `bash restart_all.sh` |
| `status.sh` | Check status of all services | `bash status.sh` |
| `init.sh` | First-time setup (legacy, use start_all.sh instead) | `bash init.sh` |

---

## Main Script: `start_all.sh`

**Purpose**: Complete startup script that restores BMS Agent to full operational status after pod boot.

### What It Does

1. **Installs ALL dependencies**:
   - Main requirements (`requirements.txt`)
   - Backend requirements (`bms-agent/reqs/requirements_file.txt`)
   - Test requirements (`bms-agent/requirements-test.txt`)

2. **Downloads NLP resources**:
   - NLTK data (punkt, stopwords, wordnet, POS tagger, NER chunker)
   - spaCy English model (`en_core_web_sm`)

3. **Creates required directories**:
   - `/workspace/qdrant-data/` (vector database storage)
   - `/workspace/ollama/` (LLM models)
   - `/workspace/openwebui/` (WebUI data)
   - `/workspace/logs/` (service logs)
   - `/workspace/visual-artifacts/` (images, slides, thumbnails)

4. **Starts all services**:
   - **Ollama** (LLM server) → `localhost:11434`
   - **Qdrant** (vector database) → `localhost:6333`
   - **OpenWebUI** (chat interface) → `localhost:8080`
   - **FastAPI** (BMS backend) → `localhost:8000`

5. **Verifies system health**:
   - Checks service status
   - Verifies Qdrant collection
   - Counts visual artifacts
   - Reports storage usage

### When to Use

- **After pod boot**: Run this script to restore full operational status
- **After code updates**: Ensures all new dependencies are installed
- **After crashes**: Restarts all services from a clean state
- **When debugging**: Provides comprehensive status output

### Usage

```bash
cd /workspace/bms-agent
bash start_all.sh
```

### Features

- ✅ **Idempotent**: Safe to run multiple times (won't duplicate running services)
- ✅ **Smart detection**: Skips services that are already running
- ✅ **Health checks**: Waits for services to be ready before proceeding
- ✅ **Detailed output**: Color-coded status messages for easy debugging
- ✅ **Error handling**: Continues even if optional components fail

---

## Supporting Scripts

### `stop_all.sh`

Stops all BMS Agent services gracefully.

**Usage**:
```bash
bash stop_all.sh
```

**Stops**:
- FastAPI
- OpenWebUI
- Qdrant
- Ollama

**Note**: Does NOT delete any data. All persistent storage remains intact.

---

### `restart_all.sh`

Convenient wrapper that stops all services, waits 3 seconds, then runs `start_all.sh`.

**Usage**:
```bash
bash restart_all.sh
```

**When to use**:
- After configuration changes
- To clear memory leaks
- When services become unresponsive

---

### `status.sh`

Comprehensive status check of all services and data.

**Usage**:
```bash
bash status.sh
```

**Shows**:
- Service status (running/stopped)
- Process IDs (PIDs)
- Health check results
- Service URLs
- Qdrant collection statistics
- Visual artifacts count
- Storage usage breakdown
- Recent log activity (last 5 lines from each log)

**Sample Output**:
```
SERVICE              STATUS          PID             HEALTH          URL
-------------------------------------------------------------------------------------------------------------
Ollama               ✅ Running     214             ✅ Healthy     http://localhost:11434
Qdrant               ✅ Running     336052          ✅ Healthy     http://localhost:6333/dashboard
OpenWebUI            ✅ Running     326773          ✅ Healthy     http://localhost:8080
FastAPI              ✅ Running     337734          ✅ Healthy     http://localhost:8000/docs
```

---

## Service Details

### 1. Ollama

**Purpose**: Large Language Model server (runs Mistral, Llama, etc.)

**Port**: `11434`
**URL**: http://localhost:11434
**Log**: `/workspace/logs/ollama.log`
**Models**: `/workspace/ollama/` (persistent)

**Environment**:
- `OLLAMA_HOST=0.0.0.0` (accessible from all interfaces)
- `OLLAMA_MODELS=/workspace/ollama` (persistent storage)
- `OLLAMA_KEEP_ALIVE=-1` (keep models loaded indefinitely)

**Manual Start**:
```bash
nohup env OLLAMA_HOST=0.0.0.0 OLLAMA_MODELS=/workspace/ollama OLLAMA_KEEP_ALIVE=-1 ollama serve > /workspace/logs/ollama.log 2>&1 &
```

---

### 2. Qdrant

**Purpose**: Vector database for semantic search

**Port**: `6333`
**URL**: http://localhost:6333/dashboard
**Log**: `/workspace/logs/qdrant.log`
**Data**: `/workspace/qdrant-data/` (persistent)

**Collection**: `nomad_bms_documents`

**Manual Start**:
```bash
cd /workspace/bms-agent
nohup ./qdrant --storage-path /workspace/qdrant-data > /workspace/logs/qdrant.log 2>&1 &
```

**Verify Health**:
```bash
curl http://localhost:6333/healthz
```

---

### 3. OpenWebUI

**Purpose**: Chat interface for interacting with LLMs and BMS Agent

**Port**: `8080`
**URL**: http://localhost:8080
**Log**: `/workspace/logs/webui.log`
**Data**: `/workspace/openwebui/` (persistent)

**Environment**:
- `WEBUI_HOST=0.0.0.0`
- `WEBUI_PORT=8080`
- `OLLAMA_API_BASE_URL=http://localhost:11434`
- `OPEN_WEBUI_DIR=/workspace/openwebui`

**Manual Start**:
```bash
cd /workspace/openwebui
export WEBUI_SECRET_KEY=$(cat /workspace/openwebui/.webui_secret_key)
export OLLAMA_API_BASE_URL="http://localhost:11434"
export OPEN_WEBUI_DIR="/workspace/openwebui"
export WEBUI_HOST="0.0.0.0"
export WEBUI_PORT="8080"
nohup open-webui serve > /workspace/logs/webui.log 2>&1 &
```

---

### 4. FastAPI

**Purpose**: BMS Agent backend API (document ingestion, search, etc.)

**Port**: `8000`
**URL**: http://localhost:8000/docs (Swagger UI)
**Log**: `/workspace/logs/api.log`
**Code**: `/workspace/bms-agent/bms-agent/`

**Environment**:
- `QDRANT_HOST=localhost`
- `QDRANT_PORT=6333`
- `QDRANT_COLLECTION=nomad_bms_documents`

**Manual Start**:
```bash
cd /workspace/bms-agent/bms-agent
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export QDRANT_COLLECTION=nomad_bms_documents
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/api.log 2>&1 &
```

---

## Persistent Storage Locations

**CRITICAL**: Only `/workspace` is persistent on RunPod. Everything else is ephemeral.

| Directory | Purpose | Size (typical) |
|-----------|---------|----------------|
| `/workspace/qdrant-data/` | Vector database storage | ~13GB |
| `/workspace/ollama/` | LLM models | ~23GB |
| `/workspace/openwebui/` | WebUI data, chats, config | ~100MB |
| `/workspace/visual-artifacts/` | Extracted images, slides | ~250MB |
| `/workspace/logs/` | Service logs | ~2MB |
| `/workspace/bms-agent/` | Application code | ~100MB |

**Total**: ~36GB

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs for errors
tail -100 /workspace/logs/ollama.log
tail -100 /workspace/logs/qdrant.log
tail -100 /workspace/logs/webui.log
tail -100 /workspace/logs/api.log

# Check if port is already in use
lsof -i :8000  # FastAPI
lsof -i :8080  # OpenWebUI
lsof -i :6333  # Qdrant
lsof -i :11434 # Ollama

# Kill stuck processes
pkill -9 -f "uvicorn api.main"
```

### Service Crashes Repeatedly

```bash
# Restart with fresh logs
bash stop_all.sh
rm /workspace/logs/*.log
bash start_all.sh
```

### Qdrant Collection Missing

```bash
# Verify collection exists
python3 verify_qdrant.py

# Reingest documents
python3 batch_ingest_by_department.py --department HR
```

### Dependencies Missing

```bash
# Reinstall all dependencies
bash start_all.sh
# (dependencies are installed automatically)
```

### Out of Memory

```bash
# Check memory usage
free -h

# Restart Ollama (frees GPU memory)
pkill ollama
nohup env OLLAMA_HOST=0.0.0.0 OLLAMA_MODELS=/workspace/ollama OLLAMA_KEEP_ALIVE=-1 ollama serve > /workspace/logs/ollama.log 2>&1 &
```

---

## Auto-Start on Pod Boot

The `/pre_start.sh` script automatically runs when the pod boots and starts:
- Ollama
- Qdrant (if binary exists)
- OpenWebUI

**FastAPI does NOT auto-start**. You must run `start_all.sh` to start it.

### Make `start_all.sh` Run on Boot (Optional)

Add to `/pre_start.sh` at the end:

```bash
# Auto-start BMS Agent
if [ -f "/workspace/bms-agent/start_all.sh" ]; then
    bash /workspace/bms-agent/start_all.sh
fi
```

---

## Common Workflows

### After Pod Reboot
```bash
bash /workspace/bms-agent/start_all.sh
```

### Deploy Code Changes
```bash
# 1. Update code (git pull, file edits, etc.)
# 2. Restart services
bash /workspace/bms-agent/restart_all.sh
```

### Check System Health
```bash
bash /workspace/bms-agent/status.sh
```

### Full System Reset
```bash
# Stop all services
bash /workspace/bms-agent/stop_all.sh

# Clear logs
rm /workspace/logs/*.log

# Start fresh
bash /workspace/bms-agent/start_all.sh
```

### Update Dependencies
```bash
# Edit requirements.txt
# Then run
bash /workspace/bms-agent/start_all.sh
# Dependencies are automatically reinstalled
```

---

## Advanced Usage

### Run Individual Services

```bash
# Start only Qdrant
cd /workspace/bms-agent
nohup ./qdrant --storage-path /workspace/qdrant-data > /workspace/logs/qdrant.log 2>&1 &

# Start only FastAPI
cd /workspace/bms-agent/bms-agent
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Monitor Logs in Real-Time

```bash
# All logs
tail -f /workspace/logs/*.log

# Specific service
tail -f /workspace/logs/api.log
```

### Background vs Foreground

**Background** (default in scripts):
```bash
nohup command > /workspace/logs/service.log 2>&1 &
```

**Foreground** (for debugging):
```bash
# FastAPI with live reload
cd /workspace/bms-agent/bms-agent
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Changelog

**2025-10-22** - Initial version
- Created `start_all.sh` (comprehensive startup)
- Created `stop_all.sh` (graceful shutdown)
- Created `restart_all.sh` (convenience wrapper)
- Created `status.sh` (detailed status check)
- Fixed 422 error in `bms_search.py` (removed invalid `min_score` field)

---

## Support

For issues or questions:
- Check logs: `tail -100 /workspace/logs/*.log`
- Run status: `bash status.sh`
- See CLAUDE.md for architecture details
- See README.md for API documentation
