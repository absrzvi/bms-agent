# n8n Chat Trigger Node Documentation

**Node Type**: `@n8n/n8n-nodes-langchain.chatTrigger`
**Version**: 1.1
**Purpose**: Provides web-based chat interface for the BMS AI Agent

---

## Node Configuration

### JSON Definition

```json
{
  "parameters": {
    "public": true,
    "options": {}
  },
  "id": "54d470d2-7a95-4f9d-9101-2f764787c38e",
  "name": "When chat message received",
  "type": "@n8n/n8n-nodes-langchain.chatTrigger",
  "typeVersion": 1.1,
  "position": [
    -16,
    304
  ],
  "webhookId": "bms-ai-agent-chat"
}
```

### Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `public` | `true` | Allows public access without authentication |
| `webhookId` | `bms-ai-agent-chat` | Unique identifier for the chat endpoint |
| `type` | `@n8n/n8n-nodes-langchain.chatTrigger` | LangChain-compatible chat trigger |

---

## Visual Node Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  When chat message received                 │
│                                                              │
│  Type: @n8n/n8n-nodes-langchain.chatTrigger                │
│  Webhook ID: bms-ai-agent-chat                              │
│  Public: true                                                │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Chat Interface (Auto-generated)                    │   │
│  │                                                      │   │
│  │  [User Input Field]                                 │   │
│  │  [Send Button]                                      │   │
│  │                                                      │   │
│  │  Conversation History:                              │   │
│  │  • Message 1 (User)                                 │   │
│  │  • Response 1 (AI)                                  │   │
│  │  • Message 2 (User)                                 │   │
│  │  • Response 2 (AI)                                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  Output: User message → Connected to Nomi AI Agent          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Nomi AI Agent                       │
│  (Processes message with 8 search tools + Redis memory)     │
└─────────────────────────────────────────────────────────────┘
```

---

## Workflow Connection

```
┌──────────────────────┐
│ When chat message    │
│ received             │
│ (Chat Trigger)       │
└──────────┬───────────┘
           │
           │ Main output
           │
           ▼
┌──────────────────────┐     ┌─────────────────────┐
│ Nomi                 │◄────┤ Redis Chat Memory   │
│ (AI Agent)           │     │ (Conversation       │
│                      │     │  History)           │
│ Tools:               │     └─────────────────────┘
│ • search_semantic    │
│ • search_hybrid      │
│ • ask_bms           │
│ • search_contextual  │
│ • search_metadata    │
│ • search_version     │
│ • search_faceted     │
│ • search_explained   │
│ • Send Slack msg     │
└──────────┬───────────┘
           │
           │ AI response
           │
           ▼
┌──────────────────────┐
│ Chat Interface       │
│ (Display response)   │
└──────────────────────┘
```

---

## Access URLs

### Development (Local n8n)
```
http://localhost:5678/webhook/bms-ai-agent-chat
```

### Production (RunPod)
```
https://<runpod-proxy-url>/webhook/bms-ai-agent-chat
```

**Example**:
```
https://n8n-xyz123.runpod.io/webhook/bms-ai-agent-chat
```

---

## Chat Interface Features

### Auto-Generated UI

The chat trigger automatically creates a chat interface with:

1. **Message Input**: Text box for user to type questions
2. **Send Button**: Submit button to send messages
3. **Chat History**: Scrollable conversation view
4. **Typing Indicators**: Shows when AI is processing
5. **Markdown Support**: Renders formatted text (bold, lists, code)
6. **Auto-Scroll**: Scrolls to latest message

### Example Conversation

```
┌────────────────────────────────────────────────────────┐
│ BMS AI Agent Chat                                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│ 👤 User:                                              │
│ What are the emergency brake procedures?              │
│                                                        │
│ 🤖 Nomi:                                              │
│ According to **BMS-QHSE-PRO-045** (Emergency          │
│ Procedures, v2.1), the emergency brake procedure      │
│ requires:                                              │
│                                                        │
│ 1. Immediate activation within 3 seconds              │
│ 2. Radio notification to control center               │
│ 3. Passenger evacuation if necessary                  │
│                                                        │
│ Would you like full context using search_contextual?  │
│                                                        │
│ ┌──────────────────────────────────────┐             │
│ │ [Type your message here...]          │ [Send]      │
│ └──────────────────────────────────────┘             │
└────────────────────────────────────────────────────────┘
```

---

## Session Management

### Session Identification

**Method**: Uses `sessionId` from chat interface (auto-generated)
**Storage**: Redis with key = `sessionId`
**Format**: List of messages (LPUSH/LRANGE)

### Message Storage Structure

```javascript
// Redis Key: <sessionId>
// Type: List

// Message 1 (Human)
{
  "type": "human",
  "data": {
    "content": "What are emergency procedures?",
    "additional_kwargs": {},
    "response_metadata": {}
  }
}

// Message 2 (AI)
{
  "type": "ai",
  "data": {
    "content": "According to **BMS-QHSE-PRO-045**...",
    "tool_calls": [],
    "invalid_tool_calls": [],
    "additional_kwargs": {},
    "response_metadata": {}
  }
}
```

### Conversation Context

**How it works**:
1. User sends message → Triggers workflow
2. n8n loads previous messages from Redis (using sessionId)
3. Passes full conversation history to AI agent
4. AI generates response with context
5. Both user message and AI response saved to Redis
6. Response displayed in chat interface

**Context Window**: Last N messages (configurable in Redis Chat Memory node)

---

## Integration with AI Agent

### Data Flow

```
1. User types message in chat interface
   ↓
2. Chat Trigger receives message
   Output: { chatInput: "user message", sessionId: "abc123" }
   ↓
3. Nomi AI Agent processes
   → Load conversation history from Redis
   → Analyze user intent
   → Select appropriate tool(s)
   → Execute tool workflow(s)
   → Generate response with citations
   ↓
4. Response sent back to chat interface
   ↓
5. Save to Redis for future context
```

### Output Schema

**From Chat Trigger to Nomi**:
```json
{
  "chatInput": "What are emergency procedures?",
  "sessionId": "bb3d9438-1cb9-41de-9c69-5d15c2539449",
  "action": "sendMessage"
}
```

**From Nomi to Chat Interface**:
```json
{
  "output": "According to **BMS-QHSE-PRO-045** (Emergency Procedures, v2.1), the emergency brake procedure requires...",
  "usedTools": ["search_version", "ask_bms"]
}
```

---

## Configuration Options

### Public Access (Current: Enabled)

```json
{
  "parameters": {
    "public": true  // ← Anyone can access the chat
  }
}
```

**Use Case**: Suitable for internal network or trusted users

### Restricted Access (Optional)

```json
{
  "parameters": {
    "public": false,
    "authentication": "basic",
    "credentials": {
      "username": "bms-user",
      "password": "secure-password"
    }
  }
}
```

**Use Case**: External-facing chat with authentication required

### Custom Styling (Advanced)

```json
{
  "parameters": {
    "options": {
      "loadPreviousSession": true,  // Load chat history on refresh
      "showWelcomeMessage": true,
      "welcomeMessage": "Hi! I'm Nomi, your BMS documentation assistant. Ask me anything about railway procedures, policies, or technical specs."
    }
  }
}
```

---

## Testing the Chat Trigger

### Manual Test

1. **Access the URL**:
   ```
   http://localhost:5678/webhook/bms-ai-agent-chat
   ```

2. **Type a test message**:
   ```
   What departments are covered in BMS?
   ```

3. **Expected Response**:
   ```
   I'm specialized in BMS railway documentation covering 24 departments
   including QHSE (Quality, Health, Safety, Environment), RENG (Railway
   Engineering), HUMR (Human Resources), and others. Would you like to
   search for a specific procedure or policy?
   ```

4. **Verify Redis Storage**:
   ```bash
   redis-cli KEYS "*"
   # Should show session ID

   redis-cli LRANGE <session-id> 0 -1
   # Should show message history
   ```

### Automated Test (curl)

```bash
curl -X POST http://localhost:5678/webhook/bms-ai-agent-chat \
  -H "Content-Type: application/json" \
  -d '{
    "action": "sendMessage",
    "chatInput": "What is BMS?",
    "sessionId": "test-session-123"
  }'
```

---

## Troubleshooting

### Issue 1: Chat interface not loading

**Symptoms**: 404 error when accessing webhook URL

**Solution**:
1. Check workflow is **activated** in n8n
2. Verify webhook URL matches `webhookId` in JSON
3. Check n8n logs for errors

```bash
tail -f /workspace/logs/n8n.log
```

### Issue 2: Responses not using conversation context

**Symptoms**: AI doesn't remember previous messages

**Solution**:
1. Verify Redis Chat Memory node is connected to Nomi agent
2. Check Redis is running: `redis-cli ping`
3. Verify sessionId is consistent across messages
4. Check Redis keys exist: `redis-cli KEYS "*"`

### Issue 3: Slow responses (>5 seconds)

**Symptoms**: Long wait for AI response

**Solution**:
1. Check tool execution times in n8n execution logs
2. Verify Qdrant is responsive: `curl http://localhost:6333/collections/nomad_bms_documents`
3. Check Ollama model is loaded: `curl http://localhost:11434/api/tags`
4. Monitor system resources (CPU/RAM)

---

## Embedding in Websites

### iframe Embed

```html
<!DOCTYPE html>
<html>
<head>
  <title>BMS Documentation Assistant</title>
</head>
<body>
  <h1>BMS AI Assistant</h1>
  <iframe
    src="http://localhost:5678/webhook/bms-ai-agent-chat"
    width="400"
    height="600"
    style="border: 1px solid #ccc; border-radius: 8px;"
    allow="clipboard-write">
  </iframe>
</body>
</html>
```

### Popup Chat Widget

```html
<button onclick="openChat()">Chat with BMS AI</button>

<div id="chat-widget" style="display:none; position:fixed; bottom:20px; right:20px; width:400px; height:600px; z-index:1000;">
  <iframe
    src="http://localhost:5678/webhook/bms-ai-agent-chat"
    width="100%"
    height="100%"
    style="border:none; border-radius:8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
  </iframe>
</div>

<script>
function openChat() {
  document.getElementById('chat-widget').style.display = 'block';
}
</script>
```

---

## Security Considerations

### Current Setup (Public Access)

✅ **Pros**:
- Easy access for internal users
- No authentication complexity
- Fast development/testing

⚠️ **Cons**:
- No access control
- Potential abuse if exposed externally
- No user tracking

### Recommended for Production

1. **Add Authentication**:
   - Basic auth (username/password)
   - OAuth2 (SSO integration)
   - API key validation

2. **Rate Limiting**:
   - Per-session limits (10 messages/min)
   - Per-IP limits (60 requests/hour)

3. **Input Validation**:
   - Max message length (1000 chars)
   - Sanitize user input
   - Block malicious patterns

4. **Audit Logging**:
   - Log all queries and responses
   - Track session activity
   - Monitor for abuse patterns

---

## Summary

**Node**: `When chat message received`
**Type**: `@n8n/n8n-nodes-langchain.chatTrigger`
**Status**: ✅ Configured and operational
**Access**: Public web interface at `/webhook/bms-ai-agent-chat`
**Memory**: Redis chat memory for conversation persistence
**Integration**: Connected to Nomi AI Agent with 8 search tools

**Use Case**: Provides web-based chat interface for BMS railway documentation queries with automatic source citations and conversation context.

---

**Created**: 2025-10-09
**Location**: `/workspace/002-n8n/N8N_CHAT_TRIGGER_NODE.md`
