# Open WebUI Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: Port 3000 Already in Use

**Symptom:**
```
[Errno 98] error while attempting to bind on address ('0.0.0.0', 3000): address already in use
```

**Cause:** Open WebUI is already running, or another process is using port 3000.

**Solution 1 - Check if Open WebUI is running:**
```bash
ps aux | grep open-webui | grep -v grep
```

If it shows a process, Open WebUI is already running. No action needed - just access http://localhost:3000

**Solution 2 - Kill existing process:**
```bash
# Find the PID
ps aux | grep open-webui | grep -v grep

# Kill it
kill <PID>

# Or force kill
pkill -f open-webui

# Then restart
cd /workspace/openwebui && ./start_openwebui.sh
```

**Solution 3 - Check for other processes on port 3000:**
```bash
netstat -tlnp | grep :3000
# Kill the process using the port
kill <PID>
```

---

### Issue 2: Ollama Not Running

**Symptom:**
```
⚠️  Ollama is not running on port 11434
   OpenWebUI requires Ollama to function
```

**Cause:** Ollama service not started.

**Solution:**
```bash
# Check if Ollama is running
curl -s http://localhost:11434/api/tags

# Start Ollama (RunPod auto-starts, but if needed manually)
/root/ollama serve > /workspace/logs/ollama.log 2>&1 &

# Verify it started
curl -s http://localhost:11434/api/tags | python3 -m json.tool

# Should show list of installed models
```

**If Ollama binary not found:**
```bash
# Reinstall Ollama (should be in runpod_init.sh)
cd /root
curl -L https://ollama.com/download/ollama-linux-amd64 -o ollama
chmod +x ollama
./ollama serve &
```

---

### Issue 3: BMS API Not Running

**Symptom:**
```
⚠️  BMS API is not running on port 8000
   Start it with: uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Cause:** FastAPI server not started.

**Solution:**
```bash
# Check if BMS API is running
curl -s http://localhost:8000/health

# Start BMS API
cd /workspace/001-bms-agent
source /workspace/bms-api-venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/api.log 2>&1 &

# Verify it started
curl -s http://localhost:8000/health | python3 -m json.tool
# Should return: {"status": "healthy", ...}
```

**If virtual environment activation fails:**
```bash
# Check if venv exists
ls -la /workspace/bms-api-venv

# If missing, check alternative location
source /workspace/bms-api-venv/bin/activate

# If still missing, reinstall
python3.11 -m venv /workspace/bms-api-venv
source /workspace/bms-api-venv/bin/activate
pip install -r /workspace/001-bms-agent/requirements.txt
```

---

### Issue 4: BMS Search Tool Not Found

**Symptom:**
- Open WebUI loads, but BMS Search Tool not visible in Tools settings
- Searches don't invoke the tool

**Cause:** Tool not installed in Open WebUI data directory.

**Solution:**
```bash
# Check if tool exists
ls -lh /workspace/openwebui/data/tools/bms_search.py

# If missing, copy from source
mkdir -p /workspace/openwebui/data/tools
cp /workspace/001-bms-agent/tools/bms_search.py \
   /workspace/openwebui/data/tools/

# Restart Open WebUI
pkill -f open-webui
cd /workspace/openwebui && ./start_openwebui.sh

# Verify tool installed (should be 1910 lines, 74KB)
wc -l /workspace/openwebui/data/tools/bms_search.py
```

---

### Issue 5: Search Returns No Results

**Symptom:**
- Queries execute but return 0 results
- API returns `{"results": []}`

**Possible Causes:**

**Cause 1 - No documents in Qdrant:**
```bash
# Check document count
curl -s http://localhost:6333/collections/nomad_bms_documents | python3 -m json.tool

# Look for: "points_count": <number>
# Should be >0 (expected: ~4700)
```

**Solution:** Process documents
```bash
cd /workspace/001-bms-agent
source /workspace/bms-api-venv/bin/activate
python scripts/batch_process_incoming.py
```

**Cause 2 - Score threshold too high:**
```bash
# Test with lower threshold
curl -s -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "railway safety", "limit": 5, "min_score": 0.5}'
```

**Cause 3 - Qdrant not running:**
```bash
# Check if Qdrant is running
curl -s http://localhost:6333/collections

# If not, check logs
tail -50 /workspace/logs/qdrant.log

# Restart Qdrant (usually auto-started by runpod_init.sh)
/workspace/qdrant --config-path /workspace/qdrant_storage/config.yaml &
```

---

### Issue 6: Slow Search Performance

**Symptom:**
- Queries take >5 seconds
- UI feels unresponsive

**Diagnosis:**
```bash
# Test API latency directly (5 queries)
for i in {1..5}; do
  START=$(date +%s%3N)
  curl -s -X POST http://localhost:8000/api/v1/search/semantic \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "limit": 3}' > /dev/null
  END=$(date +%s%3N)
  echo "Query $i: $((END - START))ms"
done
```

**Expected:** <100ms per query (MVP measured: 37ms average)

**If slow (>200ms):**
1. Check GPU utilization (embeddings use GPU):
   ```bash
   nvidia-smi
   ```

2. Check Qdrant index optimization:
   ```bash
   cd /workspace/001-bms-agent
   source /workspace/bms-api-venv/bin/activate
   python scripts/optimize_qdrant_index.py
   ```

3. Check system resources:
   ```bash
   htop  # Check CPU/RAM usage
   df -h # Check disk space
   ```

---

### Issue 7: Open WebUI Won't Start - Virtual Environment Error

**Symptom:**
```
start_openwebui.sh: line 29: venv/bin/activate: No such file or directory
```

**Cause:** Virtual environment path incorrect in startup script.

**Solution:**
```bash
# Check which venv exists
ls -la /workspace/openwebui/

# Should show: venv/ directory
# If missing, check alternative locations:
ls -la /workspace/openwebui/.venv

# Fix startup script to use correct path
cd /workspace/openwebui
nano start_openwebui.sh  # Edit line 29

# Correct path should be:
source venv/bin/activate  # NOT .venv/bin/activate
```

---

### Issue 8: Authentication Enabled But No User Account

**Symptom:**
- Login screen appears but no credentials work
- First user registration not working

**Cause:** Authentication enabled without initial user setup.

**Solution:**
```bash
# Disable authentication temporarily
cd /workspace/openwebui
nano .env

# Change:
WEBUI_AUTH=False

# Restart Open WebUI
pkill -f open-webui
./start_openwebui.sh

# Access UI and create user account
# Then re-enable authentication if desired
```

---

### Issue 9: Qdrant Connection Error

**Symptom:**
```
Failed to connect to Qdrant at localhost:6333
```

**Diagnosis:**
```bash
# Check if Qdrant is running
curl -s http://localhost:6333/collections

# Check Qdrant logs
tail -100 /workspace/logs/qdrant.log

# Check if port 6333 is in use
netstat -tlnp | grep :6333
```

**Solution:**
```bash
# Restart Qdrant
pkill -f qdrant
/workspace/qdrant --config-path /workspace/qdrant_storage/config.yaml \
  > /workspace/logs/qdrant.log 2>&1 &

# Wait for startup (5-10 seconds)
sleep 10

# Verify collections
curl -s http://localhost:6333/collections | python3 -m json.tool
```

---

### Issue 10: JSON Decode Error from API

**Symptom:**
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Cause:** API returned non-JSON response (likely HTML error page).

**Diagnosis:**
```bash
# Check what API actually returns
curl -s http://localhost:8000/health

# Check API logs for errors
tail -100 /workspace/logs/api.log
```

**Solution:** Usually indicates BMS API crashed or isn't running. Restart it:
```bash
cd /workspace/001-bms-agent
source /workspace/bms-api-venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 \
  > /workspace/logs/api.log 2>&1 &
```

---

## Quick Health Check Script

Run this to check all services:

```bash
#!/bin/bash
echo "=== Open WebUI Health Check ==="
echo ""

echo "1. Open WebUI (port 3000):"
curl -s http://localhost:3000/health && echo " ✅" || echo " ❌"

echo "2. BMS API (port 8000):"
curl -s http://localhost:8000/health && echo " ✅" || echo " ❌"

echo "3. Ollama (port 11434):"
curl -s http://localhost:11434/api/tags > /dev/null && echo " ✅" || echo " ❌"

echo "4. Qdrant (port 6333):"
curl -s http://localhost:6333/collections > /dev/null && echo " ✅" || echo " ❌"

echo ""
echo "5. Document count:"
curl -s http://localhost:6333/collections/nomad_bms_documents | python3 -c "import json, sys; print(f\"{json.load(sys.stdin)['result']['points_count']} documents\")"

echo ""
echo "6. BMS Search Tool:"
ls -lh /workspace/openwebui/data/tools/bms_search.py 2>/dev/null && echo " ✅" || echo " ❌"
```

Save as `/workspace/scripts/health_check_openwebui.sh` and run:
```bash
bash /workspace/scripts/health_check_openwebui.sh
```

---

## Getting Help

1. **Check logs:**
   - Open WebUI: `/workspace/logs/openwebui.log`
   - BMS API: `/workspace/logs/api.log`
   - Qdrant: `/workspace/logs/qdrant.log`
   - Ollama: `/workspace/logs/ollama.log`

2. **Reference documentation:**
   - Quickstart: `/workspace/specs/006-production-rag-interface/quickstart.md`
   - Startup: `/workspace/docs/openwebui/STARTUP.md`
   - Limitations: `/workspace/docs/openwebui/LIMITATIONS.md`

3. **Check RunPod initialization:**
   ```bash
   # Verify init script ran
   cat /workspace/.runpod_init_complete

   # Re-run if needed
   bash /workspace/001-bms-agent/scripts/runpod_init.sh
   ```

4. **For BMS Agent issues:**
   - See: `/workspace/CLAUDE.md` (comprehensive troubleshooting)
   - See: `/workspace/001-bms-agent/README.md`
