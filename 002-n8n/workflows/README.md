# n8n Workflows - Implementation Guide

## Overview

This directory contains n8n workflow JSON files for the MS Teams Bot. Due to the visual nature of n8n workflows, these files need to be created or completed in the n8n UI.

## Workflow Files Status

### ✅ Completed
- `similar-query-detector.json` (T019a) - Already implemented

### 📝 To Be Created (via n8n UI)
- `main-bot-handler.json` (T016) - Main entry point
- `query-analyzer.json` (T017) - Intent classification
- `bms-api-caller.json` (T018) - BMS API integration
- `context-manager.json` (T019) - Conversation storage
- `admin-commands.json` (T020) - Admin operations

## How to Create Workflows

### Method 1: Using n8n UI (Recommended)

1. **Open n8n**: http://localhost:5678

2. **Create New Workflow**: Click "+" or "New Workflow"

3. **Follow Implementation Guide**:
   - Reference: `/workspace/002-n8n/docs/workflow-implementation-guide.md`
   - Each workflow has detailed node-by-node instructions

4. **Add Required Nodes**:
   - Drag nodes from left panel
   - Configure settings per guide
   - Connect nodes in correct order

5. **Test Workflow**:
   - Use "Execute Workflow" button
   - Check outputs in each node
   - Fix any errors

6. **Export JSON**:
   - Click workflow menu (3 dots)
   - Select "Download"
   - Save to this directory with correct filename

7. **Activate**:
   - Toggle "Active" switch ON
   - Workflow will start receiving webhooks

### Method 2: Import Template & Complete

1. **Import Base Template** (if provided):
   ```bash
   # In n8n UI: Settings → Import from File
   # Select workflow JSON from this directory
   ```

2. **Complete Configuration**:
   - Add credential connections
   - Update URLs and endpoints
   - Test each node

3. **Save & Activate**

## Workflow Dependencies

```
main-bot-handler (T016)
  ├── Calls → query-analyzer (T017)
  ├── Calls → bms-api-caller (T018)
  ├── Calls → context-manager (T019)
  ├── Calls → admin-commands (T020)
  └── Calls → similar-query-detector (T019a) ✓
```

**Important**: Create workflows in order or ensure all called sub-workflows exist before activating main-bot-handler.

## Required Credentials

Add these in n8n UI (Credentials menu):

1. **Microsoft Bot Framework**
   - App ID: From Azure Bot registration
   - App Password: From Azure Bot registration

2. **Redis**
   - Host: localhost
   - Port: 6379
   - Database: 0

3. **HTTP Auth** (for Ollama, optional)
   - Type: None (local)

## Helper Modules Available

Your workflows can use these Node.js modules:

- **Redis Client**: `/workspace/002-n8n/lib/redis-client.js`
  ```javascript
  const { getRedisClient } = require('/workspace/002-n8n/lib/redis-client.js');
  const redis = getRedisClient();
  ```

- **Whitelist Manager**: `/workspace/002-n8n/lib/whitelist.js`
  ```javascript
  const { getWhitelistManager } = require('/workspace/002-n8n/lib/whitelist.js');
  const whitelist = getWhitelistManager();
  ```

## Testing Workflows

### Test Main Bot Handler
```bash
curl -X POST http://localhost:5678/webhook/teams \
  -H "Content-Type: application/json" \
  -d '{
    "type": "message",
    "id": "test-123",
    "from": {"id": "29:test-user"},
    "conversation": {"id": "conv-1"},
    "text": "What are brake procedures?",
    "serviceUrl": "https://smba.trafficmanager.net"
  }'
```

### Test Query Analyzer
- Call from main-bot-handler
- Or execute workflow manually in n8n UI

### Test BMS API Caller
- Requires BMS API running at http://localhost:8000
- Test with mock intent data

## Common Issues & Solutions

### Issue: "Module not found"
**Solution**: Ensure n8n can access /workspace/002-n8n/lib/ files
```bash
# Check Node.js can require modules
node -e "require('/workspace/002-n8n/lib/redis-client.js')"
```

### Issue: "Redis connection failed"
**Solution**: Start Redis first
```bash
./scripts/manage-services.sh start
```

### Issue: "Webhook not triggering"
**Solution**: 
1. Verify workflow is Active (green toggle)
2. Check webhook URL in MS Teams Bot Framework settings
3. Test with curl command above

### Issue: "BMS API timeout"
**Solution**:
1. Check BMS API: `curl http://localhost:8000/health`
2. Increase timeout in workflow (currently 2500ms)

## Deployment

Once workflows are created and tested:

```bash
# Export all workflows from n8n UI to this directory

# Deploy to another n8n instance
./scripts/deploy-workflows.sh
```

## Integration Tests

After creating workflows, run tests:

```bash
cd /workspace/002-n8n
npm test

# Expected: Tests should pass once workflows are active
```

## Documentation

- **Full Implementation Guide**: `/workspace/002-n8n/docs/workflow-implementation-guide.md`
- **Quickstart**: `/workspace/specs/002-create-a-microsoft/quickstart.md`
- **Troubleshooting**: `/workspace/002-n8n/docs/troubleshooting.md`

---

**Next Steps**:
1. Open n8n UI: http://localhost:5678
2. Create workflows using implementation guide
3. Test each workflow individually
4. Run integration tests
5. Deploy to MS Teams

**Estimated Time**: 4-5 hours for all 5 workflows
