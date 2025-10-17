# Startup Script Fix - Model Download Issue

**Date**: 2025-10-03  
**Issue**: RunPod initialization script was automatically downloading mistral-nemo:12b-instruct model on every pod restart  
**Impact**: Caused unnecessary delays and bandwidth usage during pod startup

## Problem

The `scripts/runpod_init_v2.sh` script contained logic that would:
1. Check if `mistral-nemo:12b-instruct` model exists
2. If not found, automatically download it (7+ GB download)
3. This happened on every pod restart if models weren't in persistent storage

**Original Code** (lines 116-125):
```bash
# 5. Pre-load Ollama Models
log "Step 5: Checking Ollama models..."
REQUIRED_MODEL="mistral-nemo:12b-instruct"
if OLLAMA_MODELS=/workspace/data/ollama_models ollama list | grep -q "$REQUIRED_MODEL"; then
    log "✅ Model $REQUIRED_MODEL already available"
else
    log "Pulling model $REQUIRED_MODEL (this may take several minutes)..."
    OLLAMA_MODELS=/workspace/data/ollama_models ollama pull "$REQUIRED_MODEL" >> "$LOG_FILE" 2>&1
    log "✅ Model $REQUIRED_MODEL downloaded"
fi
```

## Solution

Changed the script to:
1. Check if ANY models exist in persistent storage
2. List available models for visibility
3. Skip automatic downloads entirely
4. Log a warning if no models found

**Fixed Code**:
```bash
# 5. Pre-load Ollama Models
log "Step 5: Checking Ollama models..."
# Check if any models exist in the persistent storage
MODEL_COUNT=$(OLLAMA_MODELS=/workspace/data/ollama_models ollama list 2>/dev/null | grep -v "NAME" | wc -l)
if [ "$MODEL_COUNT" -gt 0 ]; then
    log "✅ Found $MODEL_COUNT model(s) in /workspace/data/ollama_models"
    OLLAMA_MODELS=/workspace/data/ollama_models ollama list | grep -v "NAME" | while read line; do
        log "   - $line"
    done
else
    log "⚠️  No models found in /workspace/data/ollama_models"
    log "   Models should be pre-downloaded and stored in persistent storage"
    log "   Skipping automatic model download to avoid delays"
fi
```

## Benefits

1. **Faster Startup**: No automatic model downloads during pod initialization
2. **Bandwidth Savings**: Avoids re-downloading 7+ GB models
3. **Predictable Behavior**: Models must be explicitly pre-downloaded and stored in `/workspace/data/ollama_models`
4. **Better Visibility**: Lists all available models in startup logs

## Model Management

### Pre-download Models (One-time Setup)

```bash
# Set the persistent models directory
export OLLAMA_MODELS=/workspace/data/ollama_models

# Download required models
ollama pull mistral-nemo:12b-instruct
ollama pull sentence-transformers/all-mpnet-base-v2

# Verify models are stored correctly
ollama list
ls -lh /workspace/data/ollama_models/
```

### Verify Models After Pod Restart

```bash
# Check startup logs
tail -100 /workspace/logs/runpod_init.log | grep -A 5 "Step 5"

# List available models
OLLAMA_MODELS=/workspace/data/ollama_models ollama list
```

## Files Modified

- `/workspace/001-bms-agent/scripts/runpod_init_v2.sh` - Lines 116-129

## Testing

After this fix:
1. Pod restarts should complete faster (no model download delays)
2. Startup logs should show: "✅ Found N model(s) in /workspace/data/ollama_models"
3. If no models exist, logs show warning but continue without downloading

## Related Documentation

- `/workspace/001-bms-agent/docs/RUNPOD_PERSISTENCE_GUIDE.md` - Ollama persistence setup
- `/workspace/001-bms-agent/docs/OLLAMA_GPU_SETUP_COMPLETE.md` - GPU optimization guide
- `/workspace/001-bms-agent/scripts/runpod_init_v2.sh` - Full initialization script
