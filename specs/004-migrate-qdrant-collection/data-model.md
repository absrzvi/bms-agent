# Data Model: Qdrant Collection Migration

**Feature**: 004-migrate-qdrant-collection
**Generated**: 2025-10-17 (Phase 1 of /plan command)

## Overview

This document defines the data entities and their relationships for the Qdrant collection migration from 768-d to 4096-d embeddings. These entities support migration orchestration, backup management, validation reporting, and rollback capabilities.

---

## Core Entities

### MigrationJob

**Purpose**: Tracks the execution state and progress of a collection migration

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| job_id | UUID | Yes | Must be unique | Unique identifier for migration job |
| start_time | datetime | Yes | Must be < end_time | Migration start timestamp (ISO 8601) |
| end_time | datetime | No | Must be > start_time | Migration completion timestamp (null if in progress) |
| status | enum | Yes | One of: backup, recreate, reprocess, validate, monitoring, complete, rollback, failed | Current migration phase |
| source_dimension | int | Yes | Must be 768 | Original embedding dimension |
| target_dimension | int | Yes | Must be 4096 | Target embedding dimension |
| backup_snapshot_path | str | Yes | File must exist | Absolute path to snapshot backup |
| documents_processed | int | Yes | ≥ 0 | Number of documents successfully reprocessed |
| documents_failed | int | Yes | ≥ 0 | Number of documents that failed processing |
| validation_results | JSON | No | Must match ValidationReport schema | Search quality validation metrics |
| rollback_reason | str | No | Max 500 chars | Reason for rollback (if status=rollback) |

**State Transitions**:
```
pending → backup → recreate → reprocess → validate → monitoring → complete
                                               ↓
                                           rollback/failed
```

**Business Rules**:
- Job cannot transition to `recreate` until backup is validated (backup_integrity_validated=true in BackupSnapshot)
- Job cannot transition to `monitoring` until validation_results.validation_status = 'pass'
- Job automatically transitions to `rollback` if any validation threshold fails (accuracy <90%, p95 >200ms, etc.)
- documents_processed + documents_failed should equal total documents (~420 source files)

---

### QdrantCollection

**Purpose**: Represents vector database collection metadata and configuration

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| collection_name | str | Yes | Must be "nomad_bms_documents" | Collection identifier |
| vector_dimension | int | Yes | Must be 768 or 4096 | Embedding vector size |
| distance_metric | enum | Yes | Must be "Cosine" | Similarity metric |
| points_count | int | Yes | ≥ 0 | Number of points (document chunks) |
| indexed_vectors_count | int | Yes | ≥ 0 | Number of indexed vectors |
| status | enum | Yes | One of: active, migrating, rollback | Collection operational status |
| created_at | datetime | Yes | ISO 8601 | Collection creation timestamp |
| config | JSON | Yes | Must match Qdrant schema | Full collection configuration (vectors, sparse_vectors, payload_schema, indexes) |

**Relationships**:
- Contains many DocumentChunks (via Qdrant points)
- Backed up by one BackupSnapshot

**Business Rules**:
- status='migrating' during migration job execution (backup → monitoring phases)
- status='rollback' during rollback procedure
- status='active' before migration and after successful completion
- indexed_vectors_count may be 0 immediately after recreation (indexing happens asynchronously)

---

### BackupSnapshot

**Purpose**: Disaster recovery snapshot of Qdrant collection before migration

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| snapshot_id | UUID | Yes | Must be unique | Unique snapshot identifier |
| collection_name | str | Yes | Must match QdrantCollection.collection_name | Source collection name |
| created_at | datetime | Yes | ISO 8601 | Snapshot creation timestamp |
| file_path | str | Yes | File must exist, must be in /workspace/backups/ | Absolute path to .snapshot file |
| file_size_mb | float | Yes | > 0 | Snapshot file size in megabytes |
| point_count | int | Yes | Must match collection.points_count | Number of points in snapshot |
| integrity_validated | bool | Yes | Default false | Whether restore test passed |
| restoration_time_seconds | float | No | > 0 | Time taken to restore (measured during validation) |

**Relationships**:
- Backs up one QdrantCollection

**Business Rules**:
- integrity_validated must be true before migration proceeds to `recreate` phase
- Snapshot file naming convention: `qdrant-768d-backup-YYYYMMDD-HHMMSS.snapshot`
- Retention: Snapshots kept for 30 days after successful migration (manual cleanup)
- Restoration test creates temporary collection `nomad_bms_documents_test_restore`

---

### ValidationReport

**Purpose**: Search quality and performance validation results

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| report_id | UUID | Yes | Must be unique | Unique report identifier |
| migration_job_id | UUID | Yes | Must reference existing MigrationJob | Parent migration job |
| baseline_metrics | JSON | Yes | Must contain: accuracy, p50, p95, p99, quality_scores | Pre-migration metrics (768-d) |
| current_metrics | JSON | Yes | Must have same keys as baseline_metrics | Post-migration metrics (4096-d) |
| comparison_delta | JSON | Yes | Percent changes for each metric | Difference between current and baseline |
| validation_status | enum | Yes | One of: pass, fail, warning | Overall validation result |
| generated_at | datetime | Yes | ISO 8601 | Report generation timestamp |
| recommendations | list[str] | No | Max 10 items | Actionable recommendations if fail/warning |

**Relationships**:
- Belongs to one MigrationJob

**Business Rules**:
- validation_status = 'pass' if: accuracy ≥95%, p95 ≤100ms, no critical regressions (accuracy drop <5%)
- validation_status = 'fail' if: accuracy <90%, p95 >200ms for >1 hour, or critical errors
- validation_status = 'warning' if: between pass/fail thresholds (e.g., 90% ≤ accuracy < 95%)
- comparison_delta calculated as: ((current - baseline) / baseline) * 100

**Baseline Metrics Schema**:
```json
{
  "accuracy": 0.96,          // Retrieval accuracy (0-1)
  "p50": 42.5,               // Median latency (ms)
  "p95": 85.0,               // 95th percentile latency (ms)
  "p99": 120.0,              // 99th percentile latency (ms)
  "quality_scores": {
    "mean": 78.3,
    "median": 82.0,
    "std_dev": 12.1
  }
}
```

---

### EmbeddingModel

**Purpose**: AI model metadata and availability tracking

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| model_name | str | Yes | Must exist in Ollama | Full model identifier (e.g., "dengcao/Qwen3-Embedding-8B:F16") |
| model_provider | enum | Yes | One of: Ollama, OpenAI | Hosting provider |
| vector_dimension | int | Yes | > 0 | Output embedding dimension |
| model_size_gb | float | Yes | > 0 | Model storage size in gigabytes |
| availability_status | enum | Yes | One of: available, unavailable | Current availability |
| last_health_check | datetime | Yes | ISO 8601 | Last health check timestamp |
| performance_metrics | JSON | No | Must contain embeddings_per_second, p95_latency_ms | Model performance stats |

**Relationships**:
- Used by DocumentChunks (via processor_wrapper.py)

**Business Rules**:
- availability_status checked before migration starts (FR-004)
- Health check performed via test embedding (single query, verify 4096-d output)
- Performance metrics updated during document reprocessing phase

**Performance Metrics Schema**:
```json
{
  "embeddings_per_second": 15.2,  // Throughput (batch_size=32)
  "p95_latency_ms": 320.0,         // 95th percentile batch latency
  "gpu_utilization_percent": 85.0, // GPU usage during generation
  "memory_usage_gb": 14.5          // Peak GPU memory
}
```

---

## Entity Relationships Diagram

```
MigrationJob (1) ────── (1) ValidationReport
     │
     │ creates
     ├───────────────> (1) BackupSnapshot
     │
     │ recreates
     └───────────────> (1) QdrantCollection
                              │
                              │ contains
                              └──> (many) DocumentChunks
                                        │
                                        │ uses
                                        └──> (1) EmbeddingModel
```

---

## Storage Locations

| Entity | Storage | Format | TTL/Retention |
|--------|---------|--------|---------------|
| MigrationJob | In-memory (Python object) | Dataclass | Session lifetime |
| QdrantCollection | Qdrant metadata API | JSON (via HTTP API) | Persistent |
| BackupSnapshot | Filesystem: `/workspace/backups/` | .snapshot file | 30 days post-migration |
| ValidationReport | Filesystem: `/workspace/backups/` | JSON file | 30 days post-migration |
| EmbeddingModel | Ollama API | N/A (model binary in `/workspace/data/ollama_models/`) | Persistent |

---

## Data Flow During Migration

1. **Backup Phase**:
   - Create MigrationJob (status='backup')
   - Create BackupSnapshot from QdrantCollection
   - Validate BackupSnapshot (integrity_validated=true)

2. **Recreate Phase**:
   - Update MigrationJob (status='recreate')
   - Delete old QdrantCollection
   - Create new QdrantCollection (vector_dimension=4096)

3. **Reprocess Phase**:
   - Update MigrationJob (status='reprocess')
   - Use EmbeddingModel to generate 4096-d embeddings
   - Populate QdrantCollection with new embeddings
   - Update MigrationJob (documents_processed, documents_failed)

4. **Validate Phase**:
   - Update MigrationJob (status='validate')
   - Create ValidationReport comparing baseline vs current
   - Update MigrationJob (validation_results)

5. **Monitoring Phase**:
   - Update MigrationJob (status='monitoring')
   - Track QdrantCollection performance over 24 hours
   - Trigger rollback if thresholds violated

6. **Complete Phase**:
   - Update MigrationJob (status='complete', end_time)
   - QdrantCollection (status='active')
   - Archive ValidationReport and BackupSnapshot

---

## Validation Rules Summary

**MigrationJob**:
- ✓ job_id is unique UUID v4
- ✓ start_time < end_time (if end_time not null)
- ✓ documents_processed ≥ 0 and documents_failed ≥ 0
- ✓ status transitions follow state machine (no skipping phases)

**BackupSnapshot**:
- ✓ file_path exists on filesystem
- ✓ file_size_mb matches actual file size (±1 MB tolerance)
- ✓ point_count matches source collection (exact match required)

**ValidationReport**:
- ✓ baseline_metrics and current_metrics have identical keys
- ✓ validation_status='pass' requires accuracy ≥0.95 AND p95 ≤100
- ✓ comparison_delta calculated correctly ((current-baseline)/baseline*100)

**EmbeddingModel**:
- ✓ model_name matches `ollama list` output
- ✓ vector_dimension matches actual model output (test embedding verification)
- ✓ availability_status updated within last 5 minutes before migration

---

*Generated from spec.md requirements (FR-001 to FR-015, NFR-001 to NFR-010)*
*Entity relationships derived from migration workflow (spec.md lines 79-90)*
