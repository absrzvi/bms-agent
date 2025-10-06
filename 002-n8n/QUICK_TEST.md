# Quick POC Test - Start Here

**Estimated Time**: 15 minutes
**Purpose**: Rapid validation before full POC testing

---

## Step 1: Check Services (2 minutes)

```bash
/workspace/002-n8n/scripts/manage-services.sh status
```

**Expected**: All 4 services running (n8n, Redis, BMS API, Ollama)

**If not all running:**
```bash
/workspace/002-n8n/scripts/manage-services.sh start
```

---

## Step 2: Health Check (1 minute)

```bash
curl -s http://localhost:5678/webhook/health | jq '.status'
```

**Expected**: `"healthy"`

**If "degraded"**: See which component failed
```bash
curl -s http://localhost:5678/webhook/health | jq '.components'
```

---

## Step 3: Run Automated Tests (5 minutes)

```bash
cd /workspace/002-n8n

# Run all tests
npm test

# Or run specific test suites:
npm test tests/contract/      # Contract tests
npm test tests/integration/   # Integration tests
npm test tests/unit/          # Unit tests
```

**Expected**: All tests pass ✅

**If tests fail**: Check the error output and refer to `/workspace/002-n8n/docs/troubleshooting.md`

---

## Step 4: Test Workflows Manually (5 minutes)

### Test 4.1: Query Analyzer
```bash
curl -X POST http://localhost:5678/webhook/query-analyzer \
  -H "Content-Type: application/json" \
  -d '{"query":"What are emergency brake procedures?"}'
```

**Expected**: Returns intent classification (ASK/SEARCH)

### Test 4.2: BMS API Caller
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"test query","max_chunks":5,"include_citations":true}'
```

**Expected**: Returns answer with citations

### Test 4.3: Context Manager
```bash
redis-cli PING
```

**Expected**: `PONG`

```bash
redis-cli SET test:key "test value" EX 60
redis-cli GET test:key
```

**Expected**: `"test value"`

---

## Step 5: Performance Quick Check (2 minutes)

```bash
# Test BMS API response time
time curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the brake system?","max_chunks":3}'
```

**Expected**: Total time < 2 seconds

---

## Quick Test Summary

After completing these 5 steps, you should have:

✅ All services running
✅ Health check passing
✅ Automated tests passing
✅ Workflows responding correctly
✅ Performance within acceptable range

**If all checks pass**: ✅ **System is ready for MS Teams integration**

**Next Step**: Follow `/workspace/002-n8n/docs/POC_TESTING_GUIDE.md` for full MS Teams bot testing

---

## Troubleshooting Quick Fixes

### Service Won't Start
```bash
# Check logs
tail -50 /workspace/n8n/.n8n/logs/n8n.log

# Restart service
/workspace/002-n8n/scripts/manage-services.sh restart <service-name>
```

### Tests Fail
```bash
# Check what's failing
npm test -- --verbose

# Common fixes:
# 1. Service not running → start it
# 2. Redis connection → check Redis is running
# 3. BMS API timeout → check BMS API is running
```

### Performance Issues
```bash
# Optimize Qdrant index
cd /workspace/001-bms-agent
python scripts/optimize_qdrant_index.py

# Check system resources
top
free -h
df -h
```

---

**Need Help?**
- Detailed guide: `/workspace/002-n8n/docs/POC_TESTING_GUIDE.md`
- Troubleshooting: `/workspace/002-n8n/docs/troubleshooting.md`
- Setup guide: `/workspace/002-n8n/docs/setup-ms-teams.md`
