# RunPod Deployment Guide - Step by Step

**Version:** 1.0  
**Date:** 2025-10-04  
**Purpose:** Deploy BMS Agent to RunPod with automatic initialization

## Prerequisites

- RunPod account
- SSH key pair (for secure access)
- GitHub repository access to `absrzvi/bms-agent`

## Part 1: Prepare Your SSH Keys

### Step 1: Save Your SSH Key to Workspace

**On your current RunPod instance (or local machine):**

```bash
# Create config directory
mkdir -p /workspace/config

# Copy your SSH public key to workspace
# Option A: If you have the key locally
cat ~/.ssh/id_rsa.pub > /workspace/config/authorized_keys

# Option B: If you need to generate a new key
ssh-keygen -t rsa -b 4096 -C "your_email@example.com" -f ~/.ssh/id_rsa -N ""
cat ~/.ssh/id_rsa.pub > /workspace/config/authorized_keys

# Verify the key was saved
cat /workspace/config/authorized_keys
```

**Important:** This file will be automatically merged with RunPod's default SSH keys on every pod start.

## Part 2: RunPod GUI Configuration

### Step 1: Create/Edit Pod Template

1. **Go to RunPod Dashboard**
   - Navigate to https://www.runpod.io/console/pods

2. **Click "Edit Template" or "New Template"**
   - Choose a template with GPU support (recommended: RTX 4090, A100, or similar)

### Step 2: Configure Container Settings

**Container Image:**
```
runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04
```
(Or any PyTorch/CUDA image with Python 3.11+)

**Container Disk:**
- Minimum: 50 GB
- Recommended: 100-200 GB

**Volume Disk:**
- Minimum: 100 GB
- Recommended: 200-500 GB (for models and data)

### Step 3: Configure Docker Command (CRITICAL)

**In the "Docker Command" field, paste:**

```bash
bash -c 'sleep infinity'
```

**Why:** This keeps the container running while allowing the startup script to execute.

### Step 4: Configure Environment Variables

**Add these environment variables:**

| Variable | Value | Description |
|----------|-------|-------------|
| `OLLAMA_MODELS` | `/workspace/data/ollama_models` | Ollama model storage location |
| `PYTHONUNBUFFERED` | `1` | Unbuffered Python output |

### Step 5: Configure Volume Mount

**Volume Mount Path:**
```
/workspace
```

**Volume Size:** 200 GB (or as configured above)

**Important:** This ensures `/workspace` persists across pod restarts.

### Step 6: Configure Docker Start Command (MOST IMPORTANT)

**In the "Docker Start Command" field, paste this one-liner:**

```bash
bash -c 'cd /workspace && ([ ! -d 001-bms-agent ] && git clone https://github.com/absrzvi/bms-agent.git 001-bms-agent || (cd 001-bms-agent && git pull origin 001-bms-agent)) && cd 001-bms-agent && chmod +x scripts/runpod_init.sh && bash scripts/runpod_init.sh'
```

**What this does:**
- Clones repository if not present, or pulls latest changes if it exists
- Makes the init script executable
- Runs the latest version of `runpod_init.sh` from GitHub
- Ensures you always get the latest working version

**Note:** RunPod only provides a "Docker Start Command" field (not a full script editor), so we use a one-liner.

### Step 7: Configure Exposed Ports

**HTTP Ports (Expose HTTP Ports section in RunPod GUI):**

| Port | Service | Description |
|------|---------|-------------|
| 8000 | BMS API | FastAPI application (Swagger UI at /docs) |
| 3000 | OpenWebUI | Web interface for LLM interaction |
| 6333 | Qdrant | Vector database dashboard |

**TCP Ports (Expose TCP Ports section in RunPod GUI):**

| Port | Service | Description |
|------|---------|-------------|
| 22 | SSH | Secure shell access |
| 11434 | Ollama | Ollama API endpoint |

**How to add in RunPod GUI:**
1. Scroll to "Expose HTTP Ports" section → Add: `8000, 3000, 6333`
2. Scroll to "Expose TCP Ports" section → Add: `22, 11434`

### Step 8: Save Template

1. Click "Save Template"
2. Give it a name: "BMS Agent - Auto Init"

## Part 3: Deploy Pod

### Step 1: Deploy from Template

1. Go to "Pods" section
2. Click "Deploy" on your "BMS Agent - Auto Init" template
3. Select GPU type and region
4. Click "Deploy"

### Step 2: Wait for Initialization

**The pod will automatically:**
1. Start the container
2. Clone/update the repository
3. Run `runpod_init.sh` which will:
   - ✅ Restore SSH keys from `/workspace/config/authorized_keys`
   - ✅ Create directory structure
   - ✅ Install Ollama (in `/root` for GPU)
   - ✅ Create Python venv (in `/workspace/bms-api-venv`)
   - ✅ Install all requirements.txt dependencies
   - ✅ Download NLTK data
   - ✅ Pull Ollama models
   - ✅ Start all services
   - ✅ Create completion marker (prevents re-running)

**Initialization time:** 10-20 minutes (first time)  
**Subsequent restarts:** 1-2 minutes (services only)

### Step 3: Monitor Initialization

**Option A: Via RunPod Web Terminal**
1. Click "Connect" on your pod
2. Select "Start Web Terminal"
3. Run:
```bash
tail -f /workspace/logs/runpod_init.log
```

**Option B: Via SSH**
1. Get pod's SSH connection string from RunPod dashboard
2. Connect:
```bash
ssh root@<pod-id>.runpod.io -p <port>
```
3. Monitor logs:
```bash
tail -f /workspace/logs/runpod_init.log
```

### Step 4: Verify Initialization Complete

**Check for completion marker:**
```bash
ls -la /workspace/.runpod_init_complete
```

**Check services:**
```bash
cd /workspace/001-bms-agent
./scripts/health_check.sh
```

**Expected output:**
```
✓ Qdrant (PID: XXXX)
✓ Ollama (PID: XXXX)
✓ BMS API (PID: XXXX)
✓ OpenWebUI (PID: XXXX)

Summary: 6/6 checks passed
✓ All systems operational
```

## Part 4: Verify SSH Access

### Test SSH Connection

```bash
# From your local machine
ssh root@<pod-id>.runpod.io -p <port>
```

**If successful, you should see:**
```
Welcome to Ubuntu 22.04...
root@<pod-id>:~#
```

### Verify SSH Keys Merged

**On the pod:**
```bash
cat /root/.ssh/authorized_keys
```

**You should see:**
- RunPod's default key (starts with `ssh-rsa AAAA...`)
- Your workspace key (from `/workspace/config/authorized_keys`)

## Part 5: Access Services

### BMS API
```
http://<pod-ip>:8000
http://<pod-ip>:8000/docs  # Swagger UI
http://<pod-ip>:8000/health
```

### OpenWebUI
```
http://<pod-ip>:3000
```

### Qdrant Dashboard
```
http://<pod-ip>:6333/dashboard
```

## Part 6: Test Persistence (Pod Restart)

### Step 1: Stop Pod

1. Go to RunPod dashboard
2. Click "Stop" on your pod
3. Wait for pod to stop

### Step 2: Start Pod

1. Click "Start" on your pod
2. Wait for pod to start (~30 seconds)

### Step 3: Verify Quick Restart

**The script will:**
- ✅ Detect completion marker (`/workspace/.runpod_init_complete`)
- ✅ Skip full initialization
- ✅ Restore SSH keys
- ✅ Start services only
- ✅ Complete in 1-2 minutes

**Check logs:**
```bash
tail -50 /workspace/logs/runpod_init.log
```

**You should see:**
```
2025-10-04 XX:XX:XX: Initialization already completed. Skipping full init.
2025-10-04 XX:XX:XX: Starting services only...
2025-10-04 XX:XX:XX: Restoring SSH keys...
2025-10-04 XX:XX:XX: SSH keys restored
2025-10-04 XX:XX:XX: Services started
```

### Step 4: Verify Data Persisted

```bash
# Check virtual environment
ls -la /workspace/bms-api-venv/

# Check Qdrant data
ls -la /workspace/qdrant_storage/

# Check Ollama models
ls -la /workspace/data/ollama_models/

# Check logs
ls -la /workspace/logs/
```

**All should be present!**

## Part 7: Force Re-initialization (If Needed)

**If you need to run full initialization again:**

```bash
# Remove completion marker
rm /workspace/.runpod_init_complete

# Restart pod or run script manually
cd /workspace/001-bms-agent
bash scripts/runpod_init.sh
```

## Troubleshooting

### Issue: SSH Keys Not Working

**Solution:**
```bash
# Check if keys exist
cat /workspace/config/authorized_keys

# If not, create them
mkdir -p /workspace/config
cat ~/.ssh/id_rsa.pub > /workspace/config/authorized_keys

# Manually restore
bash scripts/runpod_init.sh
```

### Issue: Services Not Starting

**Check logs:**
```bash
tail -100 /workspace/logs/runpod_init.log
tail -50 /workspace/logs/api.log
tail -50 /workspace/logs/qdrant.log
tail -50 /workspace/logs/ollama.log
```

**Restart services:**
```bash
cd /workspace/001-bms-agent
./scripts/start_all_services.sh restart
```

### Issue: Ollama GPU Not Working

**Verify GPU:**
```bash
nvidia-smi
```

**Reinstall Ollama:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
export OLLAMA_MODELS=/workspace/data/ollama_models
ollama serve &
```

### Issue: Dependencies Missing

**Reinstall:**
```bash
cd /workspace/001-bms-agent
source /workspace/bms-api-venv/bin/activate
pip install -r requirements.txt
```

### Issue: Script Running in Loop

**This should NOT happen** because of the completion marker.

**If it does:**
```bash
# Check if marker exists
ls -la /workspace/.runpod_init_complete

# If missing, script will run again (expected)
# If present, script should skip (check logs)

# Force create marker
touch /workspace/.runpod_init_complete
```

## Quick Reference

### Important Paths

| Path | Purpose |
|------|---------|
| `/workspace/001-bms-agent` | Project repository |
| `/workspace/bms-api-venv` | Python virtual environment |
| `/workspace/config/authorized_keys` | Your SSH public key |
| `/workspace/logs/runpod_init.log` | Initialization log |
| `/workspace/.runpod_init_complete` | Completion marker (prevents re-init) |
| `/workspace/data/ollama_models` | Ollama models |
| `/workspace/qdrant_storage` | Qdrant database |

### Important Commands

```bash
# Check initialization status
tail -f /workspace/logs/runpod_init.log

# Check services
cd /workspace/001-bms-agent && ./scripts/health_check.sh

# Restart services
cd /workspace/001-bms-agent && ./scripts/start_all_services.sh restart

# Force re-initialization
rm /workspace/.runpod_init_complete && bash /workspace/001-bms-agent/scripts/runpod_init.sh

# Check SSH keys
cat /root/.ssh/authorized_keys
cat /workspace/config/authorized_keys
```

## Summary

**What happens on FIRST start:**
1. Repository cloned/updated
2. SSH keys restored
3. Full initialization (10-20 min)
4. Completion marker created
5. All services started

**What happens on SUBSEQUENT starts:**
1. Repository updated
2. SSH keys restored
3. Completion marker detected
4. Services started only (1-2 min)
5. No re-initialization

**Key Features:**
- ✅ No infinite loops (completion marker prevents re-init)
- ✅ SSH keys automatically merged (no duplicates)
- ✅ Full persistence across restarts
- ✅ GPU support maintained
- ✅ All dependencies auto-installed

---

**You're ready to deploy! 🚀**
