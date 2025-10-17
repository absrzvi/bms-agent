# Tasks: Qdrant Collection Migration to 4096-Dimensional Embeddings

**Branch**: `004-migrate-qdrant-collection`
**Generated**: 2025-10-17 (Phase 2 of /tasks command)
**Total Tasks**: 27
**Estimated Effort**: ~30 minutes active work + 24 hours monitoring

## Task Execution Order

### Phase 1: Preparation & Backup (T001-T005)
**Duration**: 5-10 minutes | **Parallel**: T001 + T002

### Phase 2: Collection Recreation (T006-T008)
**Duration**: 2 minutes | **Sequential** (destructive operations)

### Phase 3: Document Reprocessing (T009-T011)
**Duration**: 10-15 minutes | **Sequential** (data dependencies)

### Phase 4: Validation (T012-T015)
**Duration**: 5 minutes | **Sequential** (validation gates)

### Phase 5: Monitoring & Rollback (T016-T019)
**Duration**: 2 minutes + 24 hours monitoring | **Sequential**

### Phase 6: Contract Tests (T020-T023)
**Duration**: 5 minutes | **Parallel** (independent test files)

### Phase 7: Documentation (T024-T027)
**Duration**: 1 hour | **Parallel** (independent files)

---

## Tasks

### T001: Validate Qwen3 Embedding Model Availability [P]

**Prerequisites**: None (can run in parallel with T002)

**Description**: Verify that the Qwen3-Embedding-8B:F16 model is available in Ollama and returns 4096-dimensional embeddings.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/validate_embedding_model.py` (NEW)

**Implementation**:
1. Check Ollama service is running (`curl http://localhost:11434/api/version`)
2. Query Ollama for model list (`ollama list | grep Qwen3`)
3. Generate test embedding with model
4. Verify output is 4096-dimensional array
5. Log model performance metrics (embeddings/sec, latency)

**Acceptance Criteria**:
- Model `dengcao/Qwen3-Embedding-8B:F16` exists in Ollama
- Test embedding returns array of length 4096
- Ollama service responds within 5 seconds
- Script exits with code 0 on success, 1 on failure

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/validate_embedding_model.py --model dengcao/Qwen3-Embedding-8B:F16
```

**References**: FR-004, plan.md Phase 0 (Embedding Model Decision)

---

### T002: Generate Baseline Performance Metrics (768-d) [P]

**Prerequisites**: None (can run in parallel with T001)

**Description**: Run retrieval accuracy evaluation on current 768-d collection to establish baseline for comparison after migration.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/evaluate_retrieval_enhanced.py` (EXISTING)
- Output: `/workspace/backups/baseline-768d-results.json` (NEW)

**Implementation**:
1. Run evaluation script on `nomad_bms_documents` collection
2. Execute 50-query test set (10 per category: code, procedural, conceptual, metadata, edge cases)
3. Calculate retrieval accuracy, p50/p95/p99 latency, quality score distribution
4. Save results to JSON file

**Acceptance Criteria**:
- Baseline file created at `/workspace/backups/baseline-768d-results.json`
- File contains: `retrieval_accuracy`, `p50_latency_ms`, `p95_latency_ms`, `p99_latency_ms`, `quality_scores` (mean, median, std)
- Retrieval accuracy ≥0.90 (sanity check on current system)
- p95 latency ≤200ms (current system performance)

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/evaluate_retrieval_enhanced.py \
  --collection nomad_bms_documents \
  --output /workspace/backups/baseline-768d-results.json
```

**References**: FR-003, FR-010, quickstart.md Step 1.1

---

### T003: Validate Disk Space ≥5 GB Available

**Prerequisites**: None

**Description**: Check that sufficient disk space is available in `/workspace/qdrant_storage` for the 4096-d collection (estimated 3-4 GB).

**Files**:
- Script: `/workspace/001-bms-agent/scripts/validate_disk_space.py` (NEW)

**Implementation**:
1. Check available space in `/workspace/qdrant_storage` using `shutil.disk_usage()`
2. Verify available space ≥5 GB (5,000,000,000 bytes)
3. Log current usage and available space
4. Abort migration if insufficient space

**Acceptance Criteria**:
- Script checks disk space correctly
- Exits with code 0 if ≥5 GB available, code 1 otherwise
- Logs clear error message: "Insufficient disk space: X GB available, 5 GB required"

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/validate_disk_space.py --path /workspace/qdrant_storage --min-gb 5
```

**References**: NFR-006, research.md (Disk Space Management)

---

### T004: Create Qdrant Snapshot Backup

**Prerequisites**: T003 (disk space validated)

**Description**: Create a snapshot backup of the existing 768-d collection before any destructive operations.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/backup_qdrant_snapshot.py` (NEW)
- Output: `/workspace/backups/qdrant-768d-backup-YYYYMMDD-HHMMSS.snapshot` (NEW)

**Implementation**:
1. Call Qdrant Snapshot API: `POST http://localhost:6333/collections/nomad_bms_documents/snapshots`
2. Wait for snapshot creation (poll status or watch logs)
3. Copy snapshot file from `/workspace/qdrant_storage/snapshots/` to `/workspace/backups/` with timestamp
4. Document current collection stats (save to `/workspace/backups/collection-768d-stats.json`)
5. Log snapshot file size and point count

**Acceptance Criteria**:
- Snapshot file created: `/workspace/backups/qdrant-768d-backup-YYYYMMDD-HHMMSS.snapshot`
- File size ~600-800 MB (768-d vectors)
- Collection stats JSON exported with `points_count` ~2,615
- Snapshot creation completes within 5 minutes

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/backup_qdrant_snapshot.py \
  --collection nomad_bms_documents \
  --output-dir /workspace/backups
```

**References**: FR-001, quickstart.md Step 1.2

---

### T005: Validate Backup Integrity (Restore to Test Collection)

**Prerequisites**: T004 (backup created)

**Description**: Validate that the snapshot backup can be restored correctly by creating a temporary test collection and verifying data integrity.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/validate_backup_integrity.py` (NEW)

**Implementation**:
1. Create temporary collection `nomad_bms_documents_test_restore` with 768-d schema
2. Restore most recent backup snapshot to test collection
3. Verify restored point count matches original collection (from collection-768d-stats.json)
4. Spot-check 10 random points for data integrity (embeddings present, metadata valid)
5. Measure restoration time (for RTO calculation)
6. Delete temporary test collection

**Acceptance Criteria**:
- Test collection created and restored successfully
- Restored point count equals original collection point count (exact match)
- Spot-check confirms data integrity (10/10 points valid)
- Restoration time documented (expected: <2 min for 2,615 points)
- Test collection deleted cleanly
- Script sets `integrity_validated=true` flag

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/validate_backup_integrity.py \
  --backup-file /workspace/backups/qdrant-768d-backup-*.snapshot \
  --stats-file /workspace/backups/collection-768d-stats.json
```

**References**: FR-002, data-model.md (BackupSnapshot entity)

---

### T006: Delete Existing Collection

**Prerequisites**: T005 (backup validated)

**Description**: Delete the existing 768-d collection to make way for the new 4096-d collection.

**Files**:
- Script: Inline cURL command (no separate script needed)

**Implementation**:
1. Verify backup integrity flag is set (check T005 output)
2. Delete collection via Qdrant API: `DELETE http://localhost:6333/collections/nomad_bms_documents`
3. Verify deletion (GET request returns 404)
4. Log deletion timestamp

**Acceptance Criteria**:
- Collection `nomad_bms_documents` deleted successfully
- GET request to collection returns 404 error
- Operation completes within 30 seconds

**Test Command**:
```bash
curl -X DELETE http://localhost:6333/collections/nomad_bms_documents
curl http://localhost:6333/collections/nomad_bms_documents  # Should return 404
```

**References**: FR-005, quickstart.md Step 2.1

**⚠️ WARNING**: This is a destructive operation. Ensure T005 passed before proceeding.

---

### T007: Recreate Collection with 4096-d Schema

**Prerequisites**: T006 (old collection deleted)

**Description**: Create a new Qdrant collection with 4096-dimensional vector configuration for all four vector types.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/init_qdrant.py` (EXISTING - already updated for 4096-d)
- Contract: `/workspace/specs/004-migrate-qdrant-collection/contracts/qdrant-collection-schema.yaml`

**Implementation**:
1. Run init script with `--force-recreate` flag
2. Create collection with 4096-d vectors (chunk, parent, child, full_doc)
3. Configure sparse vectors for keyword search
4. Create payload indexes (document_id, chunk_key, metadata fields, quality score)
5. Verify collection status is green

**Acceptance Criteria**:
- Collection `nomad_bms_documents` created with 4096-d schema
- All 4 vector types configured: chunk_embedding (4096), parent_embedding (4096), child_embedding (4096), full_doc_embedding (4096)
- Sparse vectors configured: keyword_sparse (idf modifier)
- Payload indexes created for: document_id, chunk_key, metadata.file_name, metadata.hierarchy, quality.overall_score
- Collection status: green, points_count: 0 (ready for data)

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/init_qdrant.py --force-recreate

# Verify schema
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.config.params.vectors'
```

**References**: FR-005, FR-006, contracts/qdrant-collection-schema.yaml

---

### T008: Verify Collection Schema and Indexes

**Prerequisites**: T007 (collection recreated)

**Description**: Verify that the new collection schema matches the contract specification and all indexes are created.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/verify_collection_schema.py` (NEW)
- Contract: `/workspace/specs/004-migrate-qdrant-collection/contracts/qdrant-collection-schema.yaml`

**Implementation**:
1. Query Qdrant for collection info
2. Verify vector dimensions (4096 for all 4 types)
3. Verify distance metric (Cosine for all)
4. Verify payload indexes exist for all required fields
5. Verify sparse vector configuration
6. Compare against contract schema

**Acceptance Criteria**:
- All vector types have size: 4096
- All vector types have distance: Cosine
- Payload indexes created: 5 total (document_id, chunk_key, metadata.file_name, metadata.hierarchy, quality.overall_score)
- Sparse vectors configured: keyword_sparse
- Schema matches contracts/qdrant-collection-schema.yaml exactly

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/verify_collection_schema.py \
  --collection nomad_bms_documents \
  --contract /workspace/specs/004-migrate-qdrant-collection/contracts/qdrant-collection-schema.yaml
```

**References**: FR-005, FR-006, T020 (contract test)

---

### T009: Batch Reprocess Documents with Late Chunking

**Prerequisites**: T008 (collection schema verified)

**Description**: Reprocess all source documents from `/workspace/bms_data/` using late chunking strategy and Qwen3 embeddings.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/batch_process_incoming.py` (EXISTING)
- Processor: `/workspace/001-bms-agent/api/processor_wrapper.py` (EXISTING - already updated for Qwen3)
- Enhanced Processor: `/workspace/001-bms-agent/bms-agent/src/enhanced_document_processor.py` (EXISTING - supports late chunking)

**Implementation**:
1. Count source documents in `/workspace/bms_data/` (expect ~420 files)
2. Run batch processor with `--force-reprocess` and `--batch-size 32`
3. Process documents with late chunking (ChunkingStrategy.LATE_CHUNKING)
4. Generate 4096-d embeddings via Qwen3 model
5. Apply RAGAS quality validation (filter chunks with score <50.0)
6. Upload chunks to `nomad_bms_documents` collection
7. Monitor processing logs for errors

**Acceptance Criteria**:
- All documents processed (expected: 420/420 success, warnings acceptable for minor issues)
- Qdrant collection shows ≥2,400 points (allowing for ~10% quality filtering)
- Processing logs show `late_chunking_applied=True` for all documents (spot-check 10 random log entries)
- Quality score distribution: mean ≥70.0
- Processing completes within 15 minutes (NFR-004)

**Test Command**:
```bash
cd /workspace/001-bms-agent
source /workspace/bms-api-venv/bin/activate
python scripts/batch_process_incoming.py \
  --input-dir /workspace/bms_data \
  --force-reprocess \
  --batch-size 32 \
  --log-level INFO

# Monitor progress
tail -f /workspace/logs/batch_process.log | grep -E "(processed|failed|quality_score)"
```

**References**: FR-007, FR-008, FR-009, quickstart.md Step 3.1

---

### T010: Verify Chunking Strategy Metadata in Sample Points

**Prerequisites**: T009 (documents reprocessed)

**Description**: Verify that processed chunks have `metadata.chunking_strategy` set to "LATE_CHUNKING".

**Files**:
- Script: Inline cURL + jq command (or add to verification script)

**Implementation**:
1. Query Qdrant for 10 random points with payload
2. Extract `metadata.chunking_strategy` from each point
3. Verify all 10 samples have value "LATE_CHUNKING"
4. Log any deviations

**Acceptance Criteria**:
- All 10 sampled points have `metadata.chunking_strategy = "LATE_CHUNKING"`
- No points with missing or incorrect chunking_strategy metadata
- Verification completes within 10 seconds

**Test Command**:
```bash
curl http://localhost:6333/collections/nomad_bms_documents/points/scroll \
  -H 'Content-Type: application/json' \
  -d '{"limit": 10, "with_payload": true}' | \
  jq '.result.points[].payload.metadata.chunking_strategy' | sort | uniq -c
# Expected output: 10 "LATE_CHUNKING"
```

**References**: FR-008, contracts/qdrant-collection-schema.yaml (validation section)

---

### T011: Validate Quality Score Distribution (Mean ≥70.0)

**Prerequisites**: T010 (chunking verified)

**Description**: Validate that the quality score distribution meets the target threshold (mean ≥70.0).

**Files**:
- Script: `/workspace/001-bms-agent/scripts/validate_quality_scores.py` (NEW)

**Implementation**:
1. Query Qdrant for 100 random points with quality payload
2. Extract `quality.overall_score` from each point
3. Calculate mean, median, std deviation
4. Verify mean ≥70.0, median ≥75.0
5. Identify any outliers (score <50.0 should be in low_quality collection)

**Acceptance Criteria**:
- Quality score mean ≥70.0
- Quality score median ≥75.0
- Minimum score ≥50.0 (quality filter threshold)
- No points with score <50.0 in main collection

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/validate_quality_scores.py \
  --collection nomad_bms_documents \
  --sample-size 100 \
  --min-mean 70.0
```

**References**: FR-009, research.md (RAGAS Quality Scoring)

---

### T012: Run Retrieval Accuracy Evaluation

**Prerequisites**: T011 (quality validated)

**Description**: Run search quality evaluation on the new 4096-d collection using the same 50-query test set from baseline.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/evaluate_retrieval_enhanced.py` (EXISTING)
- Output: `/workspace/backups/qwen3-4096d-evaluation.json` (NEW)

**Implementation**:
1. Run evaluation script on `nomad_bms_documents` collection (4096-d)
2. Use same 50-query test set as baseline (T002)
3. Calculate retrieval accuracy, p50/p95/p99 latency, quality score distribution
4. Save results to JSON file

**Acceptance Criteria**:
- Evaluation completes successfully
- Output file created: `/workspace/backups/qwen3-4096d-evaluation.json`
- File contains: `retrieval_accuracy`, `p50_latency_ms`, `p95_latency_ms`, `p99_latency_ms`, `quality_scores`
- Evaluation uses same test queries as baseline (T002)

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/evaluate_retrieval_enhanced.py \
  --collection nomad_bms_documents \
  --output /workspace/backups/qwen3-4096d-evaluation.json
```

**References**: FR-010, quickstart.md Step 4.1

---

### T013: Compare Against Baseline (T002 Results)

**Prerequisites**: T012 (evaluation complete)

**Description**: Compare post-migration metrics against baseline to verify success criteria (accuracy ≥95%, p95 ≤100ms, no critical regressions).

**Files**:
- Script: `/workspace/001-bms-agent/scripts/compare_evaluation_results.py` (NEW)
- Input: `/workspace/backups/baseline-768d-results.json` (from T002)
- Input: `/workspace/backups/qwen3-4096d-evaluation.json` (from T012)
- Output: `/workspace/backups/migration-comparison-report.md` (NEW)

**Implementation**:
1. Load baseline and current evaluation results
2. Calculate delta for each metric (accuracy, latency percentiles, quality scores)
3. Check success criteria:
   - Retrieval accuracy ≥95%
   - p95 latency ≤100ms
   - No critical regressions (accuracy drop <5%)
4. Generate comparison report with side-by-side metrics
5. Flag validation status: PASS/FAIL/WARNING

**Acceptance Criteria**:
- Comparison report generated: `/workspace/backups/migration-comparison-report.md`
- Report includes side-by-side comparison table of all metrics
- Validation status clearly indicated (PASS if accuracy ≥95% AND p95 ≤100ms)
- Delta calculations correct ((current - baseline) / baseline * 100)

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/compare_evaluation_results.py \
  --baseline /workspace/backups/baseline-768d-results.json \
  --current /workspace/backups/qwen3-4096d-evaluation.json \
  --output /workspace/backups/migration-comparison-report.md
```

**References**: FR-010, data-model.md (ValidationReport entity)

---

### T014: Validate BMS API Embeddings Endpoint Returns 4096-d

**Prerequisites**: T013 (comparison complete)

**Description**: Verify that the BMS API `/api/v1/embeddings` endpoint returns 4096-dimensional vectors after migration.

**Files**:
- Test: `/workspace/001-bms-agent/tests/migration/test_embeddings_endpoint.py` (NEW)

**Implementation**:
1. Send test query to `/api/v1/embeddings` endpoint
2. Verify response contains `embedding` array of length 4096
3. Verify response contains `model: "dengcao/Qwen3-Embedding-8B:F16"`
4. Verify response contains `dimension: 4096`
5. Test error handling (query too long, empty query)

**Acceptance Criteria**:
- Embeddings endpoint returns 4096-dimensional vectors (not 768)
- Model name in response: "dengcao/Qwen3-Embedding-8B:F16"
- Dimension field in response: 4096
- Error handling works correctly (400 for invalid queries)

**Test Command**:
```bash
curl -X POST http://localhost:8000/api/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"query": "test query"}' | jq '{length: (.embedding | length), model, dimension}'
# Expected: {length: 4096, model: "dengcao/Qwen3-Embedding-8B:F16", dimension: 4096}
```

**References**: FR-011, contracts/migration-job-status.yaml (BMS API contract)

---

### T015: Execute End-to-End Search Tests (Semantic, Hybrid, Metadata)

**Prerequisites**: T014 (embeddings endpoint validated)

**Description**: Execute comprehensive end-to-end search tests for all search types to verify functionality after migration.

**Files**:
- Test: `/workspace/001-bms-agent/tests/migration/test_search_quality.py` (NEW or EXTEND existing)

**Implementation**:
1. Test semantic search with 10 representative queries
2. Test hybrid search with 10 queries (including document codes)
3. Test metadata search with 5 queries (author, date, version filters)
4. Verify non-empty results for all queries (≥3 results per query)
5. Verify response times (≤3s end-to-end, per FR-003)
6. Verify citations include source documents

**Acceptance Criteria**:
- All search types return relevant results (non-empty, ≥3 results per query)
- Response time ≤3s for end-to-end queries (measured via API)
- Citations include source documents with correct formatting
- No empty or error responses
- Semantic similarity scores reasonable (≥0.7 for relevant results)

**Test Command**:
```bash
cd /workspace/001-bms-agent
pytest tests/migration/test_search_quality.py -v

# Or manual test
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H 'Content-Type: application/json' \
  -d '{"query": "railway safety procedures", "limit": 5}' | jq '.results | length'
# Expected: ≥3 results
```

**References**: FR-012, quickstart.md Step 4.3

---

### T016: Restart BMS API with Qwen3 Configuration

**Prerequisites**: T015 (end-to-end tests pass)

**Description**: Restart the BMS API to reload the Qdrant client and confirm health checks pass.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/manage_services.sh` (EXISTING)

**Implementation**:
1. Restart BMS API via service management script
2. Wait for service to start (check logs)
3. Verify health check endpoint responds
4. Verify all components (Redis, BMS API, Ollama, Qdrant) report status="ok"

**Acceptance Criteria**:
- BMS API restarts successfully within 30 seconds
- Health check returns status="ok" for all components
- No connection errors to Qdrant in logs
- API responds within 500ms for health check

**Test Command**:
```bash
cd /workspace/001-bms-agent
./scripts/manage_services.sh restart bms-api

# Verify health
curl http://localhost:8000/health/detailed | jq '.components'
# Expected: All components have status="ok"
```

**References**: FR-011, quickstart.md Step 5.1

---

### T017: Test Rollback Procedure (Dry-Run Before Migration)

**Prerequisites**: T005 (backup validated) - Run BEFORE T006 (deletion)

**Description**: Test the rollback procedure to ensure it works correctly in case migration needs to be reversed.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/test_rollback.py` (NEW)

**Implementation**:
1. Create test collection `nomad_bms_documents_rollback_test`
2. Restore 768-d snapshot to test collection
3. Verify restored point count matches original
4. Measure snapshot restoration time (document for RTO)
5. Test BMS API connection to restored collection (use test environment variable)
6. Delete test collection

**Acceptance Criteria**:
- Snapshot restores successfully to test collection
- Restoration time documented (expected: <2 min for 2,615 points)
- Restored collection has correct schema (768-d vectors)
- BMS API can query restored collection (in test mode)
- Rollback procedure documented in `/workspace/backups/rollback-procedure.md`

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/test_rollback.py \
  --backup-file /workspace/backups/qdrant-768d-backup-*.snapshot \
  --test-collection nomad_bms_documents_rollback_test
```

**References**: FR-014, NFR-003, quickstart.md (Rollback Procedure section)

---

### T018: Monitor Performance for 24 Hours

**Prerequisites**: T016 (BMS API restarted)

**Description**: Monitor search latency, memory usage, disk I/O, and user feedback continuously for 24 hours post-migration.

**Files**:
- Script: `/workspace/001-bms-agent/scripts/monitor_migration_performance.py` (NEW)
- Output: `/workspace/backups/24h-monitoring-report.json` (NEW)

**Implementation**:
1. Set up continuous monitoring (run in background/tmux)
2. Track search latency (p50/p95/p99) every hour via API logs
3. Monitor Qdrant memory usage and disk I/O every hour
4. Monitor for rollback triggers:
   - Retrieval accuracy <90%
   - p95 latency >200ms for >1 hour
   - ≥5 user reports of irrelevant results
   - Qdrant crashes or OOM errors
   - BMS API error rate >5%
5. Generate hourly status reports
6. Generate final 24h report with aggregated metrics

**Acceptance Criteria**:
- Monitoring runs continuously for 24 hours without interruption
- p95 latency ≤100ms maintained over 24h
- No memory leaks (Qdrant RSS memory stable or decreasing)
- No disk space issues (storage growth <10% over 24h)
- User satisfaction maintained (zero complaints about search quality)
- AI agent response time ≤30s for 95% of queries (if Slack bot active)
- Final report generated: `/workspace/backups/24h-monitoring-report.json`

**Test Command**:
```bash
cd /workspace/001-bms-agent
python scripts/monitor_migration_performance.py \
  --duration-hours 24 \
  --output /workspace/backups/24h-monitoring-report.json \
  --rollback-on-failure

# Or manual monitoring
watch -n 3600 'curl http://localhost:6333/metrics && df -h /workspace/qdrant_storage'
```

**References**: FR-013, quickstart.md Step 5.2

---

### T019: Generate Migration Documentation

**Prerequisites**: T018 (24h monitoring complete)

**Description**: Update project documentation with migration details, before/after metrics, and troubleshooting guidance.

**Files**:
- Update: `/workspace/001-bms-agent/CLAUDE.md` (EXISTING)
- Create: `/workspace/001-bms-agent/docs/MIGRATION_LOG.md` (NEW)
- Update: `/workspace/001-bms-agent/docs/performance-baseline.json` (EXISTING)
- Create: `/workspace/001-bms-agent/docs/TROUBLESHOOTING_4096D.md` (NEW)

**Implementation**:
1. Update CLAUDE.md (replace references to 768-d with 4096-d, sentence-transformers with Qwen3)
2. Create MIGRATION_LOG.md with:
   - Migration date and strategy
   - Pre-migration stats (from T002 baseline)
   - Post-migration stats (from T012 evaluation)
   - Issues encountered (from monitoring logs)
   - Rollback events (if any)
3. Update performance-baseline.json with new metrics
4. Create TROUBLESHOOTING_4096D.md with common issues and solutions

**Acceptance Criteria**:
- All 4 documentation files created/updated
- CLAUDE.md references correct embedding model (no mentions of 768-d or sentence-transformers)
- Migration log includes complete before/after comparison
- Performance baselines match T012 evaluation results
- Troubleshooting guide covers at least 5 common issues

**Test Command**:
```bash
cd /workspace/001-bms-agent

# Verify CLAUDE.md updates
grep -i "qwen3\|4096" CLAUDE.md

# Verify all docs created
ls -la docs/MIGRATION_LOG.md docs/TROUBLESHOOTING_4096D.md docs/performance-baseline.json
```

**References**: FR-015, quickstart.md Step 5.3

---

### T020: Contract Test - Qdrant Collection Schema [P]

**Prerequisites**: T007 (collection recreated) - Can run in parallel with T021-T023

**Description**: Verify that the recreated Qdrant collection schema matches the contract specification.

**Files**:
- Test: `/workspace/001-bms-agent/tests/migration/test_collection_schema.py` (NEW)
- Contract: `/workspace/specs/004-migrate-qdrant-collection/contracts/qdrant-collection-schema.yaml`

**Implementation**:
1. Test: `test_recreated_collection_has_4096d_vectors()`
   - Query collection config
   - Assert all 4 vector types have size=4096
2. Test: `test_payload_indexes_created()`
   - Query collection config
   - Assert all required indexes exist (document_id, chunk_key, metadata fields, quality score)
3. Test: `test_distance_metric_is_cosine()`
   - Verify all vectors use Cosine distance
4. Test: `test_sparse_vectors_configured()`
   - Verify keyword_sparse exists with idf modifier

**Acceptance Criteria**:
- All tests pass (4/4)
- Tests use pytest framework
- Tests fail before T007 (TDD), pass after T007
- Clear assertion messages on failure

**Test Command**:
```bash
cd /workspace/001-bms-agent
pytest tests/migration/test_collection_schema.py -v
```

**References**: FR-005, FR-006, contracts/qdrant-collection-schema.yaml

---

### T021: Contract Test - Backup Restore Integrity [P]

**Prerequisites**: T004 (backup created) - Can run in parallel with T020, T022-T023

**Description**: Verify that backup snapshot can be created and restored with data integrity.

**Files**:
- Test: `/workspace/001-bms-agent/tests/migration/test_backup_restore.py` (NEW)

**Implementation**:
1. Test: `test_backup_snapshot_created()`
   - Assert snapshot file exists in `/workspace/backups/`
   - Assert file size >0
2. Test: `test_backup_restoration_preserves_data()`
   - Create test collection
   - Restore snapshot
   - Assert point count matches original
   - Spot-check data integrity (10 points)
   - Delete test collection
3. Test: `test_backup_metadata_correct()`
   - Assert collection stats JSON exported
   - Verify points_count field present

**Acceptance Criteria**:
- All tests pass (3/3)
- Tests fail before T004/T005 (TDD), pass after T005
- Test collection cleaned up after restore test

**Test Command**:
```bash
cd /workspace/001-bms-agent
pytest tests/migration/test_backup_restore.py -v
```

**References**: FR-001, FR-002, data-model.md (BackupSnapshot entity)

---

### T022: Contract Test - Search Quality Validation [P]

**Prerequisites**: T012 (evaluation complete) - Can run in parallel with T020-T021, T023

**Description**: Verify that retrieval accuracy and search latency meet success criteria after migration.

**Files**:
- Test: `/workspace/001-bms-agent/tests/migration/test_search_quality.py` (NEW or EXTEND existing)

**Implementation**:
1. Test: `test_retrieval_accuracy_meets_threshold()`
   - Run evaluation script
   - Assert accuracy ≥0.95
2. Test: `test_search_latency_meets_sla()`
   - Benchmark 100 search queries
   - Calculate p95 latency
   - Assert p95 ≤100ms
3. Test: `test_no_critical_regressions()`
   - Compare against baseline
   - Assert accuracy drop <5%
4. Test: `test_quality_scores_acceptable()`
   - Query sample of quality scores
   - Assert mean ≥70.0

**Acceptance Criteria**:
- All tests pass (4/4)
- Tests fail before T012/T013 (TDD), pass after T013
- Clear failure messages indicating which threshold violated

**Test Command**:
```bash
cd /workspace/001-bms-agent
pytest tests/migration/test_search_quality.py -v
```

**References**: FR-010, data-model.md (ValidationReport entity)

---

### T023: Contract Test - BMS API Embeddings Endpoint [P]

**Prerequisites**: T007 (collection recreated) - Can run in parallel with T020-T022

**Description**: Verify that BMS API embeddings endpoint returns correct 4096-d vectors after migration.

**Files**:
- Test: `/workspace/001-bms-agent/tests/migration/test_embeddings_endpoint.py` (NEW)

**Implementation**:
1. Test: `test_embeddings_dimension_is_4096()`
   - POST to `/api/v1/embeddings` with test query
   - Assert embedding array length = 4096
2. Test: `test_embeddings_model_is_qwen3()`
   - Assert response contains model = "dengcao/Qwen3-Embedding-8B:F16"
3. Test: `test_embeddings_error_handling()`
   - Test query too long (>1000 chars) → 400 error
   - Test empty query → 400 error
   - Test Ollama unavailable → 503 error (mock)

**Acceptance Criteria**:
- All tests pass (3/3)
- Tests fail before T007 (TDD), pass after T007
- Error handling tests use mocks to simulate failures

**Test Command**:
```bash
cd /workspace/001-bms-agent
pytest tests/migration/test_embeddings_endpoint.py -v
```

**References**: FR-011, contracts/migration-job-status.yaml (BMS API section)

---

### T024: Update CLAUDE.md with Qwen3 Model Details [P]

**Prerequisites**: T018 (24h monitoring complete) - Can run in parallel with T025-T027

**Description**: Update CLAUDE.md to reflect the new Qwen3 embedding model and 4096-d vectors.

**Files**:
- Update: `/workspace/001-bms-agent/CLAUDE.md` (EXISTING)

**Implementation**:
1. Find all references to "sentence-transformers/all-mpnet-base-v2" and replace with "dengcao/Qwen3-Embedding-8B:F16"
2. Find all references to "768-dimensional" or "768-d" and replace with "4096-dimensional" or "4096-d"
3. Update "Current Status" section with post-migration stats (from T012 evaluation)
4. Add note about late chunking in document processing section
5. Update performance targets if needed (based on T018 monitoring results)

**Acceptance Criteria**:
- No mentions of "sentence-transformers" or "768" remain (except in historical context)
- All references to embedding model now show "Qwen3-Embedding-8B:F16"
- Current Status section updated with latest stats (point count, quality scores)
- Late chunking noted in document processing description

**Test Command**:
```bash
cd /workspace/001-bms-agent

# Verify no old references remain
grep -i "sentence-transformers\|768-d\|768 dimensional" CLAUDE.md
# Expected: No results (or only in historical/rollback context)

# Verify new references present
grep -i "qwen3\|4096-d\|4096 dimensional" CLAUDE.md
# Expected: Multiple matches
```

**References**: FR-015, plan.md Phase 1 (Documentation tasks)

---

### T025: Create MIGRATION_LOG.md with Before/After Metrics [P]

**Prerequisites**: T018 (24h monitoring complete) - Can run in parallel with T024, T026-T027

**Description**: Create a comprehensive migration log documenting the entire migration process with metrics.

**Files**:
- Create: `/workspace/001-bms-agent/docs/MIGRATION_LOG.md` (NEW)

**Implementation**:
1. Document migration metadata (date, strategy, models)
2. Include pre-migration stats from `/workspace/backups/baseline-768d-results.json` (T002)
3. Include post-migration stats from `/workspace/backups/qwen3-4096d-evaluation.json` (T012)
4. Document issues encountered during T009 (reprocessing errors, quality filtering stats)
5. Document rollback events (if any occurred during T018 monitoring)
6. Include comparison report from T013
7. Add conclusion (success/rollback) with final metrics

**Acceptance Criteria**:
- Migration log created with all required sections
- Before/after comparison table included
- All metric changes documented (accuracy, latency, quality scores, point count)
- Issues section lists any errors from processing logs
- Rollback section indicates "None" if successful, or details if rollback occurred
- File is well-formatted Markdown

**Test Command**:
```bash
cd /workspace/001-bms-agent

# Verify file created
ls -la docs/MIGRATION_LOG.md

# Verify content completeness
grep -E "Pre-Migration|Post-Migration|Issues|Rollback" docs/MIGRATION_LOG.md
```

**References**: FR-015, data-model.md (MigrationJob, ValidationReport)

---

### T026: Update Performance Baselines [P]

**Prerequisites**: T018 (24h monitoring complete) - Can run in parallel with T024-T025, T027

**Description**: Update the performance baseline JSON file with new metrics from the 4096-d collection.

**Files**:
- Update: `/workspace/001-bms-agent/docs/performance-baseline.json` (EXISTING)

**Implementation**:
1. Load evaluation results from `/workspace/backups/qwen3-4096d-evaluation.json` (T012)
2. Update JSON with new values:
   - version: "2.0"
   - embedding_model: "dengcao/Qwen3-Embedding-8B:F16"
   - vector_dimensions: 4096
   - chunking_strategy: "LATE_CHUNKING"
   - p50_search_latency_ms: <from evaluation>
   - p95_search_latency_ms: <from evaluation>
   - retrieval_accuracy_percent: <from evaluation * 100>
   - quality_score_mean: <from evaluation>
   - last_updated: <current date>
3. Validate JSON syntax

**Acceptance Criteria**:
- JSON file updated with all new metrics
- File is valid JSON (can be parsed without errors)
- Values match T012 evaluation results exactly
- version incremented to "2.0"
- last_updated shows current date (YYYY-MM-DD)

**Test Command**:
```bash
cd /workspace/001-bms-agent

# Validate JSON syntax
cat docs/performance-baseline.json | jq .

# Verify key fields updated
jq '{embedding_model, vector_dimensions, p95_search_latency_ms}' docs/performance-baseline.json
```

**References**: FR-015, plan.md Phase 1 (Documentation tasks)

---

### T027: Create TROUBLESHOOTING_4096D.md Guide [P]

**Prerequisites**: T018 (24h monitoring complete) - Can run in parallel with T024-T026

**Description**: Create a troubleshooting guide specific to 4096-d embeddings covering common issues and solutions.

**Files**:
- Create: `/workspace/001-bms-agent/docs/TROUBLESHOOTING_4096D.md` (NEW)

**Implementation**:
1. Document at least 5 common issues:
   - Issue 1: "Embedding model unavailable" → Solution: Restart Ollama, verify model installed
   - Issue 2: "Disk space insufficient" → Solution: Check available space, clean old backups
   - Issue 3: "Batch processing timeout" → Solution: Reduce batch size from 32 to 16
   - Issue 4: "Quality scores below 70.0" → Solution: Check RAGAS config, review failed chunks
   - Issue 5: "p95 latency exceeds 100ms" → Solution: Optimize Qdrant index, check GPU utilization
2. Include diagnostic commands for each issue
3. Add references to relevant sections in CLAUDE.md and quickstart.md
4. Include rollback procedure reference

**Acceptance Criteria**:
- Troubleshooting guide created with ≥5 issues
- Each issue has clear symptom description, diagnosis steps, and solution
- Diagnostic commands included for each issue
- Rollback procedure referenced
- File is well-formatted Markdown with table of contents

**Test Command**:
```bash
cd /workspace/001-bms-agent

# Verify file created
ls -la docs/TROUBLESHOOTING_4096D.md

# Verify content coverage
grep -i "issue\|symptom\|solution" docs/TROUBLESHOOTING_4096D.md | wc -l
# Expected: ≥15 lines (5 issues × 3 sections each)
```

**References**: FR-015, quickstart.md (Troubleshooting section)

---

## Parallel Execution Examples

### Example 1: Phase 1 Preparation (T001 + T002)
```bash
# Both tasks can run concurrently since they're independent
# Terminal 1:
cd /workspace/001-bms-agent && python scripts/validate_embedding_model.py --model dengcao/Qwen3-Embedding-8B:F16

# Terminal 2:
cd /workspace/001-bms-agent && python scripts/evaluate_retrieval_enhanced.py --collection nomad_bms_documents --output /workspace/backups/baseline-768d-results.json
```

### Example 2: Phase 6 Contract Tests (T020-T023)
```bash
# All 4 contract tests can run in parallel
cd /workspace/001-bms-agent
pytest tests/migration/test_collection_schema.py tests/migration/test_backup_restore.py tests/migration/test_search_quality.py tests/migration/test_embeddings_endpoint.py -v -n 4  # Using pytest-xdist for parallel execution
```

### Example 3: Phase 7 Documentation (T024-T027)
```bash
# All 4 documentation tasks can run concurrently (different files)
# Use Task agent or manual execution in separate terminals
```

---

## Dependency Graph

```
T001 [P] ─┐
          ├─> T003 ─> T004 ─> T005 ─┐
T002 [P] ─┘                         ├─> T017 (dry-run rollback)
                                    │
                                    ├─> T006 ─> T007 ─> T008 ─> T009 ─> T010 ─> T011 ─> T012 ─> T013 ─> T014 ─> T015 ─> T016 ─> T018 ─> T019
                                    │
                                    └─> T020 [P] ─┐
                                        T021 [P] ─┤ (Contract tests - run after T007)
                                        T022 [P] ─┤
                                        T023 [P] ─┘

                                        T024 [P] ─┐
                                        T025 [P] ─┤ (Documentation - run after T018)
                                        T026 [P] ─┤
                                        T027 [P] ─┘
```

---

## Validation Gates

| Gate | After Task | Condition | Action if Fail |
|------|------------|-----------|----------------|
| Backup Validated | T005 | integrity_validated=true | Abort migration, fix backup |
| Collection Schema | T008 | Schema matches contract | Fix init script, recreate collection |
| Quality Scores | T011 | Mean ≥70.0 | Review RAGAS config, investigate low scores |
| Search Quality | T013 | Accuracy ≥95%, p95 ≤100ms | Trigger rollback (T017 procedure) |
| End-to-End Tests | T015 | All search types functional | Fix issues, re-test before T016 |
| 24h Monitoring | T018 | No rollback triggers | Trigger rollback if thresholds violated |

---

## Success Criteria Summary

**Migration Complete When**:
- ✅ All 27 tasks completed
- ✅ All contract tests passing (T020-T023)
- ✅ Retrieval accuracy ≥95% (T013)
- ✅ p95 search latency ≤100ms (T013)
- ✅ 24h monitoring stable (T018)
- ✅ Documentation updated (T019)

**Rollback Triggers** (execute rollback procedure from quickstart.md if any occur):
- ❌ Retrieval accuracy <90%
- ❌ p95 latency >200ms for >1 hour
- ❌ ≥5 user reports of irrelevant results
- ❌ Qdrant crashes or OOM errors
- ❌ BMS API error rate >5%

---

*Generated from plan.md Phase 2 strategy*
*27 tasks total: 10 sequential critical path, 9 parallelizable, 8 documentation/tests*
*Estimated active work: ~30 minutes + 24h monitoring*
*Next step: Execute tasks following dependency order, validate at each gate*
