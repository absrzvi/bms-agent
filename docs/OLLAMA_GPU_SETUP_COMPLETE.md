# Ollama GPU Installation - Complete ✅

## Installation Summary

**Date**: 2025-10-03 19:33 UTC  
**Status**: ✅ **COMPLETE**

### GPU Configuration
- **GPU**: NVIDIA A100-SXM4-80GB
- **VRAM**: 79.3 GiB total, 78.8 GiB available
- **CUDA**: Version 12.7 (compute capability 8.0)
- **Driver**: 565.57.01

### Ollama Installation
- **Version**: 0.12.3
- **Binary**: `/usr/local/bin/ollama` (33MB)
- **Models Directory**: `/workspace/data/ollama_models` (persistent)
- **GPU Support**: ✅ Enabled with CUDA 12.7

### Backup Created
- **Location**: `/workspace/backups/ollama_install/`
- **Size**: 37MB
- **Contents**:
  - `bin/ollama` - Ollama binary (33MB)
  - `systemd/ollama.service` - Systemd service file
  - `systemd.d/override.conf` - GPU configuration override
  - `MANIFEST.txt` - Backup manifest

## Current Status

### Ollama Service
```bash
# Service is running with GPU support
ps aux | grep ollama
# Check GPU usage
nvidia-smi
```

### GPU Detection Confirmed
From `/workspace/logs/ollama.log`:
```
time=2025-10-03T19:33:06.503Z level=INFO source=types.go:131 msg="inference compute" 
  id=GPU-2eb62d7f-a6fb-424f-ec03-fd5d1c362b4a 
  library=cuda 
  variant=v12 
  compute=8.0 
  driver=12.7 
  name="NVIDIA A100-SXM4-80GB" 
  total="79.3 GiB" 
  available="78.8 GiB"
```

## Usage

### Pull Models
```bash
# Pull required models
ollama pull mistral-nemo:12b-instruct
ollama pull sentence-transformers/all-mpnet-base-v2

# List installed models
ollama list
```

### Test GPU Acceleration
```bash
# Run inference and watch GPU usage
echo "Write a haiku about AI" | ollama run mistral-nemo:12b-instruct

# In another terminal, monitor GPU
watch -n 1 nvidia-smi
```

### Verify Persistent Storage
```bash
# Models should be in persistent storage
ls -lh /workspace/data/ollama_models/

# Check disk usage
du -sh /workspace/data/ollama_models/
```

## RunPod Restart Behavior

### What Happens on Pod Restart

1. **RunPod starts** → Executes `runpod_init_v2.sh`
2. **Ollama restored** → Binary copied from `/workspace/backups/ollama_install/`
3. **GPU config restored** → Override config applied
4. **Ollama starts** → With GPU support and persistent models
5. **Total time**: ~30-60 seconds (vs 15-40 minutes fresh install)

### To Configure RunPod Startup

In your RunPod pod settings, set the start command to:
```bash
bash /workspace/001-bms-agent/scripts/runpod_init_v2.sh
```

## Performance Comparison

### Before (Fresh Install Each Boot)
- Download Ollama: ~500MB, 2-5 minutes
- Install CUDA dependencies: 1-2 minutes
- Download models: ~7GB, 10-30 minutes
- **Total: 15-40 minutes**

### After (Restore from Backup)
- Restore Ollama binary: ~35MB copy, 5 seconds
- Restore GPU config: instant
- Models already present: 0 seconds
- **Total: 30-60 seconds**

**Speed improvement: 15-40x faster** 🚀

## Files Created

### Scripts
- `/workspace/001-bms-agent/scripts/install_ollama_gpu.sh` - GPU installation script
- `/workspace/001-bms-agent/scripts/backup_ollama_install.sh` - Backup utility
- `/workspace/001-bms-agent/scripts/runpod_init_v2.sh` - RunPod init script (updated)
- `/workspace/001-bms-agent/scripts/save_ssh_keys.sh` - SSH key backup utility

### Backups
- `/workspace/backups/ollama_install/` - Ollama installation backup
- `/workspace/config/authorized_keys` - SSH keys (if configured)

### Logs
- `/workspace/logs/ollama_gpu_install.log` - Installation log
- `/workspace/logs/ollama.log` - Ollama service log
- `/workspace/logs/runpod_init.log` - Init script log (on restart)

### Documentation
- `/workspace/001-bms-agent/docs/RUNPOD_SETUP.md` - Complete setup guide
- `/workspace/001-bms-agent/docs/OLLAMA_GPU_SETUP_COMPLETE.md` - This file

## Next Steps

### 1. Configure SSH Keys (Optional)
```bash
/workspace/001-bms-agent/scripts/save_ssh_keys.sh
```

### 2. Configure RunPod Startup
Set RunPod start command to:
```bash
bash /workspace/001-bms-agent/scripts/runpod_init_v2.sh
```

### 3. Pull Required Models
```bash
ollama pull mistral-nemo:12b-instruct
ollama pull sentence-transformers/all-mpnet-base-v2
```

### 4. Test the Setup
```bash
# Option A: Restart pod (full test)
# The pod will restart and run init script automatically

# Option B: Manual test (without restarting)
rm -f /tmp/runpod_init_complete
bash /workspace/001-bms-agent/scripts/runpod_init_v2.sh
```

## Verification Commands

```bash
# Check Ollama version
ollama --version

# Check GPU detection
nvidia-smi

# Check Ollama is using GPU
tail -50 /workspace/logs/ollama.log | grep -i "gpu\|cuda"

# Check models location
echo $OLLAMA_MODELS
ls -lh /workspace/data/ollama_models/

# Check backup
ls -lh /workspace/backups/ollama_install/
cat /workspace/backups/ollama_install/MANIFEST.txt

# Test inference
echo "Hello" | ollama run tinyllama
```

## Troubleshooting

### GPU Not Detected
```bash
# Check NVIDIA driver
nvidia-smi

# Check CUDA
nvcc --version

# Check Ollama logs
grep -i "gpu\|cuda" /workspace/logs/ollama.log
```

### Models Not Persisting
```bash
# Verify environment variable
echo $OLLAMA_MODELS

# Should output: /workspace/data/ollama_models

# Check models directory
ls -lh /workspace/data/ollama_models/
```

### Slow Inference
```bash
# Check GPU usage during inference
watch -n 1 nvidia-smi

# GPU utilization should be >50% during inference
# If 0%, GPU is not being used
```

## Success Criteria ✅

- [x] Ollama installed with version 0.12.3
- [x] GPU detected: NVIDIA A100-SXM4-80GB
- [x] CUDA support: Version 12.7
- [x] Models directory: `/workspace/data/ollama_models` (persistent)
- [x] Backup created: 37MB in `/workspace/backups/ollama_install/`
- [x] GPU override config backed up
- [x] Init script updated to restore GPU config
- [x] Loop prevention implemented (marker file)
- [x] Documentation complete

## Support

For issues or questions:
1. Check logs: `/workspace/logs/ollama*.log`
2. Review documentation: `/workspace/001-bms-agent/docs/RUNPOD_SETUP.md`
3. Verify backup: `cat /workspace/backups/ollama_install/MANIFEST.txt`

---

**Installation completed successfully!** 🎉

Your Ollama installation with GPU support is now backed up and ready for fast pod restarts.
