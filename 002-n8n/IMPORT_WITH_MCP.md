# Import Workflows Using n8n-mcp

## Quick Start (2 minutes total)

### Step 1: Create n8n API Key (30 seconds)

1. Open n8n: http://localhost:5678
2. Click your profile icon (top right) → **Settings**
3. Go to **API** tab on the left
4. Click **Create an API key**
5. Give it a name: `mcp-import`
6. Copy the generated key (starts with `n8n_api_`)

### Step 2: Set Environment Variable (10 seconds)

```bash
export N8N_API_KEY="n8n_api_xxxxxxxxxxxxxxxxxxxxxxxx"  # Paste your key here
export N8N_API_URL="http://localhost:5678"
```

### Step 3: Import Workflows via MCP (automated)

The n8n-mcp server is already running and can import the workflows. However, since we need to replace entire workflow definitions (not just partial updates), we'll use the n8n REST API directly:

```bash
# Import Context Manager
curl -X PUT http://localhost:5678/api/v1/workflows/pC8nfwxrXqHUb3gX \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/workspace/002-n8n/workflows/context-manager.json

# Import Similar Query Detector
curl -X PUT http://localhost:5678/api/v1/workflows/o9QL7V6zWIGgiWDV \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/workspace/002-n8n/workflows/similar-query-detector.json
```

### Step 4: Assign Redis Credentials in n8n UI

The workflows are imported, but Redis credentials still need to be assigned manually in the UI:

1. Open **Context Manager** workflow in n8n
2. Click each Redis node (3 total: "Redis GET", "Redis GET for Store", "Redis SET with TTL")
3. Select **Redis Local** from the credentials dropdown
4. **Save** workflow

5. Open **Similar Query Detector** workflow
6. Click each Redis node (2 total: "Get User Query History", "Save to Redis")
7. Select **Redis Local** from credentials dropdown
8. **Save** workflow

### Step 5: Test (30 seconds)

```bash
/workspace/002-n8n/test-redis-fixes.sh
```

---

## Alternative: Using n8n-mcp Tools for Partial Updates

If you only need to update specific nodes (not full workflow replacement), you can use the n8n-mcp tools:

### Example: Update a Single Node Parameter

```javascript
// This would work via Claude with n8n-mcp tools
// Update Redis node operation in Context Manager
n8n_update_partial_workflow({
  id: "pC8nfwxrXqHUb3gX",
  operations: [
    {
      type: "updateNode",
      nodeName: "Redis GET",
      updates: {
        "type": "n8n-nodes-base.redis",
        "parameters.operation": "get",
        "parameters.key": "={{ 'conversation:' + $json.conversationId }}"
      }
    }
  ]
})
```

### Why Full Workflow Import is Better Here

For the Redis fixes, we're replacing entire node definitions (changing from HTTP Request to Redis nodes), so full workflow import via REST API is cleaner than many partial update operations.

---

## Troubleshooting

### API Key Not Working
```bash
# Verify API key is set
echo $N8N_API_KEY

# Test API access
curl -H "X-N8N-API-KEY: $N8N_API_KEY" http://localhost:5678/api/v1/workflows | jq '.data | length'
```

### Import Failed
- Check workflow JSON is valid: `jq . /workspace/002-n8n/workflows/context-manager.json`
- Verify workflow ID exists: `curl -H "X-N8N-API-KEY: $N8N_API_KEY" http://localhost:5678/api/v1/workflows/pC8nfwxrXqHUb3gX`

### Credentials Not Showing
- Go to n8n **Settings** → **Credentials**
- Verify "Redis Local" exists
- If not, create it:
  - Type: Redis
  - Host: localhost
  - Port: 6379
  - Database: 0

---

## What Happens During Import

1. **curl PUT request** → Replaces entire workflow definition
2. **n8n validates** the workflow structure
3. **Nodes are created** with new Redis configuration
4. **Connections are preserved** from JSON
5. **Credentials need manual assignment** (n8n security feature)

---

## Benefits of MCP Import vs Manual UI Import

| Method | Speed | Accuracy | Reproducible | Scriptable |
|--------|-------|----------|--------------|------------|
| MCP/API | ⚡ Fast | ✅ Perfect | ✅ Yes | ✅ Yes |
| Manual UI | 🐌 Slow | ⚠️ Human error | ❌ No | ❌ No |

---

## All Fixed Workflows Ready for Import

- ✅ `/workspace/002-n8n/workflows/context-manager.json`
- ✅ `/workspace/002-n8n/workflows/similar-query-detector.json`

Both have proper Redis nodes configured and are ready to import!

---

**Next**: After import, see FIXES_APPLIED.md for remaining webhook error handling and retry logic fixes.
