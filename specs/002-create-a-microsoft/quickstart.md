# Slack Bot Quickstart Guide

**Feature**: Slack Chat Bot for BMS Agent
**Version**: 1.0.0 (POC - Implementation Complete)
**Last Updated**: 2025-10-11

## Prerequisites

Before starting, ensure you have:

- [x] RunPod GPU instance with /workspace persistence
- [x] BMS Agent API running at `http://localhost:8000`
- [x] Ollama with GPT-OSS model (`gpt-oss:latest`)
- [x] Slack workspace admin access (to create Slack app)
- [x] n8n installed on RunPod at `http://localhost:5678`
- [x] Redis running on port 6379

**Verify BMS API**:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy",...}
```

**Verify Ollama**:
```bash
curl http://localhost:11434/api/tags
# Expected: List including "gpt-oss:latest"
```

---

## Step 1: Verify Redis is Running

Redis is already set up and running for event deduplication and caching.

```bash
# Verify Redis is running
redis-cli ping
# Expected: PONG

# Check Redis can store data
redis-cli SET test "hello"
redis-cli GET test
# Expected: "hello"
```

---

## Step 2: Create Slack App and Configure Webhooks

### 2.1 Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Fill in app details:
   - **App Name**: Nomi BMS Assistant
   - **Workspace**: Select your Slack workspace
4. Click **"Create App"**

### 2.2 Configure Bot User

1. In left sidebar, click **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add the following scopes:
   - `app_mentions:read` - Read messages that @mention the bot
   - `chat:write` - Send messages to channels
   - `channels:read` - View basic channel info
4. Scroll to top, click **"Install to Workspace"**
5. Click **"Allow"**
6. **IMPORTANT**: Copy the **Bot User OAuth Token** (starts with `xoxb-`)
   - You'll need this for n8n configuration

### 2.3 Enable Event Subscriptions

1. In left sidebar, click **"Event Subscriptions"**
2. Toggle **"Enable Events"** to ON
3. Set **Request URL**: `https://<your-runpod-proxy-url>/webhook/slack-events`
   - Example: `https://nqz5l77nsrdkyt-5678.proxy.runpod.net/webhook/slack-events`
   - Slack will verify this URL (must return `200 OK` with challenge)
4. Scroll to **"Subscribe to bot events"**
5. Add **"app_mention"** event
6. Click **"Save Changes"**

### 2.4 Add Bot to Slack Channel

1. In Slack, go to the channel where you want the bot (e.g., `#bms-testing`)
2. Type `/invite @Nomi BMS Assistant`
3. Bot will join the channel
4. Test by typing: `@Nomi BMS Assistant hello`
   - Bot won't respond yet (n8n workflow not imported)

---

## Step 3: Import and Configure n8n Workflow

### 3.1 Set Up n8n Credentials

1. Open n8n UI: `https://<runpod-proxy-url>` (e.g., `https://nqz5l77nsrdkyt-5678.proxy.runpod.net`)
2. Go to **Credentials** → **New**
3. Add **Slack OAuth2 API** credential:
   - Credential Name: `Slack account 3` (must match workflow reference)
   - OAuth2 Grant Type: **Access Token**
   - Access Token: `<Bot User OAuth Token from step 2.2.6>` (starts with `xoxb-`)
4. Click **Save**

### 3.2 Import Primary Workflow

1. In n8n, go to **Workflows** → **Add workflow** → **Import from File**
2. Select `/workspace/002-n8n/workflows/bms-ai-agent.json`
3. Verify workflow imported successfully:
   - Webhook ID: `slack-events`
   - Slack credential: `Slack account 3`
   - Ollama node connected
4. **Activate the workflow** (toggle in top right)
- Port: `6379`
- Database: `0`

**HTTP Header Auth** (for Ollama)
- Credential Name: `Ollama Local`
- Name: `Content-Type`
- Value: `application/json`

### 3.2 Import n8n Workflows

```bash
cd /workspace/002-n8n

# Deploy all workflows to n8n
./scripts/deploy-workflows.sh

# This imports:
# - main-bot-handler.json (webhook trigger)
# - query-analyzer.json (LLM intent detection)
# - bms-api-caller.json (BMS API integration)
# - context-manager.json (Redis conversation storage)
# - admin-commands.json (whitelist management)
```

**Manual import alternative**:
1. In n8n, click **Workflows** → **Import from File**
2. Select each workflow JSON from `/workspace/002-n8n/workflows/`
3. Activate each workflow (toggle switch)

### 3.3 Configure Webhook URL

1. In n8n, open **main-bot-handler** workflow
2. Copy **Webhook URL** from Webhook Trigger node
   - Example: `https://n8n.runpod.io/webhook/123abc/teams`
3. Go back to Bot Framework portal
4. Update **Messaging Endpoint** with n8n webhook URL
5. Click **Save**

---

## Step 4: Initialize Configuration Files

### 4.1 Create Whitelist Configuration

```bash
cd /workspace/002-n8n

# Initialize storage and config
./scripts/init-storage.sh
```

This creates `/workspace/002-n8n/config/whitelist.json`:
```json
{
  "admins": [],
  "channels": []
}
```

### 4.1b Generate Admin Reset Secret (FR-024b)

The admin reset secret allows recovery if the initial admin becomes unavailable.

```bash
# Generate 64-character hex secret (32 bytes)
openssl rand -hex 32 > /workspace/002-n8n/config/.admin_reset_secret

# Set as environment variable
echo "ADMIN_RESET_SECRET=$(cat /workspace/002-n8n/config/.admin_reset_secret)" \
  >> /workspace/002-n8n/config/.env

# Secure the file (read-only for owner)
chmod 400 /workspace/002-n8n/config/.admin_reset_secret

# Verify secret is set
grep ADMIN_RESET_SECRET /workspace/002-n8n/config/.env
```

**Security Notes**:
- Store secret securely - never commit to Git
- Share secret only with authorized personnel via secure channel
- Rotate secret periodically (every 90 days recommended)
- All reset attempts are logged in Redis `audit:admin_resets` (90-day retention)

**Recovery Usage**:
If admin becomes unavailable, authorized user can type:
```
/admin reset <64-char-hex-secret>
```

### 4.2 Add Admin Users

Find your MS Teams user ID:
1. Send any message to the bot in MS Teams
2. Check n8n execution log (Webhook node output)
3. Copy `from.id` value (e.g., `29:1abc...def`)

Edit `whitelist.json`:
```json
{
  "admins": [
    "29:1abc...def"  // Your MS Teams user ID
  ],
  "channels": []
}
```

### 4.3 Whitelist Your First Channel

1. In MS Teams, add the bot to a channel (e.g., #test-channel)
2. As admin, send message: `/admin allow #test-channel`
3. Bot responds: **"Access granted to #test-channel"**

Alternatively, manually edit `whitelist.json`:
```json
{
  "admins": ["29:1abc...def"],
  "channels": [
    {
      "whitelist_id": "wl-001",
      "channel_id": "19:abc@thread.tacv2",
      "channel_name": "#test-channel",
      "added_by": "29:1abc...def",
      "added_at": "2025-10-06T10:00:00Z",
      "status": "active"
    }
  ]
}
```

---

## Step 5: Test End-to-End Flow

### 5.1 Basic Question & Answer

In whitelisted MS Teams channel, send:
```
What are the emergency brake procedures for Class 395 trains?
```

**Expected Response** (within 3 seconds, Session 2025-10-09: Updated with footnote citations):
```
[Bot is typing...]

Based on the railway safety documentation:

The emergency brake procedures for Class 395 trains are:
1. Immediately apply emergency brake using red handle¹
2. Notify control room via radio²
3. Evacuate passengers if necessary¹

¹ Class 395 Safety Manual, Section 4.2 (Relevance: 0.94)
² Emergency Procedures Guide, Page 12 (Relevance: 0.89)
```

### 5.2 Test Search Command

Send:
```
/search VLAN configuration
```

**Expected Response**:
```
Found 5 documents matching "VLAN configuration":

1. Network Configuration Guide (Score: 0.92)
   "VLAN configuration for emergency systems requires..."

2. Technical Specs v2.1 (Score: 0.87)
   "Configure VLANs 100-110 for safety-critical..."

[3 more results]
```

### 5.3 Test File Upload

1. Attach PDF document to message (or type `/upload` first)
2. Bot responds:
```
Document uploaded successfully!
Document ID: abc-123-def-456
Processing status: queued

Use `/status abc-123-def-456` to check indexing progress.
```

3. Check status:
```
/status abc-123-def-456
```

**Response**:
```
Document: railway_safety_manual.pdf
Status: completed
Indexed chunks: 156
Processing time: 12.3s
```

### 5.4 Test History Command

Send:
```
/history
```

**Expected Response**:
```
Your recent searches (last 7 days):

1. 2025-10-06 10:30 - "What are emergency brake procedures..."
2. 2025-10-06 10:25 - "VLAN configuration"
3. 2025-10-05 14:15 - "Signal system maintenance"

[7 more entries]
```

### 5.5 Test Conversation Context

Send two messages in sequence:
```
Message 1: What is the brake testing procedure?
```

Wait for response, then:
```
Message 2: How often should that be done?
```

Bot should understand "that" refers to "brake testing procedure" from previous message (conversation context maintained).

---

## Step 6: Validation & Testing

### 6.1 Run Integration Tests

```bash
cd /workspace/002-n8n

# Install test dependencies
npm install

# Run integration tests
npm test

# Expected output:
# ✓ MS Teams webhook receives messages
# ✓ LLM intent classification works
# ✓ BMS API integration successful
# ✓ Conversation context persists
# ✓ Whitelist access control enforced
# ✓ File upload processing works
```

### 6.2 Performance Validation

Test response time (<3s requirement):

```bash
# Load test script
./scripts/load-test.sh 20 100

# Simulates:
# - 20 concurrent users
# - 100 queries total
# - Measures p95 response time
```

**Success Criteria**:
- p50 latency: < 1.5s
- p95 latency: < 3.0s
- Error rate: < 5%

### 6.3 Verify 7-Day Data Retention

```bash
# Check Redis TTL on conversation
redis-cli TTL "conversation:abc-123-def"
# Expected: ~604800 (7 days in seconds)

# Verify auto-cleanup
./scripts/cleanup-expired.sh --dry-run
# Shows what would be deleted
```

---

## Step 7: Monitoring & Troubleshooting

### 7.1 Check n8n Execution Logs

1. In n8n UI, go to **Executions**
2. Filter by workflow: `main-bot-handler`
3. Click on execution to see detailed logs
4. Common issues:
   - **Webhook not triggering**: Check Bot Framework messaging endpoint
   - **Redis errors**: Verify Redis container is running
   - **BMS API timeout**: Check BMS API health at `/health`

### 7.2 Monitor Redis

```bash
# Check Redis memory usage
redis-cli INFO memory

# List active conversations
redis-cli KEYS "conversation:*"

# View conversation details
redis-cli GET "conversation:abc-123"
```

### 7.3 Common Issues & Fixes

**Bot doesn't respond in MS Teams**:
```bash
# 1. Verify n8n webhook is active
curl -X POST https://n8n.runpod.io/webhook/123abc/teams \
  -H "Content-Type: application/json" \
  -d '{"type":"message","text":"test"}'

# 2. Check Bot Framework messaging endpoint matches n8n webhook

# 3. Verify credentials in n8n (App ID + Password)
```

**"Channel not whitelisted" error**:
```bash
# Check whitelist config
cat /workspace/002-n8n/config/whitelist.json

# Verify channel ID matches
# Get from n8n execution log: message.channelData.channel.id
```

**Context storage failure (NFR-002)**:
```bash
# Verify Redis is running
docker ps | grep bms-bot-redis

# Restart Redis
docker restart bms-bot-redis

# Bot should continue in stateless mode with warning:
# "Conversation history is temporarily unavailable. Your question will still be answered."
```

**Slow responses (>3s)**:
```bash
# Check BMS API response time
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"test","max_chunks":5}' \
  --write-out "%{time_total}\n"

# Expected: < 2.5s

# Check Ollama response time
curl http://localhost:11434/api/generate \
  -d '{"model":"mistral-nemo:12b-instruct","prompt":"classify: test"}' \
  --write-out "%{time_total}\n"

# Expected: < 0.5s
```

---

## Step 8: Production Readiness (Post-POC)

### 8.1 Scale to 50-100 Users

1. **Redis HA**: Deploy Redis Sentinel
   ```bash
   # See /workspace/002-n8n/docs/redis-ha-setup.md
   ```

2. **n8n Clustering**: Run multiple n8n instances with shared Redis

3. **Load Balancer**: Add nginx for n8n webhook endpoints

### 8.2 Monitoring Setup

1. Enable n8n webhook execution history (persistent)
2. Set up Prometheus + Grafana for metrics
3. Configure alerting for:
   - Response time > 3s (p95)
   - Error rate > 5%
   - Redis memory > 80%

### 8.3 Backup & Disaster Recovery

```bash
# Daily Redis backup
./scripts/backup-redis.sh

# Backup whitelist config
cp /workspace/002-n8n/config/whitelist.json \
   /workspace/backups/whitelist-$(date +%Y%m%d).json
```

---

## Quick Reference

### Useful Commands

```bash
# Restart all services
./scripts/manage-services.sh restart

# View n8n logs
docker logs -f n8n

# Clear Redis (reset all conversations)
redis-cli FLUSHDB

# Export workflows for backup
./scripts/export-workflows.sh
```

### Default Ports

- BMS API: `8000`
- n8n: `5678`
- Redis: `6379`
- Ollama: `11434`

### File Locations

- Workflows: `/workspace/002-n8n/workflows/`
- Config: `/workspace/002-n8n/config/whitelist.json`
- Redis data: `/workspace/redis_data/`
- Logs: `/workspace/logs/n8n-bot.log`

---

## Success Checklist

- [ ] Redis running with 7-day TTL
- [ ] n8n workflows imported and active
- [ ] Bot Framework connected to n8n webhook
- [ ] Admin users configured in whitelist
- [ ] At least 1 channel whitelisted
- [ ] Test message receives response <3s
- [ ] Conversation context works (multi-turn)
- [ ] File upload indexing works
- [ ] Integration tests pass
- [ ] Monitoring enabled

---

**Next Steps**: Once POC is validated, proceed to `/tasks` command to generate implementation tasks for production hardening.

---

*Quickstart guide version 1.0.0*
*Questions? Check `/workspace/002-n8n/docs/troubleshooting.md`*
