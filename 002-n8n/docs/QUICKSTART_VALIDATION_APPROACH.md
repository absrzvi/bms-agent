# Quickstart Validation Approach (T032)

**Document Version**: 1.0.0
**Last Updated**: 2025-10-07
**Purpose**: Provide systematic validation approach for quickstart.md deployment

---

## Overview

This document outlines the validation approach for the MS Teams Bot quickstart deployment. It provides step-by-step verification procedures to ensure all components are correctly configured and functional.

**Related Documents**:
- Source: `/workspace/specs/002-create-a-microsoft/quickstart.md`
- Tasks: Task T032 in `/workspace/specs/002-create-a-microsoft/tasks.md`

---

## Validation Checklist

### Prerequisites Validation

Before starting the quickstart, verify all prerequisites are met:

```bash
# 1. Check BMS API is running
curl -f http://localhost:8000/health
# Expected: HTTP 200, JSON response with {"status":"healthy"}

# 2. Check Ollama is running with required model
curl -f http://localhost:11434/api/tags | jq -r '.models[].name' | grep "mistral-nemo:12b-instruct"
# Expected: Line containing "mistral-nemo:12b-instruct"

# 3. Check n8n is accessible
curl -f http://localhost:5678
# Expected: HTTP 200 (n8n UI homepage)

# 4. Check /workspace persistence
ls -la /workspace
# Expected: Directory exists and is writable

# 5. Verify RunPod environment
echo $RUNPOD_POD_ID
# Expected: Non-empty pod ID
```

**Validation Criteria**: All 5 checks must pass before proceeding.

---

## Step-by-Step Validation

### Step 1: Deploy Redis for Conversation Storage

**Commands to Execute**:
```bash
# Create persistent data directory
mkdir -p /workspace/redis_data

# Run Redis container
docker run -d \
  --name bms-bot-redis \
  -v /workspace/redis_data:/data \
  -p 6379:6379 \
  redis:7-alpine redis-server --appendonly yes
```

**Validation**:
```bash
# 1. Check container is running
docker ps | grep bms-bot-redis
# Expected: Container status "Up"

# 2. Test Redis connectivity
redis-cli ping
# Expected: "PONG"

# 3. Test Redis persistence
redis-cli SET test-key "test-value"
redis-cli GET test-key
# Expected: "test-value"

# 4. Verify AOF persistence enabled
redis-cli CONFIG GET appendonly
# Expected: "appendonly" "yes"

# 5. Check persistent directory
ls -lh /workspace/redis_data/appendonly.aof.1.incr.aof
# Expected: File exists
```

**Success Criteria**: All 5 validations pass ✅

**Rollback on Failure**:
```bash
docker stop bms-bot-redis
docker rm bms-bot-redis
rm -rf /workspace/redis_data
```

---

### Step 2: Setup MS Teams Bot Connector

**Manual Steps**:
1. Register bot in Azure Bot Framework (https://dev.botframework.com)
2. Create Microsoft App ID and Password
3. Enable MS Teams channel
4. Add bot to MS Teams workspace

**Validation**:
```bash
# 1. Verify App ID was saved
echo $MS_BOT_APP_ID
# Expected: Non-empty GUID

# 2. Verify App Password was saved
echo $MS_BOT_APP_PASSWORD | wc -c
# Expected: > 20 characters

# 3. Test bot is visible in MS Teams
# Manual: Open MS Teams → Apps → Built for your org → Search "BMS Agent Bot"
# Expected: Bot appears in search results

# 4. Verify bot added to channel/chat
# Manual: Send "hello" to bot in MS Teams
# Expected: No error (bot may not respond yet, but message should be accepted)
```

**Success Criteria**: All 4 validations pass ✅

**Notes**:
- App ID and Password must be stored securely (environment variables or secrets manager)
- Messaging endpoint can be updated later in Step 3.3

---

### Step 3: Configure n8n Workflows

**3.1 Set Up n8n Credentials**

**Manual Steps**:
1. Open n8n UI: `http://<runpod-ip>:5678`
2. Navigate to **Credentials** → **New**
3. Add 3 credentials:
   - Microsoft Bot Framework
   - Redis
   - HTTP Header Auth (Ollama)

**Validation**:
```bash
# Check credentials exist (via n8n API if available, or manual UI check)
# Manual: n8n UI → Credentials → Verify 3 credentials listed
```

**Success Criteria**: 3 credentials created ✅

---

**3.2 Import n8n Workflows**

**Commands to Execute**:
```bash
cd /workspace/002-n8n

# Check deploy script exists
test -x ./scripts/deploy-workflows.sh && echo "Deploy script found" || echo "ERROR: Deploy script missing"

# Deploy all workflows
./scripts/deploy-workflows.sh
```

**Validation**:
```bash
# 1. Verify all workflows imported
# Manual: n8n UI → Workflows → Count workflows
# Expected: At least 5 workflows:
#   - main-bot-handler
#   - query-analyzer
#   - bms-api-caller
#   - context-manager
#   - admin-commands

# 2. Verify workflows are activated
# Manual: Check toggle switches in n8n UI are green (activated)

# 3. Check workflow validation report
cat /workspace/002-n8n/validation-report.json | jq '.valid_files'
# Expected: >= 5

# 4. Test workflow JSON validity
cd /workspace/002-n8n
python3 scripts/validate-workflows.py
# Expected: "All workflows validated successfully" or "passed with warnings"
```

**Success Criteria**: All 4 validations pass ✅

**Alternative Manual Import**:
```bash
# If deploy-workflows.sh fails, manually import each workflow:
# 1. n8n UI → Workflows → Import from File
# 2. Select: /workspace/002-n8n/workflows/main-bot-handler.json
# 3. Activate workflow
# 4. Repeat for remaining 4 workflows
```

---

**3.3 Configure Webhook URL**

**Manual Steps**:
1. Open main-bot-handler workflow in n8n
2. Click on Webhook Trigger node
3. Copy "Production URL" (e.g., `https://n8n.runpod.io/webhook/abc123/teams`)
4. Navigate to Bot Framework portal
5. Update Messaging Endpoint with webhook URL
6. Click Save

**Validation**:
```bash
# 1. Test webhook URL is accessible
WEBHOOK_URL="<paste-webhook-url-here>"
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"type":"message","text":"test"}'
# Expected: HTTP 200 or 400 (400 is OK - means workflow received request)

# 2. Check n8n execution log
# Manual: n8n UI → Executions → Check for new execution from webhook test
# Expected: Execution appears in list (may show error, but confirms webhook triggered)

# 3. Verify Bot Framework messaging endpoint updated
# Manual: Bot Framework portal → Settings → Messaging endpoint
# Expected: URL matches n8n webhook URL
```

**Success Criteria**: All 3 validations pass ✅

---

### Step 4: Initialize Configuration Files

**4.1 Create Whitelist Configuration**

**Commands to Execute**:
```bash
cd /workspace/002-n8n

# Initialize storage and config
./scripts/init-storage.sh
```

**Validation**:
```bash
# 1. Verify whitelist.json created
test -f /workspace/002-n8n/config/whitelist.json && echo "Whitelist exists" || echo "ERROR: Whitelist missing"

# 2. Check whitelist structure
cat /workspace/002-n8n/config/whitelist.json | jq .
# Expected: {"admins": [], "channels": []}

# 3. Verify whitelist is writable
touch /workspace/002-n8n/config/whitelist.json.test && rm /workspace/002-n8n/config/whitelist.json.test
# Expected: No errors

# 4. Check JSON validity
jq empty /workspace/002-n8n/config/whitelist.json
# Expected: No errors (valid JSON)
```

**Success Criteria**: All 4 validations pass ✅

---

**4.1b Generate Admin Reset Secret**

**Commands to Execute**:
```bash
# Generate 64-character hex secret
openssl rand -hex 32 > /workspace/002-n8n/config/.admin_reset_secret

# Set as environment variable
echo "ADMIN_RESET_SECRET=$(cat /workspace/002-n8n/config/.admin_reset_secret)" \
  >> /workspace/002-n8n/config/.env

# Secure the file
chmod 400 /workspace/002-n8n/config/.admin_reset_secret
```

**Validation**:
```bash
# 1. Verify secret file created
test -f /workspace/002-n8n/config/.admin_reset_secret && echo "Secret exists" || echo "ERROR: Secret missing"

# 2. Check secret length (should be 64 hex characters)
SECRET_LEN=$(cat /workspace/002-n8n/config/.admin_reset_secret | wc -c)
test $SECRET_LEN -eq 65 && echo "Secret length correct (64 + newline)" || echo "ERROR: Secret length incorrect"

# 3. Verify secret in .env
grep -q "ADMIN_RESET_SECRET=" /workspace/002-n8n/config/.env && echo ".env updated" || echo "ERROR: .env not updated"

# 4. Check file permissions (should be 400 = read-only for owner)
PERMS=$(stat -c "%a" /workspace/002-n8n/config/.admin_reset_secret)
test "$PERMS" = "400" && echo "Permissions correct" || echo "WARNING: Permissions should be 400, got $PERMS"

# 5. Test secret can be read
cat /workspace/002-n8n/config/.admin_reset_secret | grep -E "^[0-9a-f]{64}$"
# Expected: Single line with 64 hex characters
```

**Success Criteria**: All 5 validations pass ✅

**Security Check**:
- Secret must NOT be committed to Git
- Add to .gitignore: `.admin_reset_secret`

---

### Step 5: Test End-to-End Flow

**Test Scenarios**:

**5.1 Basic Chat Test**

```bash
# Send message via MS Teams
# Manual: Open MS Teams → Send "What are brakes?" to bot
```

**Validation**:
```bash
# 1. Check n8n execution log
# Manual: n8n UI → Executions → main-bot-handler
# Expected: New execution with status "success"

# 2. Check Redis conversation stored
redis-cli KEYS "conversation:*"
# Expected: At least 1 conversation key

# 3. Verify response sent back to Teams
# Manual: MS Teams → Check bot replied with answer
# Expected: Bot sends response with BMS content

# 4. Check TTL on conversation
CONV_KEY=$(redis-cli KEYS "conversation:*" | head -1)
redis-cli TTL "$CONV_KEY"
# Expected: ~604800 (7 days in seconds)
```

**Success Criteria**: All 4 validations pass ✅

---

**5.2 Command Test**

```bash
# Test /help command
# Manual: MS Teams → Send "/help" to bot
```

**Validation**:
```bash
# 1. Check n8n execution
# Manual: n8n UI → Executions → main-bot-handler → Check "Help Response" node executed
# Expected: Help node shows in execution path

# 2. Verify help text returned
# Manual: MS Teams → Check bot reply contains command list
# Expected: Bot sends help message with available commands
```

**Success Criteria**: All 2 validations pass ✅

---

**5.3 Admin Command Test**

```bash
# Test admin command (requires admin user configured)
# Manual: MS Teams → Send "/admin list" to bot
```

**Validation**:
```bash
# 1. Check admin verification
# Manual: n8n UI → Executions → admin-commands → Check "Verify Admin" node
# Expected: Admin verification passed (if user is admin) or denied (if not admin)

# 2. Verify whitelist operation
# Manual: MS Teams → Check bot reply shows whitelist or access denied
# Expected: Appropriate response based on admin status
```

**Success Criteria**: All 2 validations pass ✅

---

### Step 6: Validation & Testing

**6.1 Run Integration Tests**

**Commands to Execute**:
```bash
cd /workspace/002-n8n

# Install test dependencies
npm install

# Run integration tests
npm test
```

**Expected Output**:
```
✓ T010: MS Teams webhook receives messages
✓ T011: LLM intent classification works
✓ T012: File upload processing works
✓ T013: Conversation context persists
✓ T014: Whitelist access control enforced
✓ T015: Similar query detection works
```

**Validation**:
```bash
# 1. Check all tests passed
npm test 2>&1 | grep "passing"
# Expected: "6 passing" or similar

# 2. Check test coverage (if available)
npm run test:coverage
# Expected: Coverage report generated

# 3. Review test failures (if any)
npm test 2>&1 | grep "failing"
# Expected: "0 failing"
```

**Success Criteria**: All integration tests pass ✅

---

**6.2 Performance Validation**

**Commands to Execute**:
```bash
cd /workspace/002-n8n

# Run load test
./scripts/load-test.sh 20 100
```

**Validation**:
```bash
# Parse load test results
# Expected output metrics:
# - p50 latency: < 1.5s
# - p95 latency: < 3.0s
# - Error rate: < 5%

# Check results
cat /workspace/002-n8n/load-test-results.json | jq '{p50, p95, error_rate}'
```

**Success Criteria**: Performance targets met ✅

---

**6.3 Verify 7-Day Data Retention**

**Commands to Execute**:
```bash
# Check Redis TTL on conversation
CONV_KEY=$(redis-cli KEYS "conversation:*" | head -1)
redis-cli TTL "$CONV_KEY"

# Expected: ~604800 (7 days in seconds, may be slightly less if conversation already started)
```

**Validation**:
```bash
# 1. Verify TTL is set
TTL_VALUE=$(redis-cli TTL "$CONV_KEY")
test $TTL_VALUE -gt 0 && echo "TTL set correctly" || echo "ERROR: No TTL set (value: $TTL_VALUE)"

# 2. Verify TTL is approximately 7 days
test $TTL_VALUE -gt 500000 && test $TTL_VALUE -le 604800 && echo "TTL within range" || echo "WARNING: TTL outside expected range"

# 3. Check cleanup script exists
test -x /workspace/002-n8n/scripts/cleanup-expired.sh && echo "Cleanup script exists" || echo "WARNING: Cleanup script missing"

# 4. Dry-run cleanup
./scripts/cleanup-expired.sh --dry-run
# Expected: Shows conversations that would be deleted (or none if all are fresh)
```

**Success Criteria**: All 4 validations pass ✅

---

### Step 7: Monitoring & Troubleshooting

**7.1 Check n8n Execution Logs**

**Validation**:
```bash
# Access n8n execution logs via UI
# Manual: n8n UI → Executions → Filter by workflow

# Check for common errors:
# 1. Webhook not triggering
# 2. Redis connection errors
# 3. BMS API timeouts
# 4. Ollama unavailable

# Expected: No critical errors in recent executions
```

**Success Criteria**: No critical errors in logs ✅

---

**7.2 Monitor Redis**

**Commands to Execute**:
```bash
# Check Redis memory usage
redis-cli INFO memory | grep used_memory_human

# List active conversations
redis-cli KEYS "conversation:*" | wc -l

# View conversation details
CONV_KEY=$(redis-cli KEYS "conversation:*" | head -1)
redis-cli GET "$CONV_KEY" | jq .
```

**Validation**:
```bash
# 1. Redis memory usage reasonable (<100MB for POC)
MEMORY=$(redis-cli INFO memory | grep "used_memory:" | cut -d: -f2)
test $MEMORY -lt 104857600 && echo "Memory OK" || echo "WARNING: High memory usage"

# 2. Conversations are valid JSON
redis-cli GET "$CONV_KEY" | jq empty
# Expected: No errors (valid JSON)

# 3. Check conversation structure
redis-cli GET "$CONV_KEY" | jq 'has("messages") and has("created_at")'
# Expected: true
```

**Success Criteria**: All 3 validations pass ✅

---

### Step 8: Production Readiness (Post-POC)

This step is for post-POC deployment and is out of scope for initial validation.

**Validation**: SKIP for POC ⏭️

---

## Summary Validation Report

After completing all steps, generate a validation report:

```bash
cd /workspace/002-n8n

# Create validation report
cat > validation-report.txt <<EOF
# Quickstart Validation Report
Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Validated by: $(whoami)

## Prerequisites
- [ ] BMS API health check passed
- [ ] Ollama with Mistral Nemo available
- [ ] n8n accessible
- [ ] /workspace persistence verified
- [ ] RunPod environment confirmed

## Step 1: Redis Deployment
- [ ] Redis container running
- [ ] Redis ping successful
- [ ] Persistence enabled
- [ ] Data directory created

## Step 2: MS Teams Bot Connector
- [ ] Bot registered in Azure
- [ ] App ID and Password saved
- [ ] MS Teams channel enabled
- [ ] Bot added to workspace

## Step 3: n8n Workflows
- [ ] Credentials configured (3 total)
- [ ] Workflows imported (5 minimum)
- [ ] Workflows activated
- [ ] Webhook URL configured

## Step 4: Configuration Files
- [ ] whitelist.json created
- [ ] Admin reset secret generated
- [ ] Environment variables set

## Step 5: End-to-End Testing
- [ ] Basic chat test passed
- [ ] Command test passed
- [ ] Admin command test passed

## Step 6: Validation & Testing
- [ ] Integration tests passed (6/6)
- [ ] Performance targets met (p95 < 3s)
- [ ] 7-day retention verified

## Step 7: Monitoring
- [ ] n8n logs reviewed (no critical errors)
- [ ] Redis monitoring working

## Overall Status
PASS: ___ / 29 checks
FAIL: ___ / 29 checks

EOF

# Display report
cat validation-report.txt
```

---

## Validation Automation

For automated validation, run:

```bash
cd /workspace/002-n8n

# Run validation script
./scripts/quickstart-validation.sh

# Expected output:
# ✅ All checks passed
# Or:
# ❌ X checks failed (see details above)
```

---

## Troubleshooting Common Issues

### Redis Connection Failures

```bash
# Check Redis container status
docker ps -a | grep bms-bot-redis

# Restart Redis if needed
docker restart bms-bot-redis

# Check Redis logs
docker logs bms-bot-redis
```

### n8n Webhook Not Triggering

```bash
# Verify webhook URL in Bot Framework portal matches n8n
# Check n8n webhook node is activated
# Test webhook directly:
curl -X POST "https://n8n.runpod.io/webhook/abc/teams" \
  -H "Content-Type: application/json" \
  -d '{"type":"message","text":"test"}'
```

### BMS API Timeouts

```bash
# Check BMS API health
curl http://localhost:8000/health

# Check BMS API logs
tail -100 /workspace/logs/api.log

# Restart BMS API if needed
/workspace/scripts/manage_services.sh restart
```

---

## Sign-Off Checklist

Before marking T032 complete, verify:

- [ ] All 8 quickstart steps executed
- [ ] All 5 test scenarios passed (T010-T014)
- [ ] Validation report generated and reviewed
- [ ] No critical errors in logs
- [ ] Performance targets met (p95 < 3s)
- [ ] Documentation updated with any deviations

**Date**: _______________
**Validated by**: _______________
**Status**: PASS ☐ / FAIL ☐
