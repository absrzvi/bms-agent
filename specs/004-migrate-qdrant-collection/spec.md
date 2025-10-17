# Feature Specification: Qdrant Collection Migration to 4096-Dimensional Embeddings

**Feature Branch**: `004-migrate-qdrant-collection`
**Created**: 2025-10-17
**Status**: Active (Planning Phase)
**Platform**: BMS Agent - Vector Database Infrastructure
**Input**: User description: "Migrate Qdrant collection from 768-dimensional embeddings to 4096-dimensional embeddings using Qwen3-Embedding-8B:F16 model with late chunking strategy"

## Glossary

- **POC DECISION**: Marker indicating a requirement relaxation or deferral specifically permitted for Proof-of-Concept phase per constitution's POC/MVP Exception Framework. All POC DECISION items must be upgraded to full compliance before production deployment.
- **NFR**: Non-Functional Requirement
- **FR**: Functional Requirement
- **Late Chunking**: Advanced chunking strategy that preserves document structure by creating chunks at semantic boundaries with hierarchical parent-child relationships
- **Blue-Green Deployment**: Zero-downtime deployment strategy where new version is deployed alongside existing version before traffic cutover
- **Vector Embedding**: Numerical representation of text as fixed-size array of floating-point numbers enabling semantic similarity search
- **RAGAS**: Retrieval-Augmented Generation Assessment Score - quality metric for RAG system outputs (faithfulness, relevance, precision)
- **Qwen3-Embedding-8B:F16**: Large embedding model producing 4096-dimensional vectors with superior semantic understanding compared to smaller 768-d models

---

## Execution Flow (main)
```
1. Parse user description from Input
   ’ Feature identified: Qdrant collection migration from 768-d to 4096-d embeddings
2. Extract key concepts from description
   ’ Actors: System administrators, DevOps engineers, end users (indirectly affected)
   ’ Actions: Backup collection, recreate schema, reprocess documents, validate quality, monitor performance
   ’ Data: Document chunks (2,615 points), embeddings (768-d ’ 4096-d), quality scores, metadata
   ’ Constraints: Zero downtime, rollback capability, quality preservation (e95% accuracy), p95 latency d100ms
3. For each unclear aspect:
   ’ Clarified: Disk space requirements, processing time estimates, validation criteria
4. Fill User Scenarios & Testing section
   ’ Primary flow: Admin triggers migration ’ system backs up ’ recreates collection ’ reprocesses documents ’ validates ’ production cutover
5. Generate Functional Requirements
   ’ 15 requirements identified (10 functional + 5 non-functional)
6. Identify Key Entities
   ’ QdrantCollection, DocumentChunk, EmbeddingModel, MigrationJob, ValidationReport
7. Run Review Checklist
   ’ PASS: Technical details abstracted to plan phase
8. Return: SUCCESS (spec ready for planning)
```

---

## =Ë Quick Guidelines
- Focus on WHAT users need and WHY
- Avoid HOW to implement (no tech stack, APIs, code structure)
- Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-17

**Q: What is the acceptable downtime window for this migration?**
’ A: Zero downtime required - use blue-green deployment strategy with backup and rollback capability

**Q: What are the success criteria for validating the migrated collection?**
’ A: (1) Retrieval accuracy e95% compared to baseline, (2) p95 search latency d100ms, (3) Quality score distribution mean e70.0

**Q: How should the system handle rollback if migration fails validation?**
’ A: Restore from snapshot backup created before migration, revert application configuration, validate restored collection functionality

**Q: What disk space is required for the new 4096-d embeddings?**
’ A: Approximately 5x storage increase (from ~600 MB to ~3-4 GB for 2,615 points) - validate available disk space before migration

**Q: How long should the system monitor post-migration performance before declaring success?**
’ A: 24-hour observation period monitoring p95 latency, memory usage, disk I/O, and user feedback

**Q: What happens to documents uploaded during the migration process?**
’ A: **POC DECISION**: Migration occurs during maintenance window when uploads are disabled. Production deployment will require online migration with upload queueing.

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
System administrators need to upgrade the BMS Agent's vector database to use more powerful 4096-dimensional embeddings for better semantic search quality. The migration must preserve all existing documents, maintain search quality, and require zero downtime. If any issues occur, the system must support immediate rollback to the previous 768-dimensional configuration.

**Example interaction:**
- Admin runs migration script: `python scripts/migrate_qdrant_collection.py --execute`
- System creates backup snapshot of existing collection
- System validates backup integrity
- System recreates collection with 4096-d schema
- System reprocesses all 2,615 documents with late chunking
- System validates search quality against baseline
- System monitors performance for 24 hours
- Admin confirms migration success or triggers rollback

### Acceptance Scenarios

1. **Given** a Qdrant collection with 2,615 points using 768-d embeddings, **When** the migration process starts, **Then** the system creates a snapshot backup before any destructive operations

2. **Given** a backup snapshot has been created, **When** the system validates backup integrity, **Then** it creates a temporary test collection, restores the snapshot, verifies point count matches, and confirms data integrity

3. **Given** the backup is validated, **When** the system recreates the collection with 4096-d schema, **Then** all four vector types (chunk, parent, child, full_doc) are configured for 4096 dimensions with cosine distance metric

4. **Given** the new collection schema is created, **When** the system reprocesses documents with late chunking, **Then** all documents are processed successfully with chunking_strategy metadata set to "LATE_CHUNKING"

5. **Given** document reprocessing completes, **When** the system runs search quality validation, **Then** retrieval accuracy is e95% compared to the 768-d baseline

6. **Given** search quality validation passes, **When** the system measures search latency, **Then** p95 latency is d100ms for typical queries

7. **Given** the migrated collection is in use, **When** the system monitors performance over 24 hours, **Then** no memory leaks, disk space issues, or quality degradation occurs

8. **Given** validation fails on any criteria, **When** the admin triggers rollback, **Then** the system restores the 768-d snapshot, reverts configuration, and validates restored functionality within 5 minutes

9. **Given** a migration is in progress, **When** the process encounters errors during document reprocessing, **Then** the system logs errors, continues with remaining documents, and reports processing statistics

10. **Given** migration completes successfully, **When** the system generates documentation, **Then** it updates CLAUDE.md, creates migration log with before/after metrics, and updates performance baselines

### Edge Cases
- **What happens if backup snapshot creation fails?** ’ System aborts migration immediately before any destructive operations, logs error with disk space and permissions details
- **What happens if disk space is insufficient for 4096-d vectors?** ’ System validates available disk space (minimum 5 GB) before starting migration, aborts with clear error message if insufficient
- **What happens if document reprocessing times out?** ’ System continues processing remaining documents, logs timeout errors, and reports partial completion statistics (e.g., "2,500/2,615 documents processed successfully")
- **What happens if embedding model (Qwen3) is unavailable?** ’ System validates model availability before migration, aborts with error "Embedding model dengcao/Qwen3-Embedding-8B:F16 not available in Ollama" if not found
- **What happens if search quality drops below 95% after migration?** ’ System flags as validation failure, admin triggers rollback to restore 768-d collection
- **What happens if the system runs out of memory during embedding generation?** ’ System processes documents in smaller batches (reduce batch_size from 32 to 16), logs memory warnings, and continues with adjusted batch size
- **How does the system handle documents that fail late chunking processing?** ’ System moves failed documents to quarantine directory, logs failure reasons, continues with successful documents, and generates failure report for manual review
- **What happens to scheduled document uploads during migration?** ’ **POC DECISION**: Migration scheduled during maintenance window (off-hours) when uploads are disabled. Production deployment will implement upload queueing with status notifications.

---

## Requirements *(mandatory)*

### Functional Requirements

**Backup & Preparation**
- **FR-001**: System MUST create a snapshot backup of the existing Qdrant collection before any destructive operations
- **FR-002**: System MUST validate backup integrity by creating a temporary test collection, restoring the snapshot, verifying point count matches original, and confirming data integrity before proceeding with migration
- **FR-003**: System MUST generate baseline performance metrics (retrieval accuracy, p50/p95/p99 latency, quality score distribution) from the existing 768-d collection before migration for comparison
- **FR-004**: System MUST validate that the target embedding model (Qwen3-Embedding-8B:F16) is available in Ollama before starting migration

**Collection Recreation**
- **FR-005**: System MUST delete the existing collection and recreate it with 4096-dimensional vector configuration for all four vector types (chunk_embedding, parent_embedding, child_embedding, full_doc_embedding)
- **FR-006**: System MUST create payload indexes on all metadata fields (document_id, chunk_key, file_name, hierarchy, quality score) for optimized query performance

**Document Reprocessing**
- **FR-007**: System MUST reprocess all source documents from persistent storage (/workspace/bms_data/) using late chunking strategy with the Qwen3 embedding model
- **FR-008**: System MUST set metadata.chunking_strategy to "LATE_CHUNKING" for all processed chunks to enable verification
- **FR-009**: System MUST apply RAGAS quality validation during document reprocessing and filter low-quality chunks (quality score <50.0) to a separate collection

**Validation & Testing**
- **FR-010**: System MUST run search quality evaluation comparing migrated collection against baseline using a standardized test query set
  - **Success Criteria**: Retrieval accuracy e95%, p95 latency d100ms, no critical regressions (accuracy drop <5%)
- **FR-011**: System MUST validate that the BMS API embeddings endpoint returns 4096-dimensional vectors (not 768-d) after migration
- **FR-012**: System MUST execute end-to-end tests for all search types (semantic, hybrid, metadata) using representative queries from production logs

**Monitoring & Rollback**
- **FR-013**: System MUST monitor performance metrics (p50/p95/p99 latency, memory usage, disk I/O) continuously for 24 hours post-migration and flag anomalies
  - **Rollback Triggers**: (1) Retrieval accuracy <90%, (2) p95 latency >200ms for >1 hour, (3) e5 user reports of irrelevant results, (4) Qdrant crashes or OOM errors
- **FR-014**: System MUST support rollback to 768-d collection by restoring snapshot backup, reverting BMS API configuration, and validating restored functionality within 5 minutes
- **FR-015**: System MUST update project documentation (CLAUDE.md, migration log, performance baselines, troubleshooting guide) after successful migration with before/after metrics

### Non-Functional Requirements

**Reliability**
- **NFR-001**: Migration process MUST be idempotent - if interrupted, it can be safely restarted without data corruption
- **NFR-002**: System MUST maintain data integrity throughout migration - no document chunks lost or corrupted
- **NFR-003**: Rollback procedure MUST restore full system functionality (search quality, performance, API compatibility) within 5 minutes

**Performance**
- **NFR-004**: Document reprocessing MUST complete within 15 minutes for 2,615 documents (batch size 32, GPU-accelerated embeddings)
- **NFR-005**: Search latency MUST meet production targets after migration - p95 d100ms for Qdrant queries (excluding end-to-end bot response time)
  - **Context**: This is Qdrant query latency only. End-to-end bot response time (FR-003 in Slack bot spec) includes additional processing overhead.
  - **POC DECISION**: Production may require index optimization or hardware upgrades if p95 consistently exceeds 100ms under load

**Storage & Capacity**
- **NFR-006**: System MUST validate minimum 5 GB available disk space in /workspace/qdrant_storage before migration
- **NFR-007**: Migrated collection MUST fit within disk capacity limits (estimated 3-4 GB for 2,615 points with 4096-d vectors)

**Monitoring & Observability**
- **NFR-008**: Migration process MUST log all major steps (backup, validation, recreation, reprocessing, validation, rollback) with timestamps and status
- **NFR-009**: System MUST generate a migration report with before/after comparison (point count, quality scores, retrieval accuracy, latency percentiles)

**Compatibility**
- **NFR-010**: Migrated collection MUST maintain API compatibility - existing BMS API endpoints (/api/v1/search/semantic, /api/v1/search/hybrid) continue working without code changes
- **POC DECISION**: Migration performed during maintenance window to avoid compatibility issues during transition. Production deployment will implement graceful degradation for ongoing requests.

---

## Key Entities *(mandatory)*

- **QdrantCollection**: Represents the vector database collection storing document embeddings
  - Attributes: collection_name, vector_dimension (768 ’ 4096), distance_metric (Cosine), points_count, indexed_vectors_count, status (active/migrating/rollback)
  - Relationships: Contains multiple DocumentChunks

- **DocumentChunk**: Individual chunk of a processed document with embeddings
  - Attributes: chunk_id, document_id, chunk_key (index within document), text_content, chunking_strategy (LATE_CHUNKING), quality_score (RAGAS), metadata (file_name, hierarchy, processing_profile)
  - Relationships: Belongs to one Document, has four Embeddings (chunk, parent, child, full_doc)

- **Embedding**: Vector representation of text in high-dimensional space
  - Attributes: embedding_type (chunk/parent/child/full_doc), vector_dimension (768 or 4096), model_name (sentence-transformers/all-mpnet-base-v2 or dengcao/Qwen3-Embedding-8B:F16), vector_data (array of floats)
  - Relationships: Belongs to one DocumentChunk

- **MigrationJob**: Tracks the progress and status of a collection migration
  - Attributes: job_id, start_time, end_time, status (backup/recreate/reprocess/validate/monitoring/complete/rollback/failed), source_dimension (768), target_dimension (4096), backup_snapshot_path, documents_processed, documents_failed, validation_results
  - Relationships: References one QdrantCollection (source), creates one QdrantCollection (target)

- **ValidationReport**: Results of search quality and performance validation
  - Attributes: report_id, migration_job_id, baseline_metrics (accuracy, p50, p95, p99, quality_scores), current_metrics (accuracy, p50, p95, p99, quality_scores), comparison_delta, validation_status (pass/fail), generated_at
  - Relationships: Belongs to one MigrationJob

- **BackupSnapshot**: Qdrant collection snapshot for disaster recovery
  - Attributes: snapshot_id, collection_name, created_at, file_path, file_size_mb, point_count, integrity_validated (boolean), restoration_time_seconds
  - Relationships: Backs up one QdrantCollection

- **EmbeddingModel**: AI model used for generating vector embeddings
  - Attributes: model_name, model_provider (Ollama/OpenAI), vector_dimension, model_size_gb, availability_status (available/unavailable), last_health_check
  - Relationships: Used by DocumentChunks for embedding generation

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain (all 6 clarifications resolved in Session 2025-10-17)
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (6 clarifications identified)
- [x] User scenarios defined
- [x] Requirements generated (10 functional + 5 non-functional)
- [x] Entities identified (7 core entities)
- [x] Review checklist passed
- [x] All clarifications resolved (Session 2025-10-17: 6 clarifications)

---

## Success Metrics (Migration Phase)

**Migration Performance Metrics:**
- **Backup Creation Time**: <5 minutes for snapshot creation and validation
- **Document Reprocessing Time**: d15 minutes for 2,615 documents (batch size 32)
- **Total Migration Duration**: d30 minutes active work (excluding 24h monitoring period)

**Search Quality Metrics (Post-Migration):**
- **Retrieval Accuracy**: e95% compared to 768-d baseline
- **p95 Search Latency**: d100ms for Qdrant queries
- **Quality Score Distribution**: Mean e70.0, median e75.0
- **False Positive Rate**: No increase compared to baseline

**System Stability Metrics (24h Monitoring):**
- **Memory Stability**: Qdrant RSS memory stable or decreasing (no memory leaks)
- **Disk Usage**: Storage growth <10% over 24 hours
- **Error Rate**: <1% of search queries result in errors
- **Availability**: 100% uptime during monitoring period

**Rollback Capability Metrics:**
- **Rollback Execution Time**: <5 minutes from trigger to restored functionality
- **Data Integrity**: 100% of original 2,615 points restored accurately
- **Functionality Verification**: All search endpoints operational after rollback

**POC DECISION**: Migration performed during scheduled maintenance window (off-hours, no active users) to minimize risk. Production deployment will require online migration strategy with user notifications and graceful degradation for in-flight requests.
