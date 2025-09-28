# BMS Agent MVP Task List

## Setup
- **T001  Provision Persistent Storage**
  - Summary: Create `~/persistent/qdrant_storage`, `~/persistent/bms_data/{uploads,processed,evaluations}`, and `~/persistent/logs` with correct permissions.
  - Dependencies: None
  - Files/Paths: `~/persistent/`
  - Parallel: No
- **T002  Python Environment Bootstrap**
  - Summary: Create `.venv`, install `requirements.txt` and `requirements-test.txt`, pin versions in `requirements.txt` as needed.
  - Dependencies: T001
  - Files/Paths: `requirements.txt`, `requirements-test.txt`
  - Parallel: No
- **T003  Qdrant Binary Install & Service Script**
  - Summary: Install Qdrant 1.7.4 (non-Docker) and finalize `scripts/start_qdrant.sh` with start/stop/status commands logging to `~/persistent/logs/qdrant.log`.
  - Dependencies: T002
  - Files/Paths: `scripts/start_qdrant.sh`
  - Parallel: No
- **T004  Qdrant Collection Initializer**
  - Summary: Implement `scripts/init_qdrant.py` to create the `nomad_bms_documents` multi-vector collection with named vectors (`chunk_embedding`, `parent_embedding`, both 1024-d cosine), payload indexes for `document_id`, `version_id`, hierarchical metadata, and sparse keyword/BM25 fields plus default HNSW params.
  - Dependencies: T003
  - Files/Paths: `scripts/init_qdrant.py`
  - Parallel: No

## Tests First (TDD)
- **T005  Contract Test – Document Upload [P]**
  - Summary: Add failing contract tests in `tests/contract/test_upload_document.py` covering success, 400 (invalid type), and 413 responses based on `contracts/api-documents.yaml`.
  - Dependencies: T002
  - Files/Paths: `tests/contract/test_upload_document.py`
  - Parallel: Yes ([P])
- **T006  Contract Test – Search Endpoints [P]**
  - Summary: Add failing contract tests in `tests/contract/test_search_endpoints.py` for semantic and hybrid routes per `contracts/api-search.yaml`.
  - Dependencies: T002
  - Files/Paths: `tests/contract/test_search_endpoints.py`
  - Parallel: Yes ([P])
- **T007  Integration Smoke Tests [P]**
  - Summary: Extend `tests/test_basic.py` with ingestion+search smoke flows using fixtures; include 413 scenario.
  - Dependencies: T002
  - Files/Paths: `tests/test_basic.py`
  - Parallel: Yes ([P])
- **T008  Locust Performance Suite**
  - Summary: Expand `tests/performance/load/test_locust.py` to emit JSON stats (latency p95/p99, throughput) and parameterize host/credentials.
  - Dependencies: T002
  - Files/Paths: `tests/performance/load/test_locust.py`
  - Parallel: No

## Core Implementation
- **T009  EnhancedDocumentProcessor Integration**
  - Summary: Implement `api/processor_wrapper.py` configuring `EnhancedDocumentProcessor` with hierarchical parent/child chunking, late chunking, contextual retrieval, hybrid search preparation (dense + BM25), advanced entity extraction, RAGAS quality validation, railway-specific term preservation, version tracking, and optional distributed processing fallbacks while streaming 1 GB uploads into Qdrant with full metadata.
  - Dependencies: T004, T005–T008
  - Files/Paths: `api/processor_wrapper.py`
  - Parallel: No
- **T010  Upload Endpoint**
  - Summary: Implement `POST /api/v1/documents/upload` in `api/main.py`, wiring streaming pipeline, MIME/type validation, checksum logging, and versioning.
  - Dependencies: T009, T005
  - Files/Paths: `api/main.py`
  - Parallel: No
- **T011  Semantic Search Endpoint**
  - Summary: Implement `POST /api/v1/search/semantic` returning top chunks with dense scores and latency metadata.
  - Dependencies: T009, T006
  - Files/Paths: `api/main.py`
  - Parallel: No
- **T012  Hybrid Search Endpoint**
  - Summary: Implement `POST /api/v1/search/hybrid` with fusion weights, sparse tokens, and response schema from contract.
  - Dependencies: T011
  - Files/Paths: `api/main.py`
  - Parallel: No
- **T013  Health Endpoints**
  - Summary: Implement `/health` and `/health/detailed` including checks for Qdrant, Ollama, n8n webhook, OpenWebUI, and storage space.
  - Dependencies: T009
  - Files/Paths: `api/main.py`
  - Parallel: No
- **T014  Metrics Endpoint**
  - Summary: Implement `/metrics/uplink` returning latency histogram, ingestion throughput, error counts, and scrape freshness per data model.
  - Dependencies: T009, T008
  - Files/Paths: `api/main.py`
  - Parallel: No

## Security & Compliance
- **T015  Security Module Implementation**
  - Summary: Build `api/security.py` with JWT (RS256) validation, API key fallback, RBAC roles, and 60 req/min rate limiting.
  - Dependencies: T011
  - Files/Paths: `api/security.py`
  - Parallel: No
- **T016  Security Wiring & Tests**
  - Summary: Integrate security middleware into FastAPI app, update tests for 401/403/429, and document configuration in `docs/security-notes.md`.
  - Dependencies: T015, T005–T007
  - Files/Paths: `api/main.py`, `docs/security-notes.md`, `tests/security/`
  - Parallel: No

## Integrations
- **T017  n8n Slack Workflow**
  - Summary: Author `n8n/workflows/slack_bot.json` to call search endpoints, handle auth headers, and format responses with top snippets.
  - Dependencies: T011, T016
  - Files/Paths: `n8n/workflows/slack_bot.json`
  - Parallel: No
- **T018  OpenWebUI Tool Script**
  - Summary: Implement `~/.openwebui/tools/bms_search.py` (and repo copy) that queries semantic/hybrid endpoints with configurable weights.
  - Dependencies: T011, T012
  - Files/Paths: `~/.openwebui/tools/bms_search.py`, `tools/bms_search.py`
  - Parallel: No

## Observability & Operations
- **T019  Manage Services Script**
  - Summary: Complete `scripts/manage_services.sh` with start/stop/status/restart flows for Qdrant and API, logging to `~/persistent/logs/`.
  - Dependencies: T003, T010
  - Files/Paths: `scripts/manage_services.sh`
  - Parallel: No
- **T020  Health Check Script**
  - Summary: Extend `scripts/health_check.sh` to probe API endpoints, Ollama, n8n, OpenWebUI, metrics, and log results with timestamps.
  - Dependencies: T013, T019
  - Files/Paths: `scripts/health_check.sh`
  - Parallel: No
- **T021  Manual Alert Runbooks & Grafana Dashboards**
  - Summary: Configure Prometheus scrape targets, create Grafana panels, and document manual alert escalation (latency, ingestion, dependency) in `DEPLOYMENT_CHECKLIST.md`.
  - Dependencies: T014, T020
  - Files/Paths: `grafana/`, `DEPLOYMENT_CHECKLIST.md`
  - Parallel: No

## Documentation & Validation
- **T022  Quickstart Verification [P]**
  - Summary: Walk through `quickstart.md`, update instructions with actual commands, ensure curl examples function end-to-end.
  - Dependencies: T010–T018
  - Files/Paths: `specs/001-bms-agent/quickstart.md`
  - Parallel: Yes ([P])
- **T023  README/Docs Sync [P]**
  - Summary: Refresh `README.md`, `TESTING.md`, `reports/performance-baseline.md`, and `docs/security-notes.md` to mirror current workflow and metrics.
  - Dependencies: T008–T021
  - Files/Paths: `README.md`, `TESTING.md`, `reports/performance-baseline.md`, `docs/security-notes.md`
  - Parallel: Yes ([P])
- **T024  Performance Baseline Publication**
  - Summary: Run Locust suite, capture JSON stats, and summarize latency/throughput in `reports/performance-baseline.md` with acceptance criteria checks.
  - Dependencies: T008, T014
  - Files/Paths: `reports/performance-baseline.md`
  - Parallel: No
- **T025  Retrieval Accuracy & Quality Evaluation**
  - Summary: Build `data/evaluation/ground_truth.jsonl`, implement `scripts/evaluate_retrieval.py`, compute RAGAS metrics (faithfulness, relevancy, context precision/recall), and wire CI hook enforcing ≥95 % top-5 accuracy plus quality thresholds from EnhancedDocumentProcessor.
  - Dependencies: T009, T011, T016
  - Files/Paths: `data/evaluation/ground_truth.jsonl`, `scripts/evaluate_retrieval.py`, `.github/workflows/ci-cd.yml`
  - Parallel: No

## Polish
- **T026  Pre-commit & CI Hooks [P]**
  - Summary: Configure `.pre-commit-config.yaml` with Black, Ruff, mypy; update CI to enforce hooks before merge.
  - Dependencies: T016, T023
  - Files/Paths: `.pre-commit-config.yaml`, `.github/workflows/ci-cd.yml`
  - Parallel: Yes ([P])
- **T027  Release Pipeline Prep**
  - Summary: Draft container build steps and migration automation placeholders (`.github/workflows/ci-cd.yml`, `docs/migrations.md`) for post-MVP release process.
  - Dependencies: T015, T019, T026
  - Files/Paths: `.github/workflows/ci-cd.yml`, `docs/migrations.md`
  - Parallel: No
