# n8n Live Workflows Status

**Query Date**: 2025-10-06
**n8n Instance**: http://localhost:5678
**Total Workflows**: 13/13 ✅

---

## Current Workflows in n8n Instance

| Workflow ID | Workflow Name | Status | JSON File Exists |
|-------------|---------------|--------|------------------|
| 0N6Wm7z1365fESrA | MS Teams Bot - BMS API Caller | ⭕ Inactive | ✅ Yes |
| 2CYCWujMgXMVWryr | MS Teams Bot - Query Analyzer | ⭕ Inactive | ✅ Yes |
| 6fj4iOSHiA9WkbAO | Health Check | ⭕ Inactive | ✅ Yes |
| BFDMwaYVCaPoRFw2 | MS Teams Bot - Main Handler | ⭕ Inactive | ✅ Yes |
| FiA7ttEV19p6as4e | Tool: Contextual Search | ⭕ Inactive | ✅ Yes |
| H4PNLouLnNsyZ6ks | Tool: Search by Metadata Filters | ⭕ Inactive | ✅ Yes |
| SpPc24TPGHkaj7K3 | MS Teams Bot - Admin Commands | ⭕ Inactive | ✅ Yes |
| j1kX1U1gicdWDn1v | LangChain Agent Orchestrator | ⭕ Inactive | ✅ Yes |
| kGG5OXsm7P1m1AMg | Tool: Search Hybrid | ⭕ Inactive | ✅ Yes |
| mck76ydIzx0E0ET8 | Tool: Search Semantic | ⭕ Inactive | ✅ Yes |
| o9QL7V6zWIGgiWDV | Similar Query Detector | ⭕ Inactive | ✅ Yes |
| pC8nfwxrXqHUb3gX | MS Teams Bot - Context Manager | ⭕ Inactive | ✅ Yes |
| tvzyTniDZ7XpVloI | Tool: Ask BMS (Enhanced) | ⭕ Inactive | ✅ Yes |

**⚠️ All workflows are currently INACTIVE**

---

## Workflow ID Mapping

This mapping is critical for the LangChain Agent Orchestrator to reference other workflows:

```bash
# Environment variables for langchain-agent-orchestrator.json
export WORKFLOW_ID_BMS_CALLER="0N6Wm7z1365fESrA"
export WORKFLOW_ID_CONTEXT_MANAGER="pC8nfwxrXqHUb3gX"
export WORKFLOW_ID_SIMILAR_QUERY="o9QL7V6zWIGgiWDV"
```

**Add these to your `.env` file or n8n environment configuration**

---

## How to Apply Enhancement Fixes

You have two options to apply the fixes from `QUICK_FIXES.md`:

### Option 1: Edit Directly in n8n UI (Recommended for Testing)

1. Open n8n: http://localhost:5678
2. Open each workflow
3. Apply fixes from `QUICK_FIXES.md`
4. Test the workflow
5. Activate when ready

**Advantages**:
- Visual editing
- Immediate testing
- Easy rollback

**Disadvantages**:
- Manual work for 13 workflows
- Risk of missing changes

---

### Option 2: Update JSON Files and Re-import

1. **Backup current workflows** (already done - they're in `workflows/` directory)

2. **Apply fixes to JSON files**:
   ```bash
   cd /workspace/002-n8n
   # Edit each JSON file according to QUICK_FIXES.md
   ```

3. **Delete existing workflows in n8n**:
   ```bash
   # Via API (be careful!)
   for id in 0N6Wm7z1365fESrA 2CYCWujMgXMVWryr ...; do
     curl -X DELETE \
       -H "X-N8N-API-KEY: YOUR_API_KEY" \
       http://localhost:5678/api/v1/workflows/$id
   done
   ```

4. **Import updated workflows**:
   ```bash
   # Via n8n UI: Workflows → Import
   # Or via API:
   for file in workflows/*.json; do
     curl -X POST \
       -H "X-N8N-API-KEY: YOUR_API_KEY" \
       -H "Content-Type: application/json" \
       -d @"$file" \
       http://localhost:5678/api/v1/workflows
   done
   ```

**Advantages**:
- Version controlled
- Can review diffs in git
- Reproducible

**Disadvantages**:
- New workflow IDs (need to update references)
- Requires re-importing all workflows

---

### Option 3: Use n8n MCP Tools (Partial Updates - BEST)

Since the n8n MCP server is configured, we can use it to make targeted updates without re-importing:

```javascript
// Example: Add webhook error handling to main-bot-handler
// Use n8n MCP tool: update_partial_workflow

{
  "workflowId": "BFDMwaYVCaPoRFw2",
  "operations": [
    {
      "type": "updateNode",
      "nodeId": "webhook-trigger",
      "updates": {
        "parameters.options.onError": "continueRegularOutput"
      }
    }
  ]
}
```

**Advantages**:
- Preserves workflow IDs
- Minimal changes
- Can be automated
- No downtime

**Disadvantages**:
- Requires scripting
- More complex

---

## Recommended Approach: Hybrid Strategy

**Phase 1: Critical Fixes via MCP Tools**

Use n8n MCP to update existing workflows with critical fixes:

1. **Webhook error handling** (11 workflows)
2. **Retry logic** (4 workflows)
3. **Timeout adjustments** (2 workflows)

This keeps workflow IDs intact and minimizes disruption.

**Phase 2: Major Refactoring via JSON + Re-import**

For complex changes like Redis node replacements:

1. Create new versions with `-v2` suffix
2. Test thoroughly
3. Update references in other workflows
4. Activate v2 workflows
5. Deactivate old versions
6. Delete old versions after validation

---

## Critical Action Items

### 1. Set Environment Variables for Workflow IDs

**File**: Create `/workspace/002-n8n/config/workflow-ids.env`

```bash
# Workflow IDs for cross-workflow references
WORKFLOW_ID_BMS_CALLER="0N6Wm7z1365fESrA"
WORKFLOW_ID_CONTEXT_MANAGER="pC8nfwxrXqHUb3gX"
WORKFLOW_ID_SIMILAR_QUERY="o9QL7V6zWIGgiWDV"
WORKFLOW_ID_ASK_BMS="tvzyTniDZ7XpVloI"
WORKFLOW_ID_SEARCH_SEMANTIC="mck76ydIzx0E0ET8"
WORKFLOW_ID_SEARCH_HYBRID="kGG5OXsm7P1m1AMg"
WORKFLOW_ID_SEARCH_METADATA="H4PNLouLnNsyZ6ks"
WORKFLOW_ID_SEARCH_CONTEXTUAL="FiA7ttEV19p6as4e"

# n8n Configuration
N8N_BASE_URL="http://localhost:5678"
N8N_WEBHOOK_BASE_URL="http://localhost:5678"

# BMS API
BMS_API_URL="http://localhost:8000"

# Ollama
OLLAMA_URL="http://localhost:11434"

# Redis
REDIS_HOST="localhost"
REDIS_PORT="6379"
```

**Load in n8n**:
- Add to n8n startup environment
- Or use n8n's Variables feature (Settings → Variables)

### 2. Set Up Redis Credentials in n8n

1. Open n8n: http://localhost:5678
2. Go to **Settings** → **Credentials** → **Add Credential**
3. Select **Redis**
4. Configure:
   - **Name**: `Redis Local`
   - **Host**: `localhost`
   - **Port**: `6379`
   - **Database**: `0`
   - **Password**: (leave empty if no password)
5. **Save**
6. Note the credential ID for updates

### 3. Activate Workflows in Correct Order

**Order matters** due to dependencies:

```bash
# 1. Support workflows first
curl -X PATCH \
  -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows/6fj4iOSHiA9WkbAO \
  -d '{"active": true}'  # Health Check

# 2. Context and cache workflows
curl -X PATCH \
  -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows/pC8nfwxrXqHUb3gX \
  -d '{"active": true}'  # Context Manager

curl -X PATCH \
  -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows/o9QL7V6zWIGgiWDV \
  -d '{"active": true}'  # Similar Query Detector

# 3. Tool workflows
for id in tvzyTniDZ7XpVloI mck76ydIzx0E0ET8 kGG5OXsm7P1m1AMg H4PNLouLnNsyZ6ks FiA7ttEV19p6as4e; do
  curl -X PATCH \
    -H "X-N8N-API-KEY: YOUR_KEY" \
    http://localhost:5678/api/v1/workflows/$id \
    -d '{"active": true}'
done

# 4. BMS API Caller and Query Analyzer
curl -X PATCH \
  -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows/0N6Wm7z1365fESrA \
  -d '{"active": true}'  # BMS API Caller

curl -X PATCH \
  -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows/2CYCWujMgXMVWryr \
  -d '{"active": true}'  # Query Analyzer

# 5. Admin Commands
curl -X PATCH \
  -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows/SpPc24TPGHkaj7K3 \
  -d '{"active": true}'  # Admin Commands

# 6. Main handlers (LAST)
curl -X PATCH \
  -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows/BFDMwaYVCaPoRFw2 \
  -d '{"active": true}'  # Main Bot Handler

curl -X PATCH \
  -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows/j1kX1U1gicdWDn1v \
  -d '{"active": true}'  # LangChain Agent
```

---

## Testing Checklist Before Activation

### Test Each Workflow Individually

```bash
# Health Check
curl http://localhost:5678/webhook/health

# Context Manager (store)
curl -X POST http://localhost:5678/webhook/context-manager \
  -H "Content-Type: application/json" \
  -d '{
    "action": "store",
    "conversationId": "test-123",
    "userMessage": "Hello",
    "botResponse": "Hi there!"
  }'

# Context Manager (get)
curl -X POST http://localhost:5678/webhook/context-manager \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get",
    "conversationId": "test-123"
  }'

# BMS API Caller
curl -X POST http://localhost:5678/webhook/bms-api-caller \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are brake procedures?",
    "intent": "ASK"
  }'

# Query Analyzer
curl -X POST http://localhost:5678/webhook/query-analyzer \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find brake manuals",
    "conversationId": "test-123"
  }'

# Main Bot Handler
curl -X POST http://localhost:5678/webhook/teams \
  -H "Content-Type: application/json" \
  -d '{
    "type": "message",
    "text": "test query",
    "from": {"id": "user123", "name": "Test User"},
    "conversation": {"id": "conv123"}
  }'
```

---

## Monitoring After Activation

### Check Workflow Execution History

```bash
# List recent executions
curl -H "X-N8N-API-KEY: YOUR_KEY" \
  "http://localhost:5678/api/v1/executions?limit=50"

# Check specific workflow executions
curl -H "X-N8N-API-KEY: YOUR_KEY" \
  "http://localhost:5678/api/v1/executions?workflowId=BFDMwaYVCaPoRFw2&limit=10"
```

### Watch n8n Logs

```bash
# If running with Docker
docker logs -f n8n

# If running as node process
tail -f /root/.n8n/logs/n8n.log
```

### Monitor Services

```bash
# BMS API
curl http://localhost:8000/health

# Ollama
curl http://localhost:11434/api/tags

# Redis
redis-cli PING
```

---

## Next Steps

1. ✅ **Create environment variables file** with workflow IDs
2. ✅ **Set up Redis credentials** in n8n
3. 🔄 **Choose update strategy** (MCP tools vs JSON re-import)
4. 🔄 **Apply critical fixes** from `QUICK_FIXES.md`
5. 🔄 **Test each workflow** with sample data
6. 🔄 **Activate workflows** in dependency order
7. 🔄 **Monitor execution logs** for errors
8. 🔄 **Validate end-to-end** MS Teams bot flow

---

## Useful Commands

### Export Current Workflow as JSON
```bash
curl -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows/BFDMwaYVCaPoRFw2 \
  | jq . > backup-main-handler.json
```

### Compare Live vs File
```bash
# Get live workflow
curl -s -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows/BFDMwaYVCaPoRFw2 \
  | jq .nodes > /tmp/live-nodes.json

# Compare with file
jq .nodes workflows/main-bot-handler.json > /tmp/file-nodes.json
diff /tmp/live-nodes.json /tmp/file-nodes.json
```

### Bulk Activate All Workflows
```bash
# Get all workflow IDs
curl -s -H "X-N8N-API-KEY: YOUR_KEY" \
  http://localhost:5678/api/v1/workflows \
  | jq -r '.data[].id' \
  | while read id; do
      curl -X PATCH \
        -H "X-N8N-API-KEY: YOUR_KEY" \
        -H "Content-Type: application/json" \
        http://localhost:5678/api/v1/workflows/$id \
        -d '{"active": true}'
      echo "Activated $id"
    done
```

---

## Summary

✅ All 13 workflows are present in n8n instance
⚠️ All workflows are currently inactive
🔧 Critical fixes needed before activation (see QUICK_FIXES.md)
📝 Workflow IDs documented for environment configuration
🎯 Ready to apply enhancements and activate

**Recommendation**: Apply webhook error handling fixes first, then activate one workflow at a time for testing.
