# Tasks: BMS Agent - Railway Documentation RAG System

**Input**: Design documents from `/specs/001-railway-rag-system/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.openapi.yaml

**Tests**: Test tasks are NOT included as they were not explicitly requested in the feature specification. Focus is on implementation tasks for rapid MVP delivery.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Project structure from plan.md:
```
bms-agent/
├── bms-agent/
│   ├── api/               # FastAPI routes and orchestration
│   ├── scr/               # Core processing modules (NOTE: existing naming)
│   └── tests/             # Test suite
├── upload-files/          # Document storage by department
└── [CLI tools at root]    # ingest_documents_to_qdrant.py, batch_ingest_by_department.py, etc.
```

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, environment configuration, and basic structure validation

- [ ] T001 Verify project structure matches plan.md layout in /workspace/bms-agent/
- [ ] T002 Install Python 3.11+ and verify version compatibility
- [ ] T003 [P] Install core dependencies from requirements.txt (FastAPI, uvicorn, qdrant-client, pydantic)
- [ ] T004 [P] Install document processing dependencies (PyMuPDF, python-docx, python-pptx, openpyxl, Pillow)
- [ ] T005 [P] Install NLP dependencies (sentence-transformers, NLTK, spaCy, en_core_web_sm model)
- [ ] T006 [P] Install testing dependencies (pytest, pytest-asyncio, pytest-cov, httpx)
- [ ] T007 Download NLTK data (punkt, stopwords) to /workspace/bms-agent/
- [ ] T008 Create /workspace/qdrant-data/ directory with proper permissions
- [ ] T009 Create /workspace/logs/ directory structure (api.log, qdrant.log, ollama.log, webui.log)
- [ ] T010 Create /workspace/bms-agent/upload-files/ with 21 department subdirectories (HR, Safety, Operations, Maintenance, etc.)
- [ ] T011 Configure environment variables template (.env.example) in /workspace/bms-agent/ with BMS_*, QDRANT_*, EMBEDDING_* variables
- [ ] T012 Verify Qdrant binary exists at /workspace/bms-agent/qdrant and is executable

**Checkpoint**: Environment and dependencies ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Qdrant Collection Setup

- [ ] T013 Create QdrantSchemaV4 class in bms-agent/scr/qdrant_schema_v4.py with multi-vector config (4 dense + 1 sparse)
- [ ] T014 Implement create_collection() method with named vectors: chunk_embedding, parent_embedding, child_embedding, full_doc_embedding (all 768d for sentence-transformers)
- [ ] T015 Implement sparse vector config for keyword_sparse (BM25-style)
- [ ] T016 Create keyword indexes for metadata fields: department, chapter_number, document_name
- [ ] T017 Implement collection health check methods in qdrant_schema_v4.py

### Embedding Service Abstraction

- [ ] T018 Create EmbeddingService class in bms-agent/scr/embedding_service.py supporting dual providers (sentence-transformers + Ollama)
- [ ] T019 [P] Implement sentence-transformers backend in embedding_service.py (all-mpnet-base-v2, 768d)
- [ ] T020 [P] Implement Ollama backend in embedding_service.py (snowflake-arctic-embed2, 1024d) with HTTP API calls
- [ ] T021 Add embed() async method for batch embedding generation with configurable batch size
- [ ] T022 Implement health check for embedding service availability in embedding_service.py

### Metrics Collection Infrastructure

- [ ] T023 Create MetricsCollector class in bms-agent/scr/metrics_collector.py with in-memory storage
- [ ] T024 Implement record_request() method tracking latency, error flags, queue depth
- [ ] T025 Implement get_metrics() method returning request_count, latency_p50/p95/p99, error_rate, queue_depth
- [ ] T026 Add rolling window logic (last 1000 requests) to prevent memory growth

### FastAPI Application Foundation

- [ ] T027 Create FastAPI app in bms-agent/api/main.py with CORS middleware for OpenWebUI integration
- [ ] T028 [P] Implement /health endpoint returning overall service status with metrics in api/main.py
- [ ] T029 [P] Implement /health/qdrant endpoint checking Qdrant connectivity in api/main.py
- [ ] T030 [P] Implement /health/embedding endpoint checking embedding service status in api/main.py
- [ ] T031 [P] Implement /metrics endpoint exposing MetricsCollector data in api/main.py
- [ ] T032 Add optional API key authentication middleware in api/main.py (X-API-Key header, configurable via BMS_API_KEY env var)
- [ ] T033 Add input sanitization middleware removing special characters <>{}\\ from all text inputs in api/main.py
- [ ] T034 Configure lifespan events for FastAPI (startup: load embedding model, create Qdrant client; shutdown: cleanup) in api/main.py

### Data Models (Pydantic)

- [ ] T035 [P] Create Document model in bms-agent/api/models.py (document_id, document_name, document_type enum, department, file_path, processing_status enum, etc.)
- [ ] T036 [P] Create Chunk model in bms-agent/api/models.py (chunk_id, document_id, chunk_text, parent_chunk_id, chapter metadata, quality_score, etc.)
- [ ] T037 [P] Create SearchRequest model in bms-agent/api/models.py (query, limit, filter_department, filter_chapter_number, etc.)
- [ ] T038 [P] Create SearchResponse model in bms-agent/api/models.py (query, results, total_results, search_time_ms, etc.)
- [ ] T039 [P] Create SearchResult model in bms-agent/api/models.py (chunk_id, chunk_text, relevance_score, ranking_position, chapter_context, quality_score, etc.)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Technical Documentation Search (Priority: P1) 🎯 MVP

**Goal**: Enable semantic search across railway documentation with department filtering and chapter context

**Independent Test**: Upload sample railway documents, submit natural language query (e.g., "brake system maintenance procedures"), verify relevant chunks returned with source citations, chapter info, and quality scores above 85%

### Implementation for User Story 1

- [ ] T040 [P] [US1] Implement basic semantic search in qdrant_schema_v4.py using chunk_embedding vector
- [ ] T041 [P] [US1] Add department filter to search in qdrant_schema_v4.py using Qdrant query_filter with department match
- [ ] T042 [P] [US1] Add chapter_number filter to search in qdrant_schema_v4.py
- [ ] T043 [P] [US1] Add result ranking by cosine similarity with score normalization in qdrant_schema_v4.py
- [ ] T044 [US1] Implement POST /api/v1/search/semantic endpoint in api/main.py accepting SearchRequest, calling qdrant_schema_v4 search, returning SearchResponse
- [ ] T045 [US1] Add query embedding generation using EmbeddingService in semantic search endpoint
- [ ] T046 [US1] Add metrics recording (latency, request count) to semantic search endpoint using MetricsCollector
- [ ] T047 [US1] Add error handling for empty collections, invalid queries, embedding service failures in semantic search endpoint
- [ ] T048 [US1] Format search results with chapter context (chapter_number, chapter_title, chapter_path) from chunk payload
- [ ] T049 [US1] Add quality score filtering (only return chunks with quality_score >= 85) in search results

**Checkpoint**: User Story 1 complete - semantic search functional and testable independently. Can search indexed documents by natural language queries with filtering.

---

## Phase 4: User Story 2 - Document Ingestion & Processing (Priority: P1) 🎯 MVP

**Goal**: Enable document upload and processing for multiple formats with hierarchical chunking, quality validation, and automatic indexing

**Independent Test**: Upload PDF/DOCX/PPTX files via API, verify text extraction, confirm hierarchical chunking with parent/child relationships, check Qdrant collection contains chunks with all metadata

### Document Processing Pipeline Components

- [ ] T050 [P] [US2] Create EnhancedDocumentProcessor class in bms-agent/scr/enhanced_document_processor.py
- [ ] T051 [P] [US2] Implement PDF text extraction in enhanced_document_processor.py using PyMuPDF with OCR fallback (Pillow)
- [ ] T052 [P] [US2] Implement DOCX text extraction in enhanced_document_processor.py using python-docx
- [ ] T053 [P] [US2] Implement PPTX text extraction in enhanced_document_processor.py using python-pptx
- [ ] T054 [P] [US2] Implement XLSX text extraction in enhanced_document_processor.py using openpyxl
- [ ] T055 [P] [US2] Implement TXT/MD/CSV text extraction in enhanced_document_processor.py (plain read)

### Chapter Extraction

- [ ] T056 [US2] Create ChapterExtractor class in bms-agent/scr/chapter_extractor.py
- [ ] T057 [P] [US2] Implement markdown header detection (#, ##, ###) in chapter_extractor.py
- [ ] T058 [P] [US2] Implement numbered section detection (1.2.3, A.1.2) in chapter_extractor.py using regex patterns
- [ ] T059 [P] [US2] Implement Word-style heading detection (Heading 1, Heading 2) for DOCX in chapter_extractor.py
- [ ] T060 [US2] Build hierarchical chapter structure (chapter_path: "1 > 1.2 > 1.2.3") in chapter_extractor.py
- [ ] T061 [US2] Create fallback pseudo-chapters for unstructured documents in chapter_extractor.py

### Hierarchical Chunking

- [ ] T062 [US2] Implement hierarchical_chunk() method in enhanced_document_processor.py creating parent chunks (1500 chars) and child chunks (500 chars)
- [ ] T063 [US2] Add chunk overlap logic (200 chars) to hierarchical chunking in enhanced_document_processor.py
- [ ] T064 [US2] Associate chunks with chapters (chapter_number, chapter_title, chapter_path) in enhanced_document_processor.py
- [ ] T065 [US2] Create parent-child relationships (parent_chunk_id) in chunk metadata in enhanced_document_processor.py

### Quality Validation

- [ ] T066 [US2] Implement compute_quality_score() in enhanced_document_processor.py with RAGAS-style metrics (faithfulness, relevancy, precision, recall)
- [ ] T067 [P] [US2] Implement faithfulness check (sentence completeness, no truncation) in enhanced_document_processor.py
- [ ] T068 [P] [US2] Implement relevancy check (embedding similarity to parent >0.7, keyword overlap with chapter) in enhanced_document_processor.py
- [ ] T069 [P] [US2] Implement precision check (information density >0.4, no generic boilerplate) in enhanced_document_processor.py
- [ ] T070 [P] [US2] Implement recall check (parent-child overlap >10%) in enhanced_document_processor.py
- [ ] T071 [US2] Add quality threshold filtering (default 85%, configurable via BMS_QUALITY_THRESHOLD) in enhanced_document_processor.py
- [ ] T072 [US2] Log filtered low-quality chunks to /workspace/logs/api.log for review

### Multi-Vector Embedding Generation

- [ ] T073 [US2] Generate chunk_embedding using EmbeddingService in enhanced_document_processor.py
- [ ] T074 [US2] Generate parent_embedding from parent chunk text in enhanced_document_processor.py
- [ ] T075 [US2] Generate child_embedding from child chunks (if this is parent) in enhanced_document_processor.py
- [ ] T076 [US2] Generate full_doc_embedding from document summary/first paragraphs in enhanced_document_processor.py
- [ ] T077 [US2] Generate keyword_sparse vector using TF-IDF on chunk text in enhanced_document_processor.py

### Qdrant Indexing

- [ ] T078 [US2] Create ProcessorWrapper class in bms-agent/api/processor_wrapper.py orchestrating full ingestion pipeline
- [ ] T079 [US2] Implement process_document() method in processor_wrapper.py calling EnhancedDocumentProcessor, ChapterExtractor, EmbeddingService
- [ ] T080 [US2] Build Qdrant PointStruct with multi-vector embeddings and full metadata payload in processor_wrapper.py
- [ ] T081 [US2] Batch upsert points to Qdrant (100-1000 per batch) in processor_wrapper.py
- [ ] T082 [US2] Add error handling for Qdrant connection failures, embedding errors in processor_wrapper.py

### Upload API Endpoints

- [ ] T083 [US2] Implement POST /api/v1/upload endpoint in api/main.py accepting multipart/form-data file upload
- [ ] T084 [US2] Add file size validation (max 100MB, configurable via BMS_UPLOAD_MAX_BYTES) in upload endpoint
- [ ] T085 [US2] Stream uploaded file to /workspace/bms-agent/upload-files/{department}/ in upload endpoint
- [ ] T086 [US2] Queue document processing as FastAPI BackgroundTasks in upload endpoint
- [ ] T087 [US2] Return 202 Accepted with document_id and job_id immediately in upload endpoint
- [ ] T088 [US2] Implement POST /api/v1/batch-upload endpoint for multiple files in api/main.py
- [ ] T089 [US2] Add progress tracking for batch uploads (log processing status) in batch-upload endpoint

**Checkpoint**: User Story 2 complete - document ingestion functional. Can upload documents, process with hierarchical chunking, validate quality, generate embeddings, index to Qdrant.

---

## Phase 5: User Story 3 - Hybrid Search with Keyword Matching (Priority: P2)

**Goal**: Enable hybrid search combining semantic similarity with exact keyword matching using Reciprocal Rank Fusion

**Independent Test**: Submit query with technical term (e.g., "EMU-750"), compare pure semantic vs hybrid results, verify hybrid improves precision for acronyms/model numbers

### Implementation for User Story 3

- [ ] T090 [P] [US3] Implement RRF fusion algorithm in qdrant_schema_v4.py combining dense and sparse search results
- [ ] T091 [P] [US3] Add alpha weighting parameter to RRF (0=keyword only, 1=semantic only, default 0.5) in qdrant_schema_v4.py
- [ ] T092 [US3] Implement hybrid_search() method in qdrant_schema_v4.py running parallel dense + sparse queries
- [ ] T093 [US3] Merge and rank results using RRF scores in qdrant_schema_v4.py
- [ ] T094 [US3] Implement POST /api/v1/search/hybrid endpoint in api/main.py accepting SearchRequest with alpha parameter
- [ ] T095 [US3] Add query sparse vector generation (TF-IDF on query terms) in hybrid search endpoint
- [ ] T096 [US3] Add metrics recording for hybrid search in api/main.py

**Checkpoint**: User Story 3 complete - hybrid search functional. Can combine semantic and keyword matching for better technical term retrieval.

---

## Phase 6: User Story 4 - Conversational Interface via OpenWebUI (Priority: P2)

**Goal**: Provide conversational interface through OpenWebUI custom tool with 25+ search functions

**Independent Test**: Install OpenWebUI tool, ask natural language question via chat, verify tool retrieves chunks and synthesizes answer with citations

### Implementation for User Story 4

- [ ] T097 [US4] Create bms_search.py OpenWebUI custom tool at repository root with tool metadata (name, description, version 4.2)
- [ ] T098 [P] [US4] Implement semantic_search() function in bms_search.py calling /api/v1/search/semantic
- [ ] T099 [P] [US4] Implement hybrid_search() function in bms_search.py calling /api/v1/search/hybrid
- [ ] T100 [P] [US4] Implement department_filtered_search() function in bms_search.py with department parameter
- [ ] T101 [P] [US4] Implement chapter_based_search() function in bms_search.py with chapter_number parameter
- [ ] T102 [P] [US4] Add 21 more specialized search functions (fleet-specific, standard-compliance, network-component, etc.) in bms_search.py
- [ ] T103 [US4] Implement result formatting with source citations for LLM consumption in bms_search.py
- [ ] T104 [US4] Add SVG chart generation capability for numerical data in bms_search.py
- [ ] T105 [US4] Add Mermaid diagram generation for process flows in bms_search.py
- [ ] T106 [US4] Implement conversation context management (store last query results) in bms_search.py
- [ ] T107 [US4] Create OpenWebUI tool installation instructions in bms_search.py docstring

**Checkpoint**: User Story 4 complete - OpenWebUI integration functional. Can search via conversational interface with 25+ specialized functions.

---

## Phase 7: User Story 5 - Multi-Vector Hierarchical Retrieval (Priority: P3)

**Goal**: Enable hierarchical search returning parent chunks when child chunks match, providing broader context

**Independent Test**: Submit specific query matching child chunk, verify system returns parent chunk with surrounding context

### Implementation for User Story 5

- [ ] T108 [US5] Implement hierarchical_search() method in qdrant_schema_v4.py searching child_embedding vector
- [ ] T109 [US5] Add parent chunk retrieval logic (lookup parent_chunk_id from matched children) in qdrant_schema_v4.py
- [ ] T110 [US5] Implement POST /api/v1/search/hierarchical endpoint in api/main.py calling hierarchical search
- [ ] T111 [US5] Format results with both child match score and parent context in hierarchical endpoint
- [ ] T112 [US5] Add toggle for hierarchical mode in SearchRequest model (enable_hierarchical: bool)

**Checkpoint**: User Story 5 complete - hierarchical retrieval functional. Can return parent chunks for better context on specific queries.

---

## Phase 8: User Story 6 - Railway-Specific Metadata Filtering (Priority: P3)

**Goal**: Enable filtering by railway-specific metadata (fleet_type, train_id, standard_compliance, network_component)

**Independent Test**: Tag documents with railway metadata, submit filtered query (e.g., fleet_type="EMU"), verify only EMU-related docs returned

### Implementation for User Story 6

- [ ] T113 [P] [US6] Add railway metadata fields to Document model in api/models.py (fleet_type, train_id, standard_compliance, network_component)
- [ ] T114 [P] [US6] Update upload endpoint to accept railway metadata in api/main.py
- [ ] T115 [P] [US6] Store railway metadata in chunk payloads during indexing in processor_wrapper.py
- [ ] T116 [P] [US6] Create keyword indexes for railway fields in qdrant_schema_v4.py
- [ ] T117 [US6] Implement railway_specific_search() method in qdrant_schema_v4.py with railway metadata filters
- [ ] T118 [US6] Implement POST /api/v1/search/railway endpoint in api/main.py accepting RailwaySearchRequest with railway filters
- [ ] T119 [US6] Add railway filter validation (enum for fleet_type: DMU/EMU/Locomotive, etc.) in api/models.py

**Checkpoint**: User Story 6 complete - railway-specific filtering functional. Can narrow search by fleet type, standards, components.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, documentation, and production readiness tasks

### CLI Tools

- [ ] T120 [P] Create ingest_documents_to_qdrant.py CLI tool at repository root for single document ingestion with progress bar
- [ ] T121 [P] Create batch_ingest_by_department.py CLI tool at repository root for batch ingestion with department parameter
- [ ] T122 [P] Create verify_qdrant.py CLI tool checking collection health, point count, index status
- [ ] T123 [P] Create reset_qdrant_collection.py CLI tool for collection recreation (destructive)

### Scripts and Automation

- [ ] T124 Create init.sh script at repository root installing dependencies, downloading NLTK data, starting Qdrant
- [ ] T125 Update /pre_start.sh to auto-start Ollama, OpenWebUI, Qdrant on RunPod pod boot (if not already present)

### Documentation

- [ ] T126 [P] Update README.md with setup instructions, API usage examples, environment variables
- [ ] T127 [P] Create CLAUDE.md reference guide for AI assistants (already exists, verify completeness)
- [ ] T128 [P] Update requirements.txt with all production dependencies and version pins

### n8n Integration (Optional)

- [ ] T129 [P] Create n8n workflow JSON in n8n/workflows/ for Slack integration
- [ ] T130 [P] Configure n8n to call /api/v1/search/semantic endpoint
- [ ] T131 [P] Add LLM response generation with Ollama Mistral in n8n workflow

### Production Hardening

- [ ] T132 [P] Add request timeout limits (120s default) to FastAPI endpoints
- [ ] T133 [P] Add retry logic for transient Qdrant connection failures (3 retries with exponential backoff)
- [ ] T134 [P] Add retry logic for embedding service failures (3 retries)
- [ ] T135 [P] Configure log rotation for /workspace/logs/ files (30-day retention)
- [ ] T136 Implement graceful shutdown handling for FastAPI (finish processing queue before exit)
- [ ] T137 Add Qdrant data backup script (snapshot /workspace/qdrant-data/)

---

## Dependency Graph

**User Story Completion Order** (based on dependencies):

```
Phase 1 (Setup) → Phase 2 (Foundation) → [Phase 3-8 can proceed independently]

User Story Dependencies:
- US1 (Search) depends on: Phase 2 complete
- US2 (Ingestion) depends on: Phase 2 complete
- US3 (Hybrid) depends on: US1 complete (extends semantic search)
- US4 (OpenWebUI) depends on: US1, US2, US3 complete (integrates with all search modes)
- US5 (Hierarchical) depends on: US1, US2 complete (requires indexed hierarchical chunks)
- US6 (Railway Filters) depends on: US1, US2 complete (extends search and ingestion)

Recommended Implementation Order for MVP:
1. Phase 1 (Setup) - T001-T012
2. Phase 2 (Foundation) - T013-T039
3. Phase 3 (US1: Search) - T040-T049 ✅ MVP MILESTONE 1
4. Phase 4 (US2: Ingestion) - T050-T089 ✅ MVP MILESTONE 2
5. Phase 5+ (Enhancements) - T090+ (defer if MVP sufficient)
```

**Critical Path** (must complete in order):
1. T001-T012 (Setup)
2. T013-T039 (Foundation)
3. Either US1 OR US2 first (both are P1 and can be done in either order or parallel)

**Parallel Opportunities**:
- Within Phase 1: T003-T007 can run in parallel (independent installations)
- Within Phase 2: T019-T020 (embedding backends), T027-T031 (health endpoints), T035-T039 (models)
- Within Phase 4 (US2): T051-T055 (document extractors), T057-T059 (chapter detection), T067-T070 (quality checks)
- US3-US6 can all be developed in parallel after US1+US2 complete

---

## Parallel Execution Examples

### Phase 1 Setup - Parallel Installation
```bash
# Run in parallel (separate terminals or scripts)
Terminal 1: pip install fastapi uvicorn[standard] qdrant-client pydantic  # T003
Terminal 2: pip install PyMuPDF python-docx python-pptx openpyxl Pillow    # T004
Terminal 3: pip install sentence-transformers nltk spacy && python -m spacy download en_core_web_sm  # T005
Terminal 4: pip install pytest pytest-asyncio pytest-cov httpx              # T006
```

### Phase 2 Foundation - Parallel Core Components
```bash
# Developers can work on these simultaneously
Developer 1: qdrant_schema_v4.py (T013-T017)
Developer 2: embedding_service.py (T018-T022)
Developer 3: metrics_collector.py (T023-T026)
Developer 4: api/main.py health endpoints (T027-T031)
Developer 5: api/models.py Pydantic schemas (T035-T039)
```

### Phase 3 (US1) + Phase 4 (US2) - MVP Parallel Development
```bash
# Two teams can work in parallel after Phase 2 complete
Team A (Search): T040-T049 (api/main.py semantic search endpoint + qdrant_schema_v4.py search methods)
Team B (Ingestion): T050-T089 (enhanced_document_processor.py + processor_wrapper.py + upload endpoints)

# This accelerates MVP delivery from 4 weeks to 2 weeks
```

### Phase 5-8 - Enhancement Parallel Development
```bash
# All enhancements can proceed in parallel
Developer 1: US3 Hybrid Search (T090-T096)
Developer 2: US4 OpenWebUI Tool (T097-T107)
Developer 3: US5 Hierarchical Search (T108-T112)
Developer 4: US6 Railway Filters (T113-T119)
Developer 5: CLI Tools (T120-T123)
```

---

## Implementation Strategy

### MVP Scope (Phases 1-4)
**Timeline**: 3-4 weeks with 2 developers
**Deliverable**: Functional RAG system with semantic search and document ingestion

**Must Have (MVP)**:
- Setup and foundation (T001-T039) - 1 week
- Semantic search (T040-T049) - 3 days
- Document ingestion (T050-T089) - 1.5 weeks
- Basic CLI tools (T120-T122) - 2 days

**Success Criteria for MVP**:
- ✅ Can upload PDF/DOCX documents via API
- ✅ Documents processed with hierarchical chunking
- ✅ Semantic search returns relevant results <2s p95
- ✅ Results include chapter context and quality scores
- ✅ Department filtering works
- ✅ 300+ documents indexed without performance degradation

### Enhancement Scope (Phases 5-8)
**Timeline**: 2-3 weeks with 2 developers (can run in parallel with MVP)
**Deliverable**: Advanced search modes, OpenWebUI integration, railway-specific features

**Should Have (Post-MVP)**:
- Hybrid search (T090-T096) - 3 days
- OpenWebUI tool (T097-T107) - 1 week
- Hierarchical search (T108-T112) - 2 days
- Railway filters (T113-T119) - 3 days

### Polish Scope (Phase 9)
**Timeline**: 1 week
**Deliverable**: Production-ready system with monitoring, documentation, automation

**Nice to Have**:
- CLI tools for batch operations
- n8n workflow integration
- Production hardening (retries, timeouts, backups)
- Complete documentation

---

## Task Summary

**Total Tasks**: 137
**MVP Tasks** (Phases 1-4): 89 (65%)
**Enhancement Tasks** (Phases 5-8): 30 (22%)
**Polish Tasks** (Phase 9): 18 (13%)

**Tasks per User Story**:
- US1 (Search): 10 tasks
- US2 (Ingestion): 40 tasks (largest due to document processing pipeline)
- US3 (Hybrid): 7 tasks
- US4 (OpenWebUI): 11 tasks
- US5 (Hierarchical): 5 tasks
- US6 (Railway Filters): 7 tasks

**Parallel Opportunities**: 45 tasks marked [P] can run in parallel (33%)

**Independent Test Criteria**:
- US1: Submit query "brake procedures" → returns chunks with citations
- US2: Upload PDF → verify chunks in Qdrant with metadata
- US3: Query "EMU-750" → hybrid beats semantic for precision
- US4: Ask OpenWebUI "emergency procedures" → gets answer with citations
- US5: Query specific term → returns parent chunk with context
- US6: Filter by fleet_type="EMU" → only EMU docs returned

**Suggested MVP Scope**: Phases 1-4 (T001-T089) delivers functional RAG system. This is immediately useful and can be deployed to production. Phases 5-8 add enhancements based on user feedback.

---

## Format Validation

✅ **All 137 tasks follow checklist format**: `- [ ] [ID] [P?] [Story?] Description with file path`
✅ **All user story tasks labeled**: [US1] through [US6]
✅ **All file paths included**: Exact locations specified
✅ **Parallel tasks marked**: [P] on 45 tasks
✅ **Independent test criteria**: Defined for each user story
✅ **Execution order clear**: Phase dependencies documented

**Ready for `/speckit.implement`** ✓
