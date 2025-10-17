# Data Model: Slack Chat Bot for BMS Agent

**Date**: 2025-10-06 (Updated 2025-10-11 for Slack)
**Feature**: Slack bot integration with BMS Agent API

## Overview

This data model defines the entities used for conversation management (Slack threads), message tracking, search history, event deduplication, and access control. Storage uses Redis for TTL-based data management and n8n workflow static data for event caching.

---

## Core Entities

### 1. Conversation

Represents an ongoing chat session between user(s) and the bot with 7-day retention.

**Storage**: Redis key `bms:context:{conversation_id}` with 604800s TTL (Session 2025-10-09: Updated with `bms:` prefix)

**Schema**:
```json
{
  "conversation_id": "string (Slack thread_ts, e.g., '1728691234.123456')",
  "channel_id": "string (Slack channel ID, format: C#########)",
  "participants": ["string (Slack user IDs, format: U#########)"],
  "created_at": "string (ISO 8601 timestamp)",
  "last_message_at": "string (ISO 8601 timestamp)",
  "expires_at": "string (ISO 8601, created_at + 7 days)",
  "context_summary": "string (condensed history for LLM)",
  "message_count": "integer",
  "thread_ts": "string (Slack thread timestamp for replies)"
}
```

**Validation Rules**:
- `conversation_id`: Must be valid UUID v4
- `expires_at`: Automatically set to `created_at + 7 days`
- `context_summary`: Max 2000 characters (last 5 exchanges condensed)
- `participants`: At least 1 user

**State Transitions**:
1. **Created** → New conversation on first message from user
2. **Active** → `last_message_at` updated on each exchange
3. **Expired** → Auto-deleted by Redis TTL after 7 days

**Relationships**:
- Contains multiple `Message` entities
- Associated with one or more `User` entities

---

### 2. Message

Individual message in a conversation (question, answer, or command).

**Storage**: Embedded in `Conversation` entity as array

**Schema**:
```json
{
  "message_id": "string (Slack message timestamp)",
  "conversation_id": "string (FK to Conversation, Slack thread_ts)",
  "sender": "string (enum: 'user' | 'bot')",
  "user_id": "string (Slack user ID format: U#########, null if sender=bot)",
  "content": "string (message text, cleaned of @mention)",
  "timestamp": "string (ISO 8601 timestamp)",
  "message_type": "string (enum: 'question' | 'answer' | 'command')",
  "bms_query_type": "string (enum: 'ask' | 'search' | 'upload' | null)",
  "event_id": "string (Slack event_id for deduplication)"
}
```

**Validation Rules**:
- `content`: Max 10,000 characters
- `sender`: Must be 'user' or 'bot'
- `message_type`: One of ['question', 'answer', 'command']
- `bms_query_type`: Required if `message_type === 'question'`

**Embedded in Conversation**:
```json
{
  "conversation_id": "abc-123",
  "messages": [
    {"message_id": "msg-1", "sender": "user", ...},
    {"message_id": "msg-2", "sender": "bot", ...}
  ]
}
```

**Relationships**:
- Belongs to one `Conversation`
- May reference one `SearchResult` (via message_id)

---

### 3. SearchResult

Outcome of a BMS API query (ask or search), linked to bot response message.

**Storage**: Redis key `bms:result:{result_id}` with 7-day TTL (Session 2025-10-09: Updated with `bms:` prefix)

**Schema**:
```json
{
  "result_id": "string (UUID v4)",
  "conversation_id": "string (FK to Conversation)",
  "message_id": "string (FK to Message)",
  "query": "string (original user query)",
  "query_type": "string (enum: 'ask' | 'search')",
  "answer_text": "string (generated answer or null)",
  "citations": [
    {
      "footnote_number": "integer (1-based sequential number)",
      "document_name": "string",
      "document_section": "string (chunk_id or page)",
      "relevance_score": "float (0.0-1.0)",
      "excerpt_text": "string (preview, max 500 chars)"
    }
  ],
  "confidence_score": "float (0.0-1.0, null for search)",
  "response_time_ms": "integer",
  "timestamp": "string (ISO 8601)",
  "bms_endpoint": "string (/api/v1/ask or /api/v1/search/semantic)"
}
```

**Validation Rules**:
- `query`: Max 1000 characters
- `citations`: Array of 0-10 citation objects
- `relevance_score`: Between 0.0 and 1.0
- `response_time_ms`: Positive integer
- `bms_endpoint`: Must match actual endpoint called

**Relationships**:
- Referenced by one `Message` (bot answer)
- Belongs to one `Conversation`

---

### 4. User

Person interacting with the bot, identified by Slack user ID.

**Storage**: Redis key `bms:user:{user_id}` (minimal, mostly derived from Slack user profile) (Session 2025-10-09: Updated with `bms:` prefix)

**Schema**:
```json
{
  "user_id": "string (Slack user ID, format: U#########)",
  "display_name": "string (from Slack user profile)",
  "channel_membership": ["string (Slack channel IDs, format: C#########)"],
  "last_active": "string (ISO 8601 timestamp)",
  "is_admin": "boolean",
  "search_history": [
    {
      "query": "string",
      "embedding": "array[float] (768 dimensions, sentence-transformers/all-mpnet-base-v2)",
      "timestamp": "string (ISO 8601)",
      "result_id": "string (FK to SearchResult)"
    }
  ]
}
```

**Validation Rules**:
- `user_id`: Must match Slack ID format `U#########` (9 alphanumeric characters after U)
- `is_admin`: Checked against whitelist.json admins array
- `search_history`: Max 50 entries, auto-pruned > 7 days
- `embedding`: Required for FR-017 similar query detection; generated via BMS API `/api/v1/embeddings` endpoint using same model as document embeddings for consistency

**Derivation**:
- `user_id`, `display_name`: From Slack event payload (event.user field)
- `is_admin`: Lookup in `/workspace/002-n8n/config/whitelist.json`

**Relationships**:
- Participates in multiple `Conversation` entities
- Creates multiple `SearchResult` entities

---

### 5. Whitelist

Channel/team access control list for POC phase.

**Storage**: File `/workspace/002-n8n/config/whitelist.json`

**Schema**:
```json
{
  "admins": [
    "string (Slack user IDs, format: U#########)"
  ],
  "channels": [
    {
      "whitelist_id": "string (UUID v4)",
      "channel_id": "string (Slack channel ID, format: C#########)",
      "channel_name": "string (#channel-name)",
      "added_by": "string (admin user_id)",
      "added_at": "string (ISO 8601 timestamp)",
      "status": "string (enum: 'active' | 'revoked')"
    }
  ]
}
```

**Validation Rules**:
- `admins`: Array of valid Slack user IDs (format: U#########)
- `channel_id`: Must match Slack channel ID format (C#########)
- `status`: One of ['active', 'revoked']
- `added_by`: Must exist in `admins` array

**Access Control Logic**:
```javascript
// Check if channel is whitelisted (FR-021)
function isChannelAllowed(channelId) {
  return channels.some(ch =>
    ch.channel_id === channelId &&
    ch.status === 'active'
  );
}

// Check if user is admin (FR-021a)
function isAdmin(userId) {
  return admins.includes(userId);
}
```

**Relationships**:
- Managed by `User` entities (admins)
- Controls access to `Conversation` creation

---

### 6. DocumentUploadJob

Tracks document upload to BMS API with processing status.

**Storage**: Redis key `bms:upload:job:{job_id}` with 30-day TTL (longer than conversations) (Session 2025-10-09: Updated with `bms:` prefix)

**Schema**:
```json
{
  "job_id": "string (UUID v4)",
  "document_id": "string (from BMS API response, null if failed)",
  "file_name": "string",
  "file_type": "string (extension, e.g., 'pdf')",
  "file_size_bytes": "integer",
  "uploaded_by": "string (MS Teams user_id)",
  "conversation_id": "string (FK to Conversation)",
  "upload_date": "string (ISO 8601 timestamp)",
  "processing_status": "string (enum: 'queued' | 'processing' | 'completed' | 'failed')",
  "indexed_chunks_count": "integer (null until completed)",
  "error_message": "string (null if successful)",
  "bms_async_job_id": "string (from /api/v1/documents/upload/async)"
}
```

**Validation Rules**:
- `file_type`: Must be in [pdf, csv, xlsx, xls, txt, md, docx, pptx]
- `file_size_bytes`: Max 1GB (1073741824 bytes)
- `processing_status`: State machine (see below)

**State Transitions**:
1. **queued** → Upload accepted, waiting for BMS API
2. **processing** → BMS API is processing document
3. **completed** → Document indexed successfully (`indexed_chunks_count` set)
4. **failed** → Error occurred (`error_message` set)

**Relationships**:
- Created by one `User`
- Associated with one `Conversation`
- May trigger proactive message to user (FR-013)

---

## Storage Implementation

### Redis Key Patterns (Session 2025-10-09: Updated with `bms:` namespace)

**Namespace Convention**: All Redis keys use the `bms:` prefix to prevent collisions and enable clear debugging.

```
bms:context:{uuid}              → Conversation entity (TTL: 7 days)
bms:result:{uuid}               → SearchResult entity (TTL: 7 days)
bms:user:{teams_id}             → User entity (TTL: 7 days)
bms:user:{teams_id}:history     → Search history with embeddings (TTL: 7 days, array of {query, embedding[768], timestamp, result_id})
bms:upload:job:{uuid}           → DocumentUploadJob (TTL: 30 days)
bms:upload:jobs:pending         → Sorted set of pending upload job IDs (score = timestamp)
bms:whitelist:cache             → Cached whitelist data (TTL: 1 hour)
bms:audit:admin:resets          → Admin reset audit log
```

**Secondary Indexes**:
```
bms:index:channel:{channel_id}            → SET of conversation_ids
bms:index:user:{user_id}:conversations    → ZSET (sorted by last_message_at)
bms:index:user:{user_id}:uploads          → SET of job_ids (status != 'completed')
```

### File Storage

```
/workspace/002-n8n/config/whitelist.json  → Whitelist (persistent)
/workspace/002-n8n/config/admins.json     → Admin backup (persistent)
```

### Redis Connection

```javascript
const redis = require('redis');
const client = redis.createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379',
  retry_strategy: (options) => {
    // Fallback to file-based storage on failure (NFR-002)
    if (options.total_retry_time > 10000) {
      return new Error('Redis unavailable, using stateless mode');
    }
    return Math.min(options.attempt * 100, 3000);
  }
});
```

---

## Entity Relationships Diagram

```
User (MS Teams ID)
  ├── participates in → Conversation
  ├── creates → SearchResult
  └── uploads → DocumentUploadJob

Conversation (conversation_id)
  ├── contains → Message[]
  ├── references → SearchResult[]
  └── expires after 7 days

Message (message_id)
  ├── belongs to → Conversation
  └── may reference → SearchResult

SearchResult (result_id)
  ├── belongs to → Conversation
  └── contains → Citation[]

Whitelist (file-based)
  ├── defines → admin User[]
  └── allows → channel access

DocumentUploadJob (job_id)
  ├── created by → User
  └── linked to → Conversation
```

---

## Index Requirements

### Redis Secondary Indexes (for quick lookups) - See Storage Implementation section above for updated bms: prefix patterns

### File-Based Lookup

```javascript
// Quick channel whitelist check (in-memory cache)
const whitelistCache = {
  data: null,
  lastRefresh: 0,
  TTL: 60000, // Refresh every 60s

  isChannelAllowed(channelId) {
    if (!this.data || Date.now() - this.lastRefresh > this.TTL) {
      this.data = JSON.parse(fs.readFileSync(WHITELIST_PATH));
      this.lastRefresh = Date.now();
    }
    return this.data.channels.some(ch =>
      ch.channel_id === channelId && ch.status === 'active'
    );
  }
};
```

---

## Data Retention Policy

| Entity | Retention | Enforcement |
|--------|-----------|-------------|
| Conversation | 7 days | Redis TTL auto-expire |
| Message | 7 days | Embedded in Conversation |
| SearchResult | 7 days | Redis TTL auto-expire |
| User | 7 days since last_active | Manual cleanup script |
| Whitelist | Persistent | Manual removal only |
| DocumentUploadJob | 30 days | Redis TTL auto-expire |

**Cleanup Script** (`/workspace/002-n8n/scripts/cleanup-expired.sh`) (Session 2025-10-09: Updated with `bms:` prefix):
```bash
#!/bin/bash
# Remove users inactive > 7 days
redis-cli --scan --pattern "bms:user:*" | while read key; do
  last_active=$(redis-cli hget "$key" last_active)
  if [ $(($(date +%s) - $(date -d "$last_active" +%s))) -gt 604800 ]; then
    redis-cli del "$key"
  fi
done
```

---

## Performance Considerations

### Conversation Context Summarization

To keep `context_summary` under 2000 chars (LLM token limit), condense older messages:

```javascript
function summarizeContext(messages) {
  const recent = messages.slice(-5); // Last 5 exchanges
  const older = messages.slice(0, -5);

  let summary = "";
  if (older.length > 0) {
    summary = `[Earlier: user asked about ${extractTopics(older).join(', ')}]\n\n`;
  }

  summary += recent.map(m =>
    `${m.sender}: ${m.content.substring(0, 200)}`
  ).join('\n');

  return summary.substring(0, 2000);
}
```

### Query Performance

- **Conversation lookup**: O(1) via `conversation:{id}` key
- **Channel whitelist check**: O(1) with in-memory cache
- **User history**: O(log N) via sorted set `index:user:{id}:conversations`

---

## Migration Plan (POC → Production)

### POC (Current Design)
- Redis for conversations (single instance)
- File-based whitelist
- 20 users, 2-3 channels

### Post-POC (50-100 users)
- Redis Sentinel/Cluster for HA
- Migrate whitelist to Redis (dynamic updates)
- Add user analytics table (PostgreSQL)

### Production (>100 users)
- Separate Redis instances (conversations vs cache)
- PostgreSQL for permanent records (users, audit log)
- S3/object storage for conversation archives

---

*Data model designed: 2025-10-06*
*Next: Create API contracts and quickstart guide*
