# Quick Fixes - Critical Enhancements

This document provides copy-paste ready fixes for the most critical issues identified in the workflow analysis.

## 1. Webhook Error Handling (ALL Webhook Nodes)

### Before:
```json
{
  "parameters": {
    "httpMethod": "POST",
    "path": "teams",
    "responseMode": "responseNode",
    "options": {}
  },
  "type": "n8n-nodes-base.webhook"
}
```

### After:
```json
{
  "parameters": {
    "httpMethod": "POST",
    "path": "teams",
    "responseMode": "responseNode",
    "options": {
      "onError": "continueRegularOutput"
    }
  },
  "type": "n8n-nodes-base.webhook"
}
```

**Apply to**: All 11 workflows with webhook triggers

---

## 2. HTTP Request Retry Configuration

### Before:
```json
{
  "parameters": {
    "url": "http://localhost:8000/api/v1/ask",
    "method": "POST",
    "options": {
      "timeout": 30000
    }
  },
  "type": "n8n-nodes-base.httpRequest"
}
```

### After:
```json
{
  "parameters": {
    "url": "http://localhost:8000/api/v1/ask",
    "method": "POST",
    "options": {
      "timeout": 30000,
      "retry": {
        "enabled": true,
        "maxRetries": 3,
        "retryInterval": 1000
      }
    }
  },
  "type": "n8n-nodes-base.httpRequest",
  "continueOnFail": true
}
```

**Apply to**:
- bms-api-caller.json: `Call BMS Ask Endpoint`, `Call BMS Search Endpoint`
- query-analyzer.json: `Ollama Intent Classification`
- tool-ask-bms-enhanced.json: `Call BMS Ask API`
- All tool workflows: API call nodes

---

## 3. Fix Redis Nodes in context-manager.json

### Replace HTTP Redis Calls

#### Before (Redis GET via HTTP - INCORRECT):
```json
{
  "parameters": {
    "url": "http://localhost:6379",
    "method": "GET",
    "sendQuery": true,
    "queryParameters": {
      "parameters": [
        {
          "name": "key",
          "value": "conversation:={{ $json.conversationId }}"
        }
      ]
    }
  },
  "type": "n8n-nodes-base.httpRequest"
}
```

#### After (Native Redis Node - CORRECT):
```json
{
  "parameters": {
    "operation": "get",
    "key": "={{ 'conversation:' + $json.conversationId }}"
  },
  "id": "redis-get",
  "name": "Redis GET",
  "type": "n8n-nodes-base.redis",
  "typeVersion": 1,
  "position": [850, 200],
  "credentials": {
    "redis": {
      "id": "redis-credentials-id",
      "name": "Redis Local"
    }
  }
}
```

#### For SET Operations:

Before (HTTP - INCORRECT):
```json
{
  "parameters": {
    "url": "http://localhost:6379",
    "method": "POST",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "key",
          "value": "conversation:={{ $json.context.conversation_id }}"
        },
        {
          "name": "value",
          "value": "={{ JSON.stringify($json.context) }}"
        }
      ]
    }
  },
  "type": "n8n-nodes-base.httpRequest"
}
```

After (Native Redis - CORRECT):
```json
{
  "parameters": {
    "operation": "set",
    "key": "={{ 'conversation:' + $json.context.conversation_id }}",
    "value": "={{ JSON.stringify($json.context) }}",
    "expire": true,
    "ttl": 604800
  },
  "id": "redis-set",
  "name": "Redis SET with TTL",
  "type": "n8n-nodes-base.redis",
  "typeVersion": 1,
  "credentials": {
    "redis": {
      "id": "redis-credentials-id",
      "name": "Redis Local"
    }
  }
}
```

**Critical**: Update all Redis operations in context-manager.json

---

## 4. Fix similar-query-detector.json Redis Nodes

### Same issue - replace lines 30-42 and 163-175

Use the same pattern as above:
- Line 30-42: GET operation
- Line 163-175: SETEX operation (use `expire: true` + `ttl` parameter)

---

## 5. Add Input Validation to All Tool Workflows

### Add this Code node AFTER Parse Input in each tool:

```json
{
  "parameters": {
    "functionCode": "// Input validation\nconst query = $json.query || '';\nconst limit = $json.limit || 10;\n\n// Validate query\nif (!query || query.trim().length === 0) {\n  throw new Error('Query cannot be empty');\n}\n\nif (query.length > 1000) {\n  throw new Error('Query too long (max 1000 characters)');\n}\n\n// Validate limit\nif (limit < 1 || limit > 50) {\n  throw new Error('Limit must be between 1 and 50');\n}\n\n// Sanitize query\nconst sanitizedQuery = query\n  .replace(/[<>]/g, '')\n  .replace(/[\\x00-\\x1F\\x7F]/g, '')\n  .trim();\n\nreturn {\n  json: {\n    ...$json,\n    query: sanitizedQuery,\n    limit: Math.min(Math.max(parseInt(limit), 1), 50)\n  }\n};"
  },
  "id": "validate-input",
  "name": "Validate Input",
  "type": "n8n-nodes-base.code",
  "typeVersion": 1,
  "continueOnFail": false
}
```

**Add to**:
- tool-ask-bms-enhanced.json (after line 26)
- tool-search-semantic.json (after line 26)
- tool-search-hybrid.json (after line 26)
- tool-search-by-metadata.json (after line 26)
- tool-contextual-search.json (after line 26)

---

## 6. Fix Workflow ID Fetching in langchain-agent-orchestrator.json

### Replace Dynamic API Calls with Environment Variables

#### Before (Lines 189-209 - FRAGILE):
```javascript
// Get workflow IDs for tools
const workflows = await this.helpers.request({
  method: 'GET',
  url: 'http://localhost:5678/api/v1/workflows',
  headers: {
    'Accept': 'application/json'
  }
});

const workflowMap = {};
workflows.data.forEach(wf => {
  if (wf.name === 'MS Teams Bot - BMS API Caller') {
    workflowMap.bmsCallerId = wf.id;
  }
  // ... etc
});
```

#### After (Environment Variables - ROBUST):
```javascript
// Use environment variables for workflow IDs
const workflowMap = {
  bmsCallerId: $env.WORKFLOW_ID_BMS_CALLER || 'default-bms-caller-id',
  contextManagerId: $env.WORKFLOW_ID_CONTEXT_MANAGER || 'default-context-id',
  similarQueryId: $env.WORKFLOW_ID_SIMILAR_QUERY || 'default-similar-id'
};

// Validate IDs exist
if (!workflowMap.bmsCallerId || workflowMap.bmsCallerId === 'default-bms-caller-id') {
  throw new Error('BMS Caller workflow ID not configured. Set WORKFLOW_ID_BMS_CALLER environment variable.');
}

return { json: workflowMap };
```

**Environment Variables to Set**:
```bash
export WORKFLOW_ID_BMS_CALLER="actual-workflow-id"
export WORKFLOW_ID_CONTEXT_MANAGER="actual-workflow-id"
export WORKFLOW_ID_SIMILAR_QUERY="actual-workflow-id"
```

---

## 7. Standardize Error Response Format

### Add this template to all workflows:

```javascript
// Standard error response function
function createErrorResponse(code, message, details = null) {
  return {
    success: false,
    error: {
      code: code,
      message: message,
      details: details,
      timestamp: new Date().toISOString()
    }
  };
}

// Usage examples:
// API unreachable
return createErrorResponse('BMS_API_UNAVAILABLE', 'BMS API is temporarily unavailable', { statusCode: 503 });

// Invalid input
return createErrorResponse('INVALID_INPUT', 'Query cannot be empty');

// Timeout
return createErrorResponse('TIMEOUT', 'Request timed out after 30s', { timeout: 30000 });

// Success response format:
return {
  success: true,
  data: results,
  metadata: {
    timestamp: new Date().toISOString(),
    executionTime: executionTimeMs
  }
};
```

---

## 8. Add Redis Chat Memory to langchain-agent-orchestrator.json

### Replace Current Memory Node (Line 172-177)

#### Before (Buffer Window Memory):
```json
{
  "parameters": {
    "sessionIdType": "customKey",
    "sessionKey": "={{ $json.conversation.id }}"
  },
  "id": "memory",
  "name": "Conversation Memory",
  "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
  "typeVersion": 1.2
}
```

#### After (Redis Chat Memory):
```json
{
  "parameters": {
    "sessionKey": "={{ $json.conversation.id }}",
    "sessionTTL": 604800,
    "contextWindowLength": 10
  },
  "id": "memory",
  "name": "Conversation Memory",
  "type": "@n8n/n8n-nodes-langchain.memoryRedisChat",
  "typeVersion": 1,
  "credentials": {
    "redis": {
      "id": "redis-credentials-id",
      "name": "Redis Local"
    }
  }
}
```

**Benefits**:
- Persistent across n8n restarts
- Shared across workflow instances
- Automatic TTL management
- Better performance

---

## 9. Add Timeout Configuration to Ollama Calls

### query-analyzer.json Line 78-94

Before:
```json
{
  "parameters": {
    "url": "http://localhost:11434/api/generate",
    "options": {
      "timeout": 10000
    }
  }
}
```

After:
```json
{
  "parameters": {
    "url": "http://localhost:11434/api/generate",
    "options": {
      "timeout": 3000,
      "retry": {
        "enabled": true,
        "maxRetries": 2,
        "retryInterval": 500
      }
    }
  },
  "continueOnFail": true
}
```

**Reasoning**: Intent classification should be fast (<3s). If Ollama is slow, fail fast and use fallback.

---

## 10. Redis Credentials Setup

### Create Redis Credentials in n8n:

1. Go to n8n Settings → Credentials → Add Credential
2. Select "Redis"
3. Configure:
   ```
   Host: localhost
   Port: 6379
   Database: 0
   Password: (if required)
   ```
4. Save as "Redis Local"
5. Copy credential ID
6. Update all Redis nodes to use this credential

---

## Implementation Checklist

Use this to track your fixes:

- [ ] 1. Add `onError: "continueRegularOutput"` to all webhook nodes
- [ ] 2. Add retry configuration to all HTTP Request nodes
- [ ] 3. Replace HTTP Redis calls with native Redis nodes in context-manager.json
- [ ] 4. Replace HTTP Redis calls with native Redis nodes in similar-query-detector.json
- [ ] 5. Add input validation to all 5 tool workflows
- [ ] 6. Replace workflow ID fetching with environment variables
- [ ] 7. Standardize error response format across all workflows
- [ ] 8. Replace Buffer Window Memory with Redis Chat Memory
- [ ] 9. Reduce Ollama timeout and add retry logic
- [ ] 10. Set up Redis credentials in n8n

---

## Testing After Fixes

### Test Each Fix:

1. **Webhook error handling**: Trigger workflow with invalid data
2. **Retry logic**: Stop BMS API mid-request
3. **Redis nodes**: Verify data persistence in Redis
4. **Input validation**: Send empty queries, long queries
5. **Workflow IDs**: Restart n8n, verify workflows still work
6. **Error responses**: Check all error paths return consistent format
7. **Redis memory**: Check conversation persistence
8. **Ollama timeout**: Monitor response times
9. **Credentials**: Verify Redis connection

### Performance Testing:
```bash
# Test webhook with 100 concurrent requests
for i in {1..100}; do
  curl -X POST http://localhost:5678/webhook/teams \
    -H "Content-Type: application/json" \
    -d '{"type":"message","text":"test query"}' &
done
```

---

## Rollback Plan

If issues occur:

1. Keep backup of original workflows
2. Test each fix in development first
3. Deploy one fix at a time
4. Monitor error logs after each deployment
5. Have rollback workflows ready

---

## Getting Help

If you encounter issues:

1. Check n8n logs: `docker logs n8n`
2. Check Redis: `redis-cli PING`
3. Check BMS API: `curl http://localhost:8000/health`
4. Review n8n community forum: https://community.n8n.io
5. Check MCP documentation for node-specific issues
