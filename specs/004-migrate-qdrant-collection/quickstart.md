# Quickstart: Qdrant Collection Migration Execution

**Feature**: 004-migrate-qdrant-collection
**Generated**: 2025-10-17 (Phase 1 of /plan command)
**Estimated Time**: ~30 minutes active work + 24 hours monitoring

## Prerequisites

Before starting the migration, verify the following:

```bash
# 1. Check current Qdrant collection status
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result | {points_count, vectors_count}'
# Expected: points_count ~2615, vectors with size 768

# 2. Verify Qwen3 embedding model is available
ollama list | grep "dengcao/Qwen3-Embedding-8B"
# Expected: dengcao/Qwen3-Embedding-8B:F16  15 GB

# 3. Check available disk space
df -h /workspace/qdrant_storage | awk 'NR==2 {print $4}'
# Expected: ≥5 GB available

# 4. Verify source documents exist
find /workspace/bms_data -type f \( -name "*.pdf" -o -name "*.xlsx" -o -name "*.docx" \) | wc -l
# Expected: ~420 files

# 5. Confirm BMS API venv is activated
source /workspace/bms-api-venv/bin/activate
python --version
# Expected: Python 3.11+
```

---

## Step-by-Step Execution

### Phase 1: Preparation & Backup (5-10 minutes)

**Step 1.1: Generate Baseline Metrics** (runs in parallel with backup)

```bash
cd /workspace/001-bms-agent

# Run retrieval accuracy evaluation on current 768-d collection
python scripts/evaluate_retrieval_enhanced.py \
  --collection nomad_bms_documents \
  --output /workspace/backups/baseline-768d-results.json

# Verify baseline file was created
cat /workspace/backups/baseline-768d-results.json | jq '.retrieval_accuracy, .p95_latency_ms'
# Expected: accuracy ~0.96, p95 ~85ms
```

**Step 1.2: Create Snapshot Backup**

```bash
# Create Qdrant snapshot
curl -X POST http://localhost:6333/collections/nomad_bms_documents/snapshots

# Wait for snapshot creation (check logs)
tail -f /workspace/logs/qdrant.log | grep -i "snapshot created"

# Copy snapshot to backups directory with timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
cp /workspace/qdrant_storage/snapshots/nomad_bms_documents-*.snapshot \
   /workspace/backups/qdrant-768d-backup-${TIMESTAMP}.snapshot

# Document current collection stats
curl http://localhost:6333/collections/nomad_bms_documents > \
   /workspace/backups/collection-768d-stats.json

# Verify backup file size
ls -lh /workspace/backups/qdrant-768d-backup-*.snapshot
# Expected: ~600-800 MB
```

**Step 1.3: Validate Backup Integrity**

```bash
# Create temporary test collection for restore validation
curl -X POST http://localhost:6333/collections/nomad_bms_documents_test_restore \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "chunk_embedding": {"size": 768, "distance": "Cosine"}
    }
  }'

# Restore snapshot to test collection (use most recent backup)
BACKUP_FILE=$(ls -t /workspace/backups/qdrant-768d-backup-*.snapshot | head -1)
curl -X POST http://localhost:6333/collections/nomad_bms_documents_test_restore/snapshots/upload \
  -F "snapshot=@${BACKUP_FILE}"

# Verify restored point count matches original
ORIGINAL_COUNT=$(jq '.result.points_count' /workspace/backups/collection-768d-stats.json)
RESTORED_COUNT=$(curl -s http://localhost:6333/collections/nomad_bms_documents_test_restore | jq '.result.points_count')

if [ "$ORIGINAL_COUNT" -eq "$RESTORED_COUNT" ]; then
  echo "✓ Backup validation PASSED: ${RESTORED_COUNT} points restored"
else
  echo "✗ Backup validation FAILED: Expected ${ORIGINAL_COUNT}, got ${RESTORED_COUNT}"
  exit 1
fi

# Delete test collection
curl -X DELETE http://localhost:6333/collections/nomad_bms_documents_test_restore
```

---

### Phase 2: Collection Recreation (2 minutes)

**Step 2.1: Delete Existing Collection**

```bash
# ⚠️ DESTRUCTIVE OPERATION - Ensure backup is validated first!
curl -X DELETE http://localhost:6333/collections/nomad_bms_documents

# Verify deletion
curl http://localhost:6333/collections/nomad_bms_documents
# Expected: {"status": {"error": "Not found: Collection `nomad_bms_documents` doesn't exist!"}}
```

**Step 2.2: Recreate Collection with 4096-d Schema**

```bash
cd /workspace/001-bms-agent

# Run init script with force recreate flag
python scripts/init_qdrant.py --force-recreate

# Verify collection schema
curl http://localhost:6333/collections/nomad_bms_documents | \
  jq '.result.config.params.vectors'
# Expected output:
# {
#   "chunk_embedding": {"size": 4096, "distance": "Cosine"},
#   "parent_embedding": {"size": 4096, "distance": "Cosine"},
#   "child_embedding": {"size": 4096, "distance": "Cosine"},
#   "full_doc_embedding": {"size": 4096, "distance": "Cosine"}
# }

# Verify payload indexes
curl http://localhost:6333/collections/nomad_bms_documents | \
  jq '.result.config.params.payload_index | keys'
# Expected: ["document_id", "chunk_key", "metadata.file_name", "metadata.hierarchy", "quality.overall_score"]
```

---

### Phase 3: Document Reprocessing (10-15 minutes)

**Step 3.1: Batch Reprocess All Documents**

```bash
cd /workspace/001-bms-agent
source /workspace/bms-api-venv/bin/activate

# Run batch processor with late chunking
python scripts/batch_process_incoming.py \
  --input-dir /workspace/bms_data \
  --force-reprocess \
  --batch-size 32 \
  --log-level INFO

# Monitor processing logs in separate terminal
tail -f /workspace/logs/batch_process.log | grep -E "(processed|failed|quality_score)"

# Wait for completion (typically 10-15 minutes for 420 documents)
# Expected output: "Processing complete: 420/420 documents processed successfully"
```

**Step 3.2: Verify Late Chunking Applied**

```bash
# Check that processed chunks have late chunking metadata
curl http://localhost:6333/collections/nomad_bms_documents/points/scroll \
  -H 'Content-Type: application/json' \
  -d '{"limit": 10, "with_payload": true}' | \
  jq '.result.points[].payload.metadata.chunking_strategy'

# Expected: All 10 samples should output "LATE_CHUNKING"

# Verify total points count (allow ±10% variance due to quality filtering)
curl http://localhost:6333/collections/nomad_bms_documents | \
  jq '.result.points_count'
# Expected: 2,350-2,750 points (target: ~2,615)
```

**Step 3.3: Validate Quality Score Distribution**

```bash
# Query quality scores from sample of points
curl http://localhost:6333/collections/nomad_bms_documents/points/scroll \
  -H 'Content-Type: application/json' \
  -d '{"limit": 100, "with_payload": true}' | \
  jq '.result.points[].payload.quality.overall_score' | \
  python -c "import sys; scores = [float(x) for x in sys.stdin]; print(f'Mean: {sum(scores)/len(scores):.2f}, Min: {min(scores):.2f}, Max: {max(scores):.2f}')"

# Expected: Mean ≥70.0, Min ≥50.0 (quality filter threshold)
```

---

### Phase 4: Validation (5 minutes)

**Step 4.1: Run Retrieval Accuracy Evaluation**

```bash
cd /workspace/001-bms-agent

# Run evaluation on new 4096-d collection
python scripts/evaluate_retrieval_enhanced.py \
  --collection nomad_bms_documents \
  --output /workspace/backups/qwen3-4096d-evaluation.json

# Compare against baseline
python scripts/compare_evaluation_results.py \
  --baseline /workspace/backups/baseline-768d-results.json \
  --current /workspace/backups/qwen3-4096d-evaluation.json \
  --output /workspace/backups/migration-comparison-report.md

# Review comparison report
cat /workspace/backups/migration-comparison-report.md

# Verify success criteria:
# - Retrieval accuracy ≥95% ✓
# - p95 latency ≤100ms ✓
# - No critical regressions (accuracy drop <5%) ✓
```

**Step 4.2: Validate BMS API Embeddings Endpoint**

```bash
# Test embeddings endpoint returns 4096-d vectors
curl -X POST http://localhost:8000/api/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"query": "test query"}' | \
  jq '.embedding | length'

# Expected: 4096 (not 768)

# Verify model name
curl -X POST http://localhost:8000/api/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"query": "test"}' | \
  jq '.model'

# Expected: "dengcao/Qwen3-Embedding-8B:F16"
```

**Step 4.3: Execute End-to-End Search Tests**

```bash
# Test semantic search
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What are the emergency brake procedures for Class 395 trains?",
    "limit": 5,
    "min_score": 0.7
  }' | jq '.results | length'
# Expected: ≥3 results

# Test hybrid search
curl -X POST http://localhost:8000/api/v1/search/hybrid \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "BMS-NET-VLAN-042 emergency systems",
    "limit": 5
  }' | jq '.results | length'
# Expected: ≥3 results

# Verify response times
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H 'Content-Type: application/json' \
  -d '{"query": "railway safety", "limit": 5}' \
  -w "\nTime: %{time_total}s\n" | tail -1
# Expected: <3s (end-to-end including BMS API processing)
```

---

### Phase 5: Monitoring & Finalization (24 hours)

**Step 5.1: Restart BMS API**

```bash
cd /workspace/001-bms-agent

# Restart BMS API to reload Qdrant client
./scripts/manage_services.sh restart bms-api

# Verify health check
curl http://localhost:8000/health/detailed | jq '.components'
# Expected: All components (Redis, BMS API, Ollama, Qdrant) status="ok"
```

**Step 5.2: Monitor Performance (24 hours)**

```bash
# Set up continuous monitoring (run in tmux/screen session)
watch -n 3600 'curl http://localhost:6333/metrics && df -h /workspace/qdrant_storage'

# Track search latency (parse API logs every hour)
while true; do
  grep "search_semantic\|search_hybrid" /workspace/logs/api.log | \
    tail -1000 | \
    jq -r '.response_time_ms' | \
    python -c "import sys, statistics; times = [float(x) for x in sys.stdin]; print(f'p50: {statistics.median(times):.1f}ms, p95: {statistics.quantiles(times, n=20)[18]:.1f}ms')"
  sleep 3600
done

# Monitor for rollback triggers:
# - Retrieval accuracy <90%
# - p95 latency >200ms for >1 hour
# - ≥5 user reports of irrelevant results
# - Qdrant crashes or OOM errors
```

**Step 5.3: Generate Migration Documentation**

```bash
cd /workspace/001-bms-agent

# Update CLAUDE.md (line ~30)
sed -i 's/sentence-transformers\/all-mpnet-base-v2/dengcao\/Qwen3-Embedding-8B:F16/g' CLAUDE.md
sed -i 's/768-dimensional embeddings/4096-dimensional embeddings/g' CLAUDE.md

# Create migration log
cat > /workspace/001-bms-agent/docs/MIGRATION_LOG.md <<EOF
# Qdrant Migration Log: 768-d → 4096-d Embeddings

**Date**: $(date +%Y-%m-%d)
**Migration**: sentence-transformers/all-mpnet-base-v2 (768-d) → Qwen3-Embedding-8B:F16 (4096-d)
**Strategy**: Blue-green deployment with late chunking

## Pre-Migration Stats
$(cat /workspace/backups/baseline-768d-results.json | jq .)

## Post-Migration Stats
$(cat /workspace/backups/qwen3-4096d-evaluation.json | jq .)

## Issues Encountered
- None (migration completed successfully)

## Rollback Events
- None (no rollback triggered)
EOF

# Update performance baselines
cat > /workspace/001-bms-agent/docs/performance-baseline.json <<EOF
{
  "version": "2.0",
  "embedding_model": "dengcao/Qwen3-Embedding-8B:F16",
  "vector_dimensions": 4096,
  "chunking_strategy": "LATE_CHUNKING",
  "p50_search_latency_ms": $(jq '.p50_latency_ms' /workspace/backups/qwen3-4096d-evaluation.json),
  "p95_search_latency_ms": $(jq '.p95_latency_ms' /workspace/backups/qwen3-4096d-evaluation.json),
  "retrieval_accuracy_percent": $(jq '.retrieval_accuracy * 100' /workspace/backups/qwen3-4096d-evaluation.json),
  "quality_score_mean": $(jq '.quality_scores.mean' /workspace/backups/qwen3-4096d-evaluation.json),
  "last_updated": "$(date -I)"
}
EOF

echo "✓ Migration documentation complete"
```

---

## Rollback Procedure (if needed)

**Only execute if validation fails or critical issues occur within 24h monitoring**

```bash
# Step 1: Stop BMS API
./scripts/manage_services.sh stop bms-api

# Step 2: Delete new 4096-d collection
curl -X DELETE http://localhost:6333/collections/nomad_bms_documents

# Step 3: Restore 768-d collection from backup
BACKUP_FILE=$(ls -t /workspace/backups/qdrant-768d-backup-*.snapshot | head -1)
curl -X POST http://localhost:6333/collections/nomad_bms_documents/snapshots/upload \
  -F "snapshot=@${BACKUP_FILE}"

# Step 4: Verify restored collection
curl http://localhost:6333/collections/nomad_bms_documents | \
  jq '.result | {points_count, vectors: .config.params.vectors.chunk_embedding.size}'
# Expected: points_count ~2615, vector size 768

# Step 5: Restart BMS API
./scripts/manage_services.sh restart bms-api

# Step 6: Validate restored functionality
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H 'Content-Type: application/json' \
  -d '{"query": "test", "limit": 1}'

echo "✓ Rollback complete - system restored to 768-d embeddings"
```

---

## Success Criteria Checklist

After 24-hour monitoring period, verify:

- [ ] Retrieval accuracy ≥95% (compare to baseline)
- [ ] p95 search latency ≤100ms (Qdrant queries only)
- [ ] Quality score distribution: mean ≥70.0, median ≥75.0
- [ ] No memory leaks (Qdrant RSS memory stable)
- [ ] Disk usage growth <10% over 24 hours
- [ ] Zero user complaints about search quality
- [ ] All search endpoints operational (semantic, hybrid, metadata)
- [ ] Documentation updated (CLAUDE.md, MIGRATION_LOG.md, performance baselines)

**If all criteria met**: Migration successful ✓ - Delete backup snapshot after 30 days

**If any criteria fail**: Trigger rollback procedure immediately

---

## Troubleshooting

**Issue: "Embedding model unavailable"**
```bash
# Verify Ollama is running
curl http://localhost:11434/api/version
# Restart Ollama if needed
./scripts/manage_services.sh restart ollama
```

**Issue: "Disk space insufficient"**
```bash
# Check available space
df -h /workspace/qdrant_storage
# Clean up old logs/backups
find /workspace/backups -name "*.snapshot" -mtime +30 -delete
```

**Issue: "Batch processing timeout"**
```bash
# Reduce batch size in batch_process_incoming.py
python scripts/batch_process_incoming.py --batch-size 16  # Instead of 32
```

**Issue: "Quality scores below 70.0"**
```bash
# Check RAGAS configuration
grep "min_quality" /workspace/001-bms-agent/api/processor_wrapper.py
# Review failed chunks
curl http://localhost:6333/collections/nomad_bms_documents_low_quality/points/scroll
```

---

*Generated from plan.md Phase 1 design*
*Execution time: ~30 minutes active + 24h monitoring*
*Prerequisites: Qwen3 model installed, 5+ GB disk space, backup validated*
