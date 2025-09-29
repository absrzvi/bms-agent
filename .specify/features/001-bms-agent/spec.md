# BMS Agent Specification

## Overview
- **Purpose**: Deliver a retrieval-augmented assistant for railway network documentation, deployed on a single RunPod pod with persistent storage.
- **Scope**: **MVP DECISION**: Full integration stack - Document ingestion (PDF, CSV, XLSX, TXT), semantic search, Slack integration, OpenWebUI custom tool, n8n workflows, API endpoints for internal services. Health checks simplified for POC.
- **Constitution Alignment**: Implements Railway IT standards (EN50155, EN45545), RAG architecture mandates, n8n workflow authentication (JWT + API key), code quality & testing minimums, availability/monitoring targets.

## User Stories
- As a network engineer, I need to search railway documentation via Slack
- As a RunPod operator, I need health and monitoring endpoints to validate uptime targets
- As a QA engineer, I need automated tests and metrics to verify retrieval accuracy

## Requirements
- **Document Processing**
  - R1.1: Ingest PDF, CSV, XLSX, and TXT files up to 1 GB with rejection for unsupported types.
    - *Acceptance*: Upload endpoint streams and processes 1 GB test fixtures without memory errors; returns HTTP 400/413 with descriptive errors for invalid types or oversize payloads.
  - R1.2: **MVP DECISION**: Full advanced processing - Chunk documents using hierarchical strategy (1,500 tokens, 200 overlap), quality validation, contextual retrieval, and BM25 keyword extraction. Store multiple embeddings per chunk in Qdrant collection `nomad_bms_documents`.
    - *Acceptance*: `scripts/test_processor.py` logs chunk counts and quality scores; Qdrant collection contains hierarchical metadata, quality metrics, contextual descriptions, BM25 sparse vectors, and all enhanced processor features per chunk.

- **Search & Retrieval**
  - R2.1: **MVP DECISION**: Provide semantic search via `/api/v1/search/semantic` with best effort performance; focus on functionality over specific latency targets.
  - R2.2: Achieve ≥95 % top-5 retrieval accuracy on curated validation set (`data/evaluation/ground_truth.jsonl`).
    - *Acceptance*: `scripts/evaluate_retrieval.py` reports accuracy ≥95 %.
  - R2.3: Support hybrid retrieval (semantic + keyword/BM25) with query-time fusion.
    - *Acceptance*: Hybrid search endpoint returns both dense and sparse scores; integration tests verify BM25 keywords stored in Qdrant payload and exposed via API.
  - R3.1: **POC DECISION**: Disable JWT authentication for proof of concept; protect endpoints with optional API key only (`BMS_API_KEY` environment variable). JWT implementation deferred to production phase.
  - R3.2: Enforce basic rate limiting (default 60 requests/min per IP) without external dependencies.
  - R3.3: Expose OpenAPI 3.0 documentation at `/openapi.json` with simplified security schemes (API key optional).

  - R4.1: **POC DECISION**: Provide basic `/health` endpoint only; detailed service health checks (Qdrant, Ollama, n8n, OpenWebUI) deferred to production phase.
  - R4.2: Provide `/metrics/uplink` endpoint publishing latency, throughput, and recent errors for monitoring.
  - R4.3: Maintain 99.99 % availability target via documented monitoring + incident response playbook (`DEPLOYMENT_CHECKLIST.md`).

- **Testing & Quality**
  - R5.1: **MVP DECISION**: Basic testing scope - Core functionality tests with manual quality checks; comprehensive CI and security scans deferred to production phase.
  - R5.2: Include basic regression tests for core document processing and search functionality.
  - R5.3: **MVP DECISION**: Manual code quality checks; automated pre-commit tooling and strict typing enforcement deferred to production phase.

- **Workflow & Change Management**
  - R6.1: Adopt Git flow branching for feature development (e.g., `feature/<name>`, `release/<version>`) with semantic commit messages.
  - R6.3: Produce container images for the API service, follow semantic versioning, and automate database migrations as part of the release workflow.
  
- **Observability & Operations**
  - R7.1: Expose Prometheus-compatible metrics and ship Grafana dashboards with 99.99 % availability visualizations per constitution §8 as part of the MVP.
  - R7.2: Document manual alert runbooks for latency, ingestion, and dependency degradation; automated notification delivery is deferred to a post-MVP roadmap item.
  - R7.3: Maintain `DEPLOYMENT_CHECKLIST.md` with escalation steps and contact matrix.

- **Success Criteria**
  - Ingestion workload runs successfully; invalid files rejected with specific errors.
  - Semantic/hybrid search responds ≤100 ms p95 under 1,000 concurrent users, validated via `tests/performance/load/test_locust.py`.
  - Retrieval evaluation script reports ≥95 % accuracy.
  - Optional API key enforcement validated by automated tests; unauthorized access returns 401 when API key is configured.
  - Monitoring endpoints return status objects and metrics; Prometheus scrape targets and Grafana dashboards are operational with documented manual alert runbooks.
  - Manual alert runbooks cover latency threshold breaches, ingestion failures, and dependency degradation; automated delivery is tracked as follow-up work.
  - CI pipeline passes tests, coverage, and security scans on main branch.
