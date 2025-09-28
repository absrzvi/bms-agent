# BMS Agent Task List

- **T000  Maintain MVP Specification**
  - Summary: Keep .specify/specs/001-bms-agent/spec.md aligned with constitution mandates (1GB ingestion, 100ms p95 @ 1,000 concurrent users, hybrid retrieval).
  - Dependencies: None
  - Output: Specification that matches plan and tasks.
- **T001  Provision Persistent Storage**
  - Summary: Ensure ~/persistent/ contains qdrant_storage/, bms_data/uploads/, bms_data/processed/, bms_data/evaluations/, and logs/ with 1TB free space.
  - Dependencies: T000
  - Output: Storage layout ready for ingestion and indexing.
- **T002  Create Python Environment**
  - Summary: Set up Python 3.11 venv, install reqs/requirements.txt, optional extras, and NLP models (NLTK corpora, en_core_web_sm).
  - Dependencies: T001
  - Output: Reproducible development environment.
- **T003  Install Qdrant Binary**
  - Summary: Install Qdrant 1.7.4 under /usr/local/bin/qdrant on the RunPod instance.
  - Dependencies: T001
  - Output: Qdrant executable on PATH.
- **T004  Configure Qdrant Service**
  - Summary: Maintain scripts/start_qdrant.sh with on-disk vectors/payloads, logging, and lifecycle commands.
  - Dependencies: T003
  - Output: Launch script for Qdrant with tuned settings.
- **T005  Initialize Qdrant Schema**
  - Summary: Use scripts/init_qdrant.py to create nomad_bms_documents with dense (1024-d) and sparse (BM25) vectors plus payload indexes.
  - Dependencies: T002, T004
  - Output: Ready-to-use Qdrant collection.

## Processing & API
- **T006  Integrate Enhanced Document Processor**
  - Summary: Keep api/processor_wrapper.py exposing full processing output, propagating metadata, honoring env overrides, and preparing hybrid payloads.
  - Dependencies: T005
  - Output: Wrapper returning sanitized processor results and Qdrant payloads.
- **T007  Processor Smoke Test**
  - Summary: Maintain scripts/test_processor.py to run ingestion and basic search against local Qdrant.
  - Dependencies: T006
  - Output: CLI smoke test for ingestion flow.
- **T008  n8n Slack Workflow**
  - Summary: Provide n8n/workflows/slack_bot.json that queries /api/v1/search/semantic and formats Slack responses.
  - Dependencies: T011
  - Output: Importable Slack workflow for operators.
- **T009  OpenWebUI Tool**
  - Summary: Supply ~/.openwebui/tools/bms_search.py enabling semantic/hybrid search from OpenWebUI once API is live.
  - Dependencies: T005, T006
  - Output: Custom tool script for OpenWebUI.
- **T010  Integration Test Orchestrator**
  - Summary: Maintain scripts/run_tests.sh to start dependencies, execute smoke tests, and report status.
  - Dependencies: T006, T007
  - Output: One-command integration check.
- **T011  FastAPI Application**
  - Summary: Ensure api/main.py streams 1GB uploads, exposes /api/v1/search/semantic, /metrics/uplink, health endpoints, and (post T020) /api/v1/search/hybrid with metrics counters.
  - Dependencies: T006, T007
  - Output: Production-ready API aligned with the processor wrapper.

## Security & Compliance
- **T012  Service Management Script**
  - Summary: Maintain scripts/manage_services.sh for start/stop/status/restart covering API and Qdrant.
  - Dependencies: T010, T011
  - Output: Operational command-line utility.
- **T013  Health Check Script**
  - Summary: Maintain scripts/health_check.sh querying API, Qdrant, Ollama, n8n, OpenWebUI, and metrics uplink.
  - Dependencies: T012
  - Output: Health diagnostics for operators.
- **T014  Core Security Controls**
  - Summary: Implement api/security.py, enforce JWT + API key, rate limiting, security headers, and extend tests/docs per constitution 3.
  - Dependencies: T011, T010
  - Output: Constitution-compliant security layer.

## Documentation & CI
- **T015  Documentation Synchronization**
  - Summary: Keep README.md, TESTING.md, DEPLOYMENT_CHECKLIST.md, and reports/performance-baseline.md aligned with current architecture and tasks.
  - Dependencies: Ongoing
  - Output: Accurate operator/developer documentation.
  - Summary: Maintain .github/workflows/ci-cd.yml for tests, coverage, security scans, and deployment placeholders with documented secrets.
  - Dependencies: T010, T014, T015
  - Output: Automated quality gates.

## Testing & Quality
- **T017  Performance Validation**
  - Summary: Use tests/performance/load/test_locust.py to verify ≤100 ms p95 latency @ 1,000 concurrent users; publish JSON statistics and update reports/performance-baseline.md.
  - Dependencies: T010, T016
  - Output: Performance baselines and reports.
- **T018  Operational Metrics**
  - Summary: Implement /metrics/uplink, extend health scripts, and document monitoring routines for the 99.99% availability target.
  - Dependencies: T011, T012, T013
{{ ... }}
  - Summary: Introduce sparse vector support, hybrid fusion helpers, /api/v1/search/hybrid, and integration tests (placeholders exist; implement real assertions).
  - Dependencies: T006, T011, T017, T019
  - Output: Full hybrid retrieval pipeline and documentation updates.

## Post-MVP Backlog
- **T021  Prometheus &Grafana Integration**
  - Summary: Deploy exporters and Grafana dashboards with documented manual alert runbooks (latency, ingestion, dependency); schedule automated paging as post-MVP follow-up.
  - Dependencies: T017, T018
  - Output: Prometheus scrape targets, Grafana dashboards, alerting playbook.
- **T023  Pre-commit Tooling & CI Gates**
  - Summary: Configure .pre-commit-config.yaml, Black, Ruff, mypy, and enforce hooks locally/CI.
  - Dependencies: T015, T016
- **T024  Containerization & Release Automation**
  - Summary: Build OCI images, define semantic versioning workflow, and automate migrations during deployments.
  - Dependencies: T015, T016, T021
  - Output: Release pipeline and rollback procedures.