# BMS Agent Specification

## Overview
- **Purpose**: Deliver a retrieval-augmented assistant for railway network documentation, deployed on a single RunPod pod with persistent storage.
- **Scope**: Document ingestion (PDF, CSV, XLSX, TXT), semantic search, Slack integration, OpenWebUI custom tool, API endpoints for internal services.
- **Constitution Alignment**: Implements Railway IT standards (EN50155, EN45545), RAG architecture mandates, n8n workflow authentication (JWT + API key), code quality & testing minimums, availability/monitoring targets.

## User Stories
- As a network engineer, I need to search railway documentation via Slack
- As a system admin, I need to upload and process new documentation
- As a RunPod operator, I need health and monitoring endpoints to validate uptime targets
- As a QA engineer, I need automated tests and metrics to verify retrieval accuracy

## Requirements
- **Document Processing**
  - R1.1: Ingest PDF, CSV, XLSX, and TXT files up to 1 GB with rejection for unsupported types.
    - *Acceptance*: Upload endpoint streams and processes 1 GB test fixtures without memory errors; returns HTTP 400/413 with descriptive errors for invalid types or oversize payloads.
  - R1.2: Chunk documents using hierarchical strategy (1,500 tokens, 200 overlap) and store embeddings in Qdrant collection `nomad_bms_documents`.
    - *Acceptance*: `scripts/test_processor.py` logs chunk counts; Qdrant collection contains payload metadata per chunk.

- **Search & Retrieval**
  - R2.1: Provide semantic search via `/api/v1/search/semantic` returning responses ≤100 ms p95 latency under 1,000 concurrent requests.
    - *Acceptance*: `tests/performance/load/test_locust.py` records ≤100 ms p95 latency with 1,000 simulated clients and publishes latency reports.
  - R2.2: Achieve ≥95 % top-5 retrieval accuracy on curated validation set (`data/evaluation/ground_truth.jsonl`).
  - R2.3: Support hybrid retrieval (semantic + keyword/BM25) with query-time fusion.
    - *Acceptance*: Hybrid search endpoint returns both dense and sparse scores; integration tests verify BM25 keywords stored in Qdrant payload and exposed via API.

- **Security & Compliance**
  - R3.1: Protect all API and webhook endpoints with JWT (RS256) plus internal API key as per constitution §3; tokens validated against the public key provided in `BMS_JWT_PUBLIC_KEY` (signing key managed by upstream identity service).
  - R3.2: Enforce rate limiting (default 60 requests/min per JWT subject) without external dependencies.
  - R3.3: Expose OpenAPI 3.0 documentation at `/openapi.json` with correct security schemes.
  - R3.4: Ensure encryption at rest for stored documents, embeddings, and secrets (RunPod volume + Qdrant payloads) with documented key rotation process.
  - R3.5: Implement role-based access control (RBAC) for administrative, operator, and service identities across API and n8n workflows.
  - R3.6: Provide immutable audit logging for authentication events, document ingestion, search queries, and administrative actions with retention ≥90 days.

{{ ... }}
  - R4.2: Provide `/metrics/uplink` endpoint publishing latency, throughput, and recent errors for monitoring.
  - R4.3: Maintain 99.99 % availability target via documented monitoring + incident response playbook (`DEPLOYMENT_CHECKLIST.md`).

- **Observability & Operations**
  - R7.1: Expose Prometheus-compatible metrics and ship Grafana dashboards with 99.99 % availability alerts (latency/error budgets) per constitution §8 as part of the MVP.
  - R7.2: Automate alerting for latency threshold breaches, ingestion failures, and degraded dependencies with documented on-call response steps.
## Acceptance Criteria Summary
- Supported file types (≤1 GB) ingest successfully; invalid files rejected with specific errors.
- Semantic/hybrid search responds ≤100 ms p95 under 1,000 concurrent users, validated via `tests/performance/load/test_locust.py`.
- Retrieval evaluation script reports ≥95 % accuracy.
- JWT + API key enforcement validated by automated tests; unauthorized access denied.
- Monitoring endpoints return status objects and metrics; Prometheus scrape targets and Grafana dashboards are operational with alert policies defined.
- Encryption at rest, RBAC policies, and audit logging verified by configuration inspection and automated security tests.
- CI pipeline passes tests, coverage, and security scans on main branch.

## Clarifications

### Session 1 (2025-09-28)
- **Q:** Which encryption approach should we adopt for RunPod persistent storage and Qdrant payloads?
- **A:** Option C – rely on RunPod-managed encryption services.
- **Notes:** Use RunPod platform-managed volume encryption for stored documents, embeddings, and secrets; document rotation procedures provided by RunPod operations.
