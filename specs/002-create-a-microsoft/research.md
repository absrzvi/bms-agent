# Research: Slack Chat Bot for BMS Agent

**Date**: 2025-10-06 (Updated 2025-10-11 for Slack)
**Feature**: Slack chat bot integration with BMS Agent API via n8n
**Note**: Changed from MS Teams to Slack during implementation for better API support

## Research Summary

This document consolidates research findings for 8 key technical decisions required to implement the Slack bot integration. Implementation complete with Slack Events API + Slack Web API. Currently optimizing AI agent performance (8 tools → 4 tools).

---

## 1. Slack Bot Integration Options

### Decision: Slack Events API + Slack Web API (IMPLEMENTED)
**Rationale**:
- **Simpler setup than MS Teams**: No Bot Framework registration, just Slack app creation
- **Better webhook support**: Slack Events API provides clean JSON payloads for app_mention events
- **Rich formatting**: Slack Block Kit provides superior message formatting vs MS Teams plain text
- **Built-in retry handling**: Slack automatically retries failed webhook deliveries (requires deduplication)
- **n8n compatibility**: Direct HTTP nodes work perfectly with Slack Web API (no special node needed)

**Alternatives Considered**:
- **MS Teams Bot Framework REST API v3**: Rejected due to complex credential setup, limited formatting options, and webhook configuration difficulties
- **Slack RTM API**: Rejected as deprecated, webhook-based Events API is recommended approach
- **Slack Socket Mode**: Rejected as requires persistent connection, not suitable for n8n workflows

**Implementation Details** (as deployed):
1. Create Slack app at api.slack.com/apps
2. Enable Event Subscriptions with n8n webhook URL (e.g., `https://runpod-proxy.net/webhook/slack-events`)
3. Subscribe to `app_mention` bot event
4. Install app to Slack workspace, grant `chat:write`, `app_mentions:read` scopes
5. Configure Bot User OAuth Token in n8n credentials
6. Implement event deduplication using `event_id` to handle Slack retries

---

## 2. n8n Slack Integration

### Decision: Webhook Trigger + HTTP Request Nodes (IMPLEMENTED)
**Rationale**:
- n8n Slack node exists but limited to simple message posting
- Custom webhook + HTTP approach provides full control over Block Kit formatting
- Handles Slack retry logic properly with event deduplication
- Supports threading (thread_ts parameter) for conversation context

**Implementation Pattern** (as deployed in bms-ai-agent.json):
```
[Slack Events API Webhook Trigger: "slack-events"]
  → [Process Event - Extract query, dedup check via event_id]
  → [AI Agent Logic - Tool selection & execution]
  → [Format Slack Reply - Block Kit formatting]
  → [HTTP Request to slack.com/api/chat.postMessage]
```

**Key Implementation Details**:
1. **Event Deduplication**:
   - Uses workflow static data to cache processed event_ids
   - 5-minute TTL for dedup cache
   - Prevents duplicate processing from Slack retries

2. **Block Kit Formatting**:
   - Header with emoji (🤖 Nomi BMS Assistant)
   - User question quoted section
   - Main answer with collapsible sections
   - Document references with hyperlinks
   - Footer with timestamp

3. **Required Slack API Scopes**:
   - `app_mentions:read` - Receive @mention events
   - `chat:write` - Post messages to channels
   - `channels:read` - List channels (for admin whitelist)

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

**Storage Schema** (Session 2025-10-09: Updated with `bms:` prefix convention):
```
Key: bms:context:{conversation_id}
Value: JSON {participants, messages[], created_at, expires_at}
TTL: 604800 seconds (7 days)

Key: bms:user:{user_id}:history
Value: JSON [{query, timestamp, embedding}] (for /history and similar query detection)
TTL: 604800 seconds

Key: bms:upload:job:{job_id}
Value: JSON {document_id, file_name, uploaded_by, processing_status, created_at}
TTL: 604800 seconds

Key: bms:whitelist:cache
Value: JSON {admins[], channels[]}
TTL: 3600 seconds (1 hour cache refresh)
```

**Namespace Convention** (Session 2025-10-09):
- All Redis keys MUST use `bms:` prefix to prevent collisions and enable clear debugging
- Standard format: `bms:{entity_type}:{identifier}` or `bms:{entity_type}:{id}:{attribute}`
- Examples: `bms:context:{id}`, `bms:user:{id}:history`, `bms:upload:jobs:pending`

**Deployment**:
```bash
docker run -d \
  -v /workspace/redis_data:/data \
  -p 6379:6379 \
  redis:7-alpine redis-server --appendonly yes
```

---

## 4. LLM Query Analysis with Ollama

### Decision: Mistral Nemo via Ollama with Structured Prompts + Confidence Thresholds
**Rationale**:
- Already running on RunPod for BMS API
- Good at intent classification and query understanding
- Structured prompts ensure consistent routing decisions
- **Session 2025-10-09**: Added confidence thresholds for intent detection (≥0.80) and query validation (<0.60)

**Prompt Templates**:

**Query Validation** (Session 2025-10-09: New - FR-022):
```
You are a query quality validator for a railway documentation bot.
Assess the clarity and completeness of the user's query.

User query: "{query}"

Evaluate:
1. Is the query specific enough to understand intent?
2. Does it contain meaningful content (not just stopwords)?
3. Is the context clear or are there ambiguous references?

Respond with a JSON object:
{
  "clarity_score": 0.0-1.0,
  "is_clear": true/false,
  "reason": "brief explanation"
}

Threshold: clarity_score ≥ 0.60 is considered clear.
```

**Intent Classification** (Session 2025-10-09: Updated with confidence threshold):
```
You are a query classifier for a railway documentation bot.
Classify the user's query into one of these intents:

1. ASK - User wants a direct answer to a question
2. SEARCH - User wants to find specific documents
3. UPLOAD - User wants to upload a document
4. COMMAND - User typed a slash command (/help, /history, /status, /admin)

User query: "{query}"

Respond with a JSON object:
{
  "intent": "ASK|SEARCH|UPLOAD|COMMAND",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}

Routing Decision:
- If intent == ASK AND confidence ≥ 0.80 → Route to /api/v1/ask (FR-006)
- If confidence < 0.80 → Route to /api/v1/search/semantic (safe fallback)
```

**Query Improvement** (FR-022):
```
The user's query was unclear or returned no results: "{query}"

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
- Max tokens: 150 (increased for JSON responses with confidence)

**Processing Flow** (Session 2025-10-09):
```
1. Query Validation (clarity_score check)
   → If clarity_score < 0.60: Return suggestions (FR-022)
   → If clarity_score ≥ 0.60: Proceed to step 2

2. Intent Classification (confidence check)
   → If intent == ASK AND confidence ≥ 0.80: Route to /api/v1/ask (FR-006)
   → If confidence < 0.80: Route to /api/v1/search/semantic (safe fallback)
   → If intent == COMMAND: Handle locally
   → If intent == UPLOAD: Route to upload-handler workflow
```

---

## 5. BMS API Integration Patterns

### Decision: Intent-Based Routing with Error Handling + Footnote Citations
**Rationale**:
- FR-006 requires intelligent routing between /ask and /search
- LLM intent classification determines endpoint
- Fallback chain ensures reliability
- **Session 2025-10-09**: Citation format specified as footnote style (FR-004)

**Routing Logic**:
```
IF query starts with "/" → Handle as command
ELSE IF intent == "ASK" AND confidence ≥ 0.80 → POST /api/v1/ask
ELSE IF intent == "SEARCH" OR confidence < 0.80 → POST /api/v1/search/semantic
ELSE IF attachments present → POST /api/v1/documents/upload
```

**Citation Formatting** (Session 2025-10-09: FR-004):
```
Format: Footnote style with numbered superscript references

Example Response:
"The emergency brake procedure requires activation within 3 seconds.¹
This applies to all Class 395 trains.²

¹ Railway Safety Manual, Section 4.2
² Fleet Operations Guide, Page 47"

Implementation:
1. Parse BMS API response citations[] array
2. Insert superscript numbers (¹, ², ³) at end of relevant sentences
3. Append full citations list at bottom with matching numbers
4. Ensure numbered order matches citation relevance
```

**Error Handling** (FR-020, NFR-001):
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

## 9. BMS API Embeddings Endpoint

### Decision: Implement POST /api/v1/embeddings for Similar Query Detection
**Rationale** (Session 2025-10-09: FR-017):
- Similar query detection requires query embeddings (FR-017 similarity threshold ≥0.85)
- Reuse existing sentence-transformers/all-mpnet-base-v2 model from BMS API
- Consistent with existing BMS API architecture
- Required by query-analyzer workflow for comparing user queries with history

**Endpoint Specification** (Session 2025-10-09):
```
POST http://localhost:8000/api/v1/embeddings

Request:
{
  "query": "string (max 1000 characters, consistent with FR-031)"
}

Response (200 OK):
{
  "embedding": [768 floats],  // sentence-transformers/all-mpnet-base-v2 dimensions
  "model": "sentence-transformers/all-mpnet-base-v2",
  "query_length": 42
}

Error Responses:
- 400 Bad Request: Query exceeds 1000 characters or is empty
  {
    "detail": "Query exceeds maximum length of 1000 characters"
  }
- 500 Internal Server Error: Model unavailable or embedding generation failed
  {
    "detail": "Embedding model unavailable"
  }

Rate Limiting:
- 60 requests/minute (shared with other BMS API endpoints)
- HTTP 429 Too Many Requests if exceeded
- Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

Timeout:
- 2000ms maximum (2 seconds)
- Includes model loading + inference + response formatting
```

**Implementation Notes**:
```python
# api/endpoints/embeddings.py (NEW)
from sentence_transformers import SentenceTransformer
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

class EmbeddingRequest(BaseModel):
    query: str = Field(..., max_length=1000)

@router.post("/api/v1/embeddings")
async def generate_embedding(request: EmbeddingRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        embedding = model.encode(request.query).tolist()  # 768-d vector
        return {
            "embedding": embedding,
            "model": "sentence-transformers/all-mpnet-base-v2",
            "query_length": len(request.query)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Embedding model unavailable")
```

**Usage in n8n** (query-analyzer workflow):
```javascript
// Call embeddings endpoint for current query
const response = await axios.post('http://localhost:8000/api/v1/embeddings', {
  query: userQuery
});
const currentEmbedding = response.data.embedding;

// Retrieve user's query history from Redis
const historyKey = `bms:user:${userId}:history`;
const queryHistory = await redis.get(historyKey);

// Calculate cosine similarity with each historical query
queryHistory.forEach(item => {
  const similarity = cosineSimilarity(currentEmbedding, item.embedding);
  if (similarity >= 0.85) {
    // Suggest previous query (FR-017)
    suggestions.push({
      query: item.query,
      timestamp: item.timestamp,
      similarity: similarity
    });
  }
});
```

**Dependencies**:
- sentence-transformers >= 2.2.0
- torch >= 2.0.0 (GPU acceleration if available)
- FastAPI rate limiting middleware (existing)

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
