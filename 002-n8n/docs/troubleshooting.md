# MS Teams Bot Troubleshooting Guide

This guide covers common issues encountered with the BMS Agent MS Teams bot and their solutions.

---

## Quick Diagnostic Commands

Run these to check system health:

```bash
# Check all services status
/workspace/002-n8n/scripts/manage-services.sh status

# View n8n logs
tail -100 /workspace/n8n/.n8n/logs/n8n.log

# Test Redis connectivity
redis-cli ping

# Check BMS API health
curl http://localhost:8000/health

# View recent n8n executions
curl http://localhost:5678/rest/executions?limit=10
```

---

## Issue Categories

- [Bot Not Responding](#bot-not-responding)
- [Authentication Errors](#authentication-errors)
- [Webhook Issues](#webhook-issues)
- [Search/Query Problems](#searchquery-problems)
- [Document Upload Failures](#document-upload-failures)
- [Context/History Issues](#contexthistory-issues)
- [Performance Problems](#performance-problems)
- [Whitelist/Access Control](#whitelistaccess-control)

---

## Bot Not Responding

### Symptom
Messages sent to bot in MS Teams receive no response

### Diagnosis

**Step 1: Check n8n is running**
```bash
ps aux | grep n8n
curl http://localhost:5678/healthz
```

**Step 2: Check webhook is registered**
```bash
# In n8n, check main-bot-handler workflow
# Webhook URL should match Bot Framework messaging endpoint
```

**Step 3: Test webhook manually**
```bash
curl -X POST http://localhost:5678/webhook/teams \
  -H "Content-Type: application/json" \
  -d '{"type":"message","text":"test","from":{"id":"test-user"},"conversation":{"id":"test-conv"}}'
```

### Solutions

**Solution 1: Restart n8n**
```bash
/workspace/002-n8n/scripts/manage-services.sh restart n8n
```

**Solution 2: Redeploy workflows**
```bash
cd /workspace/002-n8n
./scripts/deploy-workflows.sh
```

**Solution 3: Check Bot Framework messaging endpoint**
- Go to [Bot Framework Portal](https://dev.botframework.com/)
- Verify messaging endpoint matches n8n webhook URL
- Ensure HTTPS if in production (use ngrok for local testing)

---

## Authentication Errors

### Symptom
Error: "401 Unauthorized" or "403 Forbidden" in n8n logs

### Diagnosis

**Check Bot credentials:**
```bash
echo $BOT_APP_ID
echo $BOT_APP_PASSWORD

# Should both return non-empty values
```

**Verify credentials in Bot Framework Portal:**
- Login to https://dev.botframework.com/
- Check App ID matches environment variable
- Generate new password if needed

### Solutions

**Solution 1: Update credentials**
```bash
# Edit /workspace/002-n8n/config/n8n.env
BOT_APP_ID=your-actual-app-id
BOT_APP_PASSWORD=your-actual-password

# Restart n8n
/workspace/002-n8n/scripts/manage-services.sh restart n8n
```

**Solution 2: Regenerate Bot password**
1. Go to Bot Framework Portal
2. Find your bot → "Configuration"
3. Click "Manage" next to App ID
4. "Certificates & secrets" → "New client secret"
5. Copy new password immediately
6. Update `BOT_APP_PASSWORD` in n8n.env
7. Restart n8n

---

## Webhook Issues

### Symptom
Bot Framework shows "Endpoint not reachable" or webhook timeout

### Diagnosis

**Check webhook is accessible:**
```bash
# From external machine (not localhost)
curl -X POST https://your-domain.com/webhook/teams \
  -H "Content-Type: application/json" \
  -d '{"type":"message","text":"ping"}'
```

**Check firewall/network:**
```bash
# Ensure port is open (if using direct IP)
sudo netstat -tulpn | grep 5678
```

### Solutions

**Solution 1: Use ngrok for local testing**
```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-*.tgz
./ngrok http 5678

# Copy HTTPS URL (e.g., https://abc123.ngrok.io)
# Update Bot Framework messaging endpoint to:
# https://abc123.ngrok.io/webhook/teams
```

**Solution 2: Check n8n webhook configuration**
```bash
# In n8n UI, open main-bot-handler workflow
# Ensure webhook trigger is:
# - Method: POST
# - Path: /webhook/teams
# - Response Mode: "When Last Node Finishes"
```

**Solution 3: Verify WEBHOOK_URL environment variable**
```bash
echo $TEAMS_WEBHOOK_URL
# Should match Bot Framework messaging endpoint
```

---

## Search/Query Problems

### Symptom 1: "BMS-search tool cannot be accessed at this time"

**Diagnosis:**
```bash
# Check BMS API is running
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

**Solution:**
```bash
# Start BMS API
cd /workspace/001-bms-agent
source /workspace/bms-api-venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Or use service manager
/workspace/001-bms-agent/scripts/manage_services.sh start
```

### Symptom 2: "No results found" for valid queries

**Diagnosis:**
```bash
# Check Qdrant has documents
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'

# Should return > 0
```

**Solution:**
```bash
# Verify Qdrant is running
curl http://localhost:6333/collections

# If empty, re-index documents
cd /workspace/001-bms-agent
python scripts/batch_process_incoming.py
```

### Symptom 3: Response takes > 3 seconds

**Diagnosis:**
```bash
# Check n8n execution time in logs
tail -50 /workspace/n8n/.n8n/logs/n8n.log | grep "execution time"

# Check BMS API response time
time curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"test query"}'
```

**Solution:**
```bash
# Optimize BMS API (if slow)
cd /workspace/001-bms-agent
python scripts/optimize_qdrant_index.py

# Reduce timeout in bms-api-caller workflow (if needed)
# Default: 2.5s
```

---

## Document Upload Failures

### Symptom
Upload returns error or gets stuck in "processing" state

### Diagnosis

**Check file type:**
```bash
# Supported: PDF, CSV, XLSX, XLS, TXT, MD, DOCX, PPTX
# Invalid files return: "Invalid file type. Supported: ..."
```

**Check file size:**
```bash
# Max size: 1GB (1073741824 bytes)
ls -lh uploaded-file.pdf

# If > 1GB, returns: "File too large"
```

**Check upload job status:**
```bash
# In MS Teams: /status [document_id]
# Or directly via Redis:
redis-cli GET upload:abc-123-def-456
```

### Solutions

**Solution 1: Retry upload**
- Ensure file is < 1GB
- Use supported file format
- Try `/upload` command instead of direct attachment

**Solution 2: Check BMS API upload endpoint**
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload/async \
  -F "file=@test.pdf" \
  -F "profile=RAILWAY"

# Should return: {"job_id":"abc-123","status":"queued"}
```

**Solution 3: Check async upload queue**
```bash
curl http://localhost:8000/api/v1/documents/queue/stats

# Shows pending/processing/completed counts
```

---

## Context/History Issues

### Symptom 1: "Conversation history is temporarily unavailable"

**Diagnosis:**
```bash
# Check Redis connectivity
redis-cli ping

# Should return: PONG
```

**Solution:**
```bash
# Restart Redis
/workspace/002-n8n/scripts/manage-services.sh restart redis

# Or if Redis not installed:
/workspace/002-n8n/scripts/init-storage.sh
```

### Symptom 2: Context not persisting between messages

**Diagnosis:**
```bash
# Check conversation TTL
redis-cli
> KEYS conversation:*
> TTL conversation:abc-123

# Should return ~604800 (7 days)
```

**Solution:**
```bash
# Verify context-manager workflow is deployed
curl http://localhost:5678/rest/workflows | jq '.[] | select(.name=="Context Manager")'

# If missing, redeploy:
/workspace/002-n8n/scripts/deploy-workflows.sh
```

### Symptom 3: History shows queries from > 7 days ago

**Diagnosis:**
```bash
# Check cleanup cron job
crontab -l | grep cleanup-expired

# Should run daily at 2 AM
```

**Solution:**
```bash
# Run cleanup manually
/workspace/002-n8n/scripts/cleanup-expired.sh

# Setup automated cleanup
(crontab -l ; echo "0 2 * * * /workspace/002-n8n/scripts/cleanup-expired.sh") | crontab -
```

---

## Performance Problems

### Symptom
Response times > 3 seconds or bot feels sluggish

### Diagnosis

**Check system resources:**
```bash
# CPU usage
top -n 1 | head -20

# Memory usage
free -h

# Redis memory
redis-cli INFO memory | grep used_memory_human
```

**Check n8n execution queue:**
```bash
curl http://localhost:5678/rest/executions?status=running

# High number of concurrent executions = bottleneck
```

### Solutions

**Solution 1: Optimize BMS API**
```bash
cd /workspace/001-bms-agent
python scripts/optimize_qdrant_index.py

# Enable caching in BMS API config
```

**Solution 2: Increase n8n workers**
```bash
# Edit /workspace/002-n8n/config/n8n.env
N8N_CONCURRENCY_PRODUCTION=5

# Restart n8n
/workspace/002-n8n/scripts/manage-services.sh restart n8n
```

**Solution 3: Monitor performance metrics**
```bash
# Run load test (from tests/)
cd /workspace/002-n8n
npm test tests/performance/load-test.js

# Check p95 response time
```

---

## Whitelist/Access Control

### Symptom 1: "This bot is currently in POC phase. Contact your admin to request access."

**Diagnosis:**
User's channel is not whitelisted

**Solution (Admin):**
```
/admin allow #channel-name
```

**Solution (Manual):**
```bash
# Edit whitelist.json
vim /workspace/002-n8n/config/whitelist.json

# Add channel:
{
  "channels": [
    {
      "whitelist_id": "unique-uuid",
      "channel_id": "19:abc@thread.tacv2",
      "channel_name": "#new-channel",
      "added_by": "admin-user-id",
      "added_at": "2025-10-06T12:00:00Z",
      "status": "active"
    }
  ]
}
```

### Symptom 2: "You don't have admin permissions"

**Diagnosis:**
User trying to run `/admin` command is not in admins list

**Solution:**
```bash
# Edit whitelist.json
vim /workspace/002-n8n/config/whitelist.json

# Add user to admins:
{
  "admins": [
    "29:existing-admin-id",
    "29:new-admin-id"
  ]
}
```

### Symptom 3: Whitelist changes not taking effect

**Diagnosis:**
Whitelist cache not refreshed (60s TTL)

**Solution:**
```bash
# Wait 60 seconds for cache to refresh
# Or restart n8n to force reload:
/workspace/002-n8n/scripts/manage-services.sh restart n8n
```

---

## n8n Workflow Errors

### Symptom
Workflow execution fails with error in n8n logs

### Common Errors

**Error: "Cannot find module 'redis'"**
```bash
# Solution: Install Node.js dependencies
cd /workspace/002-n8n
npm install
```

**Error: "ECONNREFUSED localhost:6379"**
```bash
# Solution: Start Redis
/workspace/002-n8n/scripts/manage-services.sh start redis
```

**Error: "ECONNREFUSED localhost:8000"**
```bash
# Solution: Start BMS API
cd /workspace/001-bms-agent
/workspace/001-bms-agent/scripts/manage_services.sh start
```

**Error: "Workflow not found"**
```bash
# Solution: Redeploy workflows
/workspace/002-n8n/scripts/deploy-workflows.sh
```

---

## Logging & Debugging

### Enable Debug Logging

**n8n debug mode:**
```bash
# Edit /workspace/002-n8n/config/n8n.env
N8N_LOG_LEVEL=debug

# Restart n8n
/workspace/002-n8n/scripts/manage-services.sh restart n8n
```

**View logs:**
```bash
# n8n logs
tail -f /workspace/n8n/.n8n/logs/n8n.log

# BMS API logs
tail -f /workspace/logs/api.log

# Redis logs (if configured)
tail -f /workspace/logs/redis.log
```

### Test Individual Workflows

**Via n8n UI:**
1. Open workflow in n8n editor
2. Click "Execute Workflow"
3. Provide test data
4. Check execution results

**Via curl (webhook-triggered workflows):**
```bash
# Test main-bot-handler
curl -X POST http://localhost:5678/webhook/teams \
  -H "Content-Type: application/json" \
  -d @test-payload.json

# Test similar-query-detector
curl -X POST http://localhost:5678/webhook/similar-query-check \
  -H "Content-Type: application/json" \
  -d '{"query":"test","user_id":"test-user","conversation_id":"test-conv"}'
```

---

## Emergency Recovery

### Nuclear Option: Full Reset

**WARNING: This will delete all conversation history and whitelist**

```bash
# Stop all services
/workspace/002-n8n/scripts/manage-services.sh stop

# Clear Redis data
redis-cli FLUSHALL

# Reinitialize
/workspace/002-n8n/scripts/init-storage.sh

# Redeploy workflows
/workspace/002-n8n/scripts/deploy-workflows.sh

# Restart services
/workspace/002-n8n/scripts/manage-services.sh start
```

### Backup Before Reset

```bash
# Backup whitelist
cp /workspace/002-n8n/config/whitelist.json /workspace/backups/whitelist-backup.json

# Backup Redis data
redis-cli --rdb /workspace/backups/redis-dump.rdb

# Export n8n workflows
curl http://localhost:5678/rest/workflows > /workspace/backups/n8n-workflows.json
```

---

## Getting Help

### Check Documentation
1. `/workspace/002-n8n/docs/setup-ms-teams.md` - Setup guide
2. `/workspace/002-n8n/docs/QUICKSTART.md` - Quick reference
3. `/workspace/specs/002-create-a-microsoft/` - Design docs

### Check Constitution Compliance
- POC exceptions documented in spec.md with "POC DECISION" markers
- Constitution: `/workspace/.specify/memory/constitution.md`

### Run Health Check
```bash
# Automated health check for all services
/workspace/002-n8n/scripts/manage-services.sh status

# Or use health-check workflow (once deployed)
curl http://localhost:5678/webhook/health
```

---

## Known Issues (POC Phase)

1. **Simultaneous multi-user queries**: May experience queuing delays (deferred to production per spec.md edge case)
2. **Query length > 1000 chars**: Enforced limit per FR-031, returns error
3. **5x load testing**: Not executed in POC, scheduled for post-POC per T015b

---

**Last Updated**: 2025-10-06
**Spec Reference**: `/workspace/specs/002-create-a-microsoft/spec.md`
**Constitution**: `/workspace/.specify/memory/constitution.md`
