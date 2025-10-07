# Research: MS Teams Chat Bot for BMS Agent

**Date**: 2025-10-06
**Feature**: MS Teams chat bot integration with BMS Agent API via n8n

## Research Summary

This document consolidates research findings for 8 key technical decisions required to implement the MS Teams bot integration.

---

## 1. MS Teams Bot Integration Options

### Decision: Bot Framework REST API v3 with Incoming Webhook
**Rationale**:
- No custom app package required (POC constraint)
- Supports typing indicators via Bot Framework REST API v3
- Enables proactive messages for document processing notifications
- n8n can receive messages via webhook and respond via Bot Framework REST API v3

###Alternatives Considered

:
- **Incoming Webhook Only**: Simple but no typing indicators or proactive messages
- **Custom Teams App Package**: Full features but requires app deployment and tenant approval (blocked for POC)
- **Power Automate**: No control over logic, limited LLM integration

**Implementation Notes**:
- Register Bot Framework REST API v3 bot at dev.botframework.com
- Get bot ID and app password
- Configure MS Teams Bot Framework webhook endpoint in n8n (e.g., https://n8n.runpod.io/webhook/teams)
- Use MS Teams connector in Teams to add bot to channels

---

## 2. n8n MS Teams Integration

### Decision: Webhook Trigger + HTTP Request Nodes
**Rationale**:
- No official n8n MS Teams node exists (as of v1.x)
- Webhook trigger receives MS Teams messages
- HTTP Request nodes send responses via Bot Framework API
- Flexible for typing indicators, proactive messages, adaptive cards

**Alternatives Considered**:
- **Community MS Teams Node**: Outdated, no typing indicator support
- **Microsoft Graph API**: Overkill for messaging, requires more auth setup

**Implementation Pattern**:
```
[MS Teams Bot Framework Webhook Trigger]
  → [Extract message data]
  → [Process logic]
  → [HTTP Request to Bot Framework REST API v3]
```

**Required Credentials**:
- Bot Framework REST API v3 App ID
- Bot Framework REST API v3 App Password
- MS Teams Service URL (from incoming message)

---

## 3. Conversation Context Storage

### Decision: Redis with 7-Day TTL
**Rationale**:
- Native TTL support for automatic 7-day expiration (FR-023, FR-024)
- Fast key-value access for conversation lookup
- Handles concurrent users better than SQLite
- Available as Docker container on RunPod (/workspace mount)
- Fallback: File-based JSON if Redis unavailable (stateless mode per NFR-002)

**Alternatives Considered**:
- **SQLite**: Simpler setup but no native TTL, requires cron job for cleanup
- **PostgreSQL**: Overkill for key-value storage
- **File-based JSON**: Simple but no TTL, poor concurrent access

**Storage Schema**:
```
Key: conversation:{conversation_id}
Value: JSON {participants, messages[], created_at, expires_at}
TTL: 604800 seconds (7 days)

Key: user:{user_id}:history
Value: JSON [{query, timestamp}] (for /history command)
TTL: 604800 seconds
```

**Deployment**:
```bash
docker run -d \
  -v /workspace/redis_data:/data \
  -p 6379:6379 \
  redis:7-alpine redis-server --appendonly yes
```

---

## 4. LLM Query Analysis with Ollama

### Decision: Mistral Nemo via Ollama with Structured Prompts
**Rationale**:
- Already running on RunPod for BMS API
- Good at intent classification and query understanding
- Structured prompts ensure consistent routing decisions

**Prompt Templates**:

**Intent Classification**:
```
You are a query classifier for a railway documentation bot.
Classify the user's query into one of these intents:

1. ASK - User wants a direct answer to a question
2. SEARCH - User wants to find specific documents
3. UPLOAD - User wants to upload a document
4. COMMAND - User typed a slash command (/help, /history, /status, /admin)

User query: "{query}"

Respond with ONLY the intent name (ASK, SEARCH, UPLOAD, or COMMAND).
```

**Query Improvement**:
```
The user's query returned no results: "{query}"

Suggest 2-3 alternative phrasings that might work better.
Be specific to railway documentation (brakes, VLAN, signals, etc.).

Format:
1. [alternative phrasing]
2. [alternative phrasing]
```

**n8n Integration**:
- HTTP Request node to http://localhost:11434/api/generate
- Model: mistral-nemo:12b-instruct
- Temperature: 0.3 (deterministic classification)
- Max tokens: 50

---

## 5. BMS API Integration Patterns

### Decision: Intent-Based Routing with Error Handling
**Rationale**:
- FR-006 requires intelligent routing between /ask and /search
- LLM intent classification determines endpoint
- Fallback chain ensures reliability

**Routing Logic**:
```
IF query starts with "/" → Handle as command
ELSE IF intent == "ASK" → POST /api/v1/ask
ELSE IF intent == "SEARCH" → POST /api/v1/search/semantic
ELSE IF attachments present → POST /api/v1/documents/upload
```

**Error Handling** (FR-018, NFR-001):
```
TRY:
  response = call BMS API
CATCH connection_error:
  return "BMS-search tool cannot be accessed at this time. Please try again later."
CATCH no_results (empty citations):
  IF retry_with_search:
    Try /api/v1/search/semantic
  ELSE:
    Suggest query improvements via LLM
```

**Timeout**: 2.5s max (leaves 0.5s buffer for 3s SLA per FR-003)

---

## 6. File Upload Handling in n8n

### Decision: Detect Attachments → Download → Multipart Upload
**Rationale**:
- MS Teams includes attachment metadata in message payload
- FR-010 requires both file attachment and /upload command support
- BMS API expects multipart/form-data

**Implementation Flow**:
```
1. Check message.attachments array
2. IF attachments present:
   a. Download file via attachment.contentUrl (requires auth)
   b. Validate file type against allowed extensions
   c. Construct multipart form-data:
      - file: binary data
      - profile: "railway" (default) or from command args
   d. POST to http://localhost:8000/api/v1/documents/upload/async
   e. Store job_id for /status command
   f. Return confirmation with document_id
```

**File Type Validation** (NFR-007):
```javascript
const allowedTypes = ['.pdf', '.csv', '.xlsx', '.xls', '.txt', '.md', '.docx', '.pptx'];
const extension = path.extname(filename).toLowerCase();
if (!allowedTypes.includes(extension)) {
  return "Invalid file type. Supported: PDF, CSV, XLSX, TXT, MD, DOCX, PPTX";
}
```

---

## 7. Typing Indicators in MS Teams

### Decision: Bot Framework REST API v3 Typing Activity
**Rationale**:
- FR-018 requires typing indicator during processing
- Bot Framework REST API v3 supports `type: "typing"` activity
- Shows "Bot is typing..." in Teams UI

**Implementation**:
```
POST https://smba.trafficmanager.net/amer/v3/conversations/{conversationId}/activities
Headers:
  Authorization: Bearer {botToken}
Body:
{
  "type": "typing",
  "from": {"id": "{botId}"},
  "conversation": {"id": "{conversationId}"}
}
```

**n8n Workflow Pattern**:
```
[Receive message via MS Teams Bot Framework webhook]
  → [Send typing indicator via Bot Framework REST API v3]
  → [Process query (LLM + BMS API)]
  → [Send response via Bot Framework REST API v3]
```

**Note**: Typing activity lasts ~3 seconds, perfect for our <3s response SLA

---

## 8. Channel Whitelist Management

### Decision: JSON File Storage with Admin Role Check
**Rationale**:
- Simple for POC (20 users, 2-3 channels)
- Easy to inspect/edit manually
- Migrate to Redis/DB post-POC if needed

**Storage Format** (`/workspace/002-n8n/config/whitelist.json`):
```json
{
  "admins": [
    "29:1abc...def" // MS Teams user IDs
  ],
  "channels": [
    {
      "channel_id": "19:abc...def@thread.tacv2",
      "channel_name": "#operations-team",
      "added_by": "29:1abc...def",
      "added_at": "2025-10-06T10:30:00Z",
      "status": "active"
    }
  ]
}
```

**Admin Verification**:
```javascript
function isAdmin(userId) {
  const whitelist = JSON.parse(fs.readFileSync('/workspace/002-n8n/config/whitelist.json'));
  return whitelist.admins.includes(userId);
}
```

**Whitelist Check** (FR-021, FR-021b):
```javascript
function isChannelAllowed(channelId) {
  const whitelist = JSON.parse(fs.readFileSync('/workspace/002-n8n/config/whitelist.json'));
  return whitelist.channels.some(ch =>
    ch.channel_id === channelId && ch.status === 'active'
  );
}
```

**Channel ID Extraction**:
```javascript
// From MS Teams message payload
const channelId = message.channelData.channel.id; // For channel messages
const conversationId = message.conversation.id;   // For personal chats
```

---

## Technology Stack Summary

| Component | Technology | Version | Location |
|-----------|-----------|---------|----------|
| Workflow Engine | n8n | 1.x | /workspace/n8n |
| Conversation Storage | Redis | 7.x | /workspace/redis |
| LLM (Query Analysis) | Mistral Nemo via Ollama | 12b-instruct | http://localhost:11434 |
| BMS API | FastAPI | 1.0.0 | http://localhost:8000 |
| MS Teams Integration | Bot Framework REST API v3 | v3 | HTTPS endpoints |
| Testing Framework | Jest | 29.x | /workspace/002-n8n/tests |
| Language | Node.js (n8n) | 18+ | - |

---

## Configuration Requirements

### Environment Variables
```bash
# MS Teams Bot
BOT_APP_ID=<bot-framework-app-id>
BOT_APP_PASSWORD=<bot-framework-app-password>
TEAMS_WEBHOOK_URL=<n8n-webhook-url>

# BMS API
BMS_API_URL=http://localhost:8000
BMS_API_TIMEOUT=2500 # 2.5s

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral-nemo:12b-instruct

# Storage
REDIS_URL=redis://localhost:6379
REDIS_TTL=604800 # 7 days

# Config Paths
WHITELIST_PATH=/workspace/002-n8n/config/whitelist.json
```

### n8n Credentials
- Bot Framework REST API v3: App ID + Password
- HTTP Basic Auth: For securing MS Teams Bot Framework webhook endpoint
- Redis: Connection string

---

## Performance Considerations

### Response Time Budget (FR-003: <3s total)
```
MS Teams → n8n:           100ms
n8n Webhook Processing:   50ms
LLM Intent Classification: 300ms
BMS API Call:             1500ms (max)
Response Formatting:      200ms
n8n → MS Teams:           100ms
---
Buffer:                   750ms
Total:                    3000ms
```

### Optimizations
1. **Parallel Processing**: Send typing indicator while calling LLM
2. **Caching**: Cache whitelist in memory (refresh every 60s)
3. **Connection Pooling**: Reuse HTTP connections to BMS API
4. **Early Returns**: Whitelist check before any processing

---

## Security Considerations

### Input Validation
- Sanitize user input before LLM prompts (prevent injection)
- Validate file extensions (NFR-007)
- Verify MS Teams webhook signature (prevent spoofing)

### Authentication
- Bot Framework REST API v3 uses bearer tokens (auto-refresh)
- Admin commands require is_admin check
- Channel whitelist enforced before processing

### Data Privacy
- Conversation data auto-expires after 7 days (NFR-006)
- No PII stored beyond MS Teams user IDs
- Redis persistence file encrypted at rest (RunPod default)

---

## Deployment Checklist

- [ ] Install Redis to /workspace (per constitution §11 RunPod persistence)
- [ ] Import n8n workflows
- [ ] Configure Bot Framework REST API v3 credentials in n8n
- [ ] Create MS Teams Bot Framework webhook connector
- [ ] Initialize whitelist.json with admin users
- [ ] Test end-to-end flow
- [ ] Set up monitoring (n8n executions log)
- [ ] Configure cleanup cron for expired conversations

---

## Next Steps

✅ **Phase 0 Complete** - All research consolidated

**Ready for Phase 1**:
1. Generate data-model.md from entities above
2. Create API contracts for MS Teams, BMS API, storage
3. Write contract tests
4. Create quickstart.md deployment guide

---

*Research completed: 2025-10-06*
