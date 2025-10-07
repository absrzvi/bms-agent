# MS Teams + BMS AI Agent Integration Architecture

**Task**: T020d
**Date**: 2025-10-07
**Status**: Complete

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Configuration Guide](#configuration-guide)
3. [Message Flow](#message-flow)
4. [Agent Tools Available](#agent-tools-available)
5. [Troubleshooting](#troubleshooting)
6. [Testing Procedures](#testing-procedures)

---

## Architecture Overview

### System Components

```
┌─────────────────┐
│   MS Teams      │
│   (User Chat)   │
└────────┬────────┘
         │ 1. User sends message
         ↓
┌─────────────────────────┐
│  Azure Bot Service      │
│  (Bot Framework)        │
└────────┬────────────────┘
         │ 2. POST to webhook
         ↓
┌──────────────────────────────────────────────┐
│  n8n Workflow: teams-webhook-bot-handler     │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │ 1. Receive MS Teams Activity       │    │
│  └──────────┬─────────────────────────┘    │
│             ↓                                │
│  ┌────────────────────────────────────┐    │
│  │ 2. Parse Message Data              │    │
│  │    - Extract text                  │    │
│  │    - Extract user ID               │    │
│  │    - Extract conversation ID       │    │
│  └──────────┬─────────────────────────┘    │
│             ↓                                │
│  ┌────────────────────────────────────┐    │
│  │ 3. Is Valid Message? (IF check)    │    │
│  │    - Filter non-message activities │    │
│  │    ⚠️ NO WHITELIST CHECK (yet)      │    │
│  └──────────┬─────────────────────────┘    │
│             ↓                                │
│  ┌────────────────────────────────────┐    │
│  │ 4. Get Bot Framework OAuth Token   │    │
│  └──────────┬─────────────────────────┘    │
│             ↓                                │
│  ┌────────────────────────────────────┐    │
│  │ 5. Send Typing Indicator           │    │
│  └──────────┬─────────────────────────┘    │
│             ↓                                │
│  ┌────────────────────────────────────┐    │
│  │ 6. Query BMS Agent (direct API)    │    │
│  │    OR Execute Workflow (ai-agent)  │────┼─┐
│  └──────────┬─────────────────────────┘    │ │
│             ↓                                │ │
│  ┌────────────────────────────────────┐    │ │
│  │ 7. Format Response for Teams       │    │ │
│  └──────────┬─────────────────────────┘    │ │
│             ↓                                │ │
│  ┌────────────────────────────────────┐    │ │
│  │ 8. Send Reply to MS Teams          │    │ │
│  │    (Bot Framework API)             │    │ │
│  └────────────────────────────────────┘    │ │
└──────────────────────────────────────────────┘ │
         │ 9. Response posted                    │
         ↓                                        │
┌─────────────────┐                              │
│   MS Teams      │                              │
│   (Bot Reply)   │                              │
└─────────────────┘                              │
                                                  │
    ┌─────────────────────────────────────────────┘
    │ 5. Sub-workflow execution
    ↓
┌──────────────────────────────────────────────┐
│  n8n Workflow: bms-ai-agent                  │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │ Input: chatInput, sessionId        │    │
│  └──────────┬─────────────────────────┘    │
│             ↓                                │
│  ┌────────────────────────────────────┐    │
│  │ LangChain Agent                    │    │
│  │  - Ollama LLM (gpt-oss:latest)     │    │
│  │  - Window Buffer Memory (10 msgs)  │    │
│  │  - Tool Selection Decision Tree    │    │
│  └──────────┬─────────────────────────┘    │
│             ↓                                │
│  ┌────────────────────────────────────┐    │
│  │ Tool Execution (selected by agent):│    │
│  │  • ask_bms                         │────┼─┐
│  │  • semantic_search                 │────┼─┤
│  │  • hybrid_search                   │────┼─┤
│  │  • contextual_search               │────┼─┤
│  └──────────┬─────────────────────────┘    │ │
│             ↓                                │ │
│  ┌────────────────────────────────────┐    │ │
│  │ 6. Return Agent Output             │    │ │
│  │    {text, sources, toolCalls}      │    │ │
│  └────────────────────────────────────┘    │ │
└──────────────────────────────────────────────┘ │
                                                  │
    ┌─────────────────────────────────────────────┘
    │ All tools call BMS API
    ↓
┌──────────────────────────────────────────────┐
│  BMS API (FastAPI)                           │
│  http://localhost:8000                       │
│                                              │
│  • POST /api/v1/ask                          │
│  • POST /api/v1/search/semantic              │
│  • POST /api/v1/search/hybrid                │
│  • POST /api/v1/search/contextual            │
│  • POST /api/v1/embeddings                   │
└──────────────┬───────────────────────────────┘
               ↓
    ┌────────────────────┐
    │  Qdrant Vector DB  │
    │  (1,794 documents) │
    └────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **MS Teams** | User interface for chat | Microsoft Teams client |
| **Azure Bot Service** | Bot Framework webhook routing | Azure hosted service |
| **teams-webhook-bot-handler** | Entry point, MS Teams protocol handling, whitelist enforcement | n8n workflow |
| **bms-ai-agent** | LLM-powered agent with tool selection | n8n LangChain agent |
| **BMS API** | Document search and retrieval | FastAPI + Qdrant |
| **Redis** | Conversation history, cache | Redis 7 |
| **Ollama** | LLM inference (gpt-oss:latest) | Ollama runtime |

---

## Configuration Guide

### 1. Environment Variables

Configure in `/workspace/002-n8n/config/n8n.env`:

```bash
# MS Teams Bot Framework
BOT_APP_ID=<your-azure-app-id>
BOT_APP_PASSWORD=<your-azure-app-secret>

# BMS API
BMS_API_URL=http://localhost:8000

# Redis
REDIS_URL=redis://localhost:6379

# Ollama
OLLAMA_URL=http://localhost:11434

# n8n
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_EDITOR_BASE_URL=https://nqz5l77nsrdkyt-5678.proxy.runpod.net/
WEBHOOK_URL=https://nqz5l77nsrdkyt-5678.proxy.runpod.net/
```

### 2. Azure Bot Service Configuration

**Messaging Endpoint**:
```
https://nqz5l77nsrdkyt-5678.proxy.runpod.net/webhook/teams-bot
```

**Configuration Steps**:
1. Azure Portal → Your Bot Resource → Configuration
2. Set Messaging endpoint to webhook URL above
3. Save configuration
4. Verify bot enabled for MS Teams channel

### 3. n8n Workflow Activation

**Required Workflows**:
1. `teams-webhook-bot-handler.json` - Entry point (MUST be active)
2. `bms-ai-agent.json` - Agent workflow (called by handler)

**Activation Steps**:
```bash
# Start n8n
./scripts/start-n8n.sh

# Navigate to n8n UI
open http://localhost:5678

# For each workflow:
# 1. Open workflow
# 2. Click "Active" toggle (top right)
# 3. Verify green status indicator
```

### 4. Whitelist Configuration (Optional - Not Currently Implemented)

**⚠️ IMPORTANT**: The current `teams-webhook-bot-handler.json` workflow **does NOT include whitelist validation**.

**Current Behavior**: All messages from any channel are processed (no access control).

**To Add Whitelist Functionality** (optional enhancement):

1. **Create whitelist configuration** at `/workspace/002-n8n/config/whitelist.json`:
   ```json
   {
     "admins": ["user-id-001"],
     "channels": [
       "19:channel-id-001@thread.tacv2",
       "19:channel-id-002@thread.tacv2"
     ]
   }
   ```

2. **Add whitelist check node** in n8n workflow:
   - Position: Between "Is Valid Message?" and "Get Bot Framework Token"
   - Type: Code node or HTTP Request to whitelist validation service
   - Uses: `/workspace/002-n8n/lib/whitelist.js` module (already exists)
   - Logic:
     ```javascript
     const { getWhitelistManager } = require('/workspace/002-n8n/lib/whitelist');
     const whitelist = getWhitelistManager();

     const channelId = $json.conversationId;
     const isAllowed = whitelist.isChannelAllowed(channelId);

     if (!isAllowed) {
       // Send rejection message
       return {
         json: {
           ...$json,
           rejected: true,
           rejectReason: 'Channel not whitelisted'
         }
       };
     }

     return { json: $json };
     ```

3. **Add rejection response branch**:
   - If `rejected: true`, send "This bot is currently in POC phase. Contact your admin to request access."
   - Skip agent execution

**Note**: The whitelist module (`lib/whitelist.js`) and documentation exist, but the workflow integration is not implemented. This is an optional security enhancement for POC phase access control.

---

## Message Flow

### Detailed Message Processing Steps

#### 1. Message Reception (teams-webhook-bot-handler)

**Input**: MS Teams Bot Framework activity
```json
{
  "type": "message",
  "id": "msg-1234567890",
  "timestamp": "2025-10-07T12:00:00Z",
  "from": {
    "id": "user-abc-123",
    "name": "John Doe"
  },
  "conversation": {
    "id": "19:meeting_xyz@thread.v2",
    "name": "General"
  },
  "text": "What are the railway safety procedures?",
  "serviceUrl": "https://smba.trafficmanager.net/teams/"
}
```

**Processing**:
```javascript
// Node: Parse Teams Activity
const messageText = activity.text;
const userId = activity.from.id;
const conversationId = activity.conversation.id;
const serviceUrl = activity.serviceUrl;
```

#### 2. Message Validation

**Check**: Is activity type "message" with non-empty text?

**If NOT valid message**:
```javascript
// Response sent to Bot Framework
{
  "status": "ok",
  "processed": false,
  "reason": "not a message"
}
// STOP - Do not proceed to agent
```

**If valid message**: Continue to token acquisition

**⚠️ Note**: Current workflow does NOT perform whitelist validation. All messages from any channel are processed.

#### 3. OAuth Token Acquisition

**Get Bot Framework OAuth token** from Azure AD:
```javascript
POST https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token
Body:
  grant_type=client_credentials
  client_id={BOT_APP_ID}
  client_secret={BOT_APP_PASSWORD}
  scope=https://api.botframework.com/.default
```

**Token cached** for later use in sending reply.

#### 4. Agent Invocation (Execute Workflow node or Direct API)

**Data Mapping**:
```javascript
// Execute Workflow configuration
{
  "workflowId": "bms-ai-agent",
  "waitForResponse": true,
  "dataToSend": {
    "chatInput": messageText,      // "What are the railway safety procedures?"
    "sessionId": conversationId    // "19:meeting_xyz@thread.v2"
  }
}
```

#### 5. Agent Processing (bms-ai-agent workflow)

**Step 5a: Agent Analysis**

Agent receives input and analyzes query:
```
Query: "What are the railway safety procedures?"
Analysis: Broad/exploratory question asking WHAT something is
Decision Tree:
  - Contains document code? NO
  - Contains "what are" keyword? YES
  - Query type: Definition/discovery
Selected Tool: semantic_search
Reason: Need to find multiple documents about safety procedures
```

**Step 5b: Tool Execution**

Agent calls `semantic_search` tool:
```javascript
// Tool configuration
{
  "name": "semantic_search",
  "description": "Search for documents and information about topics",
  "parameters": {
    "query": "railway safety procedures",
    "limit": 8
  }
}
```

Tool makes HTTP request to BMS API:
```javascript
POST http://localhost:8000/api/v1/search/semantic
{
  "query": "railway safety procedures",
  "limit": 8,
  "min_score": 0.7
}
```

**Step 5c: Agent Response Formatting**

Agent receives tool results and formats response:
```
According to BMS-QHSE-PRO-007 (Railway Safety Standards), the key safety procedures are:

1. **Pre-departure Checks**: Verify all safety systems operational before departure
2. **Signal Compliance**: All signals must be obeyed without exception
3. **Speed Restrictions**: Adhere to all posted speed limits
4. **Emergency Protocols**: Follow emergency brake procedures when hazards detected

Sources:
- BMS-QHSE-PRO-007: Railway Safety Standards (Score: 0.92)
- BMS-QHSE-GDE-015: Safety Procedure Guide (Score: 0.88)
- BMS-TRAIN-MAN-003: Train Operation Manual (Score: 0.85)
```

**Output** returned to teams-webhook-bot-handler:
```json
{
  "output": {
    "text": "According to BMS-QHSE-PRO-007...",
    "toolCalls": [
      {
        "tool": "semantic_search",
        "query": "railway safety procedures",
        "results": [...]
      }
    ]
  }
}
```

#### 6. Response Formatting for MS Teams

**Format agent output** as Bot Framework activity:
```javascript
// Node: Format Response
const agentText = $json.output.text;

const replyActivity = {
  "type": "message",
  "from": {
    "id": process.env.BOT_APP_ID,
    "name": "BMS AI Agent"
  },
  "text": agentText,
  "textFormat": "markdown"
};
```

#### 7. Send Reply to MS Teams

**HTTP POST** to Bot Framework API:
```javascript
POST {serviceUrl}/v3/conversations/{conversationId}/activities
Headers:
  Authorization: Bearer {access_token}
  Content-Type: application/json
Body: {replyActivity}
```

#### 8. Store Conversation Context (Optional)

**Redis storage** (for context continuity - if implemented):
```javascript
// Key: conversation:{conversationId}:history
// Value: List of message objects
await client.lPush(
  `conversation:${conversationId}:history`,
  JSON.stringify({
    query: messageText,
    response: agentText,
    timestamp: new Date().toISOString()
  })
);
await client.expire(`conversation:${conversationId}:history`, 604800); // 7 days
```

---

## Agent Tools Available

The BMS AI Agent has 4 LangChain tools configured. The agent selects the appropriate tool based on query analysis.

### Tool 1: ask_bms

**When Used**: Specific procedural "how-to" questions

**Query Patterns**:
- "How do I [ACTION]?"
- "What is the process for [SPECIFIC ACTION]?"
- "When do I need to [ACTION]?"

**Examples**:
- ✅ "How do I report an incident?"
- ✅ "What is the process for requesting leave?"
- ✅ "When do I need to notify HR?"

**BMS API Endpoint**: `POST /api/v1/ask`

**Tool Configuration**:
```javascript
{
  "name": "ask_bms",
  "description": "Get direct answers to specific procedural questions",
  "parameters": {
    "query": {
      "type": "string",
      "description": "The question to answer"
    },
    "limit": {
      "type": "number",
      "description": "Number of sources to retrieve (default: 5)"
    }
  }
}
```

### Tool 2: semantic_search

**When Used**: Exploratory/discovery queries, definitions, "what is" questions

**Query Patterns**:
- "What is [CONCEPT]?"
- "What policies/documents cover [TOPIC]?"
- "Tell me about [SUBJECT]"
- "What information exists on [TOPIC]?"

**Examples**:
- ✅ "What is business continuity?"
- ✅ "What policies cover employee benefits?"
- ✅ "Tell me about railway safety procedures"

**BMS API Endpoint**: `POST /api/v1/search/semantic`

**Tool Configuration**:
```javascript
{
  "name": "semantic_search",
  "description": "Search for documents and information about topics (for exploration and discovery)",
  "parameters": {
    "query": {
      "type": "string",
      "description": "Topic or concept to search for"
    },
    "limit": {
      "type": "number",
      "description": "Number of results (default: 8)"
    }
  }
}
```

### Tool 3: hybrid_search

**When Used**: Exact document codes, technical identifiers, specific IDs

**Query Patterns**:
- "BMS-[DEPT]-[TYPE]-[###]"
- "Form [ID]"
- "VLAN [NUMBER]"

**Examples**:
- ✅ "BMS-QHSE-PRO-007"
- ✅ "Form FOR-015"
- ✅ "VLAN 100"

**BMS API Endpoint**: `POST /api/v1/search/hybrid`

**Tool Configuration**:
```javascript
{
  "name": "hybrid_search",
  "description": "Search for exact document codes and technical identifiers",
  "parameters": {
    "query": {
      "type": "string",
      "description": "Exact code or ID to find"
    },
    "limit": {
      "type": "number",
      "description": "Number of results (default: 5)"
    }
  }
}
```

### Tool 4: contextual_search

**When Used**: Requests for complete sections, full procedures, detailed information

**Query Patterns**:
- "Complete [PROCEDURE]"
- "Full [PROCESS] with all steps"
- "Entire [DOCUMENT/SECTION]"

**Examples**:
- ✅ "Complete incident reporting procedure"
- ✅ "Full onboarding process with all steps"
- ✅ "Entire safety checklist"

**BMS API Endpoint**: `POST /api/v1/search/contextual`

**Tool Configuration**:
```javascript
{
  "name": "contextual_search",
  "description": "Retrieve complete sections and full procedures with all context",
  "parameters": {
    "query": {
      "type": "string",
      "description": "Procedure or section to retrieve in full"
    },
    "limit": {
      "type": "number",
      "description": "Number of results (default: 5)"
    }
  }
}
```

### Tool Selection Decision Tree

The agent follows this exact decision tree (from system prompt):

```
Step 1: Check for Document Codes/IDs
  IF query contains "BMS-[LETTERS]-[LETTERS]-[NUMBERS]"
  OR query contains exact equipment IDs, form numbers, VLAN numbers
  THEN use hybrid_search
  STOP

Step 2: Check for Broad/Exploratory Keywords
  IF query contains ANY of:
    - "what policies", "what documents", "what information"
    - "show me documents", "what is [CONCEPT]"
    - "tell me about [TOPIC]", "all information"
    - "documents about", "policies covering", "exists about"
  THEN use semantic_search
  STOP

Step 3: Check for Specific How-To Questions
  IF query contains ANY of:
    - "how do I [ACTION]", "how to [ACTION]"
    - "what is the process for [SPECIFIC ACTION]"
    - "what are the steps to [SPECIFIC ACTION]"
    - "when do I need to [SPECIFIC ACTION]"
    - "who do I contact for [SPECIFIC ACTION]"
  THEN use ask_bms
  STOP

Step 4: Check for Complete/Full Context
  IF query contains ANY of:
    - "complete", "full", "entire"
    - "all steps", "detailed"
  THEN use contextual_search
  STOP

Step 5: Default Fallback
  - Is it asking WHAT something IS? → semantic_search
  - Is it asking HOW to do something specific? → ask_bms
  - Unsure? → semantic_search (safer default for exploration)
```

---

## Troubleshooting

### Issue 1: Webhook not triggering agent

**Symptoms**:
- User sends message in MS Teams
- No response from bot
- No execution logs in n8n

**Diagnosis**:
```bash
# Check n8n is running
curl http://localhost:5678/healthz

# Check webhook endpoint
curl -X POST https://nqz5l77nsrdkyt-5678.proxy.runpod.net/webhook/teams-bot \
  -H "Content-Type: application/json" \
  -d '{"type":"message","text":"test"}'
# Should return: {"status":"ok"}

# Check workflow is active
# n8n UI → teams-webhook-bot-handler → Verify green "Active" toggle
```

**Solutions**:
1. ✅ Activate teams-webhook-bot-handler workflow in n8n UI
2. ✅ Verify Azure Bot Service messaging endpoint matches webhook URL
3. ✅ Check n8n logs: `tail -f /workspace/logs/n8n.log`

### Issue 2: Agent receives malformed input

**Symptoms**:
- Agent executes but returns errors
- n8n execution log shows "undefined" values
- Agent complains about missing chatInput or sessionId

**Diagnosis**:
```javascript
// Check Execute Workflow node output
// Should see:
{
  "chatInput": "user's question",
  "sessionId": "conversation-id-here"
}

// NOT:
{
  "text": "user's question",  // Wrong field name
  "conversation_id": "..."     // Wrong field name
}
```

**Solutions**:
1. ✅ Verify data mapping in Execute Workflow node:
   - `chatInput` = `{{ $json.messageText }}`
   - `sessionId` = `{{ $json.conversationId }}`
2. ✅ Check Parse Teams Activity node extracts correct fields
3. ✅ Test with n8n manual execution (inject test data)

### Issue 3: Tool execution failures

**Symptoms**:
- Agent responds but says "I don't have information"
- Tools return empty results
- BMS API errors in agent reasoning

**Diagnosis**:
```bash
# Check BMS API is running
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Check Ollama is running
curl http://localhost:11434/api/tags
# Should return: JSON with available models

# Check Qdrant has documents
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'
# Should return: > 1000
```

**Solutions**:
1. ✅ Start BMS API: `/workspace/scripts/manage_services.sh start`
2. ✅ Verify Ollama has gpt-oss:latest model
3. ✅ Check Qdrant collection not empty
4. ✅ Review agent execution logs for tool call details

### Issue 4: Response not appearing in Teams

**Symptoms**:
- Agent executes successfully (n8n logs show success)
- No message appears in MS Teams channel

**Diagnosis**:
```bash
# Check Bot Framework API authentication
# Verify BOT_APP_ID and BOT_APP_PASSWORD in config/n8n.env

# Check Send Reply to Teams node execution
# Should see HTTP 200 response
```

**Solutions**:
1. ✅ Verify Bot Framework OAuth token is obtained (check "Get Bot Framework Token" node)
2. ✅ Check `serviceUrl` is correctly passed from webhook to reply
3. ✅ Verify Bot has permission to post in channel (check Azure Bot Service channels)
4. ✅ Test with Bot Framework Emulator for local debugging

---

## Testing Procedures

### Manual Testing via MS Teams

**Prerequisites**:
- Bot added to MS Teams
- User in whitelisted channel
- All services running (Redis, BMS API, Ollama, n8n)

**Test Scenarios**:

#### Test 1: Basic Question (semantic_search)
```
User: What is business continuity?

Expected Response:
✅ Agent analyzes query
✅ Selects semantic_search tool
✅ Returns documents about business continuity
✅ Includes citations with document IDs
✅ Response time < 10s
```

#### Test 2: How-To Question (ask_bms)
```
User: How do I report an incident?

Expected Response:
✅ Agent selects ask_bms tool
✅ Returns step-by-step procedure
✅ Includes specific actions to take
✅ Citations from procedure documents
```

#### Test 3: Document Code Lookup (hybrid_search)
```
User: BMS-QHSE-PRO-007

Expected Response:
✅ Agent selects hybrid_search tool
✅ Returns exact document match
✅ Includes document summary
✅ May include related documents
```

#### Test 4: Follow-Up Question (context memory)
```
User: What are the safety procedures?
Agent: [Lists safety procedures]

User: Can you explain step 3?

Expected Response:
✅ Agent remembers previous answer
✅ Provides detailed explanation of step 3
✅ References original safety procedures
```

### Automated Testing

**Run Integration Tests**:
```bash
cd /workspace/002-n8n
npm test tests/integration/test-teams-ai-agent-integration.js
```

**Expected Output**:
```
PASS tests/integration/test-teams-ai-agent-integration.js
  MS Teams → BMS AI Agent Integration
    ✓ Natural language question triggers AI agent and returns answer (5234ms)
    ✓ AI agent uses semantic_search for exploratory questions (4876ms)
    ✓ Agent maintains conversation context across messages (10145ms)
    ✓ Whitelist blocks non-whitelisted channels from agent (2012ms)
    ✓ Agent handles BMS API errors gracefully (3456ms)

  AI Agent Tool Selection Logic
    ✓ Agent selects hybrid_search for document codes (4532ms)
    ✓ Agent selects ask_bms for how-to questions (5123ms)

Test Suites: 1 passed, 1 total
Tests:       7 passed, 7 total
```

### Monitoring Agent Execution Logs

**n8n Execution Logs**:
```bash
# n8n UI → Executions tab
# Filter by workflow: teams-webhook-bot-handler, bms-ai-agent
# Check for:
# - Successful execution (green checkmark)
# - Tool selection reasoning (agent node output)
# - BMS API response (tool node output)
# - Final response sent to Teams
```

**Agent Reasoning Visibility**:

The agent shows its reasoning in the output:
```
Query: "What is business continuity?"
Analysis: Asking for definition/explanation of a concept
Decision Tree:
  - Contains document code? NO
  - Contains "what is [CONCEPT]"? YES → This triggers semantic_search
  - This is asking WHAT something IS (definition), not HOW to do something
Selected Tool: semantic_search
Reason: Definition questions need to find relevant documents about the concept
Tool Call: semantic_search("business continuity", limit=8)
```

This makes debugging tool selection issues straightforward.

---

## Additional Resources

- **Quick Start Guide**: `/workspace/002-n8n/docs/MS_TEAMS_AI_AGENT_QUICKSTART.md`
- **MS Teams Webhook Setup**: `/workspace/002-n8n/docs/MS_TEAMS_WEBHOOK_SETUP.md`
- **Integration Tests**: `/workspace/002-n8n/tests/integration/test-teams-ai-agent-integration.js`
- **Task Definition**: `/workspace/specs/002-create-a-microsoft/tasks.md` (T020b-T020d)

---

**Last Updated**: 2025-10-07
**Task**: T020d
**Status**: Complete
