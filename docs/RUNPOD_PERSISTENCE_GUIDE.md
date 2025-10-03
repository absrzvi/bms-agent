# RunPod Persistence Guide for BMS Agent

## Overview

This guide explains how the BMS Agent maintains data persistence on RunPod, where only `/workspace` is persistent across pod restarts.

## Persistent vs Non-Persistent Storage

### ✅ Persistent (Survives Pod Restarts)

All critical data is stored in `/workspace`:

| Directory | Contents | Size | Purpose |
|-----------|----------|------|---------|
| `/workspace/data/qdrant_storage` | Qdrant vector database | ~465MB | Document embeddings and metadata |
| `/workspace/data/ollama_models` | Ollama model files | ~21GB | LLM models (mistral-nemo, etc.) |
| `/workspace/data/openwebui` | OpenWebUI data | ~512 bytes | UI configuration |
| `/workspace/bms_data/` | Processed documents | ~522MB | Uploaded and processed files |
| `/workspace/logs/` | Service logs | ~5.9MB | Application logs |
| `/workspace/apps/qdrant/` | Qdrant binary + config | ~51MB | Qdrant application |
| `/workspace/001-bms-agent/` | BMS Agent code | ~6.0GB | Application code and dependencies |

**Total Persistent Data**: ~28GB

### ⚠️ Non-Persistent (Reinstalled on Startup)

| Item | Location | Auto-Install | Time |
|------|----------|--------------|------|
| Ollama binary | `/usr/local/bin/ollama` | Yes | ~30 seconds |
| System packages | `/root`, `/usr`, `/etc` | Manual if needed | Varies |

## Automatic Startup Configuration

### RunPod Startup Script

The BMS Agent automatically starts all services on pod restart using `/workspace/001-bms-agent/scripts/runpod_init.sh`.

**Add this to RunPod's "Docker Command" or "Start Script" field:**

```bash
bash /workspace/001-bms-agent/scripts/runpod_init.sh
```

### What Happens on Startup

1. **Wait for system** (10 seconds)
2. **Check Ollama installation**
   - If not found: Download and install from https://ollama.com/install.sh
   - Takes ~30 seconds
3. **Set environment variables**
   - `OLLAMA_MODELS=/workspace/data/ollama_models`
4. **Start all services**
   - Qdrant (from `/workspace/apps/qdrant/`)
   - Ollama (with models from `/workspace`)
   - BMS API (port 8000)
   - OpenWebUI (port 3000)

### Startup Logs

Monitor startup progress:
```bash
tail -f /workspace/logs/startup.log
```

## Service Management

### Start All Services
```bash
/workspace/scripts/start_all_services.sh
```

### Check Service Status
```bash
/workspace/001-bms-agent/scripts/health_check.sh
```

### Check Persistence
```bash
/workspace/001-bms-agent/scripts/check_persistence.sh
```

## Configuration Files (All Persistent)

| File | Purpose |
|------|---------|
| `/workspace/apps/qdrant/config.yaml` | Qdrant configuration |
| `/workspace/001-bms-agent/config/config.yaml` | BMS Agent config |
| `/workspace/scripts/env.sh` | Environment variables |
| `/workspace/001-bms-agent/.env` | API keys and secrets |

## Ollama Models Persistence

### Current Setup

- **Models Location**: `/workspace/data/ollama_models` (persistent)
- **Binary Location**: `/usr/local/bin/ollama` (non-persistent, auto-installed)
- **Environment Variable**: `OLLAMA_MODELS=/workspace/data/ollama_models`

### Verify Models After Restart

```bash
export OLLAMA_MODELS=/workspace/data/ollama_models
ollama list
```

Expected output:
```
NAME                    ID              SIZE    MODIFIED
mistral-nemo:latest     ...             7.1GB   ...
mistral-small:latest    ...             7.7GB   ...
```

### Pull New Models

Models are automatically saved to `/workspace/data/ollama_models`:

```bash
export OLLAMA_MODELS=/workspace/data/ollama_models
ollama pull llama3.1:8b
```

## Data Backup Strategy

### What to Backup

**Critical (Must backup)**:
1. `/workspace/data/qdrant_storage` - Vector database
2. `/workspace/bms_data/processed` - Processed documents
3. `/workspace/001-bms-agent/config/` - Configuration files

**Important (Recommended)**:
4. `/workspace/data/ollama_models` - LLM models (large, can re-download)
5. `/workspace/logs/` - Service logs (for debugging)

**Optional**:
6. `/workspace/001-bms-agent/` - Code (can re-clone from git)

### Backup Commands

```bash
# Quick backup (critical data only)
tar -czf /workspace/backups/bms-critical-$(date +%Y%m%d).tar.gz \
    /workspace/data/qdrant_storage \
    /workspace/bms_data/processed \
    /workspace/001-bms-agent/config

# Full backup (includes models)
tar -czf /workspace/backups/bms-full-$(date +%Y%m%d).tar.gz \
    /workspace/data \
    /workspace/bms_data \
    /workspace/001-bms-agent/config \
    /workspace/logs
```

### Restore from Backup

```bash
# Extract backup
tar -xzf /workspace/backups/bms-critical-YYYYMMDD.tar.gz -C /

# Restart services
/workspace/scripts/start_all_services.sh
```

## Troubleshooting

### Pod Restarted - Services Not Running

**Check startup log:**
```bash
tail -100 /workspace/logs/startup.log
```

**Manually start services:**
```bash
/workspace/scripts/start_all_services.sh
```

### Ollama Not Found After Restart

**Reinstall Ollama:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
export OLLAMA_MODELS=/workspace/data/ollama_models
ollama serve &
```

### Qdrant Data Missing

**Check collection:**
```bash
curl http://localhost:6333/collections/nomad_bms_documents
```

**Restore from backup if needed:**
```bash
tar -xzf /workspace/backups/bms-critical-YYYYMMDD.tar.gz -C /
/workspace/apps/qdrant/qdrant --config-path /workspace/apps/qdrant/config.yaml &
```

### Models Not Loading

**Verify models directory:**
```bash
ls -lh /workspace/data/ollama_models/
```

**Set environment and restart Ollama:**
```bash
export OLLAMA_MODELS=/workspace/data/ollama_models
pkill ollama
ollama serve &
```

## Verification Checklist

After pod restart, verify:

- [ ] Ollama binary installed (`which ollama`)
- [ ] Ollama models accessible (`ollama list`)
- [ ] Qdrant running (`curl http://localhost:6333/health`)
- [ ] BMS API running (`curl http://localhost:8000/health`)
- [ ] OpenWebUI accessible (http://localhost:3000)
- [ ] Documents in Qdrant (`curl http://localhost:6333/collections/nomad_bms_documents`)

## Quick Reference

### Service URLs
- **OpenWebUI**: http://localhost:3000
- **BMS API**: http://localhost:8000
- **Qdrant**: http://localhost:6333
- **Ollama**: http://localhost:11434

### Important Paths
- **Persistent Storage**: `/workspace/`
- **Qdrant Data**: `/workspace/data/qdrant_storage`
- **Ollama Models**: `/workspace/data/ollama_models`
- **BMS Documents**: `/workspace/bms_data/`
- **Logs**: `/workspace/logs/`

### Key Commands
```bash
# Check persistence
/workspace/001-bms-agent/scripts/check_persistence.sh

# Start all services
/workspace/scripts/start_all_services.sh

# Check health
/workspace/001-bms-agent/scripts/health_check.sh

# View logs
tail -f /workspace/logs/startup.log
tail -f /workspace/logs/api.log
tail -f /workspace/logs/qdrant.log
tail -f /workspace/logs/ollama.log
```

## Summary

✅ **All critical data is in `/workspace` (persistent)**  
✅ **Ollama models preserved across restarts**  
✅ **Automatic service startup configured**  
⚠️ **Ollama binary auto-installs on startup (~30 seconds)**  
✅ **No data loss on pod restart**  

The BMS Agent is fully configured for RunPod persistence. All data, models, and configurations survive pod restarts.
