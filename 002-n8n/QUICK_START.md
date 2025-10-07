# BMS AI Agent Workflow - Quick Start Guide

**5-Minute Setup** | Last Updated: 2025-10-06

---

## TL;DR

Your AI Agent workflow had n8n 1.113.3 compatibility issues. I created a simplified working version that bypasses these issues.

**Status**: ✅ **READY TO USE**

---

## Quick Setup (3 Commands)

```bash
# 1. Ensure BMS API is running
curl http://localhost:8000/health || \
  (cd /workspace/001-bms-agent && \
   source /workspace/bms-api-venv/bin/activate && \
   uvicorn api.main:app --host 0.0.0.0 --port 8000 &)

# 2. Import workflow to n8n
cd /workspace/002-n8n
./import-workflow.sh

# 3. Test it (after activating in n8n UI)
curl -X POST http://localhost:5678/webhook-test/bms-ai-direct \
  -H "Content-Type: application/json" \
  -d '{"chatInput": "What are emergency brake procedures?", "sessionId": "test-001"}'
```

---

## Files You Need

| File | Purpose | Status |
|------|---------|--------|
| `workflows/bms-ai-simple-direct.json` | Working workflow | ✅ Ready to import |
| `import-workflow.sh` | Import automation | ✅ Executable |
| `RESOLUTION_SUMMARY.md` | What was fixed | ✅ Read this |
| `WORKFLOW_FIX_EXPLANATION.md` | Detailed guide | ✅ Reference |

---

## Step-by-Step

### 1️⃣ Import Workflow (1 minute)

**Via n8n UI**:
1. Open http://localhost:5678
2. Click "Workflows" → "Import from File"
3. Select: `/workspace/002-n8n/workflows/bms-ai-simple-direct.json`
4. Click "Import"

**Via Script**:
```bash
cd /workspace/002-n8n
./import-workflow.sh
```

### 2️⃣ Activate (10 seconds)

1. Open the imported workflow in n8n UI
2. Click **Activate** toggle (top-right corner)
3. Green = Active ✅

### 3️⃣ Test (1 minute)

**In n8n Chat UI**:
1. Click "Chat" button on "When chat message received" node
2. Type: "What are VLAN configurations?"
3. Press Enter
4. ✅ Should receive answer with citations

**Via curl**:
```bash
curl -X POST http://localhost:5678/webhook-test/bms-ai-direct \
  -H "Content-Type: application/json" \
  -d '{"chatInput": "What are VLAN configurations?", "sessionId": "test-001"}'
```

**Expected Response**:
```json
{
  "response": "VLAN configurations in railway networks...",
  "citations": [...],
  "confidence": 0.85
}
```

---

## What Changed?

### Old (Broken) ❌
```
AI Agent with 4 tool nodes
↓
Error: "No execution data available"
```

### New (Working) ✅
```
Direct HTTP Request to BMS API
↓
Works reliably in n8n 1.113.3
```

**Trade-off**: Always calls `/api/v1/ask` endpoint (no dynamic tool selection)
**For POC**: This is sufficient ✅

---

## Troubleshooting

### ❌ "Cannot reach BMS API"
```bash
cd /workspace/001-bms-agent
source /workspace/bms-api-venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### ❌ "Empty response"
```bash
# Check Qdrant has documents
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'

# If 0, load documents
cd /workspace/001-bms-agent
python scripts/batch_process_incoming.py
```

### ❌ "Workflow not responding"
1. Check Activate toggle is ON
2. View Executions in n8n UI
3. Check detailed error in execution log

---

## Next: MS Teams Integration

Once tested, integrate with your MS Teams Bot:

```javascript
// In MS Teams Bot Main Handler (T016)
// Replace BMS AI Agent call with:

{
  "node": "Call BMS Workflow",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://localhost:5678/webhook-test/bms-ai-direct",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify({
      chatInput: $json.userMessage,
      sessionId: $json.conversationId
    }) }}"
  }
}
```

---

## Documentation

| Document | When to Read |
|----------|--------------|
| `QUICK_START.md` (this file) | 👈 Start here |
| `RESOLUTION_SUMMARY.md` | Understand what was fixed |
| `WORKFLOW_FIX_EXPLANATION.md` | Deep dive, troubleshooting |
| `/workspace/specs/002-create-a-microsoft/ANALYSIS_FIXES_APPLIED.md` | All 27 spec fixes applied |

---

## System Prompt

Updated system prompt for the AI Agent (if you add it back later):

**File**: `/workspace/002-n8n/system-prompt-for-agent.txt`

Copy-paste ready prompt with:
- Tool selection guide
- Response format with workflow steps
- Citation formatting
- Privacy protection rules

---

## Ready to Proceed? ✅

1. ✅ Import workflow: `./import-workflow.sh`
2. ✅ Activate in n8n UI
3. ✅ Test via Chat or curl
4. ✅ Integrate with MS Teams (T016-T020)
5. ✅ Continue with remaining tasks

---

**Questions?** → Read `WORKFLOW_FIX_EXPLANATION.md`
**Issues?** → Check Troubleshooting section above
**Success?** → Proceed to MS Teams integration 🎉

---

**Generated**: 2025-10-06
**Status**: Production-ready for POC phase
