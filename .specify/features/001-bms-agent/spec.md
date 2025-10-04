# BMS Agent Specification

## Overview
- **Purpose**: Deliver a retrieval-augmented assistant for railway network documentation, deployed on a single RunPod pod with persistent storage.
- **Scope**: Full integration stack - Document ingestion (PDF, DOCX, PPTX, CSV, XLSX, TXT), semantic search, **Direct FastAPI Slack integration** (primary), n8n workflow integration (secondary/optional), OpenWebUI custom tool, API endpoints for internal services.
- **Constitution Alignment**: Implements Railway IT standards (EN50155, EN45545), RAG architecture mandates, API authentication (JWT + API key deferred to production), code quality & testing minimums, availability/monitoring targets.

## Phase Definitions
This project follows a three-phase delivery model with progressive requirement enforcement:

- **POC (Proof of Concept)**: Initial development phase focused on core functionality validation with simplified requirements. Security, performance, and monitoring requirements are relaxed to enable rapid prototyping. Markers: "POC DECISION" indicates constitution requirement relaxation for this phase.

- **MVP (Minimum Viable Product)**: Production-ready deployment with essential features and basic operational requirements. Core functionality complete, basic security (rate limiting, headers), simplified monitoring (Prometheus/Grafana), and operational documentation. Markers: "MVP REQUIREMENT" indicates features required for initial production deployment.

- **Production**: Full-scale deployment with complete constitution compliance. All MUST requirements enforced including JWT authentication, comprehensive monitoring with automated alerting, full CI/CD pipeline, and enterprise-grade security. Target: 99.99% availability with <100ms p95 latency.

## User Stories
- As a network engineer, I need to search railway documentation via Slack
- As a RunPod operator, I need health and monitoring endpoints to validate uptime targets
- As a QA engineer, I need automated tests and metrics to verify retrieval accuracy

## Operational Requirements
- **Scale & Volume**: Design for maximum flexibility - variable document processing loads with scalable architecture
- **Concurrent Users**: Support 20-100 concurrent users (department-level deployment)
- **Network Connectivity**: Standard internet connectivity with full external access for integrations
- **Data Persistence**: All persistent storage in `/workspace` folder for backup and installation consistency
- **Integration Priority**: Slack (direct FastAPI) and OpenWebUI required for MVP; n8n integration optional/secondary for workflow orchestration

## Requirements

### Performance Targets
Progressive performance requirements aligned with deployment phases:

**Concurrent User Definition** (per Q8 clarification): Mixed workload with 95% read operations (search queries) and 5% write operations (document uploads). "Concurrent users" means simultaneous active requests in flight, not just logged-in sessions.

- **POC Phase**: Best-effort performance with baseline establishment
  - Baseline threshold: p95 latency <500ms acceptable for 20 concurrent users
  - Escalation trigger: p95 >1000ms requires optimization work before MVP
  - Document processing: ≥5 documents/minute minimum
  - Metrics collection: Establish performance baselines for production planning
  - Workload mix: 95% search / 5% upload for load testing

- **MVP Phase**: Production-ready performance with monitoring
  - Target: p95 latency <200ms for 20-50 concurrent users
  - Document processing: ≥10 documents/minute
  - Availability: 99.9% (three nines) with basic monitoring
  - Workload mix: 95% search / 5% upload

- **Production Phase**: Enterprise-grade performance
  - Target: p95 latency ≤100ms for 20-100 concurrent users
  - Document processing: ≥20 documents/minute with parallel processing
  - Availability: 99.99% (four nines) with automated alerting
  - Workload mix: 95% search / 5% upload
  - **Timeline** (per Q6 clarification): 1-2 months post-enhancement completion

### Document Processing
  - R1.1: Ingest PDF, DOCX, PPTX, CSV, XLSX, and TXT files up to 100 MB with rejection for unsupported types. **POC DECISION**: 100 MB limit for POC; 1 GB target for production.
    - *Acceptance*: Upload endpoint streams and processes 100 MB test fixtures without memory errors; returns HTTP 400/413 with descriptive errors for invalid types or oversize payloads.
  - R1.2: Enhanced Document Processor v4.0 with quality-validated processing (≥0.70 minimum score) - Sentence-aware chunking (2000 chars, 400 overlap), quality validation with measurable thresholds, contextual retrieval, perfect data cleaning, and BM25 keyword extraction. Store 768-dimensional embeddings (sentence-transformers/all-mpnet-base-v2) per chunk in Qdrant v1.7.4+ vector database with v4.0 multi-vector schema, collection `nomad_bms_documents`.
    - *Acceptance*: Quality score ≥0.70 minimum (actual: 0.72-0.85 by format) with 100% pass rate; zero data artifacts in XLSX/CSV processing; complete multi-format support covering all 6 formats (PDF, DOCX, PPTX, XLSX, CSV, TXT); 768-dim embeddings; test suite with 25+ validation scripts covering all formats and quality scenarios.
  - R1.3: **QUALITY ASSURANCE**: Achieve measurable processing quality with complete format support and data cleaning.
    - *Acceptance*: DOCX processing with python-docx (quality score 0.714-0.895); PPTX slide structure preservation with text extraction from all slide elements; XLSX perfect cleaning (zero NaN/Unnamed artifacts, 100% data integrity); CSV enhanced formatting with proper delimiter detection; multi-language support (German/English); business document intelligence (tables, lists, headers preserved).
  - R1.4: **CLARIFIED**: Document re-upload behavior - When a document with the same filename is uploaded, perform destructive replacement: remove existing document and all associated chunks, then process as new upload.
    - *Acceptance*: Re-uploading same filename removes old version from Qdrant; new chunks replace old; document ID may change or be reused.
  - R1.5: **CLARIFIED**: Upload concurrency - Support unlimited concurrent document uploads with queue-based processing to handle variable loads.
    - *Acceptance*: Multiple simultaneous uploads accepted (HTTP 202); background queue processes documents; no artificial concurrency limits; track processing status per document.
  - R1.6: **CLARIFIED**: Failed document processing - Store all chunks regardless of quality score; flag low-quality chunks (< 0.70) in metadata for filtering/monitoring.
  - R1.7: **CLARIFIED**: Document deletion - Admin-only capability via dedicated API endpoint to remove documents and associated chunks.
    - *Acceptance*: DELETE endpoint requires admin authentication (production); removes document metadata and all chunks from Qdrant; returns 204 on success; audit log records deletion.

### Search & Retrieval
  - R2.1: Provide semantic search via `/api/v1/search/semantic` with phase-appropriate performance (see Performance Targets section above).
    - **POC**: Establish baseline metrics, p95 <500ms acceptable, >1000ms triggers optimization
    - **MVP**: Target p95 <200ms for 20-50 users
    - **Production**: Target p95 ≤100ms for 20-100 users
  - R2.2: Achieve ≥95 % top-5 retrieval accuracy on curated validation set (`data/evaluation/ground_truth.jsonl`) containing minimum 50 queries across 10 categories.
    - *Acceptance*: `scripts/evaluate_retrieval.py` reports accuracy ≥95 % on dataset with ≥50 test queries.
  - R2.3: Support hybrid retrieval (semantic + keyword/BM25) with query-time fusion.
    - *Acceptance*: Hybrid search endpoint returns both dense and sparse scores; integration tests verify BM25 keywords stored in Qdrant payload and exposed via API.
  - R2.4: **CLARIFIED**: Configurable relevance filtering - Search endpoints accept optional `min_score` query parameter to filter results below specified similarity threshold (default: no filtering, return all top-k).
    - *Acceptance*: `/api/v1/search/semantic?min_score=0.7` filters results; parameter validated (0.0-1.0 range); documented in OpenAPI spec; default behavior returns all top-k results regardless of score.
### Security & API
  - R3.1: **POC DECISION**: No authentication required for proof of concept. All endpoints are publicly accessible. JWT and API key authentication deferred to production phase. Slack signature verification implemented but optional for POC (can be disabled via config). Document security roadmap in `docs/security-notes.md`.
  - R3.2: **MVP REQUIREMENT**: Enforce rate limiting optimized for 20-100 concurrent users (default 60 requests/min per IP, scalable configuration) using in-memory token bucket algorithm without external dependencies.
    - *Acceptance*: Rate limiting middleware integrated; returns HTTP 429 with Retry-After header; configurable limits; automated tests verify 400/413/429 responses.
  - R3.3: Expose OpenAPI 3.0 documentation at `/openapi.json` with simplified security schemes (API key optional).

### Health & Monitoring
  - R4.1: **POC DECISION**: Provide basic `/health` endpoint only; detailed service health checks (Qdrant, Ollama, OpenWebUI) deferred to production phase.
  - R4.2: Provide `/metrics/uplink` endpoint publishing latency, throughput, and recent errors for monitoring.
  - R4.3: Maintain availability targets per phase: POC (best effort), MVP (99.9%), Production (99.99%) via documented monitoring + incident response playbook (`DEPLOYMENT_CHECKLIST.md`).

### Testing & Quality
  - R5.1: **POC DECISION**: Basic testing scope - Core functionality tests with manual quality checks; full CI pipeline and automated security scans deferred to production phase.
    - *Acceptance*: ≥80% test coverage for core logic per constitution §4; basic functionality tests pass.
  - R5.2: Include basic regression tests for core document processing and search functionality.
  - R5.3: **POC DECISION**: Manual code quality checks; automated pre-commit tooling and strict typing enforcement deferred to production phase.

### Workflow & Change Management
  - R6.1: Adopt Git flow branching for feature development (e.g., `feature/<name>`, `release/<version>`) with semantic commit messages.
  - R6.2: Implement semantic versioning for all releases with proper changelog maintenance and dependency management.
  - R6.3: Produce container images for the API service, follow semantic versioning, and automate database migrations as part of the release workflow (for future SQL databases; not required for Qdrant NoSQL vector database).
  - R6.4: **CLARIFIED** (per Q7): Implement Alembic migration framework now for future SQL database readiness, even though current deployment uses Qdrant (NoSQL). Manual Qdrant schema changes continue to be tracked in `docs/migrations.md` per constitution §9 requirement.
    - *Acceptance*: Alembic initialized with initial migration; migration scripts executable; documentation covers both Alembic (SQL future) and manual tracking (Qdrant current); T053 task activated and completed.

### Observability & Operations
  - R7.1: **MVP REQUIREMENT**: Implement basic Prometheus/Grafana integration per constitution §8; configure `/metrics/uplink` endpoint and basic dashboards with manual alert runbooks for MVP.
    - *Acceptance*: Prometheus scraping metrics from BMS API; Grafana dashboard showing latency, throughput, errors; manual alert runbooks documented.
  - R7.2: **POC DECISION**: Basic operational documentation for POC; comprehensive manual alert runbooks deferred to post-MVP phase.
    - *Acceptance*: `DEPLOYMENT_CHECKLIST.md` contains basic operational procedures for POC. Full runbooks (latency, ingestion, dependency degradation, contact matrix) deferred to production.
  - R7.3: Maintain `DEPLOYMENT_CHECKLIST.md` with escalation steps and contact matrix.
  - R7.4: **BACKUP & RETENTION**: Implement daily automated backups of `/workspace/qdrant_storage` and `/workspace/bms_data` with 30-day retention policy for logs and 90-day retention for data backups.
    - *Acceptance*: Backup script runs daily via cron; backups stored in `/workspace/backups/` with date stamps; log rotation configured for 30-day retention; backup verification documented in `DEPLOYMENT_CHECKLIST.md`.

### SharePoint Integration & Data Synchronization
  - R8.1: **SHAREPOINT DOCUMENT SYNC**: Implement automated SharePoint document download and synchronization for BMS documentation repository.
    - *Acceptance*: Download script authenticates with cookie-based auth; filters documents by modification date (post-2023); supports parallel downloads (≥10 workers); organizes by document type; handles errors gracefully with retry logic; logs download statistics.
  - R8.2: **BATCH PROCESSING**: Process downloaded SharePoint documents with Enhanced Document Processor v4.0 in batch mode.
    - *Acceptance*: Batch processor handles variable document loads; achieves ≥95% success rate; maintains ≥0.70 quality score threshold; processes ≥10 documents/minute; moves processed files to appropriate directories; logs processing statistics and errors.

### Success Criteria by Phase

**POC Phase**:
  - Ingestion workload runs successfully; invalid files rejected with specific errors
  - Semantic/hybrid search operational; baseline p95 <500ms established
  - Retrieval evaluation script reports ≥95% accuracy
  - All integrations (Slack, OpenWebUI) operational with end-to-end testing
  - Basic health and metrics endpoints return status objects
  - All persistent data stored in `/workspace` folder
  - Basic test suite passes (≥80% coverage per constitution §4)

**MVP Phase**:
  - Performance: p95 <200ms for 20-50 concurrent users
  - Security: Rate limiting (60 req/min per IP) validated by automated tests
  - Monitoring: Prometheus/Grafana operational with manual alert runbooks
  - Operations: Automated backup system with 30-day log retention, 90-day data retention
  - Documentation: Complete operational procedures in `DEPLOYMENT_CHECKLIST.md`
  - Availability: 99.9% with documented incident response

**Production Phase** (per Q6, Q10 clarifications):
  - **Timeline**: 1-2 months starting 2025-10-04 (retrieval enhancements T056-T071 complete)
  - **Current Status**: Constitution compliance sprint (T043-T055) is NOW the active priority
  - **Sprint Priority**: Constitution compliance (T043-T055) → Production deployment → Multi-backend LLM (T047, deferred post-production)
  - Performance: p95 ≤100ms for 20-100 concurrent users (95% read / 5% write workload)
  - Security: JWT + API key authentication enforced (T046), encryption at rest (T043), GDPR compliance (T044)
  - Monitoring: Automated alerting with PagerDuty/Slack integration (T050)
  - CI/CD: Full pipeline with coverage reports, security scans (Bandit, Safety), pre-commit hooks (T054)
  - Database: Alembic migration framework implemented (T053, R6.4)
  - Availability: 99.99% with automated failover (T052)
  - **Target Completion**: 2025-12-04 (2 months from retrieval enhancement completion)

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

### Session 2 - 2025-10-04 12:15 UTC
**Clarifier**: Workflow `/clarify` execution  
**Questions Resolved**: 5 production readiness ambiguities

| ID | Category | Question | Decision | Impact |
|----|----------|----------|----------|--------|
| Q6 | Production Timeline | When should constitution compliance tasks (T043-T055) be completed? | **A**: Within 1-2 months (immediate priority after enhancements) | Production roadmap established |
| Q7 | Database Migrations | Should Alembic be implemented despite Qdrant being NoSQL? | **A**: Yes - Implement now for future SQL readiness | Activate T053 |
| Q8 | Performance Definition | What does "concurrent users" mean for performance targets? | **D**: Mixed workload - 95% read, 5% write (RAG best practice) | Load testing scenarios defined |
| Q9 | LLM Architecture | Should multi-backend LLM (T047) be in 1-2 month timeline? | **D**: Defer - Add vLLM only when performance requires | T047 deferred post-production |
| Q10 | Feature Priority | Complete retrieval enhancements before production compliance? | **A**: Yes - Finish T061, T065, T067, T068 first | Current trajectory confirmed |

**Impact**: 
- Production deployment timeline: 1-2 months post-enhancement completion
- Performance testing: 95% read / 5% write workload mix
- Database migrations: T053 activated (Alembic framework implementation)
- LLM backends: Single backend (Ollama) acceptable for initial production
- Sprint priority: Complete retrieval enhancements → Production compliance → Multi-backend LLM

### Session 3 - 2025-10-04 17:55 UTC
**Clarifier**: Workflow `/clarify` execution  
**Questions Resolved**: 5 POC scope and validation ambiguities

| ID | Category | Question | Decision | Impact |
|----|----------|----------|----------|--------|
| Q11 | Project Phase | What is the current active phase? | **A**: POC - Core functionality validation with simplified requirements | Production compliance (T001-T020) deferred to future sprint |
| Q12 | Success Criteria | Minimum document corpus for POC validation? | **B**: 700 total documents (430 PDFs + 270 Office files) required | SharePoint Office file ingestion is POC-blocking work |
| Q13 | Implementation Scope | SharePoint automation level required? | **B**: Hybrid - Automated for 70 direct URLs, manual bulk download acceptable for 212 Office Online URLs | Pragmatic automation approach for POC |
| Q14 | Validation Requirements | Retrieval evaluation requirements for POC? | **A**: Formal evaluation - 50-query ground truth dataset with ≥95% accuracy measurement | Ground truth dataset creation is POC-blocking |
| Q15 | Integration Completeness | Which integrations must be operational? | **A**: All three - Slack + OpenWebUI + n8n functional and tested | All integrations required for POC signoff despite n8n "optional" label |

**Impact**:
- POC phase confirmed as current active sprint
- Document ingestion completion is critical path: 430/700 documents (61% complete)
- SharePoint integration tasks required: Automated script for 70 files + manual bulk download documentation for 212 files
- Evaluation dataset creation added to POC scope: 50 queries across 10 categories
- Integration development scope: All three integrations (Slack, OpenWebUI, n8n) must be functional
- Production compliance tasks (T001-T020) explicitly deferred until POC completion

### Session 4 - 2025-10-04 20:00 UTC
**Context**: POC Evaluation Completion & Cross-Artifact Analysis  
**Achievement**: 80% Top-5 Accuracy (40/50 queries passing) after 15 hours comprehensive evaluation work  
**Questions Resolved**: 1 critical acceptance criteria clarification

| ID | Category | Question | Decision | Impact |
|----|----------|----------|----------|--------|
| Q16 | Retrieval Accuracy | Is 80% Top-5 accuracy sufficient for POC completion or must we reach 95%? | **A**: 80-85% acceptable for POC signoff; 95% remains production target (R2.2). Path to 95% documented (30-40 hours: missing doc recovery +6%, full BM25 +3%, fine-tuning +3-5%). | POC can proceed to integration testing; 95% target deferred to MVP/Production phases |

**Evaluation Results Summary**:
- **Achieved**: 80% Top-5 accuracy (40/50 queries, +18% from 62% baseline)
- **Category Performance**: 4 categories at 100% (Finance, Quality, Procurement, Business Development); 7/10 at 80%+
- **Technical Innovations**: Form augmentation (83 chunks), lightweight keyword matching (pseudo-BM25), metadata-based reranking (now user-accessible via search_smart() function in OpenWebUI tool)
- **Blocking Issues**: 4 missing documents (8% of queries impossible: HUMR-FOR-005, HUMR-FOR-018, ISEC-FOR-015, QHSE-FOR-029)
- **Path to 95%**: Document recovery (+6-8%) → Full BM25 integration (+2-3%) → Domain-specific fine-tuning (+3-5%)

**Impact**:
- **R2.2 Clarification**: "≥95% top-5 retrieval accuracy" remains production target; POC acceptance criteria adjusted to 80-85% with documented improvement path
- **POC Signoff Criteria**: 80% accuracy sufficient for POC completion alongside functional integrations and baseline performance
- **MVP Target**: 85-90% accuracy (missing document recovery + full BM25 integration)
- **Production Target**: 92-95% accuracy (domain-specific embedding fine-tuning)
- **Effort Estimates**: MVP improvements 12-17 hours; Production fine-tuning 45-65 hours

### Session 5 - 2025-10-04 20:45 UTC
**Context**: POC Completion Readiness & Testing Criteria Refinement  
**Trigger**: OpenWebUI tool enhancement complete (search_smart() with metadata boosting), integration testing scope clarification needed  
**Questions Resolved**: 5 POC signoff criteria clarifications

| ID | Category | Question | Decision | Impact |
|----|----------|----------|----------|--------|
| Q17 | Integration Testing | Should POC signoff require all three integrations (Slack, OpenWebUI, n8n) per Q15, or just OpenWebUI? | **B**: Honor Q15 - Complete all three integrations before POC signoff | T023 scope confirmed: all integrations required; T023b undeferred |
| Q18 | Documentation | Should search_smart() implementation be documented in Session 4 POC results? | **C**: Update Session 4 "Technical Innovations" to clarify metadata boosting now user-accessible | Session 4 results updated to reflect user-facing implementation |
| Q19 | Document Recovery | Should missing document recovery be POC-blocking? | **C**: Best effort recovery (1-2 hours); accept POC if not found | T021 scope: attempt recovery of HUMR-FOR-005, HUMR-FOR-018, ISEC-FOR-015, QHSE-FOR-029; document outcome |
| Q20 | Performance Baseline | What p95 latency threshold is required for POC signoff? | **D**: Best-effort baseline; no hard threshold for POC | T024 establishes baseline regardless of result; optimization deferred to MVP if needed |
| Q21 | Test Coverage | How is ≥80% coverage requirement enforced for POC? | **B**: Core-only strict - ≥80% on api/, scripts/; integrations/tools can be lower | T025 scope: measure coverage separately for core vs integrations; 80% required for core logic only |

**Impact**:
- **Integration Testing Scope**: All three integrations (Slack, OpenWebUI, n8n) must be functional and tested for POC signoff (reaffirms Q15 decision)
- **T023 Execution Plan**: OpenWebUI (12/12 tests passing) ✅ complete; Slack and n8n testing required before T026
- **Document Recovery**: Best-effort 1-2 hour attempt for 4 missing documents; POC proceeds regardless of recovery success
- **Performance Baseline**: T024 establishes baseline metrics without POC-blocking thresholds; <1000ms acceptable, optimization work deferred to MVP if p95 >500ms
- **Test Coverage Definition**: "Core logic" defined as api/ and scripts/ directories; tools/ and integrations can have lower coverage without blocking POC
- **POC Readiness**: Clear signoff criteria established - 80% accuracy ✅, all integrations tested, baseline established, ≥80% core coverage, evidence collected
