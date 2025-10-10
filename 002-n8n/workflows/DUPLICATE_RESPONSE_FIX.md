# Duplicate Response Bug Fix

**Date**: 2025-10-10
**Issue**: Bot posting the same answer 2-3 times to Slack
**File**: `bms-ai-agent.json`
**Root Cause**: Slack event retries due to slow webhook response

---

## 🐛 Problem

User reported bot repeating answers:
```
18:49 - Response 1: Good CSP answer
18:49 - Response 2: Warning + "How can I help you..."
18:50 - Response 3: Warning + "I'm here to help..."
```

All within 1 minute → Indicates Slack event retries, not AI agent issue.

---

## 🔍 Root Cause

**Slack Events API Behavior:**
- Sends event to webhook
- Expects 200 OK response within **3 seconds**
- If no response or timeout → **Retries event** 2-3 times (with exponential backoff)

**Current Workflow Flow:**
```
Slack Event → Webhook → Process Event1
                           ├─→ Respond to Webhook1 ("OK")
                           └─→ Nomi AI Agent (10-30s) → Format → Post to Slack
```

**The Problem:**
1. Process Event1 splits into 2 parallel paths
2. Both paths run simultaneously
3. AI agent takes 10-30 seconds to complete
4. "Respond to Webhook1" might not execute before 3-second timeout
5. Slack doesn't get "OK" → **Retries the event**
6. Each retry triggers the workflow again → Multiple responses

---

## ✅ Solution

**Option 1: Event Deduplication (Recommended)**

Add event deduplication in "Process Event1" node using Slack's `event_id`:

```javascript
// Process Slack Event WITH DEDUPLICATION
const body = $input.item.json.body;

// URL verification
if (body.type === 'url_verification') {
  return [{
    json: { challenge: body.challenge },
    pairedItem: { item: 0 }
  }];
}

// Event deduplication using event_id
const EVENT_CACHE_KEY = 'processed_slack_events';
const EVENT_CACHE_TTL = 300000; // 5 minutes

// Get or initialize event cache
const processedEvents = $getWorkflowStaticData('global')[EVENT_CACHE_KEY] || {};
const currentTime = Date.now();

// Clean expired entries (older than 5 min)
for (const [eventId, timestamp] of Object.entries(processedEvents)) {
  if (currentTime - timestamp > EVENT_CACHE_TTL) {
    delete processedEvents[eventId];
  }
}

// Handle app_mention
if (body.type === 'event_callback' && body.event.type === 'app_mention') {
  const event = body.event;
  const eventId = body.event_id;

  // Check if already processed
  if (processedEvents[eventId]) {
    console.log(`⚠️ Duplicate event detected: ${eventId} (Slack retry)`);
    // Return empty to skip processing, but webhook still gets OK
    return [];
  }

  // Mark as processed
  processedEvents[eventId] = currentTime;
  $getWorkflowStaticData('global')[EVENT_CACHE_KEY] = processedEvents;

  const query = event.text.replace(/<@U09LPC5D2U8>/g, '').trim();

  return [{
    json: {
      query: query,
      channel: event.channel,
      user: event.user,
      thread_ts: event.ts,
      team_id: body.team_id,
      event_id: eventId
    },
    pairedItem: { item: 0 }
  }];
}

// Ignore other events
return [];
```

**Benefits:**
- ✅ Prevents duplicate processing
- ✅ Slack gets immediate "OK" response
- ✅ Event retries are ignored
- ✅ Uses Slack's event_id for reliable deduplication

---

**Option 2: Immediate Webhook Response (Alternative)**

Restructure workflow to respond BEFORE processing:

```
Slack Event → Webhook → Immediate "OK" Response → Queue Event
                                                      ↓
                                              Background Processing
                                              (Nomi → Format → Post)
```

This requires workflow restructuring.

---

## 📊 Expected Behavior After Fix

### Before (BROKEN):
```
User: "what is sick leave policy?"
Slack: Sends event
n8n: Processing... (15 seconds)
Slack: No response after 3s → RETRY 1
n8n: Still processing...
Slack: No response → RETRY 2
n8n: Finally responds with 3 answers (from 3 executions)
```

### After (FIXED):
```
User: "what is sick leave policy?"
Slack: Sends event (event_id: abc123)
n8n: Checks cache → NOT found → Process + respond "OK" immediately
Slack: Receives "OK" → Happy, no retry
n8n: AI agent completes → Posts 1 answer

(If Slack retries anyway)
Slack: Retry event (event_id: abc123)
n8n: Checks cache → FOUND → Skip processing, respond "OK"
Result: Only 1 answer posted
```

---

## 🧪 Testing

**Test 1: Normal Query**
```
1. Ask bot: "what is the sick leave policy?"
2. Verify only ONE response appears
3. Check n8n execution logs for "Duplicate event detected" messages
```

**Test 2: Rapid Fire (Trigger Slack Retry)**
```
1. Ask bot question
2. Within 3 seconds, trigger webhook manually or send another query
3. Verify no duplicate responses
```

**Test 3: Event Cache Cleanup**
```
1. Wait 6+ minutes after a query
2. Ask same question again
3. Verify event is reprocessed (cache expired)
```

---

## 🚀 Implementation

**Manual Steps (n8n UI):**
1. Open `bms-ai-agent` workflow in n8n
2. Edit "Process Event1" Code node
3. Replace JavaScript with deduplicated version above
4. Save and activate workflow
5. Test with a query

**Or via JSON:**
- Update `bms-ai-agent.json` "Process Event1" node
- Import updated workflow

---

## ⚠️ Additional Notes

**Why 2-3 responses instead of more?**
- Slack retries with exponential backoff: 3s, 6s, 12s
- Most AI queries complete within 30s
- So typically 2-3 retries max

**Why some responses show warnings?**
- Later retries might process while earlier execution is still running
- Cache contention or timing issues
- Deduplication will prevent this

**Alternative: Use Slack's `retry_num` header**
- Slack includes `X-Slack-Retry-Num` header on retries
- Could check this in webhook and reject if > 0
- Event deduplication is more reliable

---

## 📁 Status

- ❌ **Not yet implemented** - Awaiting user confirmation
- 📝 Documentation ready
- 🧪 Testing plan prepared

**Next Step:** Apply fix to "Process Event1" node in bms-ai-agent.json

---

## 📞 Related Issues

This is separate from the faceted search bug (already fixed). Both issues combined were causing:
1. Wrong/inconsistent department data (faceted search bug) ✅ Fixed
2. Duplicate responses (Slack retry bug) ⏳ Fix ready

With both fixes applied, bot should work correctly.
