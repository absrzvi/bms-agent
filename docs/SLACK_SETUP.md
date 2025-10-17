# Slack Integration Setup Guide

Complete guide for setting up BMS Agent Slack integration.

## Overview

The BMS Agent Slack integration provides:
- **Slash Commands**: `/bms-search`, `/bms-search-hybrid`, `/bms-help`
- **Interactive Results**: Formatted with Slack Block Kit
- **Direct API Integration**: No n8n required
- **POC Mode**: Optional authentication

---

## Prerequisites

- Slack workspace admin access
- BMS Agent API running on accessible URL
- (Optional) Public URL or ngrok for webhooks

---

## Step 1: Create Slack App

### 1.1 Go to Slack API
Visit: https://api.slack.com/apps

### 1.2 Create New App
1. Click **"Create New App"**
2. Choose **"From scratch"**
3. App Name: `BMS Agent`
4. Select your workspace
5. Click **"Create App"**

---

## Step 2: Configure Slash Commands

### 2.1 Add Slash Commands
Go to **Features** → **Slash Commands** → **Create New Command**

#### Command 1: /bms-search
```
Command: /bms-search
Request URL: https://your-domain.com/slack/slash-command
Short Description: Search railway documentation with AI
Usage Hint: [search query]
```

#### Command 2: /bms-search-hybrid
```
Command: /bms-search-hybrid
Request URL: https://your-domain.com/slack/slash-command
Short Description: Hybrid search (semantic + keyword)
Usage Hint: [search query]
```

#### Command 3: /bms-help
```
Command: /bms-help
Request URL: https://your-domain.com/slack/slash-command
Short Description: Show BMS Agent help
Usage Hint: 
```

### 2.2 Save Commands
Click **"Save"** for each command

---

## Step 3: Configure OAuth & Permissions

### 3.1 Add Bot Token Scopes
Go to **Features** → **OAuth & Permissions** → **Scopes**

Add these **Bot Token Scopes**:
- `chat:write` - Send messages
- `commands` - Use slash commands
- `app_mentions:read` - Read @mentions (optional)

### 3.2 Install App to Workspace
1. Scroll to **OAuth Tokens**
2. Click **"Install to Workspace"**
3. Click **"Allow"**
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

---

## Step 4: Get Signing Secret

Go to **Settings** → **Basic Information** → **App Credentials**

Copy the **Signing Secret**

---

## Step 5: Configure BMS Agent

### 5.1 Set Environment Variables

```bash
# On your server
export SLACK_BOT_TOKEN="xoxb-your-token-here"
export SLACK_SIGNING_SECRET="your-signing-secret-here"
```

### 5.2 Add to Startup Script

Edit `/workspace/001-bms-agent/scripts/start_api.sh`:

```bash
#!/bin/bash
export SLACK_BOT_TOKEN="xoxb-your-token-here"
export SLACK_SIGNING_SECRET="your-signing-secret-here"

cd /workspace/001-bms-agent
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 5.3 Restart API

```bash
pkill -f "uvicorn api.main:app"
bash /workspace/001-bms-agent/scripts/start_api.sh
```

---

## Step 6: Configure Public URL

### Option A: Direct Public IP
If your server has a public IP:
```
https://your-ip:8000/slack/slash-command
```

### Option B: ngrok (Development)
```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# Start tunnel
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update Slack slash command URLs to:
# https://abc123.ngrok.io/slack/slash-command
```

### Option C: Cloudflare Tunnel
```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# Start tunnel
cloudflared tunnel --url http://localhost:8000
```

---

## Step 7: Test Integration

### 7.1 Test in Slack

In any channel:
```
/bms-help
```

Expected response:
```
BMS Agent - Railway Documentation Search

Available Commands:
• /bms-search [query] - Semantic search using AI
• /bms-search-hybrid [query] - Hybrid search (semantic + keyword)
• /bms-help - Show this help message

Examples:
• /bms-search business continuity planning
• /bms-search-hybrid railway safety procedures

Searching 448 indexed documents with 0.714 quality score
```

### 7.2 Test Search

```
/bms-search business continuity
```

Expected response:
```
🔍 Found 3 results for: business continuity

1. BMS-BCON-FOR-001-Business Continuity Response Template.docx
   📄 Type: docx | Quality: 0.85 | Relevance: 0.563
   Business continuity planning procedures for railway operations...

2. IT Disaster Notification & Recovery Process.pdf
   📄 Type: pdf | Quality: 0.72 | Relevance: 0.517
   Emergency response procedures for IT infrastructure...

---
Searched 448 documents | Powered by BMS Agent
```

---

## Step 8: Verify Health

### 8.1 Check Slack Integration Status

```bash
curl http://localhost:8000/slack/health
```

Expected response:
```json
{
  "status": "healthy",
  "slack_configured": true,
  "endpoints": [
    "/slack/slash-command",
    "/slack/events",
    "/slack/health"
  ]
}
```

---

## Troubleshooting

### Issue: "dispatch_failed" Error

**Cause**: Slack can't reach your webhook URL

**Solution**:
1. Verify API is running: `curl http://localhost:8000/health`
2. Check ngrok/tunnel is active
3. Verify URL in Slack app settings matches tunnel URL
4. Check firewall allows incoming connections

### Issue: "Invalid Signature" Error

**Cause**: Signing secret mismatch

**Solution**:
1. Verify `SLACK_SIGNING_SECRET` environment variable
2. Copy exact secret from Slack app settings
3. Restart API after setting environment variable

### Issue: No Results Returned

**Cause**: BMS API not responding

**Solution**:
1. Check API health: `curl http://localhost:8000/health`
2. Verify Qdrant is running: `curl http://localhost:6333/collections/nomad_bms_documents`
3. Check API logs: `tail -f /workspace/logs/api.log`

### Issue: Timeout Errors

**Cause**: Search taking too long

**Solution**:
1. Increase timeout in `slack_integration.py` (default: 30s)
2. Check Qdrant performance
3. Reduce result limit

---

## POC Mode (No Authentication)

For testing without Slack app setup:

### 1. Leave Environment Variables Empty
```bash
# Don't set these:
# export SLACK_BOT_TOKEN=""
# export SLACK_SIGNING_SECRET=""
```

### 2. Test with curl
```bash
curl -X POST http://localhost:8000/slack/slash-command \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "command=/bms-search&text=business continuity&user_name=test"
```

---

## Security Considerations

### Production Deployment

1. **Always set signing secret** to verify requests
2. **Use HTTPS** for webhook URLs
3. **Restrict IP access** if possible
4. **Monitor usage** via logs
5. **Rate limit** slash commands if needed

### Environment Variables

Store securely:
```bash
# Use systemd environment file
sudo nano /etc/systemd/system/bms-agent.service

[Service]
Environment="SLACK_BOT_TOKEN=xoxb-..."
Environment="SLACK_SIGNING_SECRET=..."
```

---

## Advanced Features

### Custom Response Formatting

Edit `slack_integration.py` → `format_search_results_for_slack()` to customize:
- Number of results shown
- Content preview length
- Metadata displayed
- Emoji and formatting

### Add More Commands

Add new slash commands in Slack app settings and handle in `handle_slash_command()`:

```python
if command == "/bms-stats":
    # Return statistics
    pass
```

### Interactive Buttons

Add action buttons to results:
```python
{
    "type": "actions",
    "elements": [
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "View Full Document"},
            "url": f"https://docs.example.com/{doc_id}"
        }
    ]
}
```

---

## Support

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/slack/health
- **Logs**: `/workspace/logs/api.log`

---

**Status**: ✅ Ready for deployment  
**Last Updated**: 2025-09-29  
**Version**: 1.0.0
