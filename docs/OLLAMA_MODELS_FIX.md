# Ollama Models Persistence Fix

## Problem

After RunPod restart, Ollama was attempting to re-download models even though they were already stored in `/workspace/data/ollama_models`. This happened because:

1. The `OLLAMA_MODELS` environment variable was exported in the shell but not passed to the `ollama serve` process
2. The `ollama list` and `ollama pull` commands were not using the correct models directory

## Root Cause

In bash, when you use `export VARIABLE=value`, it sets the variable for the current shell and child processes. However, when starting a background process with `&`, the environment variable needs to be explicitly passed.

**Incorrect approach:**
```bash
export OLLAMA_MODELS=/workspace/data/ollama_models
ollama serve > /workspace/logs/ollama.log 2>&1 &
```

**Correct approach:**
```bash
OLLAMA_MODELS=/workspace/data/ollama_models ollama serve > /workspace/logs/ollama.log 2>&1 &
```

## Solution

### Files Modified

1. **`/workspace/001-bms-agent/scripts/runpod_init_v2.sh`**
   - Changed Ollama startup to pass `OLLAMA_MODELS` directly to the process
   - Updated `ollama list` and `ollama pull` commands to use the environment variable

2. **`/workspace/001-bms-agent/scripts/start_all_services.sh`**
   - Fixed Ollama startup to pass `OLLAMA_MODELS` directly to the process
   - Added check to prevent starting Ollama if already running

3. **`/workspace/001-bms-agent/scripts/env.sh`** (NEW)
   - Created centralized environment configuration file
   - Can be sourced by all scripts for consistent settings

### Changes Made

#### runpod_init_v2.sh
```bash
# Before
export OLLAMA_MODELS=/workspace/data/ollama_models
ollama serve > /workspace/logs/ollama.log 2>&1 &

# After
OLLAMA_MODELS=/workspace/data/ollama_models ollama serve > /workspace/logs/ollama.log 2>&1 &
```

```bash
# Before
if ollama list | grep -q "$REQUIRED_MODEL"; then

# After
if OLLAMA_MODELS=/workspace/data/ollama_models ollama list | grep -q "$REQUIRED_MODEL"; then
```

#### start_all_services.sh
```bash
# Before
if [ -f /usr/local/bin/ollama ]; then
    echo "Starting Ollama..."
    export OLLAMA_MODELS=/workspace/data/ollama_models
    /usr/local/bin/ollama serve > /workspace/logs/ollama.log 2>&1 &
    sleep 3
fi

# After
if [ -f /usr/local/bin/ollama ]; then
    if ! pgrep -x "ollama" > /dev/null; then
        echo "Starting Ollama..."
        OLLAMA_MODELS=/workspace/data/ollama_models /usr/local/bin/ollama serve > /workspace/logs/ollama.log 2>&1 &
        sleep 3
    else
        echo "Ollama already running, skipping..."
    fi
fi
```

## Verification

After the next pod restart, you should see:

```
2025-10-03 XX:XX:XX - Step 5: Checking Ollama models...
2025-10-03 XX:XX:XX - ✅ Model mistral-nemo:12b-instruct already available
```

Instead of:
```
2025-10-03 XX:XX:XX - Pulling model mistral-nemo:12b-instruct (this may take several minutes)...
```

### Manual Verification

You can verify the models are accessible:

```bash
# Check models directory
ls -lh /workspace/data/ollama_models/

# List models with correct environment
OLLAMA_MODELS=/workspace/data/ollama_models ollama list
```

## OpenWebUI Configuration

OpenWebUI data is stored in `/workspace/data/openwebui` and is automatically restored on pod restart. The `OPENWEBUI_DATA_DIR` environment variable is set in:

- `/workspace/001-bms-agent/scripts/env.sh`
- `/workspace/001-bms-agent/scripts/start_all_services.sh` (line 40)

No changes needed for OpenWebUI persistence.

## Best Practices

1. **Always pass environment variables directly to background processes:**
   ```bash
   VAR=value command &
   ```

2. **Use the centralized env.sh file:**
   ```bash
   source /workspace/001-bms-agent/scripts/env.sh
   ```

3. **Check if services are already running before starting:**
   ```bash
   if ! pgrep -x "service_name" > /dev/null; then
       # start service
   fi
   ```

## Related Files

- `/workspace/001-bms-agent/scripts/runpod_init_v2.sh` - Main initialization script
- `/workspace/001-bms-agent/scripts/start_all_services.sh` - Service startup script
- `/workspace/001-bms-agent/scripts/env.sh` - Environment configuration
- `/workspace/data/ollama_models/` - Persistent Ollama models directory
- `/workspace/data/openwebui/` - Persistent OpenWebUI data directory
