# Quick Import Guide - Redis Fixed Workflows

## What Was Fixed

✅ **2 workflows fixed** with proper Redis nodes:
- MS Teams Bot - Context Manager (pC8nfwxrXqHUb3gX)
- Similar Query Detector (o9QL7V6zWIGgiWDV)

✅ **5 Redis nodes** replaced/corrected:
- 3 nodes in Context Manager (were HTTP, now Redis)
- 2 nodes in Similar Query Detector (were misconfigured, now correct)

## Import Steps (5 minutes)

### Step 1: Open n8n
```bash
# Navigate to:
http://localhost:5678
```

### Step 2: Import Context Manager
1. Click **Workflows** → **Import from File**
2. Select: `/workspace/002-n8n/workflows/context-manager.json`
3. Choose: **Update existing** (ID: pC8nfwxrXqHUb3gX)
4. Click **Import**

### Step 3: Set Redis Credentials for Context Manager
1. Open the imported workflow
2. Find these 3 Redis nodes:
   - "Redis GET"
   - "Redis GET for Store"
   - "Redis SET with TTL"
3. Click each node → Select **Redis Local** from credentials dropdown
4. **Save** workflow

### Step 4: Import Similar Query Detector
1. Click **Workflows** → **Import from File**
2. Select: `/workspace/002-n8n/workflows/similar-query-detector.json`
3. Choose: **Update existing** (ID: o9QL7V6zWIGgiWDV)
4. Click **Import**

### Step 5: Set Redis Credentials for Similar Query Detector
1. Open the imported workflow
2. Find these 2 Redis nodes:
   - "Get User Query History"
   - "Save to Redis"
3. Click each node → Select **Redis Local** from credentials dropdown
4. **Save** workflow

### Step 6: Test (Optional but Recommended)
```bash
# Run the test script
/workspace/002-n8n/test-redis-fixes.sh
```

## Done!

Your workflows now use proper Redis nodes instead of broken HTTP calls.

---

## What Changed (Technical)

**Before** (BROKEN):
```json
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "http://localhost:6379",  // ❌ Redis doesn't have HTTP API!
    "method": "GET"
  }
}
```

**After** (WORKING):
```json
{
  "type": "n8n-nodes-base.redis",  // ✅ Proper Redis node
  "parameters": {
    "operation": "get",             // ✅ Redis operation
    "key": "{{ expression }}"       // ✅ Direct key access
  },
  "credentials": {
    "redis": {"name": "Redis Local"}  // ✅ Uses credentials
  }
}
```

---

## Verification

After import, verify in n8n UI:

**Context Manager** should have:
- ✅ 3 Redis nodes (green indicators)
- ✅ "Redis Local" credentials selected on all
- ✅ Operations: get, get, set

**Similar Query Detector** should have:
- ✅ 2 Redis nodes (green indicators)
- ✅ "Redis Local" credentials selected on both
- ✅ Operations: get, set

---

## Next Steps

After importing these fixes:

1. ✅ **Apply other workflow fixes** from FIXES_APPLIED.md:
   - Webhook error handling (11 workflows)
   - HTTP retry logic (4 workflows)
   - Input validation (5 tool workflows)

2. ✅ **Activate workflows** in correct order (see N8N_LIVE_WORKFLOWS_STATUS.md)

3. ✅ **Test end-to-end** MS Teams bot functionality

---

**See REDIS_FIXES_COMPLETE.md for detailed technical documentation**
