# RunPod Quick Start - Copy & Paste Guide

## Step 1: Save Your SSH Key (Do This First!)

```bash
# On your current machine/pod
mkdir -p /workspace/config
cat ~/.ssh/id_rsa.pub > /workspace/config/authorized_keys
cat /workspace/config/authorized_keys  # Verify it saved
```

## Step 2: RunPod GUI Settings

### Container Image
```
runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04
```

### Docker Command
```bash
bash -c 'sleep infinity'
```

### Environment Variables
```
OLLAMA_MODELS=/workspace/data/ollama_models
PYTHONUNBUFFERED=1
```

### Volume Mount
```
/workspace
```

### Exposed Ports

**HTTP Ports (for web access):**
```
8000  - BMS API (FastAPI)
3000  - OpenWebUI
6333  - Qdrant Dashboard
```

**TCP Ports (for SSH/services):**
```
22    - SSH
11434 - Ollama API
```

**Note:** In RunPod GUI, add these ports in the "Expose HTTP Ports" and "Expose TCP Ports" sections.

### Docker Start Command (COPY THIS EXACTLY)

**Paste this into RunPod's "Docker Start Command" field:**

```bash
bash -c 'cd /workspace && ([ ! -d 001-bms-agent ] && git clone https://github.com/absrzvi/bms-agent.git 001-bms-agent || (cd 001-bms-agent && git pull origin 001-bms-agent)) && cd 001-bms-agent && chmod +x scripts/runpod_init.sh && bash scripts/runpod_init.sh'
```

**What this does:**
- Clones repository if not present, or pulls latest changes if it exists
- Makes the init script executable
- Runs the latest version of `runpod_init.sh` from GitHub

## Step 3: Deploy & Monitor

### Monitor initialization:
```bash
tail -f /workspace/logs/runpod_init.log
```

### Check when complete:
```bash
ls -la /workspace/.runpod_init_complete
cd /workspace/001-bms-agent && ./scripts/health_check.sh
```

## Step 4: Access Services

- **API:** http://YOUR_POD_IP:8000
- **API Docs:** http://YOUR_POD_IP:8000/docs
- **OpenWebUI:** http://YOUR_POD_IP:3000
- **Qdrant:** http://YOUR_POD_IP:6333/dashboard

## Important Notes

✅ **First Start:** 10-20 minutes (full initialization)  
✅ **Restarts:** 1-2 minutes (services only, no re-init)  
✅ **SSH Keys:** Automatically merged from `/workspace/config/authorized_keys`  
✅ **No Loops:** Completion marker prevents re-running  
✅ **Persistence:** Everything in `/workspace` survives restarts  

## Force Re-initialization (If Needed)

```bash
rm /workspace/.runpod_init_complete
bash /workspace/001-bms-agent/scripts/runpod_init.sh
```

## Troubleshooting

```bash
# Check logs
tail -100 /workspace/logs/runpod_init.log

# Restart services
cd /workspace/001-bms-agent
./scripts/start_all_services.sh restart

# Check SSH keys
cat /root/.ssh/authorized_keys
cat /workspace/config/authorized_keys
```

---

**Full Guide:** See `RUNPOD_DEPLOYMENT_GUIDE.md` for detailed instructions.
