# Implementation Plan: Qdrant Collection Migration to 4096-Dimensional Embeddings

**Branch**: `004-migrate-qdrant-collection` | **Date**: 2025-10-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/workspace/specs/004-migrate-qdrant-collection/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded: 272-line specification with 15 requirements
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ All technical context resolved in spec clarifications
   → Project Type: Single Python project (vector database migration)
   → Structure Decision: Extend existing BMS Agent at /workspace/001-bms-agent
3. Fill the Constitution Check section
   → ✅ Evaluated against constitution v1.0.0
4. Evaluate Constitution Check section
   → ✅ PASS: All requirements aligned with constitution
   → Update Progress Tracking: Initial Constitution Check ✓
5. Execute Phase 0 → research.md
   → ✅ Complete: All clarifications resolved in spec
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ Generated: data-model.md, quickstart.md, migration contracts
7. Re-evaluate Constitution Check section
   → ✅ PASS: No new violations after design
   → Update Progress Tracking: Post-Design Constitution Check ✓
8. Plan Phase 2 → Describe task generation approach
   → ✅ Complete: TDD-driven migration with validation gates
9. STOP - Ready for /tasks command
```

## Summary

This feature migrates the BMS Agent's Qdrant vector database from 768-dimensional embeddings (sentence-transformers/all-mpnet-base-v2) to 4096-dimensional embeddings (Qwen3-Embedding-8B:F16) with late chunking strategy. The migration uses a blue-green deployment approach to ensure zero downtime, with comprehensive backup, validation, and rollback capabilities. Primary objectives: (1) Improve semantic search quality with larger embeddings, (2) Apply late chunking for better context preservation, (3) Maintain ≥95% retrieval accuracy and p95 latency ≤100ms, (4) Support 24-hour monitoring with automated rollback triggers.

**Technical Approach**: Create Qdrant snapshot backup, validate integrity, recreate collection with 4096-d schema, batch-reprocess 2,615 documents with GPU-accelerated embeddings, validate search quality against baseline, monitor performance for 24 hours, update documentation.

## Technical Context

**Language/Version**: Python 3.11+ (existing BMS Agent stack)
**Primary Dependencies**:
- Qdrant Python Client 1.7.4+ (vector database operations)
- Ollama (Qwen3-Embedding-8B:F16 model hosting)
- sentence-transformers (baseline comparison, not used for new embeddings)
- RAGAS (quality scoring)
- FastAPI (BMS API)

**Storage**:
- Qdrant vector database at `/workspace/qdrant_storage` (persistent across RunPod restarts)
- Source documents at `/workspace/bms_data/` (~420 files)
- Backups at `/workspace/backups/` (snapshots, baseline reports)

**Testing**:
- pytest (unit tests, integration tests)
- Qdrant API tests (collection schema validation)
- End-to-end search tests (semantic, hybrid, metadata)
- Performance benchmarking (p50/p95/p99 latency)

**Target Platform**: RunPod GPU pod (Linux server, persistent /workspace only)

**Project Type**: Single Python project extending existing BMS Agent infrastructure

**Performance Goals**:
- Document reprocessing: ≤15 minutes for 2,615 documents (batch size 32, GPU-accelerated)
- Search latency: p95 ≤100ms for Qdrant queries
- Retrieval accuracy: ≥95% compared to 768-d baseline
- Rollback time: <5 minutes from trigger to restored functionality

**Constraints**:
- Zero downtime requirement (blue-green deployment)
- Disk space: Minimum 5 GB available (migration requires ~3-4 GB for 4096-d vectors)
- Memory: Batch processing must not exceed available RAM (reduce batch size if needed)
- Migration window: **POC DECISION** - Performed during maintenance window when uploads disabled

**Scale/Scope**:
- 2,615 document chunks (11,072 vectors across 4 vector types)
- ~420 source documents in various formats (PDF, XLSX, DOCX)
- 4 vector types per chunk: chunk_embedding, parent_embedding, child_embedding, full_doc_embedding
- Estimated storage increase: 5x (from ~600 MB to ~3-4 GB)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Compliance Status: PASS

**Section 2 - Data Processing & RAG Architecture**:
- ✅ Python 3.11+ with type hints (existing BMS Agent stack)
- ✅ Qdrant vector database v1.7.4+ (upgrading schema only, not version)
- ✅ Optimized chunking strategies (late chunking implementation)
- ✅ Hybrid search maintained (semantic + keyword)

**Section 4 - Code Quality & Testing**:
- ✅ Test coverage target: 60% for POC phase (constitution POC exception)
- ✅ Unit tests for migration logic (backup, validation, rollback)
- ✅ Integration tests for end-to-end search validation
- ✅ NumPy style docstrings for all migration modules

**Section 5 - Security & Compliance**:
- ✅ Data integrity maintained (snapshot backup before destructive operations)
- ✅ Audit logging for all migration steps (timestamps, status, errors)

**Section 6 - Documentation**:
- ✅ Update CLAUDE.md with new embedding model details (FR-015)
- ✅ Create migration log with before/after metrics (FR-015)
- ✅ Update performance baselines (FR-015)
- ✅ Create troubleshooting guide for 4096-d embeddings (FR-015)

**Section 7 - Performance & Scalability**:
- ✅ p95 latency target: ≤100ms (constitution §7, POC: best effort acceptable)
- ✅ Stateless migration design (idempotent, can be restarted)

**Section 8 - Monitoring & Observability**:
- ✅ Structured logging with timestamps and correlation (NFR-008)
- ✅ Migration report generation (NFR-009)
- ✅ 24-hour performance monitoring (FR-013)

**Section 11 - AI/LLM Architecture**:
- ✅ On-premises LLM hosting (Ollama with Qwen3)
- ✅ Zero external dependencies (air-gapped operation maintained)
- ✅ Model versioning (Qwen3-Embedding-8B:F16 tracked)
- ✅ Persistent storage: Ollama models in `/workspace/data/ollama_models`

**Section 12 - Vector Database**:
- ✅ Self-hosted Qdrant (existing infrastructure)
- ✅ Hybrid retrieval maintained (semantic + keyword sparse vectors)
- ✅ Embedding versioning (768-d → 4096-d tracked)
- ✅ Schema management (collection recreation with validation)

### POC Exceptions Applied:
1. **Migration Window** (NFR-010): POC performs migration during maintenance window (off-hours, uploads disabled). Production will require online migration with graceful degradation.
2. **Test Coverage**: Target 60% for POC phase (constitution §4 POC exception). Path to 80% documented for production.
3. **Performance Validation**: Manual validation acceptable for POC; automated performance regression testing required for production.

### No Violations Requiring Justification

---

## Project Structure

### Documentation (this feature)
```
specs/004-migrate-qdrant-collection/
├── plan.md              # This file (/plan command output)
├── spec.md              # Feature specification (complete)
├── research.md          # Phase 0 output (migration strategy research)
├── data-model.md        # Phase 1 output (migration entities)
├── quickstart.md        # Phase 1 output (migration execution guide)
├── contracts/           # Phase 1 output (API compatibility contracts)
│   ├── qdrant-collection-schema.yaml    # Collection configuration
│   ├── migration-job-status.yaml        # Job tracking contract
│   └── validation-report-schema.yaml    # Validation results
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
/workspace/001-bms-agent/
├── scripts/
│   ├── migrate_qdrant_collection.py     # Main migration orchestrator (NEW)
│   ├── init_qdrant.py                   # Collection initialization (EXISTING - update for 4096-d)
│   ├── batch_process_incoming.py        # Document reprocessing (EXISTING - use for migration)
│   ├── evaluate_retrieval_enhanced.py   # Search quality validation (EXISTING)
│   ├── backup_qdrant_snapshot.py        # Backup utilities (NEW)
│   └── validate_migration.py            # Post-migration validation (NEW)
├── api/
│   ├── processor_wrapper.py             # Document processor (EXISTING - already updated for Qwen3)
│   └── main.py                          # BMS API (EXISTING - verify embeddings endpoint)
├── bms-agent/src/
│   └── enhanced_document_processor.py   # Late chunking processor (EXISTING - already updated)
├── tests/
│   ├── migration/                       # Migration test suite (NEW)
│   │   ├── test_backup_restore.py       # Backup integrity tests
│   │   ├── test_collection_schema.py    # Schema validation tests
│   │   ├── test_migration_orchestrator.py  # End-to-end migration tests
│   │   └── test_rollback.py             # Rollback procedure tests
│   └── integration/
│       └── test_search_quality.py       # Search validation tests (EXISTING - extend)
├── docs/
│   ├── MIGRATION_LOG.md                 # Migration execution log (NEW)
│   ├── TROUBLESHOOTING_4096D.md         # 4096-d specific troubleshooting (NEW)
│   └── performance-baseline.json        # Baseline metrics (EXISTING - update)
└── CLAUDE.md                            # Project instructions (EXISTING - update)

/workspace/backups/
├── qdrant-768d-backup-YYYYMMDD-HHMMSS.snapshot  # Snapshot before migration
├── baseline-768d-results.json           # Baseline search quality metrics
├── collection-768d-stats.json           # Pre-migration collection stats
└── qwen3-4096d-evaluation.json          # Post-migration validation results
```

**Structure Decision**: This feature extends the existing single Python project at `/workspace/001-bms-agent`. No new project structure needed - migration scripts are added to existing `scripts/` directory, tests to `tests/migration/`, and documentation updates to `docs/`. Leverages existing BMS API, processor wrapper, and enhanced document processor (already updated for Qwen3 in Phase 3.7 of feature 002).

---

## Phase 0: Outline & Research

**Status**: ✅ Complete (all unknowns resolved in spec clarifications)

### Research Summary

All technical unknowns were resolved during specification phase (Session 2025-10-17). No additional research required. Key decisions documented:

1. **Migration Strategy Decision**:
   - **Chosen**: Blue-green deployment with snapshot backup
   - **Rationale**: Zero downtime requirement (FR from spec), rollback capability within 5 minutes
   - **Alternatives Considered**:
     - Online migration with dual collections (rejected: complex routing logic, 2x disk space)
     - Direct in-place upgrade (rejected: no rollback path, violates zero-downtime requirement)

2. **Embedding Model Decision**:
   - **Chosen**: Qwen3-Embedding-8B:F16 via Ollama (4096-d)
   - **Rationale**: Superior semantic understanding, already installed (Phase 3.7 of feature 002), GPU-accelerated
   - **Alternatives Considered**:
     - Continue with sentence-transformers/all-mpnet-base-v2 (rejected: quality plateau)
     - OpenAI ada-002 (rejected: external dependency, violates constitution §11 air-gapped requirement)

3. **Chunking Strategy Decision**:
   - **Chosen**: Late chunking with 500 tokens/chunk, 150 token overlap
   - **Rationale**: Better context preservation, already implemented in enhanced_document_processor.py
   - **Alternatives Considered**:
     - Keep existing sentence-based chunking (rejected: sub-optimal boundaries)
     - Fixed-size chunking (rejected: breaks semantic units)

4. **Validation Approach Decision**:
   - **Chosen**: Baseline comparison with 50-query test set + 24h monitoring
   - **Rationale**: Objective quality measurement, catches performance regressions, user feedback integration
   - **Alternatives Considered**:
     - Manual spot-checking only (rejected: not measurable, not repeatable)
     - Immediate cutover without monitoring (rejected: violates FR-013 24h monitoring requirement)

5. **Disk Space Mitigation Decision**:
   - **Chosen**: Pre-flight validation (minimum 5 GB check), delete old collection after successful migration
   - **Rationale**: Prevents disk exhaustion, 5x storage increase from 768-d to 4096-d
   - **Alternatives Considered**:
     - Keep both collections indefinitely (rejected: disk space constraints)
     - Compress embeddings (rejected: performance penalty, complexity)

### Dependencies Best Practices

**Qdrant Snapshot API**:
- Use POST `/collections/{collection_name}/snapshots` to create snapshots
- Export via filesystem copy from `/workspace/qdrant_storage/snapshots/`
- Restore with snapshot upload API (POST `/collections/{collection_name}/snapshots/upload`)
- Best practice: Verify snapshot integrity with test restore before proceeding

**Ollama Embedding Generation**:
- Use `/api/embeddings` endpoint with model `dengcao/Qwen3-Embedding-8B:F16`
- Batch size: 32 (optimal for GPU memory vs throughput)
- Timeout: 5000ms per batch (generous for large model)
- Best practice: Validate model availability with test embedding before migration

**RAGAS Quality Scoring**:
- Apply during document processing (enhanced_document_processor.py already implements)
- Filter chunks with quality score <50.0 to separate collection
- Best practice: Monitor quality score distribution (target mean ≥70.0)

**Output**: research.md (see separate file for detailed findings)

---

## Phase 1: Design & Contracts

*Prerequisites: research.md complete ✓*

### 1. Data Model

**Entities extracted from spec** → `data-model.md`:

**MigrationJob** (tracks migration execution):
- Fields: job_id (UUID), start_time (datetime), end_time (datetime), status (enum: backup/recreate/reprocess/validate/monitoring/complete/rollback/failed), source_dimension (768), target_dimension (4096), backup_snapshot_path (str), documents_processed (int), documents_failed (int), validation_results (JSON), rollback_reason (str, optional)
- Validation: job_id must be unique, start_time < end_time, documents_processed ≥ 0
- State Transitions: pending → backup → recreate → reprocess → validate → monitoring → complete (or → rollback/failed on error)

**QdrantCollection** (vector database collection):
- Fields: collection_name (str), vector_dimension (768 or 4096), distance_metric (Cosine), points_count (int), indexed_vectors_count (int), status (enum: active/migrating/rollback), created_at (datetime), config (JSON)
- Validation: vector_dimension in {768, 4096}, points_count ≥ 0
- Relationships: Contains many DocumentChunks

**BackupSnapshot** (disaster recovery):
- Fields: snapshot_id (UUID), collection_name (str), created_at (datetime), file_path (str), file_size_mb (float), point_count (int), integrity_validated (bool), restoration_time_seconds (float, optional)
- Validation: file_path must exist, file_size_mb > 0, point_count matches collection count
- Relationships: Backs up one QdrantCollection

**ValidationReport** (quality assurance):
- Fields: report_id (UUID), migration_job_id (UUID), baseline_metrics (JSON: accuracy, p50, p95, p99, quality_scores), current_metrics (JSON: same structure), comparison_delta (JSON: percent changes), validation_status (enum: pass/fail/warning), generated_at (datetime), recommendations (list[str])
- Validation: baseline_metrics and current_metrics must have same keys, validation_status determined by thresholds (accuracy ≥95%, p95 ≤100ms)
- Relationships: Belongs to one MigrationJob

**EmbeddingModel** (AI model metadata):
- Fields: model_name (str), model_provider (enum: Ollama/OpenAI), vector_dimension (int), model_size_gb (float), availability_status (enum: available/unavailable), last_health_check (datetime), performance_metrics (JSON: embeddings_per_second, p95_latency_ms)
- Validation: model_name must match Ollama model list, vector_dimension > 0
- Relationships: Used by DocumentChunks (via processor wrapper)

**Output**: data-model.md (see separate file)

### 2. API Contracts

**Qdrant Collection Schema Contract** (`contracts/qdrant-collection-schema.yaml`):
```yaml
collection_name: nomad_bms_documents
vectors:
  chunk_embedding:
    size: 4096
    distance: Cosine
  parent_embedding:
    size: 4096
    distance: Cosine
  child_embedding:
    size: 4096
    distance: Cosine
  full_doc_embedding:
    size: 4096
    distance: Cosine
sparse_vectors:
  keyword_sparse:
    modifier: idf
payload_schema:
  document_id: keyword
  chunk_key: integer
  text: text
  metadata:
    file_name: keyword
    hierarchy: keyword
    has_context: bool
    processing_profile: keyword
    chunking_strategy: keyword
  quality:
    overall_score: float
    faithfulness: float
    answer_relevancy: float
    context_precision: float
  term_frequencies: object
  source_url: keyword
indexes:
  - field_name: document_id
    field_schema: keyword
  - field_name: chunk_key
    field_schema: integer
  - field_name: metadata.file_name
    field_schema: keyword
  - field_name: metadata.hierarchy
    field_schema: keyword
  - field_name: quality.overall_score
    field_schema: float
```

**Migration Job Status Contract** (`contracts/migration-job-status.yaml`):
```yaml
# GET /api/v1/migration/status/{job_id}
response:
  job_id: string (UUID)
  status: enum [backup, recreate, reprocess, validate, monitoring, complete, rollback, failed]
  progress:
    current_step: string
    documents_processed: integer
    documents_total: integer
    percent_complete: float (0-100)
    estimated_time_remaining_seconds: integer
  timestamps:
    started_at: string (ISO 8601)
    completed_at: string (ISO 8601, null if in progress)
    last_updated: string (ISO 8601)
  validation_results:
    retrieval_accuracy: float (0-1, null if not validated)
    p95_latency_ms: float (null if not validated)
    quality_score_mean: float (null if not validated)
    status: enum [not_started, in_progress, pass, fail]
  errors: array[string]
```

**BMS API Embeddings Endpoint Contract** (existing, verify 4096-d output):
```yaml
# POST /api/v1/embeddings
request:
  query: string (max 1000 characters)
response:
  embedding: array[float] (length 4096 after migration)
  model: string ("dengcao/Qwen3-Embedding-8B:F16")
  dimension: integer (4096)
errors:
  400: "Query exceeds 1000 characters" | "Query is empty"
  500: "Embedding model unavailable"
  503: "Ollama service unavailable"
```

**Output**: contracts/ directory with YAML schema files

### 3. Contract Tests

**Test: Qdrant Collection Schema** (`tests/migration/test_collection_schema.py`):
```python
def test_recreated_collection_has_4096d_vectors():
    """Verify collection schema after recreation (FR-005)"""
    collection_info = qdrant_client.get_collection("nomad_bms_documents")
    assert collection_info.config.params.vectors["chunk_embedding"].size == 4096
    assert collection_info.config.params.vectors["parent_embedding"].size == 4096
    assert collection_info.config.params.vectors["child_embedding"].size == 4096
    assert collection_info.config.params.vectors["full_doc_embedding"].size == 4096
    # EXPECTED: FAIL until T044 (Recreate Collection) completes

def test_payload_indexes_created():
    """Verify all payload indexes exist (FR-006)"""
    collection_info = qdrant_client.get_collection("nomad_bms_documents")
    indexed_fields = [idx.field_name for idx in collection_info.config.params.index]
    assert "document_id" in indexed_fields
    assert "metadata.file_name" in indexed_fields
    assert "quality.overall_score" in indexed_fields
    # EXPECTED: FAIL until T044 completes
```

**Test: Backup Integrity** (`tests/migration/test_backup_restore.py`):
```python
def test_backup_snapshot_created():
    """Verify snapshot backup exists (FR-001)"""
    snapshot_path = Path("/workspace/backups/qdrant-768d-backup-*.snapshot")
    assert list(snapshot_path.parent.glob(snapshot_path.name)), "No backup snapshot found"
    # EXPECTED: FAIL until T043 (Backup) completes

def test_backup_restoration_preserves_data():
    """Verify backup can be restored with data integrity (FR-002)"""
    original_count = qdrant_client.get_collection("nomad_bms_documents").points_count
    # Create test collection
    qdrant_client.create_collection("test_restore", ...)
    # Restore snapshot
    restore_snapshot("test_restore", "/workspace/backups/qdrant-768d-backup-*.snapshot")
    restored_count = qdrant_client.get_collection("test_restore").points_count
    assert restored_count == original_count, "Point count mismatch after restore"
    # EXPECTED: FAIL until T043a (Validate Backup) completes
```

**Test: Search Quality** (`tests/migration/test_search_quality.py`):
```python
def test_retrieval_accuracy_meets_threshold():
    """Verify retrieval accuracy ≥95% after migration (FR-010)"""
    validation_report = run_retrieval_evaluation()
    assert validation_report.accuracy >= 0.95, f"Accuracy {validation_report.accuracy} below 95%"
    # EXPECTED: FAIL until T046 (Validate Search Quality) completes

def test_search_latency_meets_sla():
    """Verify p95 latency ≤100ms after migration (FR-010)"""
    latencies = benchmark_search_queries(iterations=100)
    p95_latency = np.percentile(latencies, 95)
    assert p95_latency <= 100, f"p95 latency {p95_latency}ms exceeds 100ms"
    # EXPECTED: FAIL until T046 completes
```

**Output**: Failing contract tests in `tests/migration/` (TDD approach)

### 4. Integration Test Scenarios

**From User Story (spec.md line 79-90)**: Admin migration workflow

**Integration Test** (`tests/migration/test_migration_orchestrator.py`):
```python
def test_end_to_end_migration_workflow():
    """End-to-end migration from 768-d to 4096-d (User Story)"""
    # Acceptance Scenario 1: Backup created
    job = MigrationOrchestrator.start_migration()
    assert job.status == "backup"
    assert Path(job.backup_snapshot_path).exists()

    # Acceptance Scenario 2: Backup validated
    job = MigrationOrchestrator.wait_for_status(job.job_id, "recreate", timeout=300)
    assert job.backup_integrity_validated == True

    # Acceptance Scenario 3: Collection recreated with 4096-d
    job = MigrationOrchestrator.wait_for_status(job.job_id, "reprocess", timeout=300)
    collection = qdrant_client.get_collection("nomad_bms_documents")
    assert collection.config.params.vectors["chunk_embedding"].size == 4096

    # Acceptance Scenario 4: Documents reprocessed with late chunking
    job = MigrationOrchestrator.wait_for_status(job.job_id, "validate", timeout=900)
    assert job.documents_processed >= 2400  # Allow 10% quality filtering
    sample_point = qdrant_client.retrieve("nomad_bms_documents", ids=[random_id])[0]
    assert sample_point.payload["metadata"]["chunking_strategy"] == "LATE_CHUNKING"

    # Acceptance Scenario 5: Search quality validated
    job = MigrationOrchestrator.wait_for_status(job.job_id, "monitoring", timeout=300)
    assert job.validation_results["retrieval_accuracy"] >= 0.95

    # Acceptance Scenario 6: Search latency meets SLA
    assert job.validation_results["p95_latency_ms"] <= 100

    # EXPECTED: FAIL until full migration pipeline (T043-T048) completes
```

**Output**: Integration test scenarios in `tests/migration/`

### 5. Quickstart Guide

**Output**: quickstart.md with step-by-step migration execution guide

---

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **Load base template**: `.specify/templates/tasks-template.md`

2. **Generate backup & preparation tasks** (from FR-001 to FR-004):
   - T001: Validate Qwen3 embedding model availability [P]
   - T002: Generate baseline performance metrics (768-d) [P]
   - T003: Validate disk space ≥5 GB available
   - T004: Create Qdrant snapshot backup
   - T005: Validate backup integrity (restore to test collection)

3. **Generate collection recreation tasks** (from FR-005 to FR-006):
   - T006: Delete existing collection
   - T007: Recreate collection with 4096-d schema (depends: T005)
   - T008: Verify collection schema and indexes

4. **Generate document reprocessing tasks** (from FR-007 to FR-009):
   - T009: Batch reprocess documents with late chunking (depends: T008)
   - T010: Verify chunking_strategy metadata in sample points
   - T011: Validate quality score distribution (mean ≥70.0)

5. **Generate validation tasks** (from FR-010 to FR-012):
   - T012: Run retrieval accuracy evaluation (depends: T011)
   - T013: Compare against baseline (T002 results)
   - T014: Validate BMS API embeddings endpoint returns 4096-d
   - T015: Execute end-to-end search tests (semantic, hybrid, metadata)

6. **Generate monitoring & rollback tasks** (from FR-013 to FR-015):
   - T016: Restart BMS API with Qwen3 configuration (depends: T015)
   - T017: Test rollback procedure (dry-run before migration)
   - T018: Monitor performance for 24 hours (depends: T016)
   - T019: Generate migration documentation (depends: T018)

7. **Generate contract test tasks** (from Phase 1 contracts):
   - T020: Contract test - Qdrant collection schema [P]
   - T021: Contract test - Backup restore integrity [P]
   - T022: Contract test - Search quality validation [P]
   - T023: Contract test - BMS API embeddings endpoint [P]

8. **Generate documentation tasks** (from FR-015):
   - T024: Update CLAUDE.md with Qwen3 model details
   - T025: Create MIGRATION_LOG.md with before/after metrics
   - T026: Update performance baselines
   - T027: Create TROUBLESHOOTING_4096D.md guide

**Ordering Strategy**:
- **Preparation phase first**: T001-T005 (backup before destructive ops)
- **Validation gates**: T005 before T007, T011 before T012, T015 before T016
- **Parallel execution** [P]: T001+T002 (independent), T020-T023 (contract tests run in parallel)
- **Sequential critical path**: T007 → T009 → T012 → T013 → T016 (collection lifecycle)
- **TDD order**: Contract tests (T020-T023) before implementation tasks

**Dependency Examples**:
- T007 (Recreate Collection) depends on T005 (Validate Backup) - safety gate
- T012 (Run Evaluation) depends on T011 (Validate Quality) - data dependency
- T016 (Restart API) depends on T015 (End-to-end Tests) - validation gate
- T019 (Documentation) depends on T018 (24h Monitoring) - completion gate

**Estimated Output**: 27 numbered, ordered tasks in tasks.md with [P] markers for parallelizable tasks

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

---

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute T001-T027 following TDD workflow)
**Phase 5**: Validation (run full test suite, execute quickstart.md, 24h monitoring period)

**Implementation Notes for Phase 4**:
- Use existing `scripts/init_qdrant.py` as base for T007 (already updated for 4096-d schema in Phase 3.7 of feature 002)
- Use existing `scripts/batch_process_incoming.py` for T009 (already supports late chunking)
- Use existing `scripts/evaluate_retrieval_enhanced.py` for T012 (already implements retrieval accuracy validation)
- Create new `scripts/migrate_qdrant_collection.py` as orchestrator for end-to-end workflow

**Validation Criteria for Phase 5**:
- All contract tests pass (T020-T023)
- All integration tests pass (end-to-end migration workflow)
- Retrieval accuracy ≥95% (FR-010)
- p95 latency ≤100ms (FR-010)
- 24h monitoring shows no rollback triggers (FR-013)
- Documentation updated (FR-015)

---

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**No Violations Requiring Justification**

This feature extends existing infrastructure without introducing complexity violations:
- Uses existing BMS Agent Python project (no new project)
- Uses existing Qdrant vector database (schema upgrade only)
- Uses existing processor wrapper and enhanced document processor (already updated for Qwen3)
- Migration is one-time operation (no ongoing complexity)
- TDD approach with comprehensive tests maintains quality standards

---

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - All clarifications resolved in spec
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts, quickstart.md generated
- [x] Phase 2: Task planning approach documented (/plan command)
- [ ] Phase 3: Tasks generated (/tasks command - next step)
- [ ] Phase 4: Implementation complete (T001-T027 execution)
- [ ] Phase 5: Validation passed (24h monitoring, all tests pass)

**Gate Status**:
- [x] Initial Constitution Check: PASS (no violations, POC exceptions documented)
- [x] Post-Design Constitution Check: PASS (no new violations after Phase 1)
- [x] All NEEDS CLARIFICATION resolved (all technical unknowns clarified in spec Session 2025-10-17)
- [x] Complexity deviations documented (none - extends existing infrastructure)

**Next Command**: `/tasks` to generate tasks.md from this plan

---

*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
*Spec: `/workspace/specs/004-migrate-qdrant-collection/spec.md` (272 lines, 15 requirements)*
*Plan generated: 2025-10-17 by /plan command*
