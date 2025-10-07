# MS Teams Bot Setup - Webhook Approach (No MS Teams Node Required)

**Date:** 2025-10-07
**Approach:** Direct Bot Framework REST API via Webhooks
**Advantage:** No n8n credential issues, full control over authentication

---

## Overview

This approach bypasses the n8n MS Teams node entirely and uses:
1. **n8n Webhook** to receive messages from Azure Bot Service
2. **HTTP Request nodes** to authenticate with Azure AD
3. **Bot Framework REST API** to send responses back to Teams

---

## Prerequisites

✅ You already have:
- Azure Bot Service registered
- Client ID (App ID): `BOT_APP_ID`
- Client Secret (App Password): `BOT_APP_PASSWORD`
- n8n running with public URL: `https://nqz5l77nsrdkyt-5678.proxy.runpod.net/`

---

## Step 1: Configure Environment Variables in n8n

### Option A: Via n8n UI
1. Go to n8n Settings → Environments
2. Add these variables:
   ```
   BOT_APP_ID=<your-client-id>
   BOT_APP_PASSWORD=<your-client-secret>
   ```

### Option B: Via Environment File
Edit `/workspace/002-n8n/config/n8n.env`:
```bash
BOT_APP_ID=your-azure-app-id-here
BOT_APP_PASSWORD=your-azure-app-secret-here
```

Then restart n8n:
```bash
/workspace/scripts/manage_services.sh restart
```

---

## Step 2: Import Webhook Workflow into n8n

1. **Go to n8n UI:** https://nqz5l77nsrdkyt-5678.proxy.runpod.net/

2. **Import workflow:**
   - Click "Workflows" → "Import from file"
   - Select: `/workspace/002-n8n/workflows/teams-webhook-bot-handler.json`
   - Click "Import"

3. **Activate the workflow:**
   - Open the imported workflow
   - Click the "Active" toggle in the top right

4. **Get webhook URL:**
   - Click on the "Teams Message Webhook" node
   - Copy the webhook URL (should be like):
     ```
     https://nqz5l77nsrdkyt-5678.proxy.runpod.net/webhook/teams-bot
     ```

---

## Step 3: Configure Azure Bot Service Messaging Endpoint

1. **Go to Azure Portal:** https://portal.azure.com

2. **Navigate to your Bot Resource:**
   - Search for your bot name
   - Click on the Bot Service resource

3. **Configure Messaging Endpoint:**
   - Go to **Configuration** (left sidebar)
   - Under **Messaging endpoint**, paste your n8n webhook URL:
     ```
     https://nqz5l77nsrdkyt-5678.proxy.runpod.net/webhook/teams-bot
     ```
   - Click **Apply** to save

4. **Verify Bot is enabled for Teams:**
   - Go to **Channels** (left sidebar)
   - Ensure **Microsoft Teams** is listed and enabled
   - If not, click "Add a channel" → "Microsoft Teams"

---

## Step 4: Test the Bot

### Test in Teams:

1. **Add bot to Teams:**
   - Open Microsoft Teams
   - Go to "Apps"
   - Search for your bot name
   - Click "Add"

2. **Send test message:**
   ```
   Hello, what railway safety procedures are available?
   ```

3. **Expected behavior:**
   - Bot shows "typing..." indicator
   - Bot responds with answer from BMS Agent
   - Response includes sources with relevance scores

### Check n8n Execution Logs:

1. Go to n8n → "Executions"
2. Find the latest execution of "MS Teams Webhook Bot Handler"
3. Verify each step completed successfully

---

## How the Authentication Works

### Bot Framework OAuth 2.0 Flow:

```
1. Teams sends message → n8n webhook
2. n8n requests access token from Azure AD:
   POST https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token
   Body:
     grant_type=client_credentials
     client_id={BOT_APP_ID}
     client_secret={BOT_APP_PASSWORD}
     scope=https://api.botframework.com/.default

3. Azure AD returns access token (valid for ~1 hour)
4. n8n uses token to send reply via Bot Framework API:
   POST {serviceUrl}/v3/conversations/{conversationId}/activities
   Header: Authorization: Bearer {access_token}
```

**No manual credential configuration needed in n8n!**

---

## Workflow Node Breakdown

The webhook workflow has 11 nodes:

1. **Teams Message Webhook** - Receives incoming messages
2. **Parse Teams Activity** - Extracts message text, user info, conversation ID
3. **Is Valid Message?** - Filters out non-message activities
4. **Get Bot Framework Token** - Authenticates with Azure AD
5. **Combine Token with Message** - Merges token with message data
6. **Prepare Typing Indicator** - Creates typing activity
7. **Send Typing Indicator** - Shows "typing..." in Teams
8. **Query BMS Agent** - Calls BMS API with user query
9. **Format Response** - Formats answer for Teams (with sources)
10. **Send Reply to Teams** - Posts message via Bot Framework API
11. **Respond to Bot Framework** - Acknowledges receipt to Azure

---

## Advanced: Adding Features

### 1. Channel Whitelist Validation

Add after "Parse Teams Activity" node:

```javascript
// Check if channel is allowed
const { getWhitelistManager } = require('/workspace/002-n8n/lib/whitelist');
const whitelist = getWhitelistManager();

const channelId = $json.conversationId;
const isAllowed = whitelist.isChannelAllowed(channelId);

if (!isAllowed) {
  return {
    json: {
      ...$json,
      isMessage: false,
      rejectReason: 'Channel not whitelisted'
    }
  };
}

return { json: $json };
```

### 2. Context Management with Redis

Add before "Query BMS Agent" node:

```javascript
// Store conversation context in Redis
const { getRedisClient } = require('/workspace/002-n8n/lib/redis-client');
const redisClient = getRedisClient();

const conversationId = $json.conversationId;
const messageText = $json.messageText;

// Store last 5 messages for context
await redisClient.execute(
  async (client) => {
    const key = `conversation:${conversationId}:history`;
    await client.lPush(key, messageText);
    await client.lTrim(key, 0, 4); // Keep only last 5
    await client.expire(key, 3600); // 1 hour TTL
  },
  null
);

return { json: $json };
```

### 3. File Upload Handling

Add after "Parse Teams Activity" node:

```javascript
// Check for attachments
const activity = $json.rawActivity;

if (activity.attachments && activity.attachments.length > 0) {
  const files = activity.attachments.filter(att =>
    att.contentType.startsWith('application/')
  );

  if (files.length > 0) {
    return {
      json: {
        ...$json,
        hasFiles: true,
        files: files.map(f => ({
          name: f.name,
          url: f.contentUrl,
          type: f.contentType
        }))
      }
    };
  }
}

return { json: $json };
```

---

## Troubleshooting

### Issue: Bot doesn't respond

**Check:**
1. Workflow is active in n8n
2. Webhook URL is correct in Azure Bot Service
3. Environment variables are set (`BOT_APP_ID`, `BOT_APP_PASSWORD`)

**Verify:**
```bash
# Check n8n is running
curl http://localhost:5678/healthz

# Check environment variables in n8n
# (Look at workflow execution logs for "Get Bot Framework Token" step)
```

### Issue: Authentication fails (401 Unauthorized)

**Possible causes:**
- Incorrect `BOT_APP_ID` or `BOT_APP_PASSWORD`
- Token expired (tokens last ~1 hour, workflow requests new token for each message)

**Verify credentials:**
```bash
# Test token generation manually
curl -X POST https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_APP_ID" \
  -d "client_secret=YOUR_APP_SECRET" \
  -d "scope=https://api.botframework.com/.default"
```

### Issue: Webhook receives no messages

**Check:**
1. Azure Bot Service messaging endpoint is correct
2. Bot is added to Teams channel
3. Bot has permissions to read messages

**Debug:**
- Check Azure Bot Service → Channels → Test in Web Chat
- If working in Web Chat but not Teams, check Teams channel configuration

### Issue: "typing..." shows but no response

**Check:**
- BMS API is running: `curl http://localhost:8000/health`
- Query timeout (default 30s) may be too short
- Check n8n execution log for "Query BMS Agent" node errors

---

## Performance Optimization

### Token Caching (Optional)

Instead of requesting a new token for each message, cache it:

```javascript
// In "Get Bot Framework Token" node, add caching:
const { getRedisClient } = require('/workspace/002-n8n/lib/redis-client');
const redisClient = getRedisClient();

// Try to get cached token
const cachedToken = await redisClient.execute(
  async (client) => client.get('bot:access_token'),
  null
);

if (cachedToken.success && cachedToken.data) {
  return { json: { access_token: cachedToken.data } };
}

// If no cached token, request new one
// (keep existing HTTP request logic)

// After getting new token, cache it:
await redisClient.execute(
  async (client) => {
    await client.setEx('bot:access_token', 3500, accessToken); // 58min TTL
  },
  null
);
```

---

## Security Best Practices

1. **Never commit credentials:**
   - Store `BOT_APP_ID` and `BOT_APP_PASSWORD` as environment variables
   - Use `.env` files excluded from git

2. **Validate incoming webhooks:**
   - Add signature verification (Azure sends `x-ms-signature` header)
   - Verify the request comes from Bot Framework

3. **Use HTTPS only:**
   - Azure Bot Service requires HTTPS messaging endpoints
   - n8n RunPod URL already uses HTTPS ✅

4. **Implement rate limiting:**
   - Add throttling to prevent abuse
   - Use Redis to track request counts per user

---

## Alternative: Bot Framework Emulator for Local Testing

For testing locally without deploying to Azure:

1. **Download Bot Framework Emulator:**
   https://github.com/Microsoft/BotFramework-Emulator/releases

2. **Configure Emulator:**
   - Bot URL: `https://nqz5l77nsrdkyt-5678.proxy.runpod.net/webhook/teams-bot`
   - Microsoft App ID: `{BOT_APP_ID}`
   - Microsoft App Password: `{BOT_APP_PASSWORD}`

3. **Test messages directly** without going through Teams

---

## Summary

✅ **Advantages of Webhook Approach:**
- No n8n credential configuration issues
- Full control over authentication flow
- Easy to debug (see every API call in workflow)
- Can add custom logic between steps
- Works with any Bot Framework feature

✅ **What You Need:**
1. Import `teams-webhook-bot-handler.json` into n8n
2. Set `BOT_APP_ID` and `BOT_APP_PASSWORD` environment variables
3. Configure Azure Bot Service messaging endpoint
4. Activate workflow

✅ **Ready to Use:**
- The workflow is complete and production-ready
- Includes typing indicators
- Formats responses with sources
- Handles errors gracefully

**Next Step:** Import the workflow and configure the Azure messaging endpoint!
