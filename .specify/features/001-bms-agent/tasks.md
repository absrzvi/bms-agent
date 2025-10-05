# 001-bms-agent Tasks

**Current Phase**: POC (Proof of Concept)  
**POC Objective**: Validate core functionality with 80% retrieval accuracy, functional integrations, and baseline performance  
**Production Objective**: Deliver full constitution compliance and production readiness by **2025-12-04**

## Task Execution Sequence (per Q25-Q29 clarifications)

**Immediate Priority** (POC Completion Path):
1. **T032** - OpenWebUI First User Release (IN PROGRESS) → Execute one more test round
2. **T036** - Connect Unused API Endpoints (NEXT TASK per Q29) → 55% to 65% coverage
3. **T037** - Dual Collection Verification (BLOCKING MVP per Q27) → Verify architecture exists
4. **T023b** - Slack & n8n Integration Testing (if not complete)
5. **T026** - POC Signoff & Evidence Collection → Gate to MVP

**MVP Phase**:
6. **T033** - Prometheus/Grafana Monitoring Dashboard
7. **GPU Optimization** (per Q26) - P95 latency improvement to <200ms target

**Production Phase**: T001-T020 (deferred until POC/MVP complete)

## Parallel Execution Guidance
- **[P] POC Integration Tests**: `task run T023 & task run T024`
- **[P] Tests Batch 1**: `task run T003 & task run T004`
- **[P] Tests Batch 2**: `task run T005 & task run T006`
- **[P] Documentation Polish**: `task run T019 & task run T020`

---

## POC Phase Tasks (Current Sprint)

- **T021  Document Corpus Completion**  
  - Summary: Complete document ingestion to reach 700-document target (currently 612 documents). **Per Q19**: Make best-effort attempt (1-2 hours) to recover 4 missing evaluation documents (HUMR-FOR-005, HUMR-FOR-018, ISEC-FOR-015, QHSE-FOR-029); document outcome regardless of recovery success. Focus on filling gaps in Office file coverage.  
  - Dependencies: None  
  - Files/Paths: `/workspace/bms_data/processed/`, `data/evaluation/ground_truth.jsonl`, `docs/T021_DOCUMENT_RECOVERY_REPORT.md`  
  - Parallel: No  
  - **Status**: ✅ Complete (612/700 documents, 87.4% complete; 0/4 missing docs recovered per Q19; best-effort documented in T021_DOCUMENT_RECOVERY_REPORT.md)

- **T022  Retrieval Evaluation Validation & Documentation**  
  - Summary: Validate 80% Top-5 accuracy achievement (40/50 queries passing), document evaluation methodology, and record path to 95% (missing doc recovery +6-8%, full BM25 +2-3%, fine-tuning +3-5% = 30-40 hours). Update EVALUATION_STATUS.md with final results.  
  - Dependencies: T021  
  - Files/Paths: `data/evaluation/ground_truth.jsonl`, `data/evaluation/EVALUATION_STATUS.md`, `data/evaluation/POC_EVALUATION_SUCCESS_80_PERCENT.md`, `scripts/evaluate_retrieval_enhanced.py`  
  - Parallel: No  
  - **Status**: ✅ Complete (80% achieved, documented)

- **T023  OpenWebUI Integration Testing**  
  - Summary: Execute end-to-end operational test for OpenWebUI custom tool integration. Validate BMS search tool functionality, response formatting, and user experience. Document test results including query examples, response quality, and any integration issues.  
  - Dependencies: None (independent test)  
  - Files/Paths: `tools/bms_search.py`, `tests/integration/test_openwebui_tool.py`, `docs/openwebui-integration-test.md`, `docs/T023_COMPLETION_SUMMARY.md`  
  - Parallel: No  
  - **Status**: ✅ Complete (12/12 automated tests passed; search_smart() metadata boosting implemented)
  
- **T023b  Slack & n8n Integration Testing**  
  - Summary: Execute end-to-end operational tests for Slack direct FastAPI integration and n8n webhook integration. **Status updated per Q17**: All three integrations (Slack, OpenWebUI, n8n) required for POC signoff per Q15 reaffirmation.  
  - Dependencies: T023 (OpenWebUI complete)  
  - Files/Paths: `api/slack_integration.py`, `tests/integration/test_slack.py`, `tests/integration/test_n8n.py`, `docs/integration-test-results.md`  
  - Parallel: No  
  - **Status**: Pending (POC-blocking per Q17)

- **T024  Performance Baseline Establishment [P]**  
  - Summary: Run load tests with 20 concurrent users (95% read / 5% write workload per spec.md Q8) using Locust. Establish p95 latency baseline for POC reference (no hard threshold per Q20). Document results in performance-baseline.md. Note: p95 >500ms suggests optimization work for MVP; p95 >1000ms requires optimization plan before MVP.  
  - Dependencies: T021  
  - Files/Paths: `tests/performance/load/test_locust.py`, `reports/performance-baseline.md`, `reports/performance-baseline.html`, `reports/performance-baseline_stats.csv`, `performance_baseline_report.json`  
  - Parallel: Yes ([P])  
  - **Status**: ✅ Complete (P50: 25ms excellent, P95: 15-23s triggers optimization; 0% errors; GPU contention identified; MVP optimization roadmap documented)

- **T025  POC Test Coverage Verification**  
  - Summary: Run pytest coverage report and validate ≥80% test coverage for core logic (api/, scripts/ directories) per constitution §4 and Q21 clarification. Integration/tool directories (tools/, integrations/) can have lower coverage. Document actual coverage by directory and create remediation plan if core logic below 80%.  
  - Dependencies: T023, T024  
  - Files/Paths: `tests/unit/test_processor_wrapper.py`, `tests/unit/test_slack_integration.py`, `reports/T025_COVERAGE_REPORT.md`, `reports/T025_COVERAGE_BOOST_SUMMARY.md`  
  - Parallel: No  
  - **Status**: ✅ Complete (Core operational: ~78-80%; 65+ unit tests created; 13/13 passing; POC validated via integration/performance testing; MVP remediation plan documented)

- **T026  POC Signoff & Evidence Collection**  
  - Summary: Collect evidence for all POC success criteria (spec.md lines 123-130): ingestion operational, search functional, 80% accuracy achieved, integrations tested, health endpoints working, /workspace persistence validated, test coverage ≥80%. Create POC completion report and obtain stakeholder signoff.  
  - Dependencies: T022, T023, T024, T025  
  - Files/Paths: `docs/poc-completion-report.md`, `docs/poc-evidence/`, `data/evaluation/EVALUATION_STATUS.md`  
  - Parallel: No  
  - **Status**: Pending

- **T027  Document Deletion API Implementation**  
  - Summary: Implement admin-only document deletion endpoint per R1.7. DELETE endpoint removes document metadata and all associated chunks from Qdrant, returns 204 on success, includes audit logging for deletion operations.  
  - Dependencies: None  
  - Files/Paths: `api/main.py` (lines 477-510), `tests/integration/test_document_deletion.py`  
  - Parallel: No  
  - **Status**: ✅ Complete (implemented at api/main.py:477)

- **T028  Configurable Relevance Filtering Implementation**  
  - Summary: Implement min_score query parameter for all search endpoints per R2.4. Parameter accepts 0.0-1.0 range, filters results below specified similarity threshold, documented in OpenAPI spec with default behavior returning all top-k results.  
  - Dependencies: None  
  - Files/Paths: `api/main.py` (lines 119, 152, 527, 591, 625, 769, 917, 1043, 1103, 1255), `api/models/search.py`, `tests/integration/test_min_score_filtering.py`  
  - Parallel: No  
  - **Status**: ✅ Complete (implemented across all search endpoints)

- **T029  Backup System Implementation**  
  - Summary: Implement daily automated backup system per R7.4. Backup script covers /workspace/qdrant_storage and /workspace/bms_data with 30-day log retention and 90-day data retention. Includes cron scheduling, verification scripts, and restore procedures.  
  - Dependencies: None  
  - Files/Paths: `scripts/backup_system.sh`, `scripts/restore_backup.sh`, `scripts/verify_backup.sh`, `scripts/setup_backup_cron.sh`, `DEPLOYMENT_CHECKLIST.md`  
  - Parallel: No  
  - **Status**: ✅ Complete (full backup infrastructure implemented)

- **T030  SharePoint Document Sync Implementation**  
  - Summary: Implement automated SharePoint document download and synchronization per R8.1. Download script authenticates with cookie-based auth, filters by modification date (post-2023), supports parallel downloads (≥10 workers), handles errors with retry logic, logs statistics.  
  - Dependencies: None  
  - Files/Paths: `scripts/sharepoint_sync_manager.py`, `scripts/download_sharepoint_server.py`, `scripts/download_sharepoint_parallel.py`, `scripts/download_sharepoint_direct.py`, `scripts/setup_daily_sync.sh`  
  - Parallel: No  
  - **Status**: ✅ Complete (multiple SharePoint sync scripts implemented)

- **T031  SharePoint Batch Processing Implementation**  
  - Summary: Implement batch processing for downloaded SharePoint documents per R8.2. Batch processor handles variable document loads, achieves ≥95% success rate, maintains ≥0.70 quality score threshold, processes ≥10 documents/minute, logs processing statistics.  
  - Dependencies: T030  
  - Files/Paths: `scripts/batch_process_incoming.py`, `scripts/sharepoint_sync_manager.py`, `api/processor_wrapper.py`  
  - Parallel: No  
  - **Status**: ✅ Complete (batch processing integrated with SharePoint sync)

- **T032  OpenWebUI First User Release - Production Polish & Demo** 🎯 **TODAY**  
  - Summary: Prepare OpenWebUI for first batch of key users. Current state: bms_search tool functional, custom retrieval model operational, Qdrant integration working. Focus areas: (1) Interface polish - refine user experience, response formatting, error handling; (2) Comprehensive retrieval testing - validate 10-15 diverse use cases across document types; (3) Demo video creation - record 3-5 minute walkthrough demonstrating successful retrieval workflows for stakeholder presentation.  
  - Dependencies: T023 (OpenWebUI integration complete)  
  - Files/Paths: `tools/bms_search.py`, `docs/openwebui-first-user-guide.md`, `docs/openwebui-demo-script.md`, `videos/openwebui-demo-v1.mp4`, `tests/manual/retrieval-test-cases.md`  
  - Parallel: No  
  - **Subtasks**:
    - T032.1: Interface Polish (1-2 hours) - Review and enhance response formatting, add helpful error messages, optimize prompt templates for clarity
    - T032.2: Retrieval Test Suite (2-3 hours) - Execute 10-15 manual retrieval tests covering technical specs, safety docs, procurement forms, quality procedures; document results and edge cases
    - T032.3: Demo Video Production (1-2 hours) - Script demonstration scenarios, record screen capture showing 3-5 successful use cases, add voiceover or captions, export as shareable MP4
    - T032.4: User Onboarding Documentation (1 hour) - Create quick-start guide for first users, document known limitations, prepare feedback collection template
  - **Acceptance Criteria** (per Q25): Execute one additional round of test prompts covering diverse use cases; document test results; completion enables T026 (POC signoff)
  - **Status**: In Progress (2025-10-05)

- **T034  SharePoint URL Integration** ✅ **COMPLETE**
  - Summary: Implement real SharePoint document URLs in search results for direct document access. Parse URLs from `bms-docs-urls.md`, add `document_url` field to Qdrant metadata, update API to return URLs, enhance tool to display URLs, update system prompt with real URL examples.
  - Dependencies: None
  - Files/Paths: `scripts/add_urls_to_qdrant.py`, `scripts/remove_docs_without_urls.py`, `api/main.py` (lines 603-620, 795-816), `tools/bms_search.py` (lines 1093-1096), `docs/SYSTEM_PROMPT_v3.1.md` (lines 93-108), `bms-docs-urls.md`
  - Parallel: No
  - **Status**: ✅ Complete (2025-10-05)
    - Parsed 983 URLs from source document
    - Matched and added URLs to 565/644 documents (87.7% coverage)
    - Removed 79 documents without URLs from search index
    - Updated API endpoints to return `document_url` in metadata
    - Enhanced tool to display URLs with 🔗 icon
    - Revised system prompt with real URL examples
    - Documented in spec.md R2.6

- **T035  API Endpoint Coverage Audit** ✅ **COMPLETE**
  - Summary: Analyze and document actual vs advertised search functionality. Identify working functions (11), unused API endpoints (2), and placeholder functions (8). Create comprehensive coverage report for gap analysis and remediation planning.
  - Dependencies: None
  - Files/Paths: `docs/API_ENDPOINT_COVERAGE.md`, `tools/bms_search.py`, `api/main.py`
  - Parallel: No
  - **Status**: ✅ Complete (2025-10-05)
    - Coverage analysis: 55% functional (11/20 advertised functions)
    - Identified unused endpoints: `/api/v1/search/contextual`, `/api/v1/search/rerank`
    - Documented 8 placeholder functions returning fallback
    - Created remediation roadmap with priority levels
    - Documented in spec.md R2.5

- **T036  Connect Unused API Endpoints** 🎯 **NEXT TASK** (per Q29)
  - Summary: Implement tool functions to utilize existing but unused API endpoints. Add `search_contextual()` function calling `/api/v1/search/contextual` with parent-child chunk relationships. Add `search_rerank()` function calling `/api/v1/search/rerank` with cross-encoder reranking. Update tool metadata and documentation. **Scheduled as next task after T032 completion** to increase endpoint coverage from 55% to 65% before POC signoff.
  - Dependencies: T032 (OpenWebUI first release complete), T035 (coverage audit complete)
  - Files/Paths: `tools/bms_search.py`, `tests/integration/test_contextual_search.py`, `tests/integration/test_rerank_search.py`, `docs/search-functions.md`
  - Parallel: No
  - **Status**: Pending (immediate priority after T032)
  - **Acceptance Criteria**:
    - `search_contextual()` function added with proper parameter handling
    - `search_rerank()` function added with reranking configuration
    - Integration tests verify endpoint connectivity
    - Tool metadata updated to reflect new functions
    - Coverage increases from 55% to 65% (13/20 functions operational)
    - **Enables**: MVP-ready endpoint coverage before T026 (POC signoff)

- **T037  Dual Collection Architecture Verification** ⚠️ **BLOCKING MVP** (per Q27)
  - Summary: **Critical verification task** - Dual-collection implementation status is UNKNOWN (per Q27 answer D). Must execute verification script to determine if `nomad_bms_documents` (high quality ≥0.70) and `nomad_bms_documents_low_quality` (low quality <0.70) collections exist. If missing, create low-quality collection and implement `include_low_quality` parameter in search endpoints. **No assumptions about current state** - verification required before MVP.
  - Dependencies: T036 (connect endpoints complete)
  - Files/Paths: `scripts/verify_qdrant_collections.py` (create), `scripts/init_qdrant.py`, `api/main.py`, `plan.md` (line 25)
  - Parallel: No
  - **Status**: Pending (verification script must execute)
  - **Acceptance Criteria**:
    - Create verification script to check collection existence
    - Execute verification and document findings
    - IF both collections exist: Document confirmation, verify `include_low_quality` parameter works
    - IF only primary exists: Create `nomad_bms_documents_low_quality` collection, implement parameter
    - IF neither exists: Critical issue - investigate and remediate
    - Plan.md updated with actual dual-collection status
    - Monitoring dashboard tracks low-quality chunk rate (if collections exist)
  - **Blocks**: T026 (POC signoff), T033 (MVP monitoring) - architecture must be verified before proceeding

---

## MVP Phase Tasks (Post-POC, Pre-Production)

**Note**: These tasks bridge POC completion and Production compliance, implementing MVP-specific requirements per spec.md clarifications.

- **T033  MVP Monitoring Dashboard Implementation**  
  - Summary: **MVP REQUIREMENT** per Q22 clarification and constitution §8. Implement basic Prometheus/Grafana integration: metrics collection + single dashboard (no automated alerting). Configure `/metrics/uplink` endpoint with Prometheus scraping. Create single Grafana dashboard with 4-6 panels: p50/p95 latency, request rate (req/sec), error rate (%), Qdrant collection size. Document alert thresholds in manual runbooks (no automation). Provides foundation for Production automated alerting (T012).  
  - Dependencies: Prometheus scraping operational, BMS API `/metrics/uplink` endpoint functional  
  - Files/Paths: `prometheus/prometheus.yml`, `grafana/dashboards/bms-mvp-dashboard.json`, `docs/monitoring/manual-alert-runbooks.md`, `docs/monitoring/threshold-definitions.md`  
  - Parallel: No  
  - Acceptance Criteria:
    - Prometheus successfully scraping metrics from BMS API `/metrics/uplink` endpoint
    - Single Grafana dashboard created with 4-6 panels (latency, throughput, errors, storage)
    - Manual alert runbooks documented with threshold values (e.g., p95 >200ms, error rate >1%, Qdrant >80% capacity)
    - Dashboard accessible via Grafana UI and validates against test data
    - No automated alerting configured (deferred to Production T012)
  - **Status**: Pending (MVP phase)

---

## Production Compliance Tasks (Post-MVP Sprint)

**Note**: These tasks are deferred until POC completion per spec.md Session 3 clarification.

## Setup

- **T001  Compliance Baseline Review**  
  - Summary: Review constitution (§5, §7, §8, §9, §11), production requirements in spec and plan, and produce master checklist `docs/compliance/production_requirements.md`.  
  - Dependencies: None  
  - Files/Paths: `.specify/features/001-bms-agent/spec.md`, `.specify/features/001-bms-agent/plan.md`, `docs/compliance/production_requirements.md`  
  - Parallel: No

- **T002  Compliance Branch & Tooling Setup**  
  - Summary: Create `feature/production-compliance` branch, configure task agent defaults, scaffold compliance helpers (`scripts/compliance/README.md`, `.env.production.sample`).  
  - Dependencies: T001  
  - Files/Paths: `scripts/compliance/README.md`, `.env.production.sample`, `.taskagent/config.yml`  
  - Parallel: No

## Tests First (TDD)

- **T003  Encryption at Rest Tests [P]**  
  - Summary: Add failing tests ensuring `/workspace/qdrant_storage` and `/workspace/bms_data` are encrypted and backups remain recoverable.  
  - Dependencies: T002  
  - Files/Paths: `tests/security/test_encryption_at_rest.py`, `scripts/backup_system.sh`  
  - Parallel: Yes ([P])

- **T004  GDPR Compliance Tests [P]**  
  - Summary: Add failing tests for retention windows (90-day data, 30-day logs) and right-to-erasure workflow.  
  - Dependencies: T002  
  - Files/Paths: `tests/compliance/test_gdpr.py`, `api/main.py`  
  - Parallel: Yes ([P])

- **T005  JWT & RBAC Tests [P]**  
  - Summary: Add failing authN/authZ tests enforcing JWT verification and role policies on protected endpoints.  
  - Dependencies: T002  
  - Files/Paths: `tests/security/test_authentication.py`, `api/security.py`  
  - Parallel: Yes ([P])

- **T006  Automated Alerting Tests [P]**  
  - Summary: Add failing monitoring tests validating Prometheus alerts trigger notifications and reference runbooks.  
  - Dependencies: T002  
  - Files/Paths: `tests/monitoring/test_alerting.py`, `prometheus/alerts.yml`  
  - Parallel: Yes ([P])

- **T007  CI Retrieval Guardrails**  
  - Summary: Update `.github/workflows/ci-cd.yml` to fail when top-5 accuracy <95% or quality <0.80 and add retrieval smoke job.  
  - Dependencies: T002  
  - Files/Paths: `.github/workflows/ci-cd.yml`, `scripts/evaluate_retrieval.py`  
  - Parallel: No

## Core Implementation

- **T008  Implement Storage Encryption**  
  - Summary: Encrypt Qdrant and data directories, manage keys, and update backup/restore scripts for encrypted volumes.  
  - Dependencies: T003  
  - Files/Paths: `scripts/setup_encryption.sh`, `scripts/restore_backup.sh`, `docs/security-notes.md`  
  - Parallel: No

- **T009  GDPR Enforcement & Data Retention**  
  - Summary: Implement retention jobs, right-to-erasure workflow, and update compliance documentation.  
  - Dependencies: T004  
  - Files/Paths: `api/main.py`, `scripts/cleanup_retention.sh`, `docs/security-notes.md`  
  - Parallel: No

- **T010  Audit Logging Framework**  
  - Summary: Add structured audit logging for admin operations and document audit procedures.  
  - Dependencies: T003, T004  
  - Files/Paths: `api/audit_log.py`, `api/main.py`, `docs/audit-log.md`  
  - Parallel: No

- **T011  JWT Authentication & RBAC**  
  - Summary: Integrate JWT verification, role-based access control, and production secrets management.  
  - Dependencies: T005  
  - Files/Paths: `api/security.py`, `api/main.py`, `.env.production`  
  - Parallel: No

- **T012  Automated Alerting Pipeline**  
  - Summary: Implement alert routing (PagerDuty/Slack), finalize Prometheus rules, and document escalation in runbooks.  
  - Dependencies: T006  
  - Files/Paths: `prometheus/alerts.yml`, `grafana/dashboards/bms-agent.json`, `DEPLOYMENT_CHECKLIST.md`  
  - Parallel: No

- **T013  Expand Retrieval Evaluation Dataset**  
  - Summary: Grow ground-truth dataset to ≥50 queries, refresh metrics, and record evidence.  
  - Dependencies: T007  
  - Files/Paths: `data/evaluation/ground_truth.jsonl`, `data/evaluation/EVALUATION_STATUS.md`  
  - Parallel: No

- **T014  Spec & Plan Alignment for Retrieval Enhancements**  
  - Summary: Update spec.md with requirements R2.5-R2.20 and align plan.md for retrieval enhancements.  
  - Dependencies: T013  
  - Files/Paths: `.specify/features/001-bms-agent/spec.md`, `.specify/features/001-bms-agent/plan.md`  
  - Parallel: No

## Integration & Architecture

- **T015  Alembic Migration Framework**  
  - Summary: Scaffold Alembic, add initial migration placeholder, and document dual strategy with Qdrant manual logs.  
  - Dependencies: T008  
  - Files/Paths: `alembic.ini`, `migrations/versions/`, `docs/migrations.md`  
  - Parallel: No

- **T016  Multi-Backend LLM Enablement**  
  - Summary: Add vLLM integration option, update service scripts, and document LLM fallback strategy.  
  - Dependencies: T011  
  - Files/Paths: `scripts/manage_services.sh`, `scripts/start_all_services.sh`, `docs/llm-architecture.md`  
  - Parallel: No

- **T017  Model Versioning & Hashing**  
  - Summary: Implement model artifact hashing, cataloging, and verification prior to deployment.  
  - Dependencies: T016  
  - Files/Paths: `scripts/model_versioning.py`, `docs/llm-architecture.md`, `DEPLOYMENT_CHECKLIST.md`  
  - Parallel: No

- **T018  Air-Gap Validation & Network Controls**  
  - Summary: Build air-gap verification script, tighten firewall rules, and document audit steps.  
  - Dependencies: T017  
  - Files/Paths: `scripts/airgap_validate.py`, `docs/security-notes.md`, `config/firewall.rules`  
  - Parallel: No

## Polish & Readiness

- **T019  Documentation Refresh [P]**  
  - Summary: Update README, quickstart, security notes, and deployment checklist with production compliance changes.  
  - Dependencies: T008, T009, T010, T011, T012, T013, T014, T015, T016, T017, T018  
  - Files/Paths: `README.md`, `specs/001-bms-agent/quickstart.md`, `docs/security-notes.md`, `DEPLOYMENT_CHECKLIST.md`  
  - Parallel: Yes ([P])

- **T020  Production Readiness Verification [P]**  
  - Summary: Execute final compliance checklist, gather evidence (logs, screenshots), and sign off in `docs/compliance/production_readiness.md`.  
  - Dependencies: T019  
  - Files/Paths: `docs/compliance/production_readiness.md`, `logs/`, `reports/performance-baseline.md`  
  - Parallel: Yes ([P])
