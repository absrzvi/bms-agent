# BMS Agent Specification

## Overview
- **Purpose**: Deliver a retrieval-augmented assistant for railway network documentation, deployed on a single RunPod pod with persistent storage.
- **Scope**: **MVP DECISION**: Full integration stack - Document ingestion (PDF, DOCX, PPTX, CSV, XLSX, TXT), semantic search, **Direct FastAPI Slack integration** (n8n unavailable on deployment environment), OpenWebUI custom tool, API endpoints for internal services. Health checks simplified for POC.
- **Constitution Alignment**: Implements Railway IT standards (EN50155, EN45545), RAG architecture mandates, API authentication (JWT + API key deferred to production), code quality & testing minimums, availability/monitoring targets.
- **Terminology**: "POC" (Proof of Concept) and "MVP" (Minimum Viable Product) are used interchangeably in this document to refer to the initial deployment phase with simplified requirements. Production phase refers to full-scale deployment with all constitution requirements enforced.

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
  - R1.2: **MVP DECISION**: Enhanced Document Processor v4.0 with optimized quality processing - Sentence-aware chunking (2000 chars, 400 overlap), quality validation (≥0.70 minimum score), contextual retrieval, perfect data cleaning, and BM25 keyword extraction. Store 768-dimensional embeddings (sentence-transformers/all-mpnet-base-v2) per chunk in Qdrant v1.7.4+ vector database with v4.0 multi-vector schema, collection `nomad_bms_documents`.
    - *Acceptance*: Quality score ≥0.70 minimum (actual: 0.72-0.85 by format) with 100% pass rate; zero data artifacts in XLSX/CSV processing; complete multi-format support (PDF, DOCX, PPTX, XLSX, CSV, TXT); 768-dim embeddings; comprehensive test suite validates all features.
  - R1.3: **QUALITY ASSURANCE**: Achieve measurable processing quality with comprehensive format support and data cleaning.
    - *Acceptance*: DOCX processing with python-docx (quality score 0.714-0.895); PPTX slide structure preservation with text extraction from all slide elements; XLSX perfect cleaning (zero NaN/Unnamed artifacts, 100% data integrity); CSV enhanced formatting with proper delimiter detection; multi-language support (German/English); business document intelligence (tables, lists, headers preserved).
  - R1.4: **CLARIFIED**: Document re-upload behavior - When a document with the same filename is uploaded, perform destructive replacement: remove existing document and all associated chunks, then process as new upload.
    - *Acceptance*: Re-uploading same filename removes old version from Qdrant; new chunks replace old; document ID may change or be reused.
  - R1.5: **CLARIFIED**: Upload concurrency - Support unlimited concurrent document uploads with queue-based processing to handle variable loads.
    - *Acceptance*: Multiple simultaneous uploads accepted (HTTP 202); background queue processes documents; no artificial concurrency limits; track processing status per document.
  - R1.6: **CLARIFIED**: Failed document processing - Store all chunks regardless of quality score; flag low-quality chunks (< 0.70) in metadata for filtering/monitoring.
  - R1.7: **CLARIFIED**: Document deletion - Admin-only capability via dedicated API endpoint to remove documents and associated chunks.
    - *Acceptance*: DELETE endpoint requires admin authentication (production); removes document metadata and all chunks from Qdrant; returns 204 on success; audit log records deletion.

- **Search & Retrieval**
  - R2.1: **POC DECISION**: Provide semantic search via `/api/v1/search/semantic` with POC performance target ≤500ms p95 latency under 20 concurrent users; minimum acceptable baseline ≤1000ms p95 for POC validation. Performance benchmarking for baseline establishment only. **Production target**: ≤100ms p95 for 20-100 concurrent users.
  - R2.2: Achieve ≥95 % top-5 retrieval accuracy on curated validation set (`data/evaluation/ground_truth.jsonl`) containing minimum 50 queries across 10 categories.
    - *Acceptance*: `scripts/evaluate_retrieval.py` reports accuracy ≥95 % on dataset with ≥50 test queries.
  - R2.3: Support hybrid retrieval (semantic + keyword/BM25) with query-time fusion.
    - *Acceptance*: Hybrid search endpoint returns both dense and sparse scores; integration tests verify BM25 keywords stored in Qdrant payload and exposed via API.
  - R2.4: **CLARIFIED**: Configurable relevance filtering - Search endpoints accept optional `min_score` query parameter to filter results below specified similarity threshold (default: no filtering, return all top-k).
    - *Acceptance*: `/api/v1/search/semantic?min_score=0.7` filters results; parameter validated (0.0-1.0 range); documented in OpenAPI spec; default behavior returns all top-k results regardless of score.
  - R3.1: **POC DECISION**: No authentication required for proof of concept. All endpoints are publicly accessible. JWT and API key authentication deferred to production phase. Slack signature verification implemented but optional for POC (can be disabled via config). Document security roadmap in `docs/security-notes.md`.
  - R3.2: Enforce rate limiting optimized for 20-100 concurrent users (default 60 requests/min per IP, scalable configuration) without external dependencies.
  - R3.3: Expose OpenAPI 3.0 documentation at `/openapi.json` with simplified security schemes (API key optional).

  - R4.1: **POC DECISION**: Provide basic `/health` endpoint only; detailed service health checks (Qdrant, Ollama, OpenWebUI) deferred to production phase.
  - R4.2: Provide `/metrics/uplink` endpoint publishing latency, throughput, and recent errors for monitoring.
  - R4.3: Maintain 99.99 % availability target via documented monitoring + incident response playbook (`DEPLOYMENT_CHECKLIST.md`).
- **Testing & Quality**
  - R5.1: **MVP DECISION**: Basic testing scope - Core functionality tests with manual quality checks; comprehensive CI and security scans deferred to production phase.
    - *Acceptance*: ≥80% test coverage for core logic per constitution §4; basic functionality tests pass.
  - R5.2: Include basic regression tests for core document processing and search functionality.
  - R5.3: **MVP DECISION**: Manual code quality checks; automated pre-commit tooling and strict typing enforcement deferred to production phase.
- **Workflow & Change Management**
  - R6.1: Adopt Git flow branching for feature development (e.g., `feature/<name>`, `release/<version>`) with semantic commit messages.
  - R6.2: Implement semantic versioning for all releases with proper changelog maintenance and dependency management.
  - R6.3: Produce container images for the API service, follow semantic versioning, and automate database migrations as part of the release workflow.
  
- **Observability & Operations**
  - R7.1: **MVP REQUIREMENT**: Implement basic Prometheus/Grafana integration per constitution §8; configure `/metrics/uplink` endpoint and basic dashboards for MVP.
    - *Acceptance*: Prometheus scraping metrics from BMS API; Grafana dashboard showing latency, throughput, errors; manual alert runbooks documented.
  - R7.2: **POC DECISION**: Basic operational documentation for POC; comprehensive manual alert runbooks deferred to post-MVP phase.
    - *Acceptance*: `DEPLOYMENT_CHECKLIST.md` contains basic operational procedures for POC. Full runbooks (latency, ingestion, dependency degradation, contact matrix) deferred to production.
  - R7.3: Maintain `DEPLOYMENT_CHECKLIST.md` with escalation steps and contact matrix.
  - R7.4: **BACKUP & RETENTION**: Implement daily automated backups of `/workspace/qdrant_storage` and `/workspace/bms_data` with 30-day retention policy for logs and 90-day retention for data backups.
    - *Acceptance*: Backup script runs daily via cron; backups stored in `/workspace/backups/` with date stamps; log rotation configured for 30-day retention; backup verification documented in `DEPLOYMENT_CHECKLIST.md`.

- **SharePoint Integration & Data Synchronization**
  - R8.1: **SHAREPOINT DOCUMENT SYNC**: Implement automated SharePoint document download and synchronization for BMS documentation repository.
    - *Acceptance*: Download script authenticates with cookie-based auth; filters documents by modification date (post-2023); supports parallel downloads (≥10 workers); organizes by document type; handles errors gracefully with retry logic; logs download statistics.
  - R8.2: **BATCH PROCESSING**: Process downloaded SharePoint documents with Enhanced Document Processor v4.0 in batch mode.
    - *Acceptance*: Batch processor handles variable document loads; achieves ≥95% success rate; maintains ≥0.70 quality score threshold; processes ≥10 documents/minute; moves processed files to appropriate directories; logs processing statistics and errors.

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

## Clarifications Changelog

### Session 1 - 2025-10-02 08:40 UTC
**Clarifier**: Workflow `/clarify` execution  
**Questions Resolved**: 5 critical ambiguities

| ID | Category | Question | Decision | Requirements Added |
|----|----------|----------|----------|-------------------|
| Q1 | Document Lifecycle | How to handle re-upload of same filename? | **A**: Destructive replacement | R1.4 |
| Q2 | Search Quality | Should results be filtered by minimum score? | **D**: Configurable threshold via query param | R2.4 |
| Q3 | Upload Concurrency | How many simultaneous uploads? | **A**: Unlimited queue-based processing | R1.5 |
| Q4 | Document Deletion | Should deletion be supported? | **D**: Admin-only API endpoint | R1.7 |
| Q5 | Failed Processing | What happens when quality < 0.70? | **D**: Store all, flag low-quality in metadata | R1.6 |

**Impact**: 5 new requirements added (R1.4-R1.7, R2.4); requires 5 new implementation tasks (T036-T040)
