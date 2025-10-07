# MS Teams AI Agent Integration - Quick Start Guide

**Date**: 2025-10-07
**Task**: T020b - Update bms-ai-agent workflow for MS Teams webhook triggers
**Status**: Ready to implement

---

## Current Workflow Analysis

### bms-ai-agent.json Structure

**Current Trigger**:
- Type: `@n8n/n8n-nodes-langchain.chatTrigger`
- Webhook ID: `bms-ai-agent-chat`
- Access: Public webhook at `/webhook/bms-ai-agent-chat`

**Input Format Expected**:
```json
{
  "chatInput": "user's question text",
  "sessionId": "conversation-id-for-memory"
}
```

**Components**:
1. **Chat Trigger** → Receives messages
2. **Parse Input** → Extracts `query` and `sessionId`
3. **BMS AI Agent** → LangChain agent with 4 tools
4. **Ollama Chat Model** → gpt-oss:latest
5. **Window Buffer Memory** → 10 message context window
6. **Tools**: ask_bms, semantic_search, hybrid_search, contextual_search

---

## Integration Options

### ✅ Option B: Sub-workflow Integration (RECOMMENDED)

**Architecture**:
```
MS Teams → Azure Bot Service → n8n Webhook
    ↓
teams-webhook-bot-handler.json (entry point)
    ↓
[Parse MS Teams message]
    ↓
[Whitelist check]
    ↓
[Execute Workflow: bms-ai-agent.json]
    ↓
[Format response for MS Teams]
    ↓
MS Teams (Bot Framework API)
```

**Advantages**:
- ✅ Preserves separation of concerns
- ✅ bms-ai-agent.json remains reusable (can be called from other sources)
- ✅ teams-webhook-bot-handler handles MS Teams-specific logic
- ✅ Clean data mapping layer
- ✅ Easier to test independently

**Implementation Steps**:

#### Step 1: Keep bms-ai-agent.json as-is

No changes needed to the agent workflow! It already accepts:
- `chatInput`: The user's question
- `sessionId`: For conversation memory

#### Step 2: Modify teams-webhook-bot-handler.json

**Current Workflow Structure** (as of 2025-10-07):
```
Teams Message Webhook
    ↓
Parse Teams Activity
    ↓
Is Valid Message? (IF node)
    ↓ (true branch)
Get Bot Framework Token
    ↓
Combine Token with Message
    ↓
Prepare Typing Indicator
    ↓
Send Typing Indicator
    ↓
Query BMS Agent (direct BMS API call)
    ↓
Format Response
    ↓
Send Reply to Teams
    ↓
Respond to Bot Framework
```

**⚠️ Note**: The current workflow does NOT have whitelist validation. To add it, insert a whitelist check node between "Is Valid Message?" and "Get Bot Framework Token".

**Modification**: Replace "Query BMS Agent" node with "Execute Workflow" to call bms-ai-agent:

**Node Configuration**:
```json
{
  "name": "Call BMS AI Agent",
  "type": "n8n-nodes-base.executeWorkflow",
  "parameters": {
    "workflowId": "bms-ai-agent",  // Or workflow ID from n8n
    "waitForResponse": true,
    "dataToSend": {
      "chatInput": "={{ $json.messageText }}",
      "sessionId": "={{ $json.conversationId }}"
    }
  }
}
```

**Data Mapping**:
- MS Teams `text` → Agent `chatInput`
- MS Teams `conversation.id` → Agent `sessionId`

#### Step 3: Add response formatting

After agent responds, format for MS Teams:

**Node: Format Agent Response**
```javascript
// Input: Agent response
const agentResponse = $json.output;

// Format for MS Teams
const teamsMessage = {
  type: 'message',
  text: agentResponse.text,
  textFormat: 'markdown',
  from: {
    id: process.env.BOT_APP_ID,
    name: 'BMS AI Agent'
  }
};

return {
  json: {
    ...messageData,
    responseText: agentResponse.text,
    replyActivity: teamsMessage
  }
};
```

#### Step 4: Test the integration

**Test Message**: Send via MS Teams
```
"What are the railway safety procedures?"
```

**Expected Flow**:
1. ✅ teams-webhook-bot-handler receives message
2. ✅ Whitelist check passes
3. ✅ Execute Workflow calls bms-ai-agent
4. ✅ Agent analyzes query → selects semantic_search tool
5. ✅ Tool executes → returns documents
6. ✅ Agent formats response with sources
7. ✅ Response formatted for MS Teams
8. ✅ Bot posts message to Teams channel

---

### ⚠️ Option A: Direct Integration (Alternative)

**Architecture**:
```
MS Teams → Azure Bot Service → n8n Webhook
    ↓
bms-ai-agent.json (modified with MS Teams webhook trigger)
    ↓
[Parse MS Teams activity]
    ↓
[Whitelist check]
    ↓
[BMS AI Agent]
    ↓
[Format & send to MS Teams]
```

**Advantages**:
- ✅ Fewer workflows
- ✅ Simpler architecture

**Disadvantages**:
- ❌ Tight coupling (agent knows about MS Teams)
- ❌ Harder to reuse agent for other channels
- ❌ More complex to test

**Implementation** (if you choose this):
1. Replace chatTrigger with Webhook node
2. Add MS Teams activity parsing
3. Add whitelist validation
4. Add Bot Framework response sending
5. Update input parsing to handle MS Teams format

**Not recommended** - Use Option B instead for better modularity.

---

## Implementation Checklist

### Option B Implementation (Recommended)

- [ ] **Backup current workflows**
  ```bash
  cp /workspace/002-n8n/workflows/teams-webhook-bot-handler.json \
     /workspace/002-n8n/workflows/teams-webhook-bot-handler.json.backup
  cp /workspace/002-n8n/workflows/bms-ai-agent.json \
     /workspace/002-n8n/workflows/bms-ai-agent.json.backup
  ```

- [ ] **Open n8n UI**
  ```
  http://localhost:5678
  ```

- [ ] **Open teams-webhook-bot-handler workflow**
  - Navigate to existing workflow
  - Locate the node after "Whitelist check"

- [ ] **Add Execute Workflow node**
  - Add node: "Execute Workflow"
  - Select: "bms-ai-agent" workflow
  - Enable: "Wait for sub-workflow to finish"
  - Map data:
    - `chatInput` = `{{ $json.messageText }}`
    - `sessionId` = `{{ $json.conversationId }}`

- [ ] **Update response formatting node**
  - Modify existing "Format Response" node
  - Update to use agent output instead of BMS API response
  - Map: `$json.output.text` → `responseText`

- [ ] **Remove direct BMS API call** (optional)
  - The "Query BMS Agent" node can be removed
  - Agent will call BMS API via tools instead

- [ ] **Test the integration**
  - Activate both workflows
  - Send test message in MS Teams
  - Check n8n execution logs
  - Verify response appears in Teams

- [ ] **Create integration tests** (T020c)
  - See: `/workspace/specs/002-create-a-microsoft/tasks.md` line 393

- [ ] **Document architecture** (T020d)
  - See: `/workspace/specs/002-create-a-microsoft/tasks.md` line 424

---

## Testing Scenarios

### Test 1: Basic Question
**MS Teams Message**: "What is business continuity?"

**Expected**:
1. Agent analyzes: "What is X?" → semantic_search tool
2. Tool searches BMS API for documents about business continuity
3. Agent formats response with document citations
4. Response posted to MS Teams

**Validation**:
```bash
# Check n8n execution log
# Should see:
# 1. teams-webhook-bot-handler execution
# 2. bms-ai-agent execution (sub-workflow)
# 3. semantic_search tool called
# 4. Response sent to MS Teams
```

### Test 2: Procedural Question
**MS Teams Message**: "How do I report an incident?"

**Expected**:
1. Agent analyzes: "How do I X?" → ask_bms tool
2. Tool calls /api/v1/ask endpoint
3. Agent returns direct answer with steps
4. Response posted to MS Teams

### Test 3: Document Code Lookup
**MS Teams Message**: "BMS-QHSE-PRO-007"

**Expected**:
1. Agent analyzes: Document code → hybrid_search tool
2. Tool finds exact document match
3. Agent returns document details
4. Response posted to MS Teams

### Test 4: Conversation Context
**Message 1**: "What are safety procedures?"
**Message 2**: "Can you give me more details on step 3?"

**Expected**:
1. Agent remembers message 1 context (Window Buffer Memory)
2. Agent understands "step 3" refers to previous response
3. Agent provides detailed explanation

---

## Troubleshooting

### Issue: Agent not triggered

**Check**:
1. teams-webhook-bot-handler workflow is active
2. Execute Workflow node has correct workflow ID
3. Whitelist check is passing

**Debug**:
```bash
# Check n8n execution logs
# Look for "Execute Workflow" node output
# Should see: {execution_id: "...", status: "success"}
```

### Issue: Agent receives wrong input format

**Check**:
- Data mapping in Execute Workflow node
- Should be: `chatInput` (not `text` or `query`)
- Should be: `sessionId` (not `conversation_id`)

**Fix**:
```json
{
  "chatInput": "={{ $json.messageText }}",
  "sessionId": "={{ $json.conversationId }}"
}
```

### Issue: Agent responds but no message in Teams

**Check**:
- Response formatting node
- Should extract `$json.output.text` from agent
- Should create Bot Framework activity

**Fix**:
Ensure "Send Reply to Teams" node receives:
```json
{
  "responseText": "<agent output>",
  "replyActivity": {
    "type": "message",
    "text": "<agent output>",
    "textFormat": "markdown"
  }
}
```

### Issue: Tools not executing

**Check**:
- BMS API is running: `curl http://localhost:8000/health`
- Ollama is running: `curl http://localhost:11434/api/tags`
- Agent has tool credentials configured

---

## Next Steps

1. **Implement** Option B integration (4 hours)
   - Follow checklist above
   - Test with 3 scenarios
   - Verify agent tool selection

2. **Create Integration Tests** (T020c - 2 hours)
   - See tasks.md line 393
   - 5 test scenarios
   - Automated validation

3. **Document Architecture** (T020d - 2 hours)
   - See tasks.md line 424
   - Architecture diagram
   - Configuration guide

---

## Reference

- **Task Definition**: `/workspace/specs/002-create-a-microsoft/tasks.md` line 361 (T020b)
- **Agent Workflow**: `/workspace/002-n8n/workflows/bms-ai-agent.json`
- **Webhook Handler**: `/workspace/002-n8n/workflows/teams-webhook-bot-handler.json`
- **MS Teams Setup**: `/workspace/002-n8n/docs/MS_TEAMS_WEBHOOK_SETUP.md`

---

**Status**: Ready to implement
**Recommended**: Option B (Sub-workflow integration)
**Estimated Effort**: 4 hours implementation + 2 hours testing + 2 hours documentation = 8 hours total
