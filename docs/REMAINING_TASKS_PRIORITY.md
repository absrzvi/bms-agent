# Remaining Tasks Priority & Implementation Plan

## Overview
This document prioritizes the 11 remaining tasks (39%) required to complete the BMS Agent MVP. Tasks are ordered by business value and dependency requirements.

**Current Status**: 17/28 tasks complete (61%)  
**Remaining**: 11 tasks across Observability, Documentation, and Polish phases

---

## 🔴 **HIGH PRIORITY** (Blocks MVP Success Criteria)

### T025 - Retrieval Accuracy & Quality Evaluation
**Priority**: CRITICAL  
**Effort**: 2-3 days  
**Blocks**: R2.2 (≥95% top-5 accuracy requirement)  
**Dependencies**: T009, T011, T016

**Why Critical**: Validates core MVP success criteria - retrieval accuracy ≥95%

**Implementation Steps**:
1. Create `data/evaluation/ground_truth.jsonl` with 50+ query-document pairs
2. Implement `scripts/evaluate_retrieval.py` with RAGAS metrics
3. Compute top-5 accuracy, faithfulness, relevancy
4. Add CI hook to enforce ≥95% threshold
5. Document results in evaluation report

**Acceptance Criteria**:
- ✅ Ground truth dataset with ≥50 validated pairs
- ✅ Evaluation script reports ≥95% top-5 accuracy
- ✅ RAGAS metrics computed (faithfulness, relevancy, precision, recall)
- ✅ CI fails if accuracy drops below threshold

---

### T021 - Manual Alert Runbooks & Grafana Dashboards
**Priority**: HIGH  
**Effort**: 3-4 days  
**Blocks**: R7.1-R7.3 (Observability requirements), Constitution §8  
**Dependencies**: T014, T020

**Why High**: Required for 99.99% availability target and constitution compliance

**Implementation Steps**:
1. Configure Prometheus scrape targets for API and Qdrant
2. Create Grafana dashboards:
   - API latency (p50, p95, p99)
   - Request throughput
   - Error rates
   - Qdrant collection size
   - System resources (CPU, memory, disk)
3. Document manual alert runbooks in `DEPLOYMENT_CHECKLIST.md`:
   - API latency >100ms p95 procedures
   - Document ingestion failure escalation
   - Qdrant/Ollama dependency recovery
   - Contact matrix with timelines
   - Log analysis procedures

**Acceptance Criteria**:
- ✅ Prometheus scraping API metrics
- ✅ Grafana dashboards operational
- ✅ 5 comprehensive runbooks documented
- ✅ Contact matrix with escalation timelines
- ✅ Manual monitoring procedures documented

---

## 🟡 **MEDIUM PRIORITY** (Completes MVP Features)

### T015 - Basic Security Module Implementation
**Priority**: MEDIUM  
**Effort**: 1-2 days  
**Blocks**: T016, security requirements  
**Dependencies**: T011

**Implementation Steps**:
1. Create `api/security.py` with rate limiting (60 req/min per IP)
2. Implement token bucket algorithm (in-memory)
3. Add security headers middleware (X-Frame-Options, X-Content-Type-Options)
4. Add basic error responses (429 Too Many Requests)

**Acceptance Criteria**:
- ✅ Rate limiting enforced (60 req/min per IP)
- ✅ Security headers on all responses
- ✅ 429 errors for rate limit violations

---

### T016 - Security Wiring & Tests
**Priority**: MEDIUM  
**Effort**: 1 day  
**Blocks**: Integration completion  
**Dependencies**: T015, T005-T007

**Implementation Steps**:
1. Integrate security middleware into FastAPI app
2. Add tests for 400/413/429 error handling
3. Document production security roadmap in `docs/security-notes.md`
4. Update API documentation with rate limits

**Acceptance Criteria**:
- ✅ Security middleware integrated
- ✅ Tests pass for all error codes
- ✅ Production roadmap documented

---

### T019 - Manage Services Script
**Priority**: MEDIUM  
**Effort**: 1 day  
**Dependencies**: T003, T010

**Implementation Steps**:
1. Complete `scripts/manage_services.sh` with:
   - `start` - Start Qdrant and API
   - `stop` - Stop all services
   - `status` - Check service health
   - `restart` - Restart services
2. Add logging to `/workspace/logs/`
3. Add error handling and validation

**Acceptance Criteria**:
- ✅ All commands functional
- ✅ Proper logging
- ✅ Error handling

---

### T020 - Health Check Script
**Priority**: MEDIUM  
**Effort**: 1 day  
**Dependencies**: T013, T019

**Implementation Steps**:
1. Extend `scripts/health_check.sh` to probe:
   - API endpoints (/health, /metrics)
   - Ollama (model availability)
   - Qdrant (collection status)
   - OpenWebUI (if running)
2. Log results with timestamps
3. Add exit codes for automation

**Acceptance Criteria**:
- ✅ All services checked
- ✅ Timestamped logging
- ✅ Proper exit codes

---

## 🟢 **LOW PRIORITY** (Polish & Documentation)

### T022 - Quickstart Verification
**Priority**: LOW  
**Effort**: 0.5 days  
**Dependencies**: T010-T018  
**Parallel**: Yes [P]

**Implementation Steps**:
1. Walk through `quickstart.md`
2. Update with actual commands
3. Test all curl examples
4. Add troubleshooting tips

---

### T023 - README/Docs Sync
**Priority**: LOW  
**Effort**: 1 day  
**Dependencies**: T008-T021  
**Parallel**: Yes [P]

**Implementation Steps**:
1. Update `README.md` with current features
2. Refresh `TESTING.md` with test commands
3. Update `reports/performance-baseline.md`
4. Sync `docs/security-notes.md`

---

### T024 - Performance Baseline Publication
**Priority**: LOW  
**Effort**: 0.5 days  
**Dependencies**: T008, T014

**Implementation Steps**:
1. Run Locust performance suite
2. Capture JSON stats
3. Summarize in `reports/performance-baseline.md`
4. Document baseline metrics

---

### T026 - Pre-commit & CI Hooks
**Priority**: LOW  
**Effort**: 1 day  
**Dependencies**: T016, T023  
**Parallel**: Yes [P]

**Implementation Steps**:
1. Configure `.pre-commit-config.yaml`
2. Add Black, Ruff, mypy hooks
3. Update CI to enforce hooks
4. Document setup in README

---

### T027 - Release Pipeline Prep
**Priority**: LOW  
**Effort**: 1 day  
**Dependencies**: T015, T019, T026

**Implementation Steps**:
1. Draft container build steps
2. Add migration automation placeholders
3. Document release process

---

## 📅 **Recommended Implementation Order**

### Week 1: Critical Path
1. **T025** - Retrieval Evaluation (2-3 days) - CRITICAL
2. **T015** - Security Module (1-2 days)
3. **T016** - Security Wiring (1 day)

### Week 2: Observability
4. **T019** - Manage Services (1 day)
5. **T020** - Health Check Script (1 day)
6. **T021** - Alert Runbooks & Grafana (3-4 days)

### Week 3: Documentation & Polish
7. **T022** - Quickstart Verification (0.5 days) [P]
8. **T023** - README/Docs Sync (1 day) [P]
9. **T024** - Performance Baseline (0.5 days)
10. **T026** - Pre-commit Hooks (1 day) [P]
11. **T027** - Release Pipeline (1 day)

---

## 🎯 **Success Metrics**

### MVP Completion Criteria
- ✅ All 28 tasks complete (100%)
- ✅ Retrieval accuracy ≥95%
- ✅ Grafana dashboards operational
- ✅ Manual runbooks documented
- ✅ All documentation current
- ✅ Security baseline implemented

### Estimated Total Effort
- **High Priority**: 5-7 days
- **Medium Priority**: 4-5 days
- **Low Priority**: 4-5 days
- **Total**: 13-17 days (2.5-3.5 weeks)

---

## 🚀 **Quick Start Commands**

### Start Next Task
```bash
# T025 - Retrieval Evaluation
cd /workspace/001-bms-agent
mkdir -p data/evaluation
touch data/evaluation/ground_truth.jsonl
touch scripts/evaluate_retrieval.py
```

### Check Progress
```bash
# View tasks status
cat .specify/features/001-bms-agent/tasks.md | grep "✅\|📋"

# Count remaining
grep -c "📋" .specify/features/001-bms-agent/tasks.md
```

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-09-30  
**Next Review**: After T025 completion
