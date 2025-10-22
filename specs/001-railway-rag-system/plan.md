# Implementation Plan: BMS Agent - Railway Documentation RAG System

**Branch**: `001-railway-rag-system` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-railway-rag-system/spec.md`

## Summary

Build a retrieval-augmented generation (RAG) system for railway technical documentation that enables semantic search across 300+ documents from 21 departments. The system combines FastAPI backend, Qdrant vector database, and embedding services (Ollama/sentence-transformers) to provide multi-vector hierarchical search with quality validation, chapter-aware chunking, and conversational interfaces via OpenWebUI and n8n integrations.

**Core Technical Approach**:
- **Document Processing Pipeline**: Hierarchical chunking (parent 1500 chars, child 500 chars) with quality validation (RAGAS metrics, 85% threshold)
- **Multi-Vector Strategy**: 4 dense vectors (chunk, parent, child, full_doc embeddings) + 1 sparse vector (BM25-style keywords) per chunk
- **Search Architecture**: Semantic, hybrid (RRF fusion), hierarchical, and railway-specific filtering modes
- **Integration Layer**: OpenWebUI custom tool (25+ search functions) and n8n workflow for conversational access

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- **Web Framework**: FastAPI (async API with CORS, health checks, file upload)
- **Vector Database**: Qdrant v1.15.5+ (multi-vector support, keyword indexing)
- **Embeddings**: sentence-transformers (`all-mpnet-base-v2`, 768d) or Ollama (`snowflake-arctic-embed2`, 1024d)
- **Document Processing**: PyMuPDF (PDF), python-docx (DOCX), python-pptx (PPTX), openpyxl (XLSX), OCR fallback (Pillow)
- **NLP**: NLTK (tokenization), spaCy (entity recognition for chapter extraction)
- **Testing**: pytest, pytest-asyncio, pytest-cov

**Storage**:
- **Vector DB**: Qdrant persistent storage (`/workspace/qdrant-data/`)
- **Documents**: File system (`/workspace/bms-agent/upload-files/` organized by department)
- **Logs**: File-based logging (`/workspace/logs/` - api.log, qdrant.log, ollama.log, webui.log)
- **Metrics**: In-memory metrics exposed via health endpoints (request count, latency percentiles, error rates, queue depths)

**Testing**:
- **Unit**: pytest for core processing modules (chunking, quality validation, chapter extraction)
- **Integration**: Hybrid search end-to-end tests, embedding generation, Qdrant indexing
- **Performance**: Latency benchmarks (p95 < 2s), load testing (1,000 concurrent users), processing throughput (50-200 page docs in < 5min)
- **Contract**: OpenAPI schema validation, OpenWebUI tool interface tests

**Target Platform**: Linux server (Ubuntu/Debian), RunPod POD environment with persistent `/workspace` storage
**Project Type**: Web (backend API + external integrations)
**Performance Goals**:
- Search latency: < 2s p95 for 95% of queries
- Document processing: 50-200 page documents in < 5 minutes
- Concurrent capacity: 1,000 concurrent search requests without >10% degradation
- Throughput: 100+ documents batch ingestion with progress tracking

**Constraints**:
- **Security**: Minimal (no encryption at rest, HTTP acceptable, basic input validation only - per clarification)
- **Observability**: Logging + basic metrics only (no distributed tracing)
- **Rate Limiting**: None (trust-based, relies on 1,000 user capacity)
- **Persistence**: RunPod `/workspace` only location that survives restarts
- **Memory**: Embedding models require 2-4GB RAM loaded, recommend 32-64GB total
- **Storage**: Minimum 100GB for vector DB, documents, logs, and metrics

**Scale/Scope**:
- 300+ railway documents across 21 departments
- Hierarchical chunking creates ~10-50 chunks per document (3,000-15,000 total chunks)
- Each chunk has 5 vectors (4 dense @ 768-1024 dims + 1 sparse)
- Estimated vector DB size: 10-20GB for 10,000 chunks with metadata

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: N/A - No project constitution exists yet (template only)

**Recommendation**: For this system, consider establishing:
1. **API-First Design**: All functionality exposed via REST API before building integrations
2. **Quality Gates**: Minimum 85% quality scores enforced, configurable per deployment
3. **Observability Baseline**: All services must expose health endpoints with basic metrics
4. **Minimal Security**: Documented trust model, basic input validation mandatory
5. **Persistent Storage**: All stateful data must use `/workspace` paths only

## Project Structure

### Documentation (this feature)

```text
specs/001-railway-rag-system/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (current)
├── research.md          # Phase 0 output (technical decisions and best practices)
├── data-model.md        # Phase 1 output (entity schemas and relationships)
├── quickstart.md        # Phase 1 output (developer setup guide)
├── contracts/           # Phase 1 output (OpenAPI specs)
│   ├── api.openapi.yaml
│   └── openwebui-tool.schema.json
├── checklists/          # Quality validation checklists
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
bms-agent/                          # Repository root
├── bms-agent/                      # Main package
│   ├── api/                        # FastAPI application layer
│   │   ├── main.py                 # Routes, request/response models, health checks
│   │   └── processor_wrapper.py   # High-level ingestion orchestrator
│   ├── scr/                        # Core processing modules (NOTE: naming convention from existing system)
│   │   ├── enhanced_document_processor.py  # Document chunking, quality validation
│   │   ├── qdrant_schema_v4.py             # Vector DB schema, search utilities
│   │   ├── chapter_extractor.py            # Chapter structure detection
│   │   ├── embedding_service.py            # Embedding generation abstraction (NEW)
│   │   └── metrics_collector.py            # Basic metrics collection (NEW)
│   ├── tests/                      # Test suite
│   │   ├── test_basic.py           # API endpoint tests
│   │   ├── integration/            # Hybrid search, end-to-end flows
│   │   │   ├── test_hybrid_search.py
│   │   │   ├── test_ingestion_pipeline.py
│   │   │   └── test_chapter_extraction.py
│   │   ├── performance/            # Latency and load tests
│   │   │   ├── test_search_latency.py
│   │   │   └── test_concurrent_load.py
│   │   └── contract/               # OpenAPI contract validation (NEW)
│   │       └── test_api_schema.py
│   └── reqs/
│       └── requirements_file.txt   # Python dependencies
├── upload-files/                   # Document storage (21 department folders)
│   ├── HR/
│   ├── Safety/
│   ├── Operations/
│   └── [18 more departments]
├── ingest_documents_to_qdrant.py   # CLI tool for single document ingestion
├── batch_ingest_by_department.py   # CLI tool for batch ingestion
├── bms_search.py                   # OpenWebUI custom tool (v4.2 with artifacts)
├── verify_qdrant.py                # Qdrant collection health checks
├── reset_qdrant_collection.py      # Collection recreation utility
├── init.sh                         # First-time setup script (dependencies, NLTK, Qdrant)
├── qdrant                          # Qdrant binary (must be in /workspace/bms-agent/)
└── requirements.txt                # Top-level dependencies

# External integrations (not in repository)
/workspace/qdrant-data/             # Qdrant persistent storage
/workspace/logs/                    # Service logs
/workspace/ollama/                  # Ollama models
/workspace/openwebui/               # OpenWebUI data
```

**Structure Decision**: Existing hybrid web application structure with:
- **Backend API**: `bms-agent/api/` contains FastAPI routes and orchestration
- **Core Processing**: `bms-agent/scr/` contains document processing, vector DB, and embeddings logic
- **CLI Tools**: Root-level scripts for ingestion, verification, and collection management
- **External Integrations**: OpenWebUI tool (`bms_search.py`) and n8n workflows (in `n8n/workflows/` if present)

**Note**: The `scr/` naming (not `src/`) is inherited from the existing codebase and maintained for consistency.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations to track (no active constitution). This section reserved for future governance compliance tracking.

## Phase 0: Research & Technical Decisions

**Objective**: Resolve all unknowns from Technical Context and document best practices for key technologies.

### Research Topics

1. **Embedding Model Selection** (clarified: sentence-transformers vs. Ollama)
   - Current: Dual support for both models
   - Decision needed: Which to prioritize for production, fallback strategy

2. **Quality Validation Metrics** (clarified: RAGAS-style metrics)
   - Faithfulness, relevancy, precision, recall computation
   - Threshold tuning for railway domain (default 85%)

3. **Hybrid Search Fusion** (clarified: Reciprocal Rank Fusion)
   - RRF algorithm implementation
   - Alpha weighting for semantic vs. keyword balance

4. **Chapter Extraction Patterns** (clarified: regex + NLP)
   - Markdown headers, numbered sections, Word-style headings
   - Hierarchical path construction

5. **Metrics Collection Without Distributed Tracing** (clarified: basic metrics only)
   - In-memory metrics with periodic aggregation
   - Health endpoint exposure format

6. **FastAPI Best Practices** (research needed)
   - Async processing for long-running ingestion
   - File upload handling for 100MB documents
   - CORS configuration for OpenWebUI integration

7. **Qdrant Multi-Vector Indexing** (research needed)
   - Named vector configuration for 4 dense + 1 sparse
   - Keyword index setup for metadata filtering
   - Collection creation with proper schema

**Output**: See `research.md` for detailed findings

## Phase 1: Design Artifacts

### Data Model

**Objective**: Define entity schemas, relationships, and validation rules.

Entities to model (from spec):
1. **Document** - Uploaded railway documents
2. **Chunk** - Processed segments with embeddings
3. **Chapter** - Hierarchical document sections
4. **Search Query** - User search requests
5. **Search Result** - Retrieved chunks with scores
6. **Department** - Organizational document owners
7. **Embedding Model Config** - Service configuration
8. **Processing Profile** - Chunking/validation settings

**Output**: See `data-model.md` for complete schemas

### API Contracts

**Objective**: Define REST API endpoints, request/response models, and OpenWebUI tool schema.

**Endpoints to specify**:
1. **POST /api/v1/upload** - Single document upload (with replacement support)
2. **POST /api/v1/batch-upload** - Batch upload by department
3. **DELETE /api/v1/documents/{document_name}** - Delete document by name + department (NEW - FR-026)
4. **POST /api/v1/search/semantic** - Semantic search
5. **POST /api/v1/search/hybrid** - Hybrid search (semantic + keyword)
6. **POST /api/v1/search/hierarchical** - Hierarchical search (child → parent)
7. **POST /api/v1/search/railway** - Railway-specific filtered search
8. **GET /health** - Service health check with metrics
9. **GET /health/qdrant** - Qdrant connectivity check
10. **GET /health/embedding** - Embedding service check
11. **GET /metrics** - Basic operational metrics

**OpenWebUI Tool Schema**:
- 25+ search function definitions
- Input validation schemas
- Output format specifications

**Output**: See `contracts/` directory for OpenAPI and JSON schemas

### Quickstart Guide

**Objective**: Provide developer onboarding instructions for local setup and first API call.

**Contents**:
1. **Prerequisites**: Python 3.11+, Qdrant binary, Ollama (optional)
2. **Installation**: Dependencies, NLTK data, spaCy models
3. **Configuration**: Environment variables (BMS_*, QDRANT_*, EMBEDDING_*)
4. **First Run**: Start services, upload sample document, perform search
5. **Testing**: Run test suite, verify health endpoints
6. **Troubleshooting**: Common issues (collection not found, embedding service unavailable)

**Output**: See `quickstart.md`

## Phase 2: Implementation Roadmap (Task Generation)

**Note**: Detailed task breakdown is generated by `/speckit.tasks` command after this planning phase completes.

**High-Level Implementation Phases**:

### Phase 2.1: Core Infrastructure (P1 - MVP Foundation)
- Qdrant collection schema setup (multi-vector + keyword indexes)
- Document processor refactoring (if needed) to support quality validation
- Embedding service abstraction layer
- Basic metrics collection infrastructure
- Health check endpoints with metrics exposure

### Phase 2.2: Search Capabilities (P1 - MVP Core)
- Semantic search API endpoint
- Hybrid search with RRF fusion
- Metadata filtering (department, category, chapter)
- Result ranking and citation formatting

### Phase 2.3: Document Ingestion & Lifecycle (P1 - MVP Core)
- Single document upload endpoint with replacement support (FR-025)
- Document deletion endpoint (FR-026)
- Batch upload by department
- Progress tracking for long-running ingestion
- Error handling and logging
- Document identity management (document_name + department)

### Phase 2.4: OpenWebUI Integration (P2 - Enhanced UX)
- BMS search tool v4.2 implementation
- 25+ search function variants
- Artifact generation (SVG, Mermaid diagrams)
- Conversation context management

### Phase 2.5: Advanced Search (P3 - Power User Features)
- Hierarchical search (child → parent retrieval)
- Railway-specific metadata filtering
- Multi-vector query strategies
- Search result quality scoring

### Phase 2.6: Testing & Validation (All Phases)
- Unit tests for core modules
- Integration tests for search and ingestion
- Performance tests (latency, concurrency)
- Contract tests for API schema compliance

## Implementation Notes

### Technology Choices Rationale

**FastAPI vs. Flask**:
- Chosen: FastAPI
- Rationale: Native async support critical for long-running document processing, automatic OpenAPI schema generation, type validation via Pydantic

**Qdrant vs. Pinecone/Weaviate**:
- Chosen: Qdrant
- Rationale: Multi-vector support (4 dense + 1 sparse per point), keyword indexing for metadata, self-hosted (RunPod environment), mature sparse vector support

**sentence-transformers vs. Ollama embeddings**:
- Chosen: Dual support (configurable)
- Rationale: sentence-transformers faster for batch processing (768d), Ollama supports larger models (1024d), allow runtime switching

**Hierarchical Chunking vs. Fixed-Size**:
- Chosen: Hierarchical (parent/child with overlap)
- Rationale: Preserves context for dense technical documentation, enables hierarchical search strategies, overlap prevents information loss at boundaries

### Security Model (Clarified)

**Minimal Security Posture**:
- No encryption at rest for vector DB or documents (trust model)
- HTTP acceptable (HTTPS optional, not required)
- Basic input validation and sanitization mandatory
- API key authentication optional (disabled for MVP/dev environments)
- Assumes trusted network and non-sensitive railway documentation

**Rationale**: Internal system for technical documentation, not classified data, prioritizes development velocity over defense-in-depth.

### Observability Strategy (Clarified)

**Logging + Basic Metrics Only**:
- File-based logs for all services (JSON structured preferred)
- In-memory metrics: request count, latency percentiles (p50, p95, p99), error rates, queue depths
- Metrics exposed via `/metrics` endpoint (Prometheus-compatible format optional)
- No distributed tracing, no APM integration, no user behavior analytics

**Rationale**: Sufficient for 99.9% uptime SLA monitoring, avoids complexity of tracing infrastructure, aligns with minimal security/ops posture.

### Rate Limiting Strategy (Clarified)

**No Rate Limiting**:
- Trust-based access model
- Relies on natural usage patterns staying within 1,000 concurrent capacity
- No per-user or per-IP throttling
- System capacity (CPU, memory, Qdrant throughput) is the only limiting factor

**Rationale**: Internal trusted users, no external public access, simplifies implementation, aligns with minimal security model.

### Document Lifecycle Management (Clarified - Session 2025-10-22)

**Document Replacement Strategy** (FR-025):
- When document is re-uploaded with same `document_name` + `department`
- Delete all existing chunks for that document from vector database
- Process new document through full pipeline (extraction, chunking, quality validation, embedding)
- Index new chunks with fresh embeddings
- **No version history**: Old versions completely removed (FR-027)
- **Identity**: `document_name` + `department` combination (two departments can have identical filenames)

**Document Deletion Strategy** (FR-026):
- Hard delete only (no soft delete, no retention)
- `DELETE /api/v1/documents/{document_name}?department={dept}` endpoint
- Permanently removes all chunks from vector database
- Returns 404 if document not found
- No rollback or recovery after deletion

**Rationale**:
- **Simplicity**: No version management complexity
- **Data consistency**: Search results always reflect latest document version
- **No duplicates**: Old chunks never linger to confuse search
- **External versioning**: Users can manage versions via filename conventions (e.g., "Manual_v2.0.pdf")

## Risk Assessment

### High-Risk Areas

1. **Embedding Service Availability**
   - Risk: Ollama or sentence-transformers crashes/unavailable
   - Mitigation: Health checks with retry logic, graceful degradation, clear error messages (covered in edge cases)

2. **Qdrant Data Loss**
   - Risk: Qdrant storage path misconfiguration, pod restart without `/workspace` persistence
   - Mitigation: Explicit `/workspace/qdrant-data` path validation in init scripts, health checks verify persistence

3. **Document Processing Throughput**
   - Risk: Large batch ingestion (100+ docs) exceeds 5min processing SLA
   - Mitigation: Async processing with progress tracking, configurable chunk sizes, quality validation can be disabled for throughput

4. **Quality Score False Negatives**
   - Risk: 85% threshold too high, filters out valid chunks
   - Mitigation: Threshold is configurable per deployment, logging of filtered chunks for review

5. **Search Latency Under Load**
   - Risk: 1,000 concurrent users exceed 2s p95 latency
   - Mitigation: Performance testing required, Qdrant index tuning, consider result caching (future enhancement)

### Medium-Risk Areas

1. **Document Replacement Data Loss** (NEW - FR-025)
   - Risk: User uploads corrupted new version, old chunks already deleted, processing fails
   - Mitigation: Log warning about permanent deletion, document edge case in spec (user must re-upload valid version)

2. **Concurrent Document Replacement**
   - Risk: Two users replace same document simultaneously, race condition in delete + reindex
   - Mitigation: Qdrant handles upsert atomicity, async processing with proper locking

3. **Chapter Extraction Accuracy**
   - Risk: Unstructured documents have <95% chapter detection accuracy
   - Mitigation: Fallback to hierarchical chunking without chapter metadata (covered in edge cases)

4. **Hybrid Search Tuning**
   - Risk: Default alpha=0.5 not optimal for railway domain
   - Mitigation: Configurable per request, document tuning process in quickstart

5. **OpenWebUI Tool Compatibility**
   - Risk: OpenWebUI API changes break custom tool integration
   - Mitigation: Contract tests, version pinning, fallback to direct API access

## Dependencies & Prerequisites

### External Services (Must Be Running)

1. **Qdrant v1.15.5+**
   - Installation: Binary in `/workspace/bms-agent/qdrant`
   - Start: `./qdrant --storage-path /workspace/qdrant-data`
   - Health: `curl http://localhost:6333/healthz`

2. **Ollama** (optional, for snowflake-arctic-embed2)
   - Installation: Auto-managed by `/pre_start.sh` in RunPod
   - Storage: `/workspace/ollama/`
   - API: `http://localhost:11434/api/embeddings`

3. **OpenWebUI** (optional, for conversational interface)
   - Installation: Auto-managed by `/pre_start.sh` in RunPod
   - Storage: `/workspace/openwebui/`
   - Integration: Custom tool registration

### Python Dependencies (requirements.txt)

**Core**:
- fastapi >= 0.104.0
- uvicorn[standard] >= 0.24.0
- qdrant-client >= 1.7.0
- pydantic >= 2.0.0

**Document Processing**:
- PyMuPDF >= 1.23.0 (PDF extraction)
- python-docx >= 0.8.11 (DOCX)
- python-pptx >= 0.6.21 (PPTX)
- openpyxl >= 3.1.0 (XLSX)
- Pillow >= 10.0.0 (OCR fallback)

**NLP & Embeddings**:
- sentence-transformers >= 2.2.2
- nltk >= 3.8
- spacy >= 3.7.0
- en_core_web_sm (spaCy model)

**Testing**:
- pytest >= 7.4.0
- pytest-asyncio >= 0.21.0
- pytest-cov >= 4.1.0
- httpx >= 0.25.0 (async client for API tests)

**Utilities**:
- python-multipart (file uploads)
- aiofiles (async file I/O)

### Infrastructure Requirements

**Compute**:
- 8-16 vCPU (recommended 16 for concurrent embedding generation)
- 32-64GB RAM (embedding models 2-4GB each, Qdrant vector storage, document processing)

**Storage**:
- 100GB minimum persistent storage (`/workspace/`)
- Breakdown: Vector DB 20GB, documents 30GB, logs 10GB, models 10GB, buffer 30GB

**Network**:
- Internal connectivity: FastAPI ↔ Qdrant ↔ Ollama
- External access: HTTP/HTTPS for API endpoints (port 8000 default)
- OpenWebUI integration: Localhost or internal network only

## Success Criteria Verification

**How to validate each success criterion from spec**:

- **SC-001** (2s p95 latency): Performance test with `locust` or `pytest-benchmark`, measure p50/p95/p99
- **SC-002** (95%+ chapter detection): Integration test on sample docs, manual review of chapter metadata
- **SC-003** (85%+ quality scores): Unit test quality_score computation, integration test on real chunks
- **SC-004** (1,000 concurrent users): Load test with `locust`, monitor latency degradation
- **SC-005** (5min processing for 50-200 pages): Integration test with timer, adjust chunk sizes if needed
- **SC-006** (15-20% hybrid search improvement): A/B test semantic vs. hybrid on technical queries, measure precision@10
- **SC-007** (99.9% uptime): Monitor health endpoints, simulate service failures, verify recovery
- **SC-008** (70%+ irrelevant result reduction): Filter tests, measure precision improvement
- **SC-009** (5-10% chunk filtering): Quality validation unit tests, log analysis
- **SC-010** (zero data loss): Restart Qdrant, verify collection persists, count vectors before/after
- **SC-011** (90%+ OpenWebUI task completion): User acceptance testing, feedback surveys
- **SC-012** (100+ doc batch ingestion): Batch ingestion integration test, verify progress tracking
- **SC-013** (300+ doc scale): Load 300 documents, measure search latency, no degradation
- **SC-014** (60-80% scope reduction): Railway filter tests, measure result count reduction

## Next Steps

**After `/speckit.plan` completes**:

1. **Review Phase 0 Research** (`research.md`)
   - Validate technology choices
   - Confirm best practices
   - Identify any remaining unknowns

2. **Review Phase 1 Design** (`data-model.md`, `contracts/`, `quickstart.md`)
   - Validate entity schemas
   - Review API contracts for completeness
   - Test quickstart guide for accuracy

3. **Run `/speckit.tasks`** to generate detailed implementation tasks
   - Breaks down roadmap into atomic tasks
   - Assigns priorities and dependencies
   - Estimates effort for each task

4. **Begin Implementation** with `/speckit.implement`
   - Executes tasks in dependency order
   - Tracks progress and completion
   - Validates against success criteria

**Estimated Timeline** (excluding existing code):
- Phase 0 (Research): 2-3 days
- Phase 1 (Design): 3-5 days
- Phase 2.1-2.3 (MVP): 2-3 weeks
- Phase 2.4-2.5 (Enhancements): 1-2 weeks
- Phase 2.6 (Testing): 1 week
- **Total**: 5-7 weeks for complete implementation

**Note**: This system appears to already be largely implemented based on CLAUDE.md. This plan documents the architecture for specification purposes and can guide enhancements or refactoring.
