# MS Teams Bot Setup Guide

This guide walks you through setting up the MS Teams bot integration for the BMS Agent using Bot Framework REST API v3 and n8n workflows.

## Prerequisites

- MS Teams admin access or ability to add apps/bots to channels
- Azure account (for Bot Framework registration)
- n8n instance running at `/workspace/n8n` (setup via `scripts/start-n8n.sh`)
- BMS API running at `http://localhost:8000`
- Redis running at `http://localhost:6379`

---

## Step 1: Register Bot with Bot Framework

### 1.1 Create Bot Registration

1. Go to [Bot Framework Portal](https://dev.botframework.com/)
2. Click **"Create a Bot"** → **"Register"**
3. Fill in bot details:
   - **Display name**: `BMS Agent Bot`
   - **Bot handle**: `bms-agent-bot` (must be unique)
   - **Description**: `Railway documentation assistant for MS Teams`
4. Click **"Create Microsoft App ID and password"**

### 1.2 Generate App Password

1. On the registration page, click **"Create New Password"**
2. **IMPORTANT**: Copy the generated password immediately (you won't see it again)
3. Save both:
   - **App ID** (also called Bot ID): `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - **App Password**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 1.3 Configure Messaging Endpoint

1. In Bot Framework Portal, find **"Configuration"** section
2. Set **Messaging endpoint**:
   ```
   https://your-n8n-domain.com/webhook/teams
   ```
   - For local testing: Use ngrok or similar tunnel service
   - For production: Use your actual n8n webhook URL

3. Enable **MS Teams** channel:
   - Click **"Channels"** → **"Microsoft Teams"**
   - Accept terms and click **"Save"**

---

## Step 2: Configure n8n Credentials

### 2.1 Add Bot Framework Credentials to n8n

1. Open n8n editor: `http://localhost:5678`
2. Go to **"Credentials"** → **"New"**
3. Select **"HTTP Header Auth"** (we'll use this for Bot Framework REST API v3)
4. Create credential named **"Bot Framework Auth"**:
   - **Name**: `Authorization`
   - **Value**: `Bearer <leave-empty-for-now>`
   - Note: Bearer token is generated dynamically by workflows

### 2.2 Store Bot Credentials as Environment Variables

Add to `/workspace/002-n8n/config/n8n.env`:

```bash
# MS Teams Bot Framework REST API v3
BOT_APP_ID=your-app-id-here
BOT_APP_PASSWORD=your-app-password-here
TEAMS_WEBHOOK_URL=https://your-n8n-domain.com/webhook/teams

# Service URLs (usually auto-detected from incoming messages)
TEAMS_SERVICE_URL=https://smba.trafficmanager.net/amer/
```

Reload n8n:
```bash
/workspace/002-n8n/scripts/manage-services.sh restart n8n
```

---

## Step 3: Deploy n8n Workflows

### 3.1 Import Workflows to n8n

Run the deployment script:
```bash
cd /workspace/002-n8n
./scripts/deploy-workflows.sh
```

This imports all 6 workflows:
1. `main-bot-handler.json` - Primary message routing
2. `query-analyzer.json` - Intent classification
3. `bms-api-caller.json` - BMS API integration
4. `context-manager.json` - Conversation history
5. `similar-query-detector.json` - Query similarity detection
6. `admin-commands.json` - Whitelist management
7. `health-check.json` - Health monitoring

### 3.2 Verify Workflow Import

1. Open n8n editor: `http://localhost:5678`
2. Check **"Workflows"** section
3. Ensure all 7 workflows are listed
4. Open **"main-bot-handler"** workflow
5. Verify webhook trigger URL matches Bot Framework messaging endpoint

---

## Step 4: Configure Whitelist

### 4.1 Initialize Admin Users

Edit `/workspace/002-n8n/config/whitelist.json`:

```json
{
  "admins": [
    "29:1abc123def456..."  // Your MS Teams user ID (see below)
  ],
  "channels": []
}
```

### 4.2 Find Your MS Teams User ID

**Method 1: From MS Teams message**
1. Send any message in a test channel
2. Check n8n execution logs for incoming webhook payload
3. Look for `from.id` field

**Method 2: Using Microsoft Graph Explorer**
1. Go to [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
2. Sign in with your account
3. Run: `GET https://graph.microsoft.com/v1.0/me`
4. Copy the `id` field

---

## Step 5: Add Bot to MS Teams

### 5.1 Add Bot Connector to Teams

**Option A: Direct Channel Addition (Recommended for POC)**
1. Open MS Teams
2. Go to target channel → **"..."** → **"Connectors"**
3. Search for **"Incoming Webhook"** or **"Bot"**
4. Follow prompts to add your bot (use Bot ID from Step 1.2)

**Option B: Via App Studio (Full Featured)**
1. In MS Teams, search for **"App Studio"**
2. Install App Studio if not present
3. Go to **"Manifest editor"** → **"Create a new app"**
4. Fill in app details:
   - **App ID**: Use Bot App ID from Step 1.2
   - **Manifest version**: 1.11
5. Under **"Capabilities"** → **"Bots"**:
   - Select **"Setup"**
   - Enter Bot ID from Step 1.2
   - Scope: **Personal**, **Team**, **Group Chat**
6. **"Test and distribute"** → **"Install"**

### 5.2 Test Bot Connection

1. In MS Teams, start a direct chat with the bot
2. Send: `/help`
3. Expected response:
   ```
   🤖 BMS Teams Bot - Available Commands

   I help you search railway documentation...

   [List of commands from response-templates.json]
   ```

4. If you get an error: **"This bot is currently in POC phase. Contact your admin to request access."**
   - Your user ID is not in the admins list
   - Add it to `whitelist.json` (Step 4.1)

---

## Step 6: Whitelist Channels (Admin)

### 6.1 Add Channel to Whitelist

As an admin user, in any MS Teams channel:

```
/admin allow #operations-team
```

Expected response:
```
✓ Access granted to #operations-team
```

### 6.2 Verify Whitelist

```
/admin list
```

Expected response:
```
📋 Channel Whitelist (2 channels)
• #operations-team (added by John Doe on 2025-10-06)
• #safety-team (added by Jane Smith on 2025-10-05)

👤 Administrators (2)
• John Doe (29:1abc...)
• Jane Smith (29:2def...)
```

---

## Step 7: Test End-to-End Flow

### 7.1 Natural Language Query

In whitelisted channel:
```
What are the emergency brake procedures for Class 395 trains?
```

Expected:
1. Typing indicator appears ("BMS Agent Bot is typing...")
2. Response within 3 seconds with answer + citations

### 7.2 Document Upload

Send message with PDF attachment or:
```
/upload
[Attach safety-procedures.pdf]
```

Expected response:
```
✓ Document uploaded successfully!
Document ID: abc-123-def-456
Status: Processing
Use `/status abc-123-def-456` to check progress.
```

### 7.3 Search History

```
/history
```

Expected response:
```
📜 Your Search History (Last 7 Days)
• 2025-10-06 14:32 - "emergency brake procedures" (5 results)
• 2025-10-05 09:15 - "VLAN configuration" (3 results)
...
```

---

## Troubleshooting

### Bot Not Responding

**Check 1: n8n webhook is receiving messages**
```bash
# View n8n execution logs
tail -f /workspace/n8n/.n8n/logs/n8n.log
```

**Check 2: Whitelist configuration**
```bash
cat /workspace/002-n8n/config/whitelist.json
```

**Check 3: Redis connectivity**
```bash
redis-cli ping  # Should return PONG
```

### "BMS-search tool cannot be accessed"

**Check BMS API is running:**
```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"status": "healthy", "version": "1.0.0"}
```

### Typing Indicator Not Showing

**Check Bot Framework credentials:**
```bash
echo $BOT_APP_ID
echo $BOT_APP_PASSWORD
```

Both should be set. If not, review Step 2.2.

### Messages Not Persisting in History

**Check Redis TTL:**
```bash
redis-cli
> GET conversation:abc-123
> TTL conversation:abc-123  # Should return ~604800 (7 days)
```

---

## Security Considerations

### POC Phase (Current)
- Whitelist enforced (FR-023)
- 20 user limit (FR-026)
- 7-day data retention (FR-027)
- Admin-only whitelist management (FR-024)

### Production Checklist
- [ ] Enable API key authentication (currently optional)
- [ ] Implement rate limiting (60 req/min per IP)
- [ ] Setup HTTPS for webhook endpoint (required for production)
- [ ] Review and rotate Bot Framework app password (90-day cycle)
- [ ] Enable audit logging for admin commands
- [ ] Configure Redis persistence with encryption at rest

---

## Next Steps

1. **Review `/workspace/002-n8n/docs/troubleshooting.md`** for common issues
2. **Monitor performance** via n8n execution dashboard
3. **Collect user feedback** during POC phase
4. **Scale testing** - see tasks.md T015b for 5x load validation
5. **Production deployment** - requires Prometheus/Grafana per constitution §8

---

## Reference Links

- [Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [MS Teams Bot Development](https://docs.microsoft.com/en-us/microsoftteams/platform/bots/what-are-bots)
- [n8n Documentation](https://docs.n8n.io/)
- [BMS API Reference](/workspace/001-bms-agent/README.md)

---

**Support**: For issues during POC, check `docs/troubleshooting.md` or review n8n execution logs.

**Constitution Compliance**: This setup follows constitution §11 (RunPod persistence), §8 (POC monitoring), §4 (60% test coverage for POC).
