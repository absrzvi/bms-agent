# MS Teams Bot - Quick Start Guide

Get the MS Teams bot running in **15 minutes**.

## Prerequisites Checklist

- [ ] RunPod instance with BMS Agent API running
- [ ] n8n installed (`npm install -g n8n`)
- [ ] Redis installed (`apt-get install redis-server`)
- [ ] Ollama with mistral-nemo:12b-instruct model
- [ ] MS Teams admin access

## Step 1: Start Services (2 minutes)

```bash
# Start all MS Teams bot services
cd /workspace/002-n8n
./scripts/manage-services.sh start

# Verify services
./scripts/manage-services.sh health
```

Expected output:
```
✓ Redis is running (PID: xxxx)
  ✓ Redis responding to ping
✓ n8n is running (PID: xxxx)
  ✓ n8n UI accessible
✓ BMS API is running
  ✓ Health endpoint responding
```

## Step 2: Deploy Workflows (3 minutes)

```bash
# Deploy workflows to n8n
./scripts/deploy-workflows.sh
```

**Manual Step**: Open n8n UI at http://localhost:5678

For each workflow (5 total):
1. Click on workflow name
2. Toggle "Active" switch to ON (top-right)
3. Verify no error indicators

Workflows to activate:
- ✅ MS Teams Bot - Main Handler
- ✅ MS Teams Bot - Query Analyzer
- ✅ MS Teams Bot - BMS API Caller
- ✅ MS Teams Bot - Context Manager
- ✅ MS Teams Bot - Admin Commands

## Step 3: Get Webhook URL (1 minute)

1. In n8n UI, open **MS Teams Bot - Main Handler** workflow
2. Click on the first node: **MS Teams Webhook**
3. Click **"Test step"** or **"Execute node"**
4. Copy the **Production URL** (looks like: `http://localhost:5678/webhook/teams-bot-webhook`)

**Save this URL** - you'll need it for MS Teams configuration.

## Step 4: Configure Whitelist (2 minutes)

```bash
# Edit whitelist configuration
nano /workspace/002-n8n/config/whitelist.json
```

Add your MS Teams user ID and channel:

```json
{
  "admins": [
    {
      "id": "YOUR_AAD_OBJECT_ID",
      "name": "Your Name",
      "aadObjectId": "YOUR_AAD_OBJECT_ID"
    }
  ],
  "channels": [
    {
      "id": "YOUR_TEAMS_CHANNEL_ID",
      "name": "#your-channel-name",
      "teamsChannelId": "YOUR_TEAMS_CHANNEL_ID",
      "added_by": "YOUR_AAD_OBJECT_ID",
      "added_at": "2025-10-06T00:00:00Z"
    }
  ]
}
```

**Finding your IDs**:
- AAD Object ID: Azure AD → Users → Your Profile
- Teams Channel ID: Teams → Channel → More Options → Get link to channel

Save and exit (`Ctrl+X`, `Y`, `Enter`)

## Step 5: Configure MS Teams (5 minutes)

### Option A: Incoming Webhook (Easiest for POC)

1. Open MS Teams
2. Go to your target channel
3. Click **...** (More options) → **Connectors**
4. Find **Incoming Webhook** → **Configure**
5. Name: `BMS Agent Bot`
6. Upload icon (optional)
7. Click **Create**
8. **Copy the webhook URL**

9. In n8n UI, open **MS Teams Bot - Main Handler**
10. Update the **Send Teams Response** node with your webhook URL

### Option B: Bot Framework (Production)

See [DEPLOYMENT.md](DEPLOYMENT.md) for full Bot Framework setup.

## Step 6: Test Bot (2 minutes)

### Test 1: Help Command

In MS Teams channel, type:
```
/help
```

Expected response: Help message with list of commands

### Test 2: Ask Question

```
/ask What are emergency brake procedures?
```

Expected response: Answer with source citations within 3 seconds

### Test 3: Search

```
/search VLAN configuration
```

Expected response: List of relevant documents

### Test 4: Document Upload

Attach a PDF file to a message or type:
```
/upload
```
Then attach a file.

Expected response: Upload confirmation with document ID

## Troubleshooting

### Bot Not Responding

**Check 1**: Services running?
```bash
./scripts/manage-services.sh status
```

**Check 2**: Workflows active?
- Open http://localhost:5678
- Verify all 5 workflows show green "Active" indicator

**Check 3**: Webhook URL correct?
- Verify n8n webhook URL matches MS Teams configuration

**Check 4**: Channel whitelisted?
```bash
cat /workspace/002-n8n/config/whitelist.json
```

### "Access Denied" Error

Your channel is not whitelisted. Either:

**Option 1**: Add manually to whitelist.json (see Step 4)

**Option 2**: Use admin command (if you're an admin):
```
/admin allow #your-channel-name
```

### BMS API Not Responding

```bash
# Start BMS API
/workspace/001-bms-agent/scripts/manage_services.sh start api

# Verify
curl http://localhost:8000/health
```

### Redis Connection Error

```bash
# Restart Redis
./scripts/manage-services.sh restart redis

# Test
redis-cli ping
```

### View Logs

```bash
# n8n workflow logs
tail -f /workspace/logs/n8n.log

# Redis logs
tail -f /workspace/logs/redis.log

# BMS API logs
tail -f /workspace/logs/api.log
```

## Next Steps

### Daily Operations

```bash
# Start services (after pod restart)
./scripts/manage-services.sh start

# Check health
./scripts/manage-services.sh health

# Cleanup old conversations
./scripts/cleanup-expired.sh
```

### Admin Tasks

```bash
# Add channel to whitelist
# In MS Teams, send:
/admin allow #new-channel

# Remove channel
/admin revoke #old-channel

# List all whitelisted channels
/admin list
```

### Monitoring

```bash
# View conversation statistics
./scripts/cleanup-expired.sh stats

# Check workflow execution
# Open n8n UI: http://localhost:5678
# Go to Executions tab
```

## Performance Tips

### Optimize Response Time

1. **Keep Ollama warm**: Send a test query on startup
2. **Monitor Redis**: Use `redis-cli INFO memory` to check usage
3. **Restart n8n weekly**: Prevents memory leaks

### Scaling for More Users

If you exceed 20 concurrent users:

1. Increase Redis pool size:
   ```bash
   export DB_SQLITE_POOL_SIZE=10
   ```

2. Add more n8n runners:
   ```bash
   export N8N_RUNNERS_ENABLED=true
   ```

3. Monitor response times in n8n Executions tab

## Getting Help

### Check Documentation

- [README.md](../README.md) - Full documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

### Debug Mode

Enable debug logging:
```bash
export N8N_LOG_LEVEL=debug
./scripts/manage-services.sh restart n8n
```

### Support Channels

- View n8n execution logs in UI: http://localhost:5678/executions
- Check Redis data: `redis-cli --scan --pattern "conversation:*"`
- Test BMS API directly: `curl http://localhost:8000/health`

## Success Criteria

You're ready for production when:

- [ ] All 5 workflows active in n8n
- [ ] Health check passes
- [ ] Bot responds to `/help` in <1 second
- [ ] Bot answers questions in <3 seconds
- [ ] Document uploads complete successfully
- [ ] Admin commands work
- [ ] Conversation context persists for 7 days

**Congratulations! Your MS Teams Bot is ready for use.** 🎉
