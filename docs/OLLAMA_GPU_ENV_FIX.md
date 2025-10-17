# Ollama GPU Environment Variable Fix

## Problem

Ollama was being started without the `OLLAMA_MODELS` environment variable properly passed to the process, causing it to:
1. Not find models stored in `/workspace/data/ollama_models`
2. Use the default models directory instead
3. Show no models when running `ollama ps` even though models existed

## Root Cause

In bash, when starting a background process with `&`, environment variables set with `export` in the current shell are **not always** inherited by the background process. The correct approach is to pass the environment variable directly to the command.

### Incorrect Pattern
```bash
export OLLAMA_MODELS=/workspace/data/ollama_models
ollama serve > /workspace/logs/ollama.log 2>&1 &
```

### Correct Pattern
```bash
OLLAMA_MODELS=/workspace/data/ollama_models ollama serve > /workspace/logs/ollama.log 2>&1 &
```

## Solution Applied

Updated all initialization and startup scripts to use the correct pattern for starting Ollama with the `OLLAMA_MODELS` environment variable.

### Files Modified

1. **`/workspace/001-bms-agent/scripts/runpod_init.sh`**
   - Line 212: Changed Ollama startup to pass `OLLAMA_MODELS` directly
   - Lines 222, 229: Updated `ollama pull` commands to use environment variable
   - Added logging to confirm environment variable is set

2. **`/workspace/scripts/runpod_init.sh`**
   - Line 83: Changed Ollama startup to pass `OLLAMA_MODELS` directly
   - Lines 106, 108: Updated model pull commands to use environment variable
   - Added confirmation message

3. **`/workspace/001-bms-agent/scripts/install_ollama_gpu.sh`**
   - Line 112: Changed Ollama startup to pass `OLLAMA_MODELS` directly
   - Added environment logging

4. **`/workspace/001-bms-agent/scripts/manage_services.sh`**
   - Line 93: Changed Ollama startup to pass `OLLAMA_MODELS` directly

5. **`/workspace/001-bms-agent/scripts/start_all_services.sh`**
   - Line 22: Changed Ollama startup to pass `OLLAMA_MODELS` directly
   - Added check to prevent starting if already running
   - Added confirmation message

6. **`/workspace/scripts/start_all_services.sh`**
   - Line 22: Changed Ollama startup to pass `OLLAMA_MODELS` directly
   - Added duplicate process check
   - Added confirmation message

7. **`/workspace/001-bms-agent/scripts/migrate_to_workspace.sh`**
   - Line 171: Changed Ollama startup to pass `OLLAMA_MODELS` directly

8. **`/workspace/scripts/migrate_to_workspace.sh`**
   - Line 171: Changed Ollama startup to pass `OLLAMA_MODELS` directly

9. **`/workspace/ollama/ollama.env`**
   - Line 35: Updated `OLLAMA_MODELS` path from `/workspace/ollama/models` to `/workspace/data/ollama_models`

10. **`/workspace/ollama/start_ollama.sh`**
    - Line 21: Updated directory creation to use `/workspace/data/ollama_models`

11. **`/workspace/start-ollama.sh`**
    - Lines 9, 19: Updated paths to use `/workspace/data/ollama_models`
    - Line 30: Changed Ollama startup to pass `OLLAMA_MODELS` directly

## Verification

After the fix, Ollama now correctly:
- Uses GPU (100% GPU utilization)
- Finds models in `/workspace/data/ollama_models`
- Shows loaded models when running `ollama ps`

### Before Fix
```bash
$ ollama ps
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL
# Empty - no models found
```

### After Fix
```bash
$ ollama ps
NAME              ID              SIZE      PROCESSOR    CONTEXT    UNTIL             
mistral:latest    6577803aa9a0    5.8 GB    100% GPU     4096       4 minutes from now
```

### Verify Models Directory
```bash
$ OLLAMA_MODELS=/workspace/data/ollama_models ollama list
NAME                       ID              SIZE      MODIFIED       
mistral:latest             6577803aa9a0    4.4 GB    34 minutes ago    
nomic-embed-text:latest    0a109f422b47    274 MB    36 minutes ago    
mistral-small3.2:latest    5a408ab55df5    15 GB     26 hours ago      
mistral-nemo:latest        e7e06d107c6c    7.1 GB    26 hours ago
```

## Best Practices

1. **Always pass environment variables directly to background processes:**
   ```bash
   VAR=value command &
   ```

2. **For multiple environment variables:**
   ```bash
   VAR1=value1 VAR2=value2 command &
   ```

3. **Check if service is already running before starting:**
   ```bash
   if ! pgrep -x "ollama" > /dev/null; then
       OLLAMA_MODELS=/workspace/data/ollama_models ollama serve &
   fi
   ```

4. **Use consistent paths across all scripts:**
   - Models: `/workspace/data/ollama_models`
   - Logs: `/workspace/logs/ollama.log`

## Related Documentation

- `/workspace/001-bms-agent/docs/OLLAMA_MODELS_FIX.md` - Previous fix for model persistence
- `/workspace/001-bms-agent/docs/STARTUP_FIX_MODEL_DOWNLOAD.md` - Model download optimization

## Testing After Pod Restart

After the next pod restart, verify:

1. **Ollama starts with correct environment:**
   ```bash
   ps aux | grep ollama
   # Should show the process
   ```

2. **Models are accessible:**
   ```bash
   ollama list
   # Should show all 4 models
   ```

3. **GPU is being used:**
   ```bash
   ollama ps
   # PROCESSOR column should show "100% GPU"
   ```

4. **Models directory is correct:**
   ```bash
   ls -lh /workspace/data/ollama_models/
   # Should show blobs/ and manifests/ directories with content
   ```

## Date Applied

2025-10-04

## Applied By

Cascade AI Assistant
