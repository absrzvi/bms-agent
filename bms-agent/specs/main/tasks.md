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
  - Output: Custom tool script for OpenWebUI.
- **T010  Integration Test Orchestrator**
  - Summary: Maintain scripts/run_tests.sh to start dependencies, execute smoke tests, and report status.
  - Dependencies: T006, T007
  - Output: One-command integration check.
- **T011  FastAPI Application**
  - Summary: Ensure api/main.py streams 1GB uploads, exposes /api/v1/search/semantic, /api/v1/search/hybrid, `/metrics/uplink`, and health endpoints with built-in metrics counters.
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
  - Summary: Implement api/security.py, enforce JWT + API key, rate limiting, security headers, encryption at rest configuration, RBAC policies, and immutable audit logging; extend tests/docs per constitution §3/§5.
  - Dependencies: T011, T010
  - Output: Constitution-compliant security layer.

## Documentation & CI
- **T015  Documentation Synchronization**
  - Summary: Keep README.md, TESTING.md, DEPLOYMENT_CHECKLIST.md, and reports/performance-baseline.md aligned with current architecture and tasks.
  - Dependencies: Ongoing
  - Output: Accurate operator/developer documentation.
- **T016  CI/CD Pipeline Configuration**
  - Summary: Maintain .github/workflows/ci-cd.yml for tests, coverage, security scans, and deployment placeholders with documented secrets.
  - Dependencies: T010, T014, T015
  - Output: Automated quality gates.
- **T023  Pre-commit Tooling & CI Gates**
  - Summary: Configure .pre-commit-config.yaml, Black, Ruff, mypy, and enforce hooks locally/CI; ensure CI fails on formatting/type regressions.
  - Dependencies: T015, T016
  - Output: Automated formatting and typing guardrails.

## Testing & Quality
- **T017  Performance Validation**
  - Summary: Expand tests/performance/load/test_locust.py and supporting tooling to verify ≤100 ms p95 latency @ 1,000 concurrent users; publish latency artifacts.
  - Dependencies: T010, T016
  - Output: Performance baselines and reports.
- **T018  Operational Metrics**
  - Summary: Implement /metrics/uplink, extend health scripts, and document monitoring routines for the 99.99% availability target.
  - Dependencies: T011, T012, T013
  - Output: JSON metrics endpoint and supporting docs.
- **T019  Retrieval Accuracy Evaluation**
  - Summary: Produce data/evaluation/ground_truth.jsonl, scripts/evaluate_retrieval.py, and CI hooks enforcing 95% top-5 accuracy.
  - Dependencies: T006, T010, T017
  - Output: Automated retrieval quality checks.
- **T020  Hybrid Search Enablement**
  - Summary: Introduce sparse vector support, hybrid fusion helpers, /api/v1/search/hybrid, and integration tests (placeholders exist; implement real assertions).
  - Dependencies: T006, T011, T017, T019
  - Output: Full hybrid retrieval pipeline and documentation updates.

## Observability & Operations
- **T021  Prometheus & Grafana Integration**
  - Summary: Deploy exporters, dashboards, and alert rules (latency, ingestion failures, dependency health) to satisfy observability mandates.
  - Dependencies: T017, T018
  - Output: Prometheus scrape targets, Grafana dashboards, documented alert response playbook.
- **T024  Containerization & Release Automation**
  - Summary: Build OCI images, define semantic versioning workflow, and automate migrations during deployments.
  - Dependencies: T015, T016, T021
  - Output: Release pipeline and rollback procedures.