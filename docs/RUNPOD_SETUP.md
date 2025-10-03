# RunPod Initialization Setup Guide

## Problem Statement

RunPod pods have two storage types:
- **Ephemeral storage** (`/root`, `/usr`, `/etc`) - Lost on pod restart
- **Persistent storage** (`/workspace`) - Survives pod restarts

This causes issues:
1. Ollama installation is lost on every restart (requires re-download ~500MB)
2. SSH keys are lost on restart
3. System packages need reinstallation
4. Init scripts can loop if not properly guarded

## Solution Overview

Our solution uses a three-script approach:

1. **`backup_ollama_install.sh`** - Run ONCE to backup Ollama installation
2. **`save_ssh_keys.sh`** - Run ONCE to backup SSH keys
3. **`runpod_init_v2.sh`** - RunPod startup script (runs automatically on boot)

## Initial Setup (Run Once)

### Step 1: Backup Ollama Installation

```bash
# Make scripts executable
chmod +x /workspace/001-bms-agent/scripts/*.sh

# Backup current Ollama installation
/workspace/001-bms-agent/scripts/backup_ollama_install.sh
```

**Expected Output:**
```
Ollama Installation Backup Started
Found Ollama: ollama version 0.x.x
✅ Binary backed up (33M)
✅ Systemd service backed up
✅ Libraries backed up (X files)
✅ Backup manifest created
Ollama Backup Complete!
Location: /workspace/backups/ollama_install
Total Size: 35M
```

**Verify Backup:**
```bash
cat /workspace/backups/ollama_install/MANIFEST.txt
ls -lh /workspace/backups/ollama_install/bin/ollama
```

### Step 2: Backup SSH Keys

```bash
/workspace/001-bms-agent/scripts/save_ssh_keys.sh
```

**Expected Output:**
```
SSH Keys Backup Started
✅ SSH keys backed up to /workspace/config/authorized_keys
   Found 1 SSH key(s)
Key fingerprints:
   2048 SHA256:xxxxx... user@host (RSA)
SSH Keys Backup Complete!
```

**Verify Backup:**
```bash
cat /workspace/config/authorized_keys
```

### Step 3: Configure RunPod Startup Script

1. Go to your RunPod pod settings
2. Find the "Docker Start Command" or "Start Command" field
3. Replace with:

```bash
bash /workspace/001-bms-agent/scripts/runpod_init_v2.sh
```

**Alternative: If you need to run other commands first:**
```bash
bash /workspace/001-bms-agent/scripts/runpod_init_v2.sh && exec /start.sh
```

### Step 4: Test the Setup

**Option A: Restart the pod** (recommended for full test)
```bash
# The pod will restart and run the init script automatically
```

**Option B: Manual test** (without restarting)
```bash
# Remove the marker to allow re-run
rm -f /tmp/runpod_init_complete

# Run the init script
bash /workspace/001-bms-agent/scripts/runpod_init_v2.sh

# Check the log
tail -f /workspace/logs/runpod_init.log
```

## How It Works

### Boot Sequence

1. **RunPod starts** → Runs `runpod_init_v2.sh`
2. **Check marker** → If `/tmp/runpod_init_complete` exists, exit (prevents loop)
3. **Restore SSH keys** → Copy from `/workspace/config/authorized_keys` to `/root/.ssh/`
4. **Install packages** → Install jq, htop, tmux, etc. (if missing)
5. **Restore Ollama** → Copy from `/workspace/backups/ollama_install/` to system paths
6. **Start Ollama** → Launch Ollama service with persistent model storage
7. **Pre-load models** → Ensure required models are available
8. **Start services** → Run `start_all_services.sh` (Qdrant, BMS API, OpenWebUI)
9. **Health checks** → Verify all services are running
10. **Create marker** → Touch `/tmp/runpod_init_complete` to prevent re-run

### Loop Prevention

The script uses a marker file in `/tmp/runpod_init_complete`:
- **First run**: Marker doesn't exist → Script runs fully
- **Subsequent calls**: Marker exists → Script exits immediately
- **After reboot**: `/tmp` is cleared → Script runs again

This prevents infinite loops while allowing the script to run on every boot.

## File Structure

```
/workspace/
├── backups/
│   └── ollama_install/          # Ollama installation backup
│       ├── bin/
│       │   └── ollama           # Ollama binary (33MB)
│       ├── systemd/
│       │   └── ollama.service   # Systemd service file
│       ├── lib/                 # Ollama libraries (if any)
│       └── MANIFEST.txt         # Backup manifest
├── config/
│   └── authorized_keys          # SSH keys backup
├── logs/
│   ├── runpod_init.log         # Init script log
│   ├── ollama_backup.log       # Backup script log
│   └── ssh_backup.log          # SSH backup log
└── 001-bms-agent/
    └── scripts/
        ├── runpod_init_v2.sh           # Main init script
        ├── backup_ollama_install.sh    # Ollama backup utility
        ├── save_ssh_keys.sh            # SSH backup utility
        └── start_all_services.sh       # Service startup script
```

## Troubleshooting

### Issue: Script runs in a loop

**Cause**: Old init script without loop prevention

**Solution**: Use `runpod_init_v2.sh` which has marker-based loop prevention

**Verify**:
```bash
# Check if marker exists
ls -la /tmp/runpod_init_complete

# Check log for multiple runs
grep "Initialization already completed" /workspace/logs/runpod_init.log
```

### Issue: Ollama not found after restart

**Cause**: Ollama backup not created or restore failed

**Solution**:
```bash
# Check if backup exists
ls -lh /workspace/backups/ollama_install/bin/ollama

# If missing, create backup
/workspace/001-bms-agent/scripts/backup_ollama_install.sh

# Check restore log
grep "Ollama" /workspace/logs/runpod_init.log
```

### Issue: SSH keys not working after restart

**Cause**: SSH keys not backed up or restore failed

**Solution**:
```bash
# Check if backup exists
cat /workspace/config/authorized_keys

# If missing, create backup
/workspace/001-bms-agent/scripts/save_ssh_keys.sh

# Check restore log
grep "SSH" /workspace/logs/runpod_init.log
```

### Issue: Services not starting

**Cause**: Dependencies not met or service scripts missing

**Solution**:
```bash
# Check init log
tail -50 /workspace/logs/runpod_init.log

# Check service logs
tail -20 /workspace/logs/qdrant.log
tail -20 /workspace/logs/ollama.log
tail -20 /workspace/logs/api.log
tail -20 /workspace/logs/openwebui.log

# Manually start services
/workspace/scripts/start_all_services.sh
```

### Issue: Models need re-download after restart

**Cause**: `OLLAMA_MODELS` not set to persistent storage

**Solution**: The init script sets `OLLAMA_MODELS=/workspace/data/ollama_models`

**Verify**:
```bash
# Check environment variable
echo $OLLAMA_MODELS

# Check models location
ls -lh /workspace/data/ollama_models/

# Check Ollama models
ollama list
```

## Performance Benefits

### Before (Fresh Install Each Boot)
- Ollama download: ~500MB, 2-5 minutes
- System packages: ~100MB, 1-2 minutes
- Model download: ~7GB, 10-30 minutes
- **Total: ~15-40 minutes per restart**

### After (Restore from Backup)
- Ollama restore: ~35MB copy, 5 seconds
- System packages: Skip if present, 10 seconds
- Model restore: Already in persistent storage, 0 seconds
- **Total: ~30-60 seconds per restart**

**Speed improvement: 15-40x faster boot time**

## Maintenance

### Update Ollama Version

```bash
# 1. Install new version
curl -fsSL https://ollama.com/install.sh | sh

# 2. Verify new version
ollama --version

# 3. Create new backup
/workspace/001-bms-agent/scripts/backup_ollama_install.sh

# 4. Restart pod to test
```

### Add New SSH Key

```bash
# 1. Add key to current session
echo "ssh-rsa AAAA... user@host" >> /root/.ssh/authorized_keys

# 2. Backup updated keys
/workspace/001-bms-agent/scripts/save_ssh_keys.sh

# 3. Restart pod to test
```

### View Logs

```bash
# Init script log (most important)
tail -f /workspace/logs/runpod_init.log

# All logs
tail -f /workspace/logs/*.log

# Search for errors
grep -i error /workspace/logs/runpod_init.log
grep -i failed /workspace/logs/runpod_init.log
```

## Security Notes

1. **SSH Keys**: Stored in `/workspace/config/authorized_keys` with 600 permissions
2. **Ollama Binary**: Restored to system paths with executable permissions
3. **Logs**: All operations logged for audit trail
4. **No Secrets**: No API keys or passwords stored in init scripts

## References

- RunPod Documentation: https://docs.runpod.io/
- Ollama Installation: https://ollama.com/download
- BMS Agent Docs: `/workspace/001-bms-agent/README.md`
