# BMS Agent Testing Guide

**Version:** Post-MVP (80% Complete)  
**Date:** 2025-10-04  
**Status:** Ready for staging deployment and testing

## Quick Start Testing

### 1. Service Health Check

```bash
# Check all services are running
./scripts/health_check.sh

# Expected output: All services should show "UP" or "connected"
```

### 2. API Health Validation

```bash
# Basic health check
curl http://localhost:8000/health | jq '.'

# Detailed health check
curl http://localhost:8000/health/detailed | jq '.'

# Expected: status: "healthy", all services connected
```

## New Features Testing (Post-MVP)

### Feature 1: Document Re-upload with Destructive Replacement (T036)

**Test Scenario:** Upload same document twice, verify old version is replaced

```bash
# First upload
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test_document.pdf" \
  -F "profile=general" | jq '.'

# Note the chunks_created count

# Second upload (same filename)
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test_document.pdf" \
  -F "profile=general" | jq '.'

# Expected response:
# {
#   "status": "success",
#   "replaced_existing": true,
#   "replacement_info": {
#     "deleted_chunks": <previous_chunk_count>,
#     "message": "Replaced existing document..."
#   }
# }
```

**Validation:**
- ✅ `replaced_existing` should be `true` on second upload
- ✅ `deleted_chunks` should match first upload's `chunks_created`
- ✅ New `document_id` generated for second upload

### Feature 2: Async Upload Queue (T037)

**Test Scenario:** Upload document asynchronously, track status

```bash
# Submit async upload
RESPONSE=$(curl -X POST http://localhost:8000/api/v1/documents/upload/async \
  -F "file=@test_document.pdf" \
  -F "profile=general")

echo $RESPONSE | jq '.'

# Extract job_id
JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Check status immediately
curl http://localhost:8000/api/v1/documents/status/$JOB_ID | jq '.'

# Wait a few seconds and check again
sleep 5
curl http://localhost:8000/api/v1/documents/status/$JOB_ID | jq '.'

# Check queue statistics
curl http://localhost:8000/api/v1/documents/queue/stats | jq '.'
```

**Expected Flow:**
1. Initial response: HTTP 202, status "queued"
2. After processing starts: status "processing", progress_percent increasing
3. After completion: status "completed", document_id populated
4. Queue stats show: queued, processing, completed counts

**Validation:**
- ✅ HTTP 202 Accepted returned immediately
- ✅ Status transitions: queued → processing → completed
- ✅ `progress_percent` increases during processing
- ✅ Final status includes `document_id` and `chunks_created`

### Feature 3: Document Deletion (T039)

**Test Scenario:** Delete a document by ID

```bash
# First, upload a document and note the document_id
UPLOAD_RESPONSE=$(curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test_document.pdf" \
  -F "profile=general")

DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | jq -r '.document_id')
echo "Document ID: $DOCUMENT_ID"

# Delete the document
curl -X DELETE http://localhost:8000/api/v1/documents/$DOCUMENT_ID -v

# Expected: HTTP 204 No Content (no response body)

# Try to delete again (should fail)
curl -X DELETE http://localhost:8000/api/v1/documents/$DOCUMENT_ID -v

# Expected: HTTP 404 Not Found
```

**Validation:**
- ✅ First deletion returns HTTP 204 No Content
- ✅ Second deletion returns HTTP 404 Not Found
- ✅ Check logs for deletion audit trail

## MVP Features Testing

### Semantic Search

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "railway connectivity",
    "limit": 5,
    "min_score": 0.7
  }' | jq '.'
```

**Validation:**
- ✅ Returns relevant results
- ✅ Results filtered by min_score
- ✅ Response includes relevance scores

### Hybrid Search

```bash
curl -X POST http://localhost:8000/api/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "railway connectivity",
    "limit": 5,
    "vector_weight": 0.7,
    "keyword_weight": 0.3
  }' | jq '.'
```

### Rate Limiting Test

```bash
# Send rapid requests to trigger rate limit
for i in {1..70}; do
  curl -X POST http://localhost:8000/api/v1/search/semantic \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "limit": 5}' \
    -w "\nStatus: %{http_code}\n" \
    -s -o /dev/null
done

# Expected: First 60 succeed (200), then 429 (Too Many Requests)
```

## Performance Testing

### 1. Locust Load Test (20 concurrent users)

```bash
# Install locust if not already installed
pip install locust

# Run load test
locust -f tests/performance/load/test_locust.py \
  --headless -u 20 -r 5 -t 5m \
  --host http://localhost:8000 \
  --json > performance-results.json

# View results
cat performance-results.json | jq '.'
```

**Target Metrics (MVP):**
- p95 latency < 200ms
- Document processing ≥ 10 docs/min
- 0% error rate

### 2. Retrieval Accuracy Evaluation

```bash
# Run evaluation script
python scripts/evaluate_retrieval.py

# Expected output: ≥95% top-5 accuracy
```

### 3. Concurrent Upload Test

```bash
# Test async queue with multiple simultaneous uploads
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/documents/upload/async \
    -F "file=@test_document_$i.pdf" \
    -F "profile=general" &
done

wait

# Check queue stats
curl http://localhost:8000/api/v1/documents/queue/stats | jq '.'
```

## Monitoring & Observability Testing

### 1. Metrics Endpoint

```bash
# Check Prometheus metrics
curl http://localhost:8000/metrics/uplink

# Verify metrics include:
# - Request latency histogram
# - Request counts
# - Error counts
```

### 2. Grafana Dashboard (if deployed)

**Manual Steps:**
1. Import `grafana/dashboards/bms-agent.json` into Grafana
2. Verify panels display data:
   - API Latency (p50/p95/p99)
   - Request Throughput
   - Error Rate
   - Service Health
   - Document Processing Stats

### 3. Prometheus Alerts (if deployed)

```bash
# Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# Verify alert rules loaded
curl http://localhost:9090/api/v1/rules
```

## Integration Testing

### Slack Integration

```bash
# Test Slack slash command (requires Slack workspace)
# In Slack: /bms-search railway connectivity

# Expected: Formatted response with search results
```

### OpenWebUI Tool

**Manual Steps:**
1. Open OpenWebUI at http://localhost:3000
2. Install tool from `tools/bms_search.py`
3. Test search function in chat
4. Verify results display correctly

## Backup & Recovery Testing

### 1. Backup System

```bash
# Run manual backup
./scripts/backup_system.sh

# Verify backup created
ls -lh /workspace/backups/

# Verify backup integrity
./scripts/verify_backup.sh
```

### 2. Restoration Test

```bash
# Simulate data loss (CAUTION: test environment only!)
# Stop services first
./scripts/start_all_services.sh stop

# Restore from backup
./scripts/restore_backup.sh all

# Restart services
./scripts/start_all_services.sh start

# Verify data restored
curl http://localhost:8000/health/detailed | jq '.'
```

## CI/CD Pipeline Testing

### 1. Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Expected: All hooks pass (or auto-fix issues)
```

### 2. GitHub Actions (if pushed to GitHub)

**Manual Steps:**
1. Push to GitHub repository
2. Check Actions tab for CI/CD pipeline
3. Verify all jobs pass:
   - Pre-commit checks
   - Code quality & security
   - Tests & coverage
   - Performance baseline
   - Retrieval accuracy

## Regression Testing

### Test Suite Execution

```bash
# Run all tests
pytest -v --cov=./ --cov-report=term-missing

# Expected: ≥80% coverage, all tests pass
```

### Specific Test Categories

```bash
# Unit tests only
pytest tests/ -v -m unit

# Integration tests
pytest tests/ -v -m integration

# Performance tests
pytest tests/performance/ -v
```

## Security Testing

### 1. Security Headers Validation

```bash
# Check security headers present
curl -I http://localhost:8000/health

# Expected headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
```

### 2. Rate Limiting Validation

```bash
# Test rate limit enforcement
# (See Rate Limiting Test above)
```

### 3. Input Validation

```bash
# Test invalid file type
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test.exe" \
  -F "profile=general"

# Expected: HTTP 400, error message about invalid file type

# Test oversized file (if you have one)
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@large_file_over_1gb.pdf" \
  -F "profile=general"

# Expected: HTTP 413, error about file size limit
```

## Staging Deployment Checklist

### Pre-Deployment
- [ ] All services running (`./scripts/health_check.sh`)
- [ ] Qdrant collection initialized
- [ ] Embedding model loaded
- [ ] Backup system configured
- [ ] Monitoring configured (Prometheus/Grafana)

### Deployment Steps
1. [ ] Pull latest code: `git pull origin 001-bms-agent`
2. [ ] Install dependencies: `pip install -r requirements.txt`
3. [ ] Run migrations (if any): Check `docs/migrations.md`
4. [ ] Restart services: `./scripts/start_all_services.sh restart`
5. [ ] Verify health: `./scripts/health_check.sh`

### Post-Deployment Validation
- [ ] Health checks pass
- [ ] Upload test document successfully
- [ ] Search returns results
- [ ] Async upload works
- [ ] Document deletion works
- [ ] Monitoring displays metrics
- [ ] Backups running

## Test Results Template

```markdown
## Test Execution Report

**Date:** YYYY-MM-DD  
**Tester:** [Name]  
**Environment:** Staging/Production  
**Version:** Post-MVP (80%)

### Feature Tests
- [ ] Document re-upload: PASS/FAIL
- [ ] Async upload queue: PASS/FAIL
- [ ] Document deletion: PASS/FAIL
- [ ] Semantic search: PASS/FAIL
- [ ] Hybrid search: PASS/FAIL
- [ ] Rate limiting: PASS/FAIL

### Performance Tests
- [ ] Load test (20 users): PASS/FAIL
  - p95 latency: ___ms (target: <200ms)
  - Error rate: ___% (target: 0%)
- [ ] Retrieval accuracy: ___% (target: ≥95%)
- [ ] Document processing: ___ docs/min (target: ≥10)

### Integration Tests
- [ ] Slack integration: PASS/FAIL
- [ ] OpenWebUI tool: PASS/FAIL
- [ ] Monitoring: PASS/FAIL
- [ ] Backups: PASS/FAIL

### Issues Found
1. [Issue description]
2. [Issue description]

### Recommendations
1. [Recommendation]
2. [Recommendation]
```

## Troubleshooting

### Service Not Starting
```bash
# Check logs
tail -100 /workspace/logs/api.log
tail -100 /workspace/logs/qdrant.log

# Check ports
netstat -tulpn | grep -E ':(8000|6333|11434)'

# Restart services
./scripts/start_all_services.sh restart
```

### Async Queue Not Processing
```bash
# Check queue stats
curl http://localhost:8000/api/v1/documents/queue/stats | jq '.'

# Check API logs for worker errors
tail -f /workspace/logs/api.log | grep -i "worker\|queue"

# Restart API to restart worker
pkill -f "uvicorn api.main:app"
./scripts/start_all_services.sh start
```

### Performance Issues
```bash
# Check system resources
htop
nvidia-smi

# Check Qdrant performance
curl http://localhost:6333/metrics

# Review performance baseline
cat reports/performance-baseline.md
```

## Next Steps After Testing

1. **Document Results:** Fill out test results template
2. **Fix Issues:** Address any failures found during testing
3. **Performance Tuning:** Optimize based on load test results
4. **Production Prep:** Begin implementing T043-T055 for production readiness

---

**Happy Testing! 🧪**
