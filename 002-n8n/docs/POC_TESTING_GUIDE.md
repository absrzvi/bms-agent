# POC Testing Guide - MS Teams Bot for BMS Agent

**Purpose**: Step-by-step guide to validate the POC implementation before user deployment

**Status**: Implementation complete, ready for testing
**Estimated Time**: 2-3 hours

---

## Pre-Testing Checklist

### 1. Verify All Services Are Running

```bash
# Check service status
/workspace/002-n8n/scripts/manage-services.sh status
```

**Expected Output:**
```
✓ n8n is running (PID: xxxxx)
✓ Redis is running (PID: xxxxx)
✓ BMS API is running (PID: xxxxx)
✓ Ollama is running (PID: xxxxx)
```

**If any service is not running:**
```bash
# Start all services
/workspace/002-n8n/scripts/manage-services.sh start

# Or start individual service
/workspace/002-n8n/scripts/manage-services.sh start <service-name>
```

### 2. Verify Health Check

```bash
curl -s http://localhost:5678/webhook/health | jq '.'
```

**Expected Output:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-06T...",
  "components": {
    "redis": {"status": "healthy", "message": "Redis is responsive"},
    "bms_api": {"status": "healthy", "message": "BMS API v1.0.0"},
    "ollama": {"status": "healthy", "message": "Ollama running with 2 models"}
  },
  "version": "1.0.0",
  "environment": "POC"
}
```

**If status is "degraded":**
- Check which component is unhealthy
- Refer to `/workspace/002-n8n/docs/troubleshooting.md`

### 3. Verify n8n Workflows Are Deployed

```bash
curl -s http://localhost:5678/rest/workflows | jq '.[] | {name: .name, active: .active}'
```

**Expected: 8 workflows**
1. Main Bot Handler
2. Query Analyzer
3. BMS API Caller
4. Context Manager
5. Similar Query Detector
6. Admin Commands
7. Health Check

**If workflows are missing:**
```bash
cd /workspace/002-n8n
./scripts/deploy-workflows.sh
```

### 4. Check BMS API Has Documents

```bash
curl -s http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'
```

**Expected:** Number > 0 (e.g., 1744 documents)

**If 0 documents:**
```bash
cd /workspace/001-bms-agent
python scripts/batch_process_incoming.py
```

---

## Testing Phase 1: Automated Tests (30 minutes)

### Test 1.1: Contract Tests

**Purpose**: Verify API schemas and data structures

```bash
cd /workspace/002-n8n
npm test tests/contract/
```

**Expected Results:**
```
✓ MS Teams webhook schema validation (T007)
✓ BMS API /ask endpoint contract (T008)
✓ Conversation storage API contract (T009)

Tests: 3 passed, 3 total
```

**If tests fail:**
- Check error messages for specific schema violations
- Verify BMS API is running: `curl http://localhost:8000/health`
- Check Redis connectivity: `redis-cli ping`

### Test 1.2: Integration Tests

**Purpose**: Validate end-to-end workflows

```bash
npm test tests/integration/
```

**Expected Results:**
```
✓ Natural language question flow (T010)
✓ Slash command execution (T011)
  ✓ /help command
  ✓ /search command
  ✓ /ask command
  ✓ /status command
  ✓ /history command
✓ Document upload with attachment (T012)
✓ Admin whitelist management (T013)
✓ Context storage failure fallback (T014)

Tests: 5 passed, 5 total
```

**If tests fail:**
- Review test output for specific failure
- Check n8n execution logs: `tail -100 /workspace/n8n/.n8n/logs/n8n.log`
- Verify webhook endpoints are active in n8n UI

### Test 1.3: Unit Tests

**Purpose**: Validate individual components

```bash
npm test tests/unit/
```

**Expected Results:**
```
✓ Whitelist validation logic (T028)
  ✓ isChannelAllowed returns true for active channels
  ✓ isAdmin returns true for whitelisted admins
  ✓ Cache refresh after 60s
✓ Redis TTL enforcement (T029)
  ✓ New conversation has 7-day TTL
  ✓ Expired conversations auto-deleted
  ✓ TTL refreshed on message update

Tests: 2 passed, 2 total
```

### Test 1.4: Performance Tests

**Purpose**: Verify response time targets (FR-030)

```bash
npm test tests/performance/load-test.js
```

**Expected Results:**
```
Load Test Results:
- Total queries: 100
- Concurrent users: 20
- p50 response time: <1500ms ✓
- p95 response time: <3000ms ✓
- Error rate: <5% ✓
```

**If performance tests fail:**
- Check p95 response time
- If > 3000ms: Optimize BMS API (see Section 5)
- If high error rate: Check service logs

**Action after Test Phase 1:**
```
✓ All automated tests pass → Proceed to Phase 2
✗ Some tests fail → Fix issues using troubleshooting.md before Phase 2
```

---

## Testing Phase 2: MS Teams Bot Setup (60 minutes)

**Note**: This requires MS Teams admin access and Azure account for Bot Framework

### Step 2.1: Register Bot with Bot Framework

**Follow**: `/workspace/002-n8n/docs/setup-ms-teams.md` Section 1

**Key Steps:**
1. Go to https://dev.botframework.com/
2. Create new bot registration
3. Get App ID and App Password
4. **SAVE THESE IMMEDIATELY** - you won't see password again

**Verification:**
```bash
# Check you have both credentials
echo "App ID: $BOT_APP_ID"
echo "App Password: [hidden]"  # Should not be empty
```

### Step 2.2: Configure n8n Webhook URL

**Determine your webhook URL:**

**Option A: Local Testing with ngrok (Recommended for POC)**
```bash
# Install ngrok if not available
cd /tmp
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-*.tgz
./ngrok http 5678
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

**Option B: Production Deployment**
- Use your actual domain (e.g., `https://bms-bot.company.com`)

**Configure in Bot Framework:**
1. Go to Bot Framework Portal → Your bot → Configuration
2. Set Messaging endpoint: `https://your-url/webhook/teams`
3. Click Save

**Verification:**
```bash
# Test webhook is reachable
curl -X POST https://your-url/webhook/teams \
  -H "Content-Type: application/json" \
  -d '{"type":"message","text":"test"}'

# Should return 200 OK (even if it rejects the test message)
```

### Step 2.3: Configure Bot Credentials in n8n

```bash
# Edit environment file
vim /workspace/002-n8n/config/n8n.env

# Add these lines:
BOT_APP_ID=your-app-id-from-step-2.1
BOT_APP_PASSWORD=your-app-password-from-step-2.1
TEAMS_WEBHOOK_URL=https://your-url/webhook/teams

# Save and exit
```

**Restart n8n to load new credentials:**
```bash
/workspace/002-n8n/scripts/manage-services.sh restart n8n
```

**Verification:**
```bash
# Check n8n loaded environment variables
ps aux | grep n8n  # Should show process running
curl http://localhost:5678/healthz  # Should return success
```

### Step 2.4: Initialize Whitelist with Your User

**Get your MS Teams user ID:**

Method 1 (Graph Explorer):
1. Go to https://developer.microsoft.com/en-us/graph/graph-explorer
2. Sign in with your MS Teams account
3. Run: `GET https://graph.microsoft.com/v1.0/me`
4. Copy the `id` field (format: `29:1abc123...`)

**Add yourself as admin:**
```bash
vim /workspace/002-n8n/config/whitelist.json
```

```json
{
  "admins": [
    "29:YOUR-USER-ID-HERE"
  ],
  "channels": []
}
```

**Verification:**
```bash
# Check whitelist is valid JSON
cat /workspace/002-n8n/config/whitelist.json | jq '.'

# Should display formatted JSON without errors
```

### Step 2.5: Add Bot to MS Teams

**Option A: Add via Bot Framework Direct Link (Easier)**
1. In Bot Framework Portal, go to Channels → Microsoft Teams
2. Click "Open in Teams"
3. Click "Add" to add bot to your personal chat

**Option B: Add via App Studio (More Control)**
1. In MS Teams, search for "App Studio" app
2. Install if not present
3. Manifest editor → Create new app
4. Add your Bot ID from Step 2.1
5. Test and distribute → Install

**Verification:**
```bash
# You should now see the bot in your MS Teams chat list
# Send test message: "hello"
# Expected: No response yet (whitelist check happens first)
```

---

## Testing Phase 3: End-to-End Functional Testing (45 minutes)

### Test 3.1: Help Command (FR-009)

**In MS Teams personal chat with bot:**
```
/help
```

**Expected Response:**
```
🤖 BMS Teams Bot - Available Commands

I help you search railway documentation and answer questions about procedures, technical specs, and safety guidelines.

/ask [question] - Get a direct answer to your question with source citations
/search [query] - Search for relevant documents without generating an answer
/upload - Upload a document for indexing (or attach file directly)
/status [document_id] - Check processing status of uploaded document
/history - View your search history from the last 7 days
/help - Show this help message
/admin [action] [target] - Admin commands to manage channel whitelist

💡 Tips:
- You can ask questions in natural language
- The bot remembers conversation context for 7 days
- All answers include citations
- Upload documents by attaching files directly

Response time: <3 seconds | Context retention: 7 days
```

**Validation:**
- ✅ Response received within 3 seconds (FR-003)
- ✅ All 7 commands listed (FR-007-010)
- ✅ Tips section present (NFR-004)
- ✅ Plain text format (NFR-003)

### Test 3.2: Natural Language Question (FR-001, FR-004)

**In MS Teams:**
```
What are the emergency brake procedures for Class 395 trains?
```

**Expected Behavior:**
1. Typing indicator appears ("BMS Agent Bot is typing...")
2. Response within 3 seconds

**Expected Response Format:**
```
[Answer text with specific procedures]

Sources:
• Document: "Class 395 Safety Manual" (Section 4.2, Score: 0.95)
  Excerpt: "Emergency brake activation requires..."
• Document: "Brake System Technical Guide" (Section 2.1, Score: 0.89)
  Excerpt: "The emergency brake system is designed to..."
```

**Validation:**
- ✅ Typing indicator shown (FR-018)
- ✅ Response < 3 seconds (FR-003)
- ✅ Answer includes citations (FR-004)
- ✅ Citations show document name, section, score

**If no response or error:**
```bash
# Check n8n execution logs
tail -50 /workspace/n8n/.n8n/logs/n8n.log | grep ERROR

# Check BMS API logs
tail -50 /workspace/logs/api.log | grep ERROR

# Verify Qdrant has documents
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'
```

### Test 3.3: Search Command (FR-007)

**In MS Teams:**
```
/search VLAN configuration emergency systems
```

**Expected Response:**
```
📄 Search Results (5 documents):

1. "Network Architecture Guide" (Score: 0.92)
   Excerpt: "VLAN 100 is reserved for emergency communication systems..."

2. "Emergency Systems Technical Manual" (Score: 0.88)
   Excerpt: "The emergency VLAN configuration ensures redundancy..."

3. "IT Infrastructure Standards" (Score: 0.85)
   Excerpt: "VLAN segmentation for safety-critical systems..."

[... more results ...]
```

**Validation:**
- ✅ Returns document list (not generated answer)
- ✅ Results sorted by relevance score
- ✅ Includes excerpts

### Test 3.4: Conversation Context (FR-005)

**Send follow-up question:**
```
What about VLAN 200?
```

**Expected Behavior:**
- Bot understands context from previous question
- Continues discussion about VLAN configuration

**Validation:**
- ✅ Bot references previous context
- ✅ Relevant answer to follow-up

**Then check context persistence:**
```bash
# Check conversation stored in Redis
redis-cli KEYS "conversation:*"
redis-cli GET "conversation:[one-of-the-keys]" | jq '.'

# Should show conversation with messages array
```

### Test 3.5: Document Upload (FR-011, FR-012, FR-013)

**Method 1: Attach file directly**
1. In MS Teams chat, click attachment icon
2. Select a test PDF file (< 1GB, supported format)
3. Send message with attachment

**Method 2: Use upload command**
```
/upload
[Then attach PDF file]
```

**Expected Response:**
```
✓ Document uploaded successfully!
Document ID: abc-123-def-456
Status: Processing
Use `/status abc-123-def-456` to check progress.
```

**Check status:**
```
/status abc-123-def-456
```

**Expected Response:**
```
⚙️ Status: Processing document... (45%)
```

**Wait ~30 seconds, check again:**
```
/status abc-123-def-456
```

**Expected Final Response:**
```
✅ Status: Complete | Indexed chunks: 42
```

**Validation:**
- ✅ Upload confirmation received (FR-013)
- ✅ Document ID provided (FR-012)
- ✅ Status command works (FR-015)
- ✅ Processing completes successfully

### Test 3.6: Search History (FR-016)

**In MS Teams:**
```
/history
```

**Expected Response:**
```
📜 Your Search History (Last 7 Days)

• 2025-10-06 14:32 - "emergency brake procedures" (5 results)
• 2025-10-06 14:28 - "VLAN configuration" (3 results)
• 2025-10-06 14:25 - "/help" (command)

History retention: 7 days | Auto-purged after expiration
```

**Validation:**
- ✅ Shows queries from current session
- ✅ Includes timestamps
- ✅ Shows result counts

### Test 3.7: Similar Query Detection (FR-017)

**Ask a question similar to previous one:**
```
What are the brake procedures for emergency situations?
```

**Expected Response:**
```
💡 You asked something similar on Oct 6: "What are the emergency brake procedures for Class 395 trains?"
Would you like to see that response again?

[Then provides new answer with citations]
```

**Validation:**
- ✅ Similar query detected (≥0.85 similarity)
- ✅ Suggestion shown before answer
- ✅ Original query and date referenced

---

## Testing Phase 4: Admin & Access Control (30 minutes)

### Test 4.1: Whitelist a Channel (FR-024)

**As admin, in any MS Teams channel:**
```
/admin allow #operations-team
```

**Expected Response:**
```
✓ Access granted to #operations-team
```

**Verification:**
```bash
cat /workspace/002-n8n/config/whitelist.json | jq '.channels'
```

**Expected Output:**
```json
[
  {
    "whitelist_id": "uuid-here",
    "channel_id": "19:abc@thread.tacv2",
    "channel_name": "#operations-team",
    "added_by": "29:your-user-id",
    "added_at": "2025-10-06T...",
    "status": "active"
  }
]
```

### Test 4.2: List Whitelist (FR-024)

```
/admin list
```

**Expected Response:**
```
📋 Channel Whitelist (1 channels)
• #operations-team (added by Your Name on 2025-10-06)

👤 Administrators (1)
• Your Name (29:your-user-id)
```

### Test 4.3: Non-Whitelisted Channel Rejection (FR-025)

1. Create a test channel NOT in whitelist
2. Add bot to that channel
3. Send a message in that channel

**Expected Response:**
```
This bot is currently in POC phase. Contact your admin to request access.
```

**Validation:**
- ✅ Bot rejects non-whitelisted channels
- ✅ Friendly error message shown

### Test 4.4: Revoke Channel Access

```
/admin revoke #operations-team
```

**Expected Response:**
```
✓ Access revoked for #operations-team
```

**Verification:**
```bash
cat /workspace/002-n8n/config/whitelist.json | jq '.channels[0].status'
# Should show: "revoked"
```

---

## Testing Phase 5: Error Handling & Edge Cases (20 minutes)

### Test 5.1: BMS API Unavailable (FR-020)

**Simulate BMS API failure:**
```bash
# Stop BMS API temporarily
/workspace/001-bms-agent/scripts/manage_services.sh stop
```

**In MS Teams:**
```
What are the safety procedures?
```

**Expected Response:**
```
BMS-search tool cannot be accessed at this time. Please try again later.
```

**Restore service:**
```bash
/workspace/001-bms-agent/scripts/manage_services.sh start
```

**Validation:**
- ✅ User-friendly error message (NFR-001)
- ✅ No technical jargon exposed

### Test 5.2: Redis Context Storage Failure (NFR-002)

**Simulate Redis failure:**
```bash
# Stop Redis temporarily
/workspace/002-n8n/scripts/manage-services.sh stop redis
```

**In MS Teams:**
```
Test question with Redis down
```

**Expected Response:**
```
Conversation history is temporarily unavailable. Your question will still be answered.

[Answer with citations still provided]
```

**Restore Redis:**
```bash
/workspace/002-n8n/scripts/manage-services.sh start redis
```

**Send another message:**
```
Another test
```

**Expected Response:**
```
✓ Conversation history has been restored.

[Answer with citations]
```

**Validation:**
- ✅ Stateless fallback works (NFR-002)
- ✅ Warning message shown
- ✅ Answer still provided
- ✅ Restore notification shown (NFR-002a)

### Test 5.3: No Results Found (FR-021)

**In MS Teams:**
```
/search quantum entanglement railway applications 2050
```

**Expected Response:**
```
No results found for your query. Try rephrasing or using different keywords.
```

### Test 5.4: Query Too Long (FR-031)

**In MS Teams, send a message > 1000 characters:**
```
[Paste very long text > 1000 chars]
```

**Expected Response:**
```
Query too long. Please limit to 1000 characters.
```

### Test 5.5: Invalid File Upload (NFR-007)

**Attach an unsupported file (e.g., .exe, .zip):**

**Expected Response:**
```
Invalid file type. Supported formats: PDF, CSV, XLSX, XLS, TXT, MD, DOCX, PPTX
```

---

## Testing Phase 6: Performance Validation (15 minutes)

### Test 6.1: Response Time Check

**Manual timing test:**
1. Note current time
2. Send: "What is the brake system specification?"
3. Note response time

**Expected:** < 3 seconds (FR-030)

**If > 3 seconds, check bottleneck:**
```bash
# Check BMS API response time
time curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"test query"}'

# If BMS API is slow (> 1.5s):
cd /workspace/001-bms-agent
python scripts/optimize_qdrant_index.py
```

### Test 6.2: Concurrent Users Test

**Run automated load test:**
```bash
cd /workspace/002-n8n
npm test tests/performance/load-test.js
```

**Expected Results:**
- p50 < 1500ms
- p95 < 3000ms
- Error rate < 5%
- 20 concurrent users handled

### Test 6.3: Memory Usage Check

```bash
# Check Redis memory
redis-cli INFO memory | grep used_memory_human

# Should be < 200MB for POC (20 users)
```

**If memory > 500MB:**
```bash
/workspace/002-n8n/scripts/cleanup-expired.sh
```

---

## Testing Phase 7: Data Retention (10 minutes)

### Test 7.1: Verify 7-Day TTL (FR-027)

```bash
# Check conversation TTL
redis-cli KEYS "conversation:*"
redis-cli TTL conversation:[key-from-above]

# Should return ~604800 (7 days in seconds)
# Or less if conversation already started
```

### Test 7.2: Test Cleanup Script (FR-028)

```bash
# Run cleanup manually
/workspace/002-n8n/scripts/cleanup-expired.sh

# Check output
# Should show: "Cleaned up X expired conversations"
```

---

## Post-Testing: Documentation Validation (15 minutes)

### Validate Setup Guide

**Follow:** `/workspace/002-n8n/docs/setup-ms-teams.md`
- ✅ All 7 steps completed successfully
- ✅ Screenshots/examples are accurate
- ✅ Troubleshooting tips were helpful

### Validate Troubleshooting Guide

**Test:** `/workspace/002-n8n/docs/troubleshooting.md`
- ✅ Quick diagnostic commands work
- ✅ Common issues covered
- ✅ Solutions are accurate

### Validate Monitoring

**Check health endpoint:**
```bash
curl http://localhost:5678/webhook/health | jq '.'
```

**Check logs:**
```bash
tail -100 /workspace/n8n/.n8n/logs/n8n.log
```

---

## Testing Completion Checklist

### Automated Tests
- [ ] Contract tests pass (3/3)
- [ ] Integration tests pass (5/5)
- [ ] Unit tests pass (2/2)
- [ ] Performance test passes (p95 < 3s)

### Functional Tests
- [ ] Help command works
- [ ] Natural language Q&A works
- [ ] Search command works
- [ ] Conversation context persists
- [ ] Document upload works
- [ ] Status command works
- [ ] History command works
- [ ] Similar query detection works

### Admin & Access Control
- [ ] Whitelist channel addition works
- [ ] Whitelist listing works
- [ ] Non-whitelisted rejection works
- [ ] Whitelist revocation works

### Error Handling
- [ ] BMS API unavailable handled gracefully
- [ ] Redis failure fallback works
- [ ] No results message shown
- [ ] Query length validation works
- [ ] Invalid file type rejected

### Performance
- [ ] Response time < 3s
- [ ] 20 concurrent users supported
- [ ] Memory usage acceptable

### Data Retention
- [ ] 7-day TTL set correctly
- [ ] Cleanup script works

### Documentation
- [ ] Setup guide accurate
- [ ] Troubleshooting guide helpful
- [ ] Monitoring works

---

## Known Issues & Limitations (POC)

Document any issues found during testing:

1. **Issue**: _______________
   - **Impact**: _______________
   - **Workaround**: _______________
   - **Fix Required?**: Yes/No

2. [Add more as needed]

---

## Sign-Off

**Tester Name**: _______________
**Date**: _______________
**Testing Duration**: _____ hours

**Overall POC Status**:
- [ ] ✅ Ready for user deployment (all critical tests pass)
- [ ] ⚠️ Ready with known issues (document above)
- [ ] ❌ Not ready (major issues found)

**Next Steps**:
1. Deploy to POC user group (20 users)
2. Monitor for 2 weeks
3. Collect feedback
4. Plan post-POC enhancements

---

**Support During POC**:
- Health monitoring: `curl http://localhost:5678/webhook/health`
- View logs: `tail -f /workspace/n8n/.n8n/logs/n8n.log`
- Restart services: `/workspace/002-n8n/scripts/manage-services.sh restart`
- Troubleshooting: `/workspace/002-n8n/docs/troubleshooting.md`
