# OpenWebUI BMS Search Tool - Troubleshooting Guide

## ❌ Issue: "No results found" Error

### Symptoms
```
Tool search_documents result: 🔍 No results found for query: 'business continuity meaning'
```

### Root Cause
The OpenWebUI tool needs to be **manually added** through the OpenWebUI interface. The tool file in `/workspace/openwebui/data/tools/` is not automatically loaded.

---

## ✅ Solution: Add Tool Manually in OpenWebUI

### Step 1: Access OpenWebUI
1. Open browser: **http://localhost:3000**
2. Sign in with your account

### Step 2: Navigate to Tools
1. Click **Workspace** (top menu)
2. Click **Tools** (left sidebar)
3. Click **"+"** button (top right) to add new tool

### Step 3: Copy Tool Code
```bash
# Copy the entire contents of this file:
/workspace/001-bms-agent/tools/bms_search.py
```

Or use this command to display it:
```bash
cat /workspace/001-bms-agent/tools/bms_search.py
```

### Step 4: Paste and Configure
1. Paste the entire code into the tool editor
2. Give it a name: **"BMS Search"**
3. Give it an ID: **"bms_search"**
4. Click **Save**

### Step 5: Configure Valves
1. Click the **gear icon** on the tool
2. Set these values:
   ```
   BMS_API_URL: http://localhost:8000
   DEFAULT_LIMIT: 5
   SEARCH_TYPE: semantic
   TIMEOUT: 30
   ```
3. Click **Save**

### Step 6: Enable Tool
1. Toggle the switch to **Enable** the tool
2. The tool should now show as active

### Step 7: Test
Try these queries in chat:
```
"What documents do we have about business continuity?"
"Show me the employee onboarding process"
"Find BMS-ENGI-FOR-003"
```

---

## 🔍 Verification Steps

### 1. Check API is Working
```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "business continuity", "limit": 3}'
```

Should return JSON with results.

### 2. Check Qdrant has Data
```bash
curl http://localhost:6333/collections/nomad_bms_documents
```

Should show `points_count: 448`

### 3. Check Services Running
```bash
# BMS API
curl http://localhost:8000/health

# Qdrant
curl http://localhost:6333/collections

# Ollama
curl http://localhost:11434/api/tags
```

All should respond successfully.

---

## 🎯 Common Issues

### Issue 1: Tool Not Appearing
**Solution**: Make sure you clicked "Save" after pasting the code

### Issue 2: Tool Shows But Doesn't Work
**Solution**: Check the Valves configuration - BMS_API_URL must be `http://localhost:8000`

### Issue 3: "Connection refused" Error
**Solution**: Start the BMS API:
```bash
cd /workspace/001-bms-agent
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Issue 4: "No results found" for Valid Queries
**Solution**: 
1. Check Qdrant is running: `curl http://localhost:6333/collections`
2. Restart Qdrant if needed: `bash /workspace/001-bms-agent/scripts/start_qdrant.sh start`

---

## 📊 Expected Behavior

### Correct Output
```
🔍 Found 3 results for: 'business continuity'

1. BMS-BCON-FOR-005-Business Continuity Response PR Scenario.docx
   📄 Type: docx | Quality: 0.00 | Relevance: 0.582
   📝 Questions Answers Questions Answers...

2. BMS-BCON-FOR-001-Business Continuity Response Template.docx
   📄 Type: docx | Quality: 0.00 | Relevance: 0.467
   📝 Incident Scope and scenario covered...
```

### Available Functions
- `search_semantic()` - Conceptual search
- `search_hybrid()` - Keyword + semantic
- `compare_search_types()` - Side-by-side comparison
- `search_by_document_type()` - Filter by type
- `get_api_status()` - Health check

---

## 🚀 Quick Start Commands

### Start All Services
```bash
# 1. Start Qdrant
bash /workspace/001-bms-agent/scripts/start_qdrant.sh start

# 2. Start BMS API
cd /workspace/001-bms-agent
source .venv/bin/activate
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/api.log 2>&1 &

# 3. Start OpenWebUI
bash /workspace/openwebui/start_openwebui.sh
```

### Check Status
```bash
# All services
curl http://localhost:8000/health  # BMS API
curl http://localhost:6333/health  # Qdrant
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:3000  # OpenWebUI
```

---

## 📚 Documentation

- **Tool Code**: `/workspace/001-bms-agent/tools/bms_search.py`
- **Optimization Guide**: `/workspace/001-bms-agent/tools/OPTIMIZATION_GUIDE.md`
- **Evaluation Results**: `/workspace/001-bms-agent/reports/evaluation_50_queries.md`
- **API Docs**: http://localhost:8000/docs

---

## ✅ Success Checklist

- [ ] OpenWebUI accessible at http://localhost:3000
- [ ] BMS API responding at http://localhost:8000
- [ ] Qdrant running with 448 documents
- [ ] Tool added manually in OpenWebUI Workspace → Tools
- [ ] Tool valves configured (BMS_API_URL set)
- [ ] Tool enabled (toggle switched on)
- [ ] Test query returns results

---

**Once the tool is properly added in OpenWebUI, you'll have access to all 96% accuracy search capabilities!** 🚀
