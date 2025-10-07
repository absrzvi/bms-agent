# ✅ BMS AI Agent Workflow - Import Success

**Date**: 2025-10-06
**Status**: ✅ **IMPORTED** - Workflow successfully imported to n8n
**Workflow ID**: `FyOwgZgsPFfsP2TE`

---

## What Was Imported

✅ **BMS AI Agent - Railway Documentation RAG**

**Workflow Components:**
- ✅ Chat Trigger (webhook: `bms-ai-agent-chat`)
- ✅ Ollama Chat Model (Mistral Nemo 12B Instruct)
- ✅ Window Buffer Memory (10 message context)
- ✅ BMS AI Agent (main agent node)
- ✅ 4 AI Tools:
  1. Ask BMS Tool (PRIMARY)
  2. Semantic Search BMS Tool
  3. Hybrid Search BMS Tool
  4. Contextual Search BMS Tool
- ✅ Response handler
- ✅ Documentation sticky note

**Total Nodes**: 11
**Connection Types**: main, ai_tool, ai_languageModel, ai_memory

---

## Architecture Overview

```
User Query (Webhook/Chat)
    ↓
Parse Input (extract query + sessionId)
    ↓
BMS AI Agent (Ollama Mistral Nemo)
    ├─→ Ollama Chat Model (LLM)
    ├─→ Window Buffer Memory (conversation history)
    └─→ 4 Tools (agent decides which to use):
        ├─ Ask BMS (PRIMARY)
        ├─ Semantic Search BMS
        ├─ Hybrid Search BMS
        └─ Contextual Search BMS
    ↓
Respond to Webhook
```

---

## Chat Interface URL

The workflow is available at:
```
http://localhost:5678/webhook-test/bms-ai-agent-chat
```

Or via API:
```bash
curl -X POST http://localhost:5678/webhook/bms-ai-agent-chat \
  -H "Content-Type: application/json" \
  -d '{
    "chatInput": "What are the emergency brake procedures?",
    "sessionId": "test-session-1"
  }'
```

---

## Prerequisites

Before testing, verify all required services are running:

### 1. Ollama (Required)
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Verify mistral-nemo model is installed
curl http://localhost:11434/api/tags | jq -r '.models[].name' | grep mistral-nemo

# If not installed, pull it
ollama pull mistral-nemo:12b-instruct
```

### 2. BMS API (Required)
```bash
# Check BMS API health
curl http://localhost:8000/health

# Verify /ask endpoint works
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "max_chunks": 5, "include_citations": true}'
```

### 3. n8n (Already Running)
```bash
# Check n8n is running
curl http://localhost:5678/healthz
```

---

## Testing the Agent

### Test 1: Direct Question (Should use Ask BMS Tool)

**Via n8n Chat UI:**
1. Open: http://localhost:5678/workflow/FyOwgZgsPFfsP2TE
2. Click "Active" toggle (top right) to activate workflow
3. Go to: http://localhost:5678/webhook-test/bms-ai-agent-chat
4. Ask: "What are the emergency brake procedures?"

**Expected Behavior:**
- Agent uses Ask BMS tool (PRIMARY)
- Returns comprehensive answer with source citations
- Latency: 1-3 seconds

**Via API:**
```bash
curl -X POST http://localhost:5678/webhook/bms-ai-agent-chat \
  -H "Content-Type: application/json" \
  -d '{
    "chatInput": "What are the emergency brake procedures?",
    "sessionId": "test-1"
  }'
```

### Test 2: Technical Search (Should use Hybrid Search)

**Query:**
```
Find information about VLAN 100 configuration for safety systems
```

**Expected Behavior:**
- Agent uses Hybrid Search tool (semantic + keyword)
- Returns specific technical documents with VLAN 100 mentioned
- Provides relevant context

### Test 3: Contextual Query (Should use Contextual Search)

**Query:**
```
Tell me everything about brake inspection procedures including all prerequisites and safety checks
```

**Expected Behavior:**
- Agent uses Contextual Search tool
- Returns comprehensive information with parent sections
- Includes full procedure context

### Test 4: Follow-up Question (Tests Memory)

**Conversation:**
```
User: What are emergency brake procedures?
Agent: [Provides answer with citations]

User: What are the safety requirements for that?
```

**Expected Behavior:**
- Agent remembers "that" refers to emergency brake procedures
- Uses conversation history from Window Buffer Memory
- Provides relevant safety requirements

### Test 5: Out of Scope Query

**Query:**
```
What is the weather today?
```

**Expected Behavior:**
- Agent declines politely
- Says "I don't have information about that in the railway documentation"
- Does not make up information

---

## Monitoring Workflow Executions

### Via n8n UI

1. Open n8n: http://localhost:5678
2. Go to **Executions** tab
3. Filter by workflow: "BMS AI Agent - Railway Documentation RAG"
4. Click on any execution to see:
   - Which tools were called
   - Agent's reasoning process
   - Response time for each step
   - Final output

### Via API

```bash
# Get recent executions
curl -H "X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4ODczMzU4MC1lYzVkLTQyNDQtODNiNC02Y2UzZjcyMGMwYzIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU5NzU4NjUxfQ.Jw6PkPgleHX6YsvA7gsZPI0rrYiTmVY_nDlYpZAIA2o" \
  "http://localhost:5678/api/v1/executions?workflowId=FyOwgZgsPFfsP2TE&limit=10" | jq .
```

---

## Next Steps

### 1. Activate the Workflow ⚠️ **Required**

The workflow is currently inactive. To activate:

**Via n8n UI:**
1. Open: http://localhost:5678/workflow/FyOwgZgsPFfsP2TE
2. Click the **Active** toggle switch (top right)
3. The toggle should turn green

**Via API:**
```bash
curl -X PATCH http://localhost:5678/api/v1/workflows/FyOwgZgsPFfsP2TE \
  -H "X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4ODczMzU4MC1lYzVkLTQyNDQtODNiNC02Y2UzZjcyMGMwYzIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU5NzU4NjUxfQ.Jw6PkPgleHX6YsvA7gsZPI0rrYiTmVY_nDlYpZAIA2o" \
  -H "Content-Type: application/json" \
  -d '{"active": true}'
```

### 2. Test All Query Types

Run the 5 test cases above to verify:
- ✅ Tool selection is working correctly
- ✅ Agent reasoning is sound
- ✅ Source citations are included
- ✅ Conversation memory works
- ✅ Out-of-scope handling works

### 3. Integration with MS Teams Bot

Once testing is complete, integrate with MS Teams Bot Main Handler:

**Option A: Direct Integration**
Update MS Teams Bot Main Handler to call this workflow for question-type queries:
```javascript
if (text.match(/^(what|how|why|explain|tell me)/i)) {
  // Call BMS AI Agent workflow
  const response = await callWorkflow('FyOwgZgsPFfsP2TE', {
    chatInput: text,
    sessionId: conversationId
  });
  return response;
}
```

**Option B: Replace Query Analyzer**
Replace the existing Query Analyzer + BMS API Caller with this single intelligent agent:
- Remove: query-analyzer.json
- Remove: bms-api-caller.json
- Update: main-bot-handler.json to call FyOwgZgsPFfsP2TE directly

Benefits:
- Smarter tool selection
- Better context understanding
- Automatic source citations
- Multi-turn conversation support
- Simpler architecture (1 workflow instead of 3)

### 4. Monitor Performance

Track these metrics:
- **Response time**: Target < 3 seconds
- **Tool selection accuracy**: Should use correct tool for query type
- **Answer quality**: Check source citations are included
- **Memory effectiveness**: Follow-up questions work correctly

### 5. Refine System Prompt (Optional)

Based on usage patterns, you may want to update the system prompt in the "BMS AI Agent" node:
- Add domain-specific terminology
- Adjust tool selection guidance
- Add safety warnings for critical procedures
- Modify response format

---

## Troubleshooting

### Issue 1: Workflow execution fails immediately

**Symptoms**: Workflow fails right after trigger
**Cause**: Ollama not running or model not loaded
**Fix**:
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Restart Ollama if needed
/workspace/scripts/manage_services.sh restart

# Pre-load model
curl http://localhost:11434/api/generate -d '{
  "model": "mistral-nemo:12b-instruct",
  "prompt": "test",
  "stream": false
}'
```

### Issue 2: Agent not using the right tool

**Symptoms**: Agent uses Semantic Search when it should use Ask BMS
**Cause**: Tool descriptions unclear or query ambiguous
**Fix**:
- Refine tool descriptions in workflow nodes
- Add more explicit keywords to system prompt
- Test with more specific queries

### Issue 3: Slow responses (>5 seconds)

**Symptoms**: Long wait times for agent responses
**Causes**:
1. Ollama model loading (first request)
2. BMS API slow
3. Network latency

**Fixes**:
```bash
# Pre-warm Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "mistral-nemo:12b-instruct",
  "prompt": "test"
}'

# Check BMS API performance
time curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "max_chunks": 5}'
```

### Issue 4: No conversation memory

**Symptoms**: Agent doesn't remember previous messages
**Cause**: sessionId not being passed or Window Buffer Memory issue
**Fix**:
- Ensure sessionId is included in all requests
- Check Window Buffer Memory node configuration
- Verify sessionKey expression: `={{ $json.sessionId }}`

### Issue 5: Missing source citations

**Symptoms**: Answers don't include document sources
**Cause**: Ask BMS not including citations or agent not formatting them
**Fix**:
- Verify Ask BMS tool has `include_citations: true`
- Test BMS API directly: `curl -X POST http://localhost:8000/api/v1/ask -d '{"query":"test","include_citations":true}'`
- Update system prompt to emphasize citation importance

---

## Comparison with Previous Approach

| Feature | Query Analyzer (Old) | BMS AI Agent (New) |
|---------|---------------------|---------------------|
| Tool selection | Fixed rules (if/else) | AI decides dynamically |
| Multi-tool chaining | No | Yes (agent can use multiple tools) |
| Context awareness | None | Full conversation history |
| Source citations | Manual formatting | Automatic from tools |
| Handles ambiguity | No | Yes (agent interprets intent) |
| Follow-up questions | No | Yes (memory-enabled) |
| Technical queries | Moderate | Excellent (hybrid search) |
| Setup complexity | Multiple workflows | Single workflow |

---

## Files & Documentation

- **Workflow JSON**: `/workspace/002-n8n/workflows/bms-ai-agent.json`
- **Design Document**: `/workspace/002-n8n/BMS_RAG_WORKFLOW_DESIGN.md`
- **Usage Guide**: `/workspace/002-n8n/BMS_AI_AGENT_GUIDE.md`
- **This Import Doc**: `/workspace/002-n8n/BMS_AI_AGENT_IMPORT_SUCCESS.md`
- **Sample Reference**: `/workspace/002-n8n/workflows/sample-rag.json`

---

## Summary

✅ **BMS AI Agent workflow successfully imported**
✅ **All 11 nodes configured correctly**
✅ **4 AI tools connected and ready**
✅ **Conversation memory enabled**
⚠️ **Activation required** - Toggle "Active" in n8n UI
🧪 **Ready for testing** - See test cases above
🤖 **Ready for MS Teams integration** - See integration options

---

**Impact**: Intelligent agentic RAG system that can dynamically select the best tool for each query, with conversation memory and automatic source citations! 🚂🤖
