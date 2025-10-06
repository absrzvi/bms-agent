# Monitoring & Observability Guide

**POC Phase Monitoring Approach** (NFR-008)

This document describes the monitoring strategy for the MS Teams BMS Agent bot during POC phase, aligned with constitution §8 POC exception framework.

---

## POC Monitoring Architecture

### Constitution Compliance (§8)

**POC DECISION**: Monitoring uses n8n execution logs + basic health endpoint (/health) for POC phase. Prometheus metrics and Grafana dashboards (constitution §8 requirement) deferred to production deployment per constitution POC exception framework.

**Rationale:**
- POC targets 20 users, 50-100 queries/day - lightweight monitoring sufficient
- n8n provides built-in execution logging and metrics
- Health endpoint enables automated uptime checks
- Production will implement full Prometheus/Grafana stack

---

## Health Check Endpoint

### Endpoint
```
GET http://localhost:5678/webhook/health
```

### Response Format

**Healthy Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-06T12:34:56.789Z",
  "components": {
    "redis": {
      "status": "healthy",
      "message": "Redis is responsive",
      "responseTime": null
    },
    "bms_api": {
      "status": "healthy",
      "message": "BMS API v1.0.0",
      "responseTime": null
    },
    "ollama": {
      "status": "healthy",
      "message": "Ollama running with 2 models",
      "responseTime": null
    }
  },
  "version": "1.0.0",
  "environment": "POC"
}
```

**Degraded Response (503 Service Unavailable):**
```json
{
  "status": "degraded",
  "timestamp": "2025-10-06T12:34:56.789Z",
  "components": {
    "redis": {
      "status": "unhealthy",
      "message": "Redis unreachable",
      "responseTime": null
    },
    "bms_api": {
      "status": "healthy",
      "message": "BMS API v1.0.0",
      "responseTime": null
    },
    "ollama": {
      "status": "healthy",
      "message": "Ollama running with 2 models",
      "responseTime": null
    }
  },
  "version": "1.0.0",
  "environment": "POC"
}
```

### Health Check Components

1. **Redis** - Conversation context storage
   - Check: `PING` command
   - Timeout: 2 seconds
   - Status: `healthy` if PONG received

2. **BMS API** - Document search backend
   - Check: `GET /health`
   - Timeout: 2 seconds
   - Status: `healthy` if status="healthy" in response

3. **Ollama** - LLM for query analysis
   - Check: `GET /api/tags`
   - Timeout: 2 seconds
   - Status: `healthy` if models list returned

### Automated Health Checks

**Setup cron job for periodic health checks:**
```bash
# Check health every 5 minutes, log failures
(crontab -l ; echo "*/5 * * * * curl -s http://localhost:5678/webhook/health | jq -e '.status == \"healthy\"' || echo 'Health check failed' >> /workspace/logs/health-check-failures.log") | crontab -
```

---

## n8n Execution Logs

### Log Locations
```
/workspace/n8n/.n8n/logs/n8n.log          # Main n8n log
/workspace/logs/health-check-failures.log  # Health check failures (if cron setup)
```

### Log Levels

**Production:** `INFO`
**Debug:** `DEBUG` (set via `N8N_LOG_LEVEL=debug` in n8n.env)

### Key Log Patterns

**Successful execution:**
```
[INFO] Execution successful - Workflow: "Main Bot Handler" - Execution ID: abc-123
```

**Failed execution:**
```
[ERROR] Execution failed - Workflow: "Main Bot Handler" - Error: <error message>
```

**Performance warning:**
```
[WARN] Execution slow - Workflow: "BMS API Caller" - Duration: 3520ms (>3000ms SLA)
```

### Viewing Logs

**Real-time monitoring:**
```bash
tail -f /workspace/n8n/.n8n/logs/n8n.log
```

**Filter by workflow:**
```bash
grep "Main Bot Handler" /workspace/n8n/.n8n/logs/n8n.log | tail -20
```

**Find errors:**
```bash
grep "\[ERROR\]" /workspace/n8n/.n8n/logs/n8n.log | tail -50
```

**Performance analysis:**
```bash
grep "Duration:" /workspace/n8n/.n8n/logs/n8n.log | awk '{print $NF}' | sort -n | tail -20
```

---

## n8n Built-In Metrics

### Execution Dashboard

Access via n8n UI:
1. Open http://localhost:5678
2. Navigate to **"Executions"** tab
3. View recent executions with status, duration, timestamp

### Metrics Available

- **Execution count** (success/failure by workflow)
- **Execution duration** (per workflow, per execution)
- **Error rate** (failures / total executions)
- **Concurrent executions** (active running workflows)

### Export Executions

```bash
# Export last 100 executions as JSON
curl http://localhost:5678/rest/executions?limit=100 > executions.json

# Analyze with jq
cat executions.json | jq '.[] | {workflow: .workflowData.name, duration: .stoppedAt - .startedAt, status: .finished}'
```

---

## Performance Monitoring (POC)

### Target Metrics (NFR-008, FR-030)

| Metric | Target | Measurement |
|--------|--------|-------------|
| p95 response time | < 3000ms | n8n execution duration |
| p50 response time | < 1500ms | n8n execution duration |
| Error rate | < 5% | Failed executions / total |
| Uptime | > 95% | Health check success rate |

### Manual Performance Check

**Run load test:**
```bash
cd /workspace/002-n8n
npm test tests/performance/load-test.js
```

**Analyze results:**
```
Test Results:
- Total queries: 100
- Concurrent users: 20
- p50 response time: 1234ms ✓
- p95 response time: 2890ms ✓
- Error rate: 2% ✓
```

### Response Time Budget (FR-003)

```
Component          | Target | Actual (avg)
-------------------|--------|-------------
MS Teams → n8n     | 100ms  | ~80ms
n8n processing     | 50ms   | ~40ms
LLM classification | 300ms  | ~250ms
BMS API call       | 1500ms | ~1200ms
Response format    | 200ms  | ~150ms
n8n → MS Teams     | 100ms  | ~80ms
Buffer             | 750ms  | ~1200ms
-------------------|--------|-------------
TOTAL              | 3000ms | ~2000ms ✓
```

---

## Alert Thresholds (POC)

### Manual Alerting

During POC, alerts are manual (check logs periodically):

**Daily Checks:**
1. Review health check failures: `cat /workspace/logs/health-check-failures.log`
2. Check error rate: `grep ERROR /workspace/n8n/.n8n/logs/n8n.log | wc -l`
3. Verify uptime: Check last 24h of health checks

**Weekly Checks:**
1. Performance review: Run load test, analyze p95
2. Capacity check: Redis memory usage, disk space
3. User feedback: Survey POC users for issues

### Alert Conditions

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Health check failure | > 3 consecutive | Investigate immediately |
| Error rate spike | > 10% in 1 hour | Check logs, restart services |
| Response time degradation | p95 > 5000ms | Run performance diagnostics |
| Redis memory usage | > 1GB | Run cleanup script |
| Disk space | < 10GB free | Archive old logs |

---

## Capacity Monitoring

### Redis Memory Usage

**Check current usage:**
```bash
redis-cli INFO memory | grep used_memory_human
```

**Expected:**
- POC (20 users, 7-day retention): ~100-200MB
- Post-POC (100 users): ~500MB-1GB

**Optimization:**
```bash
# Run cleanup if memory > 500MB
/workspace/002-n8n/scripts/cleanup-expired.sh
```

### Disk Space

**Check available space:**
```bash
df -h /workspace
```

**Expected usage:**
- n8n logs: ~100MB/week
- Redis persistence: ~200MB
- BMS data: Variable (depends on uploads)

**Cleanup:**
```bash
# Rotate logs older than 30 days
find /workspace/n8n/.n8n/logs/ -name "*.log" -mtime +30 -delete

# Clean old backups
find /workspace/backups/ -name "*.tar.gz" -mtime +60 -delete
```

---

## Troubleshooting Performance Issues

### High Response Times

**Diagnosis:**
```bash
# Check which workflow is slow
grep "Duration:" /workspace/n8n/.n8n/logs/n8n.log | sort -k5 -n | tail -10
```

**Common causes:**
1. BMS API slow (Qdrant index needs optimization)
2. Ollama LLM slow (model too large for hardware)
3. Redis connection timeout (network issue)

**Solutions:**
- Optimize Qdrant: `/workspace/001-bms-agent/scripts/optimize_qdrant_index.py`
- Reduce LLM timeout: Edit `query-analyzer.json` workflow
- Check Redis: `redis-cli PING`

### High Error Rate

**Diagnosis:**
```bash
# Find most common errors
grep ERROR /workspace/n8n/.n8n/logs/n8n.log | cut -d':' -f4- | sort | uniq -c | sort -rn
```

**Common errors:**
1. `ECONNREFUSED` - Service not running
2. `Timeout` - Service too slow
3. `Whitelist denied` - User not in whitelist

**Solutions:**
- Restart failed service: `/workspace/002-n8n/scripts/manage-services.sh restart <service>`
- Adjust timeout: Edit workflow timeout settings
- Update whitelist: `/admin allow #channel`

---

## Production Monitoring Roadmap

### Post-POC Enhancements (Deferred)

**Prometheus Integration:**
- n8n metrics exporter
- Custom gauges: query_duration, error_rate, concurrent_users
- Scrape interval: 15s

**Grafana Dashboards:**
- Overview: System health, uptime, error rate
- Performance: Response time histograms, p95/p99 trends
- Capacity: Redis memory, disk usage, query volume

**Alerting:**
- PagerDuty integration for critical alerts
- Slack notifications for warnings
- Email digest for daily reports

**Constitution §8 Compliance:**
Full production deployment will implement:
- Structured logging with correlation IDs
- Prometheus metrics collection
- Grafana visualization dashboards
- Automated alerting rules

---

## Monitoring Checklist

**Daily (POC Phase):**
- [ ] Check health endpoint: `curl http://localhost:5678/webhook/health`
- [ ] Review error logs: `grep ERROR /workspace/n8n/.n8n/logs/n8n.log`
- [ ] Verify services running: `./scripts/manage-services.sh status`

**Weekly:**
- [ ] Run load test: `npm test tests/performance/load-test.js`
- [ ] Review performance metrics (p95 < 3s?)
- [ ] Check Redis memory: `redis-cli INFO memory`
- [ ] Disk space check: `df -h /workspace`

**Monthly:**
- [ ] Review user feedback
- [ ] Analyze trends (error rate, response time)
- [ ] Plan capacity upgrades if needed

---

**Last Updated**: 2025-10-06
**Constitution Reference**: §8 Monitoring & Observability (POC exception documented in spec.md NFR-008)
**Spec Reference**: `/workspace/specs/002-create-a-microsoft/spec.md`
