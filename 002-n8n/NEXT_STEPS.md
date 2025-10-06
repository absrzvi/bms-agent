# Next Steps: Completing the MS Teams Bot Implementation

## 🎯 Current Status

**✅ Completed (24/38 tasks)**:
- Infrastructure setup (T001-T006)
- All tests written and failing as expected (T007-T015, T015a)
- Redis connection module (T024)
- Whitelist validation module (T025)
- Deployment scripts (T021-T023)
- Documentation and guides

**⏳ Remaining (14/38 tasks)**:
- 5 n8n workflows (T016-T020)
- 3 workflow extensions (T026, T027, T026a)
- 2 unit tests (T028-T029)
- 2 validation tasks (T032-T033)

---

## 📋 Step-by-Step Completion Guide

### Step 1: Create n8n Workflows (4-5 hours)

**Location**: n8n UI at http://localhost:5678

**Reference**: `/workspace/002-n8n/docs/workflow-implementation-guide.md`

1. **Main Bot Handler** (T016) - 1.5 hours
   - Create webhook trigger at `/webhook/teams`
   - Add message extraction, validation, whitelist check
   - Add command routing logic
   - Test with: `curl -X POST http://localhost:5678/webhook/teams -H "Content-Type: application/json" -d '{"type":"message","text":"test"}'`

2. **Query Analyzer** (T017) - 30 min
   - HTTP Request to Ollama at http://localhost:11434/api/generate
   - Parse intent (ASK vs SEARCH)
   - Return to main handler

3. **BMS API Caller** (T018) - 45 min
   - Branch on intent
   - Call BMS API /ask or /search endpoints
   - Format response with citations
   - Handle errors (timeout, unavailable)

4. **Context Manager** (T019) - 1 hour
   - Use Redis client module
   - Get/create conversation
   - Add message to context
   - Save with 7-day TTL
   - Detect storage restoration (NFR-002a)

5. **Admin Commands** (T020) - 45 min
   - Parse admin commands (/admin allow/revoke/list)
   - Use whitelist module
   - Return formatted responses

**Validation**:
```bash
# After creating workflows, run tests
cd /workspace/002-n8n
npm test

# Expected: Tests should start passing
```

---

### Step 2: Add Workflow Extensions (2-3 hours)

6. **File Upload Handler** (T026) - 1.5 hours
   - Extend main-bot-handler workflow
   - Detect attachments in message
   - Download file from Teams
   - Validate file type
   - POST to BMS API /upload/async
   - Store job_id in Redis

7. **Typing Indicator** (T027) - 30 min
   - Add to main-bot-handler before processing
   - POST typing activity to Bot Framework API
   - Use serviceUrl from incoming message

8. **Document Status Poller** (T026a) - 1 hour
   - Create new workflow with Schedule trigger (30s)
   - Query Redis for processing jobs
   - Check BMS API for status updates
   - Send proactive message on completion

---

### Step 3: Unit Tests (1 hour)

9. **Whitelist Validation Tests** (T028)
   ```javascript
   // Test file: /workspace/002-n8n/tests/unit/test-whitelist.js
   test('isChannelAllowed returns true for active channels')
   test('isAdmin returns true for whitelisted admins')
   test('Cache refresh works after 60s')
   ```

10. **Redis TTL Tests** (T029)
    ```javascript
    // Test file: /workspace/002-n8n/tests/unit/test-redis-ttl.js
    test('New conversation has 7-day TTL')
    test('Expired conversations auto-deleted')
    test('TTL refreshed on message update')
    ```

**Run**:
```bash
npm test tests/unit/
```

---

### Step 4: End-to-End Validation (1-2 hours)

11. **Quickstart Validation** (T032)
    - Follow `/workspace/specs/002-create-a-microsoft/quickstart.md`
    - Execute all 8 setup steps
    - Run all 5 test scenarios
    - Document any issues

12. **Performance Validation** (T033)
    ```bash
    # Run load test
    npm test tests/performance/load-test.js
    
    # Check results:
    # - p95 < 3000ms ✓
    # - p50 < 1500ms ✓
    # - Error rate < 5% ✓
    ```

---

## 🚀 Quick Commands

### Start Services
```bash
./scripts/manage-services.sh start
```

### Deploy Workflows
```bash
./scripts/deploy-workflows.sh
# OR manually import in n8n UI
```

### Run Tests
```bash
npm test                          # All tests
npm test tests/integration/       # Integration only
npm test tests/unit/              # Unit only
npm test tests/performance/       # Performance only
```

### Monitor Health
```bash
./scripts/manage-services.sh health
```

### Cleanup Old Data
```bash
./scripts/cleanup-expired.sh --dry-run   # Preview
./scripts/cleanup-expired.sh             # Execute
```

---

## 🔗 Key Files Reference

### Code Modules
- Redis Client: `/workspace/002-n8n/lib/redis-client.js`
- Whitelist: `/workspace/002-n8n/lib/whitelist.js`

### Scripts
- Deploy: `/workspace/002-n8n/scripts/deploy-workflows.sh`
- Cleanup: `/workspace/002-n8n/scripts/cleanup-expired.sh`
- Manage: `/workspace/002-n8n/scripts/manage-services.sh`

### Documentation
- Workflow Guide: `/workspace/002-n8n/docs/workflow-implementation-guide.md`
- Quickstart: `/workspace/specs/002-create-a-microsoft/quickstart.md`
- Implementation Status: `/workspace/002-n8n/IMPLEMENTATION_STATUS.md`

### Configuration
- Whitelist: `/workspace/002-n8n/config/whitelist.json`
- Environment: `/workspace/002-n8n/config/env.example`
- Response Templates: `/workspace/002-n8n/config/response-templates.json`

---

## ✅ Success Criteria

POC is complete when:
- [ ] All 5 n8n workflows created and active
- [ ] Integration tests pass (T010-T014)
- [ ] Performance test passes (p95 < 3s)
- [ ] Manual test in MS Teams succeeds
- [ ] Bot responds to natural language questions
- [ ] Bot responds to slash commands (/help, /search, /ask)
- [ ] Conversation context persists across messages
- [ ] Admin commands work (/admin allow/revoke/list)
- [ ] Whitelist enforcement working
- [ ] Error handling works (BMS unavailable, storage failure)

---

## 🎓 Learning Resources

### n8n Workflows
- n8n Documentation: https://docs.n8n.io
- Webhook Trigger: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/
- HTTP Request: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/
- Function Node: https://docs.n8n.io/code-examples/expressions/

### MS Teams Bot Framework
- Bot Framework Docs: https://docs.microsoft.com/en-us/azure/bot-service/
- Teams Webhooks: https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/

### Redis
- Redis Commands: https://redis.io/commands
- TTL Management: https://redis.io/commands/ttl

---

## 🆘 Getting Help

### Troubleshooting

1. **Workflows not importing**
   - Check n8n is running: `curl http://localhost:5678/healthz`
   - Try manual import in n8n UI
   - Check workflow JSON syntax

2. **Tests failing after workflow creation**
   - Verify webhook URL in tests matches n8n
   - Check all workflows are activated (green toggle)
   - View n8n execution logs for errors

3. **Redis connection issues**
   - Check Redis: `redis-cli ping`
   - Restart: `./scripts/manage-services.sh restart`
   - Check logs: `tail -f /workspace/logs/redis.log`

4. **BMS API timeout**
   - Verify BMS API: `curl http://localhost:8000/health`
   - Check timeout settings in workflow (2500ms)

### Support Files
- Troubleshooting Guide: `/workspace/002-n8n/docs/troubleshooting.md`
- Implementation Status: `/workspace/002-n8n/IMPLEMENTATION_STATUS.md`

---

## 📊 Estimated Timeline

| Phase | Tasks | Time | Priority |
|-------|-------|------|----------|
| n8n Workflows | T016-T020 | 4-5 hours | **HIGH** |
| Extensions | T026-T027, T026a | 2-3 hours | **MEDIUM** |
| Unit Tests | T028-T029 | 1 hour | **MEDIUM** |
| Validation | T032-T033 | 1-2 hours | **HIGH** |

**Total Estimated Time**: 8-11 hours

**Recommended Approach**: Complete high-priority tasks first (workflows + validation), then add extensions and unit tests.

---

**Last Updated**: 2025-10-06  
**Status**: Ready for workflow implementation
