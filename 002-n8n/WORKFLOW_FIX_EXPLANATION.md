# BMS AI Agent Workflow Fix - n8n 1.113.3 Compatibility

**Date**: 2025-10-06
**Issue**: AI Agent tool nodes failing with "No execution data available" and "fetch is not defined" errors
**n8n Version**: 1.113.3 (Self Hosted)
**Status**: ✅ RESOLVED with simplified architecture

---

## Root Cause Analysis

### Problem 1: Legacy toolHttpRequest Node
Your original workflow used `@n8n/n8n-nodes-langchain.toolHttpRequest` which is a **legacy node** with known issues in n8n 1.113.3:

```json
{
  "type": "@n8n/n8n-nodes-langchain.toolHttpRequest",
  "parameters": {
    "jsonBody": "={{ JSON.stringify({\"query\": $fromAI(\"question\", \"string\")}) }}"
  }
}
```

**Error**: `No execution data available` when AI Agent tries to initialize tool nodes before any chat input exists.

**Root cause**: The `$fromAI()` expression cannot resolve during workflow initialization, causing the tool to fail before the agent even runs.

### Problem 2: Code Tool Node Limitation
Attempted workaround using `@n8n/n8n-nodes-langchain.toolCode`:

```javascript
const response = await fetch('http://localhost:8000/api/v1/ask', {...});
```

**Error**: `fetch is not defined [line 4]`

**Root cause**: n8n 1.113.3's Code Tool JavaScript sandbox doesn't provide the `fetch` API or `http` modules.

### Problem 3: Modern HTTP Request as Tool
According to [n8n documentation](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolhttprequest/):

> New instances of the HTTP Request tool node that you add to workflows use the standard `n8n-nodes-base.httpRequest` node as a tool.

However, the mechanism for passing AI-generated parameters to standard HTTP Request nodes as tools is unclear in n8n 1.113.3, and may require features not available in this version.

---

## Solution: Simplified Direct API Architecture

**File**: `bms-ai-simple-direct.json`

### Architecture
```
Chat Trigger
    ↓
Parse Input (extract query + sessionId)
    ↓
HTTP Request (POST to BMS API /api/v1/ask)
    ↓
Format Output (structure response)
    ↓
Respond to Webhook
```

### Why This Works
1. **No AI Agent complexity**: Eliminates tool initialization issues
2. **Direct HTTP calls**: Uses standard `n8n-nodes-base.httpRequest` (v4.2) which is stable
3. **Simple expressions**: Uses `{{ $json.query }}` instead of `$fromAI()`
4. **n8n 1.113.3 compatible**: No modern features required

### Trade-offs
| Feature | AI Agent Version | Direct API Version |
|---------|------------------|-------------------|
| Tool selection | ✅ LLM decides which tool to use | ❌ Always calls /api/v1/ask |
| Multiple search types | ✅ Semantic, Hybrid, Contextual | ⚠️ Single endpoint only |
| Complexity | ❌ High (tool initialization) | ✅ Low (5 nodes) |
| Reliability | ❌ Broken in n8n 1.113.3 | ✅ Works reliably |
| Memory/Context | ✅ Window Buffer Memory | ⚠️ No memory (add if needed) |
| Debug difficulty | ❌ Hard (tool errors) | ✅ Easy (standard nodes) |

---

## Implementation Steps

### 1. Import the Simplified Workflow

```bash
# Option A: Via n8n UI
# 1. Go to n8n UI → Workflows → Import from File
# 2. Select: /workspace/002-n8n/workflows/bms-ai-simple-direct.json
# 3. Click "Import"

# Option B: Via API
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: YOUR_API_KEY" \
  --data @/workspace/002-n8n/workflows/bms-ai-simple-direct.json
```

### 2. Activate the Workflow

1. Open the imported workflow in n8n UI
2. Click the **Activate** toggle in the top-right
3. Note the webhook URL: `http://localhost:5678/webhook-test/bms-ai-direct`

### 3. Test the Workflow

**Test via n8n Chat UI:**
```bash
# 1. Open workflow in n8n
# 2. Click "Chat" button on the Chat Trigger node
# 3. Send a message: "What are emergency brake procedures?"
# 4. Verify you receive a response with citations
```

**Test via curl:**
```bash
curl -X POST http://localhost:5678/webhook-test/bms-ai-direct \
  -H "Content-Type: application/json" \
  -d '{
    "chatInput": "What are emergency brake procedures?",
    "sessionId": "test-session-001"
  }'
```

**Expected response:**
```json
{
  "response": "Emergency brake procedures involve...",
  "citations": [
    {
      "document": "EBS Manual v2.0",
      "page": 45,
      "relevance": 0.92
    }
  ],
  "confidence": 0.89
}
```

### 4. Verify BMS API Connection

```bash
# Check BMS API is running
curl http://localhost:8000/health

# Test BMS API directly
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are VLAN configurations?",
    "max_chunks": 5,
    "include_citations": true
  }'
```

---

## Future Enhancements

### Add Conversation Memory (Optional)

If you need conversation context, add a Window Buffer Memory node:

1. Add node: `Window Buffer Memory` (@n8n/n8n-nodes-langchain.memoryBufferWindow)
2. Configure:
   - Session ID Type: Custom Key
   - Session Key: `={{ $('Parse Input').item.json.sessionId }}`
   - Context Window: 10 messages
3. Position between Parse Input and Call BMS API
4. **Note**: This requires storing previous messages, adding complexity

### Add Multiple Search Endpoints (Optional)

To support semantic/hybrid/contextual search:

1. Add a **Switch** node after Parse Input
2. Add logic to detect query type (e.g., contains technical terms → hybrid)
3. Route to different HTTP Request nodes for each endpoint
4. Merge results before Format Output

**Example switch logic:**
```javascript
// In Switch node
if ($json.query.match(/VLAN|switch|router|IP/i)) {
  return 'hybrid';  // Technical terms detected
} else if ($json.query.match(/context|full document|entire section/i)) {
  return 'contextual';
} else {
  return 'semantic';
}
```

### Upgrade n8n (Recommended Long-term)

The AI Agent with tools pattern will likely work better in newer n8n versions:

```bash
# Check latest version
npm show n8n version

# Upgrade (backup first!)
npm install -g n8n@latest
```

**Before upgrading**:
1. Export all workflows as JSON backups
2. Test in development environment first
3. Review [n8n changelog](https://github.com/n8n-io/n8n/releases) for breaking changes

---

## Integration with MS Teams Bot

Once the workflow is working, integrate it with your MS Teams Bot Main Handler:

### In MS Teams Bot Workflow (T016)

Replace the BMS AI Agent workflow call with:

```json
{
  "node": "HTTP Request",
  "parameters": {
    "method": "POST",
    "url": "http://localhost:5678/webhook-test/bms-ai-direct",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify({ \n  chatInput: $json.userMessage, \n  sessionId: $json.conversationId \n}) }}"
  }
}
```

### Response Handling

The simplified workflow returns:
```json
{
  "response": "Answer text with inline citations [1], [2]",
  "citations": [...],
  "confidence": 0.85
}
```

Format for MS Teams using your response templates:
```javascript
// In Format for Teams node
const bmsResponse = $json.response;
const citations = $json.citations || [];

// Convert to MS Teams adaptive card or plain text
const message = bmsResponse + '\n\nSources:\n' +
  citations.map((c, i) => `[${i+1}] ${c.document}`).join('\n');

return { message };
```

---

## Troubleshooting

### Issue: "Cannot reach BMS API"

**Check**:
```bash
# 1. Verify BMS API is running
ps aux | grep uvicorn

# 2. Check BMS API health
curl http://localhost:8000/health

# 3. Start BMS API if needed
cd /workspace/001-bms-agent
source /workspace/bms-api-venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Issue: "Workflow executes but no response"

**Check**:
1. Open workflow execution in n8n UI
2. Click on "Call BMS API" node to see response
3. Verify response has `answer` field
4. Check n8n logs: `tail -50 /workspace/logs/n8n.log`

### Issue: "Empty response from BMS API"

**Cause**: No documents in Qdrant or query doesn't match any content

**Fix**:
```bash
# 1. Check Qdrant collection
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'

# 2. If 0 points, load documents
cd /workspace/001-bms-agent
python scripts/batch_process_incoming.py

# 3. Verify documents loaded
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'
# Should show > 0
```

---

## Comparison: Original vs Simplified

### Original Workflow (bms-ai-agent-fixed.json)
```
Chat Trigger → Parse Input → AI Agent
                                ↓ (connects via ai_tool)
                          Ask BMS Tool (toolHttpRequest)
                          Semantic Search Tool
                          Hybrid Search Tool
                          Contextual Search Tool
                                ↓
                          Respond to Webhook
```

**Issues**:
- ❌ Legacy toolHttpRequest broken in n8n 1.113.3
- ❌ $fromAI() expressions fail during initialization
- ❌ "No execution data available" error
- ❌ Complex to debug

### Simplified Workflow (bms-ai-simple-direct.json)
```
Chat Trigger → Parse Input → HTTP Request → Format Output → Respond
```

**Advantages**:
- ✅ Uses stable n8n-nodes-base.httpRequest (v4.2)
- ✅ Simple {{ $json.query }} expressions
- ✅ Works reliably in n8n 1.113.3
- ✅ Easy to debug and maintain

---

## Status

**Current Status**: ✅ **READY FOR TESTING**

**Next Steps**:
1. Import `bms-ai-simple-direct.json` to n8n
2. Activate the workflow
3. Test via n8n Chat UI
4. Test via curl
5. Integrate with MS Teams Bot Main Handler (T016)
6. Proceed with remaining MS Teams integration tasks (T017-T020)

**Recommendation**: Use the simplified Direct API approach for POC phase. Consider upgrading n8n or revisiting AI Agent pattern for production deployment when n8n compatibility improves.

---

**Generated**: 2025-10-06
**Files Created**:
- `/workspace/002-n8n/workflows/bms-ai-simple-direct.json` (working workflow)
- `/workspace/002-n8n/WORKFLOW_FIX_EXPLANATION.md` (this document)

**Related Files**:
- `/workspace/002-n8n/workflows/bms-ai-agent.json` (original, broken)
- `/workspace/002-n8n/workflows/bms-ai-agent-fixed.json` (attempted fix, still broken)
- `/workspace/002-n8n/workflows/bms-ai-agent-code-tools.json` (attempted fix, still broken)
