# BMS Agent Specification

## Overview
- **Purpose**: Deliver a retrieval-augmented assistant for railway network documentation, deployed on a single RunPod pod with persistent storage.
- **Scope**: **MVP DECISION**: Full integration stack - Document ingestion (PDF, DOCX, PPTX, CSV, XLSX, TXT), semantic search, **Direct FastAPI Slack integration** (n8n unavailable on deployment environment), OpenWebUI custom tool, API endpoints for internal services. Health checks simplified for POC.
- **Constitution Alignment**: Implements Railway IT standards (EN50155, EN45545), RAG architecture mandates, API authentication (JWT + API key deferred to production), code quality & testing minimums, availability/monitoring targets.

## User Stories
- As a network engineer, I need to search railway documentation via Slack
- As a RunPod operator, I need health and monitoring endpoints to validate uptime targets
- As a QA engineer, I need automated tests and metrics to verify retrieval accuracy

## Operational Requirements
- **Scale & Volume**: Design for maximum flexibility - variable document processing loads with scalable architecture
- **Concurrent Users**: Support 20-100 concurrent users (department-level deployment)
- **Network Connectivity**: Standard internet connectivity with full external access for integrations
- **Data Persistence**: All persistent storage in `/workspace` folder for backup and installation consistency
- **Integration Priority**: All integrations (Slack, OpenWebUI, n8n) equally important for MVP validation

## Requirements
- **Document Processing**
  - R1.1: Ingest PDF, DOCX, PPTX, CSV, XLSX, and TXT files up to 100 MB with rejection for unsupported types. **POC DECISION**: 100 MB limit for POC; 1 GB target for production.
    - *Acceptance*: Upload endpoint streams and processes 100 MB test fixtures without memory errors; returns HTTP 400/413 with descriptive errors for invalid types or oversize payloads.
  - R1.2: **MVP DECISION**: Enhanced Document Processor v4.0 with optimized quality processing - Sentence-aware chunking (2000 chars, 400 overlap), quality validation (≥0.70 minimum score), contextual retrieval, perfect data cleaning, and BM25 keyword extraction. Store 768-dimensional embeddings (sentence-transformers/all-mpnet-base-v2) per chunk in Qdrant collection `nomad_bms_documents`.
    - *Acceptance*: Quality score ≥0.70 minimum (actual: 0.72-0.85 by format) with 100% pass rate; zero data artifacts in XLSX/CSV processing; complete multi-format support (PDF, DOCX, PPTX, XLSX, CSV, TXT); 768-dim embeddings; comprehensive test suite validates all features.
  - R1.3: **QUALITY ASSURANCE**: Achieve enterprise-grade processing quality with comprehensive format support and data cleaning.
    - *Acceptance*: DOCX processing with python-docx (0.714-0.895 quality); PPTX slide structure preservation; XLSX perfect cleaning (zero NaN/Unnamed artifacts); CSV enhanced formatting; multi-language support (German/English); business document intelligence.

- **Search & Retrieval**
  - R2.1: **POC DECISION**: Provide semantic search via `/api/v1/search/semantic` with best effort performance; no hard latency requirements for POC. Performance benchmarking for baseline establishment only. **Production target**: ≤100ms p95 for 20-100 concurrent users.
  - R2.2: Achieve ≥95 % top-5 retrieval accuracy on curated validation set (`data/evaluation/ground_truth.jsonl`).
    - *Acceptance*: `scripts/evaluate_retrieval.py` reports accuracy ≥95 %.
  - R2.3: Support hybrid retrieval (semantic + keyword/BM25) with query-time fusion.
    - *Acceptance*: Hybrid search endpoint returns both dense and sparse scores; integration tests verify BM25 keywords stored in Qdrant payload and exposed via API.
  - R3.1: **POC DECISION**: No authentication required for proof of concept. All endpoints are publicly accessible. JWT and API key authentication deferred to production phase. Document security roadmap in `docs/security-notes.md`.
  - R3.2: Enforce rate limiting optimized for 20-100 concurrent users (default 60 requests/min per IP, scalable configuration) without external dependencies.
  - R3.3: Expose OpenAPI 3.0 documentation at `/openapi.json` with simplified security schemes (API key optional).

  - R4.1: **POC DECISION**: Provide basic `/health` endpoint only; detailed service health checks (Qdrant, Ollama, OpenWebUI) deferred to production phase.
  - R4.2: Provide `/metrics/uplink` endpoint publishing latency, throughput, and recent errors for monitoring.
  - R4.3: Maintain 99.99 % availability target via documented monitoring + incident response playbook (`DEPLOYMENT_CHECKLIST.md`).

- **Testing & Quality**
  - R5.1: **MVP DECISION**: Basic testing scope - Core functionality tests with manual quality checks; comprehensive CI and security scans deferred to production phase.
  - R5.2: Include basic regression tests for core document processing and search functionality.
  - R5.3: **MVP DECISION**: Manual code quality checks; automated pre-commit tooling and strict typing enforcement deferred to production phase.
- **Workflow & Change Management**
  - R6.1: Adopt Git flow branching for feature development (e.g., `feature/<name>`, `release/<version>`) with semantic commit messages.
  - R6.2: Implement semantic versioning for all releases with proper changelog maintenance and dependency management.
  - R6.3: Produce container images for the API service, follow semantic versioning, and automate database migrations as part of the release workflow.
  
- **Observability & Operations**
  - R7.1: **POC DECISION**: Basic `/metrics/uplink` endpoint for POC; full Prometheus integration and Grafana dashboards deferred to post-MVP phase per constitution §8 POC exception.
  - R7.2: **POC DECISION**: Basic operational documentation for POC; comprehensive manual alert runbooks deferred to post-MVP phase.
    - *Acceptance*: `DEPLOYMENT_CHECKLIST.md` contains basic operational procedures for POC. Full runbooks (latency, ingestion, dependency degradation, contact matrix) deferred to production.
  - R7.3: Maintain `DEPLOYMENT_CHECKLIST.md` with escalation steps and contact matrix.

- **Success Criteria (POC)**
  - Ingestion workload runs successfully; invalid files rejected with specific errors.
  - Semantic/hybrid search operational with best effort performance; baseline metrics documented.
  - Retrieval evaluation script reports ≥95 % accuracy.
  - All integrations (Slack, OpenWebUI) operational and validated with end-to-end testing.
  - Rate limiting (60 req/min per IP) validated by automated tests.
  - Basic health and metrics endpoints return status objects.
  - All persistent data stored in `/workspace` folder with documented backup procedures.
  - Basic test suite passes on main branch.
  
- **Production Criteria (Post-MVP)**
  - Performance: ≤100ms p95 under 20-100 concurrent users.
  - Security: JWT + API key authentication enforced.
  - Monitoring: Prometheus/Grafana operational with alert runbooks.
  - CI/CD: Full pipeline with coverage, security scans, pre-commit hooks.
