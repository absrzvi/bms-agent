# n8n Workflow Implementation Guide

This guide provides detailed implementation instructions for all 5 core n8n workflows (T016-T020).

## Prerequisites

- n8n running on http://localhost:5678
- Redis client and whitelist modules in `/workspace/002-n8n/lib/`
- BMS API running on http://localhost:8000
- Ollama with mistral-nemo:12b-instruct

## Workflow 1: Main Bot Handler (T016)

**File**: `/workspace/002-n8n/workflows/main-bot-handler.json`

### Nodes Required:

1. **Webhook Trigger**
   - Method: POST
   - Path: `/webhook/teams`
   - Response: 200 OK

2. **Function: Extract Message Data**
   ```javascript
   const message = $input.all()[0].json;
   return {
     messageId: message.id,
     from: message.from,
     conversation: message.conversation,
     channelId: message.channelData?.channel?.id || message.conversation.id,
     text: message.text || '',
     attachments: message.attachments || [],
     serviceUrl: message.serviceUrl
   };
   ```

3. **Function: Input Validation (FR-031)**
   ```javascript
   const text = $('Extract Message Data').item.json.text;
   
   if (text.length > 1000) {
     return {
       error: true,
       message: $('response-templates').item.json.errors.query_too_long
     };
   }
   
   return { error: false, text };
   ```

4. **Function: Whitelist Check**
   ```javascript
   const { getWhitelistManager } = require('/workspace/002-n8n/lib/whitelist.js');
   const whitelist = getWhitelistManager();
   
   const channelId = $('Extract Message Data').item.json.channelId;
   const userId = $('Extract Message Data').item.json.from.id;
   
   const allowed = whitelist.isChannelAllowed(channelId);
   const isAdmin = whitelist.isAdmin(userId);
   
   return { allowed, isAdmin, channelId, userId };
   ```

5. **IF: Channel Allowed?**
   - Condition: `{{$('Whitelist Check').item.json.allowed}} === true`

6. **Function: Route Command/Query**
   ```javascript
   const text = $('Input Validation').item.json.text;
   
   // Check for slash commands
   if (text.startsWith('/help')) {
     return { route: 'help', command: '/help' };
   } else if (text.startsWith('/search')) {
     return { route: 'search', query: text.substring(8).trim() };
   } else if (text.startsWith('/ask')) {
     return { route: 'ask', query: text.substring(5).trim() };
   } else if (text.startsWith('/history')) {
     return { route: 'history', userId: $('Extract Message Data').item.json.from.id };
   } else if (text.startsWith('/status')) {
     const docId = text.substring(8).trim();
     return { route: 'status', documentId: docId };
   } else if (text.startsWith('/admin')) {
     return { route: 'admin', command: text };
   } else if (text.startsWith('/upload')) {
     return { route: 'upload', message: 'Please attach a file' };
   }
   
   // Natural language query - route to analyzer
   return { route: 'analyze', query: text };
   ```

7. **Switch: Route Handler**
   - Routes to: query-analyzer, bms-api-caller, admin-commands, or help template

8. **Function: Send Response**
   ```javascript
   // Bot Framework API v3 response
   const conversationId = $('Extract Message Data').item.json.conversation.id;
   const serviceUrl = $('Extract Message Data').item.json.serviceUrl;
   const response = $input.all()[0].json;
   
   return {
     conversationId,
     serviceUrl,
     response: response.text || response.answer || response.message
   };
   ```

### Testing:
```bash
curl -X POST http://localhost:5678/webhook/teams \
  -H "Content-Type: application/json" \
  -d '{
    "type":"message",
    "id":"123",
    "from":{"id":"29:test"},
    "conversation":{"id":"conv-1"},
    "text":"What are brake procedures?",
    "serviceUrl":"https://smba.trafficmanager.net"
  }'
```

---

## Workflow 2: Query Analyzer (T017)

**File**: `/workspace/002-n8n/workflows/query-analyzer.json`

### Nodes Required:

1. **HTTP Request: Ollama Intent Classification**
   - Method: POST
   - URL: `http://localhost:11434/api/generate`
   - Body:
   ```json
   {
     "model": "mistral-nemo:12b-instruct",
     "prompt": "You are a query classifier. Classify this query as ASK or SEARCH:\n\n{{$json.query}}\n\nRespond with only ASK or SEARCH.",
     "temperature": 0.3,
     "max_tokens": 10,
     "stream": false
   }
   ```

2. **Function: Parse Intent**
   ```javascript
   const response = $input.all()[0].json.response;
   const intent = response.toUpperCase().includes('ASK') ? 'ask' : 'search';
   
   return {
     intent,
     query: $('Trigger').item.json.query,
     confidence: 0.9
   };
   ```

### Testing:
Call from main-bot-handler or test standalone

---

## Workflow 3: BMS API Caller (T018)

**File**: `/workspace/002-n8n/workflows/bms-api-caller.json`

### Nodes Required:

1. **IF: Intent is ASK?**
   - Condition: `{{$json.intent}} === 'ask'`

2. **HTTP Request: BMS Ask API**
   - Method: POST
   - URL: `http://localhost:8000/api/v1/ask`
   - Timeout: 2500ms
   - Body:
   ```json
   {
     "query": "{{$json.query}}",
     "max_chunks": 5,
     "include_citations": true
   }
   ```

3. **HTTP Request: BMS Search API** (else branch)
   - Method: POST
   - URL: `http://localhost:8000/api/v1/search/semantic`
   - Timeout: 2500ms
   - Body:
   ```json
   {
     "query": "{{$json.query}}",
     "limit": 5,
     "min_score": 0.7
   }
   ```

4. **Function: Format Response with Citations**
   ```javascript
   const result = $input.all()[0].json;
   
   let response = '';
   
   if (result.answer) {
     response = result.answer + '\n\nSources:\n';
     result.citations.forEach((cit, i) => {
       response += `${i+1}. ${cit.document_name} (Score: ${cit.relevance_score.toFixed(2)})\n`;
     });
   } else if (result.results) {
     response = `Found ${result.results.length} documents:\n\n`;
     result.results.forEach((r, i) => {
       response += `${i+1}. ${r.document_name} (Score: ${r.score.toFixed(2)})\n   "${r.content.substring(0, 100)}..."\n\n`;
     });
   }
   
   return { text: response };
   ```

5. **Error Handler: BMS Unavailable**
   ```javascript
   const error = $input.all()[0].error;
   
   if (error.code === 'ETIMEDOUT' || error.code === 'ECONNREFUSED') {
     return {
       text: $('response-templates').item.json.errors.bms_unavailable
     };
   }
   
   return { text: `Error: ${error.message}` };
   ```

---

## Workflow 4: Context Manager (T019)

**File**: `/workspace/002-n8n/workflows/context-manager.json`

### Nodes Required:

1. **Function: Get Conversation Context**
   ```javascript
   const { getRedisClient } = require('/workspace/002-n8n/lib/redis-client.js');
   const redis = getRedisClient();
   
   const conversationId = $json.conversationId;
   const TTL = 604800; // 7 days
   
   const result = await redis.execute(async (client) => {
     const data = await client.get(`conversation:${conversationId}`);
     return data ? JSON.parse(data) : null;
   }, null);
   
   // Check if storage was restored (NFR-002a)
   if (result.restored) {
     return {
       conversation: result.data,
       storageRestored: true,
       warning: $('response-templates').item.json.success.storage_restored
     };
   }
   
   // Create new conversation if not exists
   if (!result.data) {
     const newConv = {
       conversation_id: conversationId,
       created_at: new Date().toISOString(),
       expires_at: new Date(Date.now() + TTL * 1000).toISOString(),
       messages: []
     };
     
     await redis.execute(async (client) => {
       await client.setEx(`conversation:${conversationId}`, TTL, JSON.stringify(newConv));
     });
     
     return { conversation: newConv, storageRestored: false };
   }
   
   return { conversation: result.data, storageRestored: false };
   ```

2. **Function: Add Message to Context**
   ```javascript
   const conversation = $('Get Conversation Context').item.json.conversation;
   const newMessage = {
     message_id: Date.now().toString(),
     sender: $json.sender,
     content: $json.content,
     timestamp: new Date().toISOString()
   };
   
   conversation.messages.push(newMessage);
   conversation.last_message_at = newMessage.timestamp;
   
   // Keep only last 10 messages for context
   if (conversation.messages.length > 10) {
     conversation.messages = conversation.messages.slice(-10);
   }
   
   return conversation;
   ```

3. **Function: Save to Redis**
   ```javascript
   const { getRedisClient } = require('/workspace/002-n8n/lib/redis-client.js');
   const redis = getRedisClient();
   const conversation = $input.all()[0].json;
   
   await redis.execute(async (client) => {
     await client.setEx(
       `conversation:${conversation.conversation_id}`,
       604800,
       JSON.stringify(conversation)
     );
   });
   
   return { success: true };
   ```

---

## Workflow 5: Admin Commands (T020)

**File**: `/workspace/002-n8n/workflows/admin-commands.json`

### Nodes Required:

1. **Function: Parse Admin Command**
   ```javascript
   const command = $json.command; // e.g., "/admin allow #ops-team"
   const parts = command.split(' ');
   
   return {
     action: parts[1], // allow, revoke, list
     target: parts[2], // #channel-name
     userId: $json.userId
   };
   ```

2. **Switch: Action Type**
   - allow → Add Channel
   - revoke → Revoke Channel
   - list → List Channels

3. **Function: Add Channel to Whitelist**
   ```javascript
   const { getWhitelistManager } = require('/workspace/002-n8n/lib/whitelist.js');
   const whitelist = getWhitelistManager();
   
   const channelName = $json.target;
   const channelId = $json.channelId; // Extract from MS Teams data
   const userId = $json.userId;
   
   const result = whitelist.addChannel(channelId, channelName, userId);
   
   if (result.success) {
     return {
       text: $('response-templates').item.json.success.whitelist_added.replace('{{channel_name}}', channelName)
     };
   } else if (result.message === 'unauthorized_admin') {
     return {
       text: $('response-templates').item.json.errors.unauthorized_admin
     };
   } else {
     return { text: result.message };
   }
   ```

---

## Deployment Instructions

1. **Import Workflows**:
   ```bash
   cd /workspace/002-n8n
   ./scripts/deploy-workflows.sh
   ```

2. **Activate Workflows**:
   - In n8n UI, go to each workflow
   - Toggle "Active" switch ON

3. **Test Each Workflow**:
   - Use n8n's "Execute Workflow" feature
   - Or use curl commands provided above

4. **Monitor Execution**:
   - Check n8n Executions tab
   - View detailed logs for each run

---

## Troubleshooting

**Workflow not triggering**:
- Check webhook URL is correct
- Verify MS Teams Bot Framework messaging endpoint

**Redis connection errors**:
- Ensure Redis is running: `redis-cli ping`
- Check REDIS_URL environment variable

**BMS API timeouts**:
- Verify BMS API health: `curl http://localhost:8000/health`
- Check timeout settings (2500ms)

**Module not found errors**:
- Ensure lib/ modules exist: `ls /workspace/002-n8n/lib/`
- Check Node.js can require them: `node -e "require('/workspace/002-n8n/lib/redis-client.js')"`

---

*Workflow Implementation Guide - Last Updated: 2025-10-06*
