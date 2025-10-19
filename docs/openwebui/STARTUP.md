# Open WebUI Startup Guide

## Quick Start

### Starting Open WebUI

```bash
cd /workspace/openwebui
./start_openwebui.sh
```

The startup script will:
1. Check that Ollama is running (port 11434)
2. Check that BMS API is running (port 8000)
3. Install BMS Search Tool (if not already installed)
4. Start Open WebUI on port 3000

### Verifying Open WebUI is Running

**Check process:**
```bash
ps aux | grep open-webui | grep -v grep
```

**Check HTTP response:**
```bash
curl -s http://localhost:3000/health
# Should return: {"status":true}
```

**Access web interface:**
- Local: http://localhost:3000
- External: http://<runpod-pod-id>-3000.proxy.runpod.net

### Stopping Open WebUI

```bash
# Find the PID
ps aux | grep open-webui | grep -v grep

# Kill the process
kill <PID>

# Or force kill if needed
pkill -f open-webui
```

### Checking Logs

Logs are written to:
```bash
tail -f /workspace/logs/openwebui.log
```

## Dependencies

Open WebUI requires these services to be running:

### 1. Ollama (LLM Backend)
```bash
# Check if running
curl -s http://localhost:11434/api/tags

# Start if needed (RunPod auto-starts via runpod_init.sh)
/root/ollama serve &
```

### 2. BMS API (Search Backend)
```bash
# Check if running
curl -s http://localhost:8000/health

# Start if needed
cd /workspace/001-bms-agent
source /workspace/bms-api-venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
```

### 3. Qdrant (Vector Database)
```bash
# Check if running
curl -s http://localhost:6333/collections

# Start if needed
/workspace/qdrant --config-path /workspace/qdrant_storage/config.yaml &
```

## Configuration

Configuration file: `/workspace/openwebui/.env`

**Key settings:**
```bash
# Data directory
OPEN_WEBUI_DATA_DIR=/workspace/openwebui/data

# LLM backend
OLLAMA_BASE_URL=http://localhost:11434

# Authentication (MVP: disabled)
WEBUI_AUTH=False
```

## Service Architecture

```
┌─────────────┐
│  Open WebUI │ :3000
│   (Frontend)│
└──────┬──────┘
       │
       ├──────────────┐
       │              │
┌──────▼─────┐  ┌────▼────┐
│   Ollama   │  │ BMS API │ :8000
│    (LLM)   │  │ (Search)│
└────────────┘  └────┬────┘
      :11434         │
                ┌────▼────┐
                │ Qdrant  │ :6333
                │(Vectors)│
                └─────────┘
```

## MVP Notes

- **Authentication:** Disabled for MVP (set `WEBUI_AUTH=False`)
- **Monitoring:** Basic logging only (no Prometheus/Grafana)
- **Performance:** No specific latency targets (aspirational: <100ms p95)

## Reference

For detailed setup and troubleshooting, see:
- `/workspace/specs/006-production-rag-interface/quickstart.md`
- `/workspace/docs/openwebui/TROUBLESHOOTING.md`
