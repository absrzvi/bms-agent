# Full Migration Recommendations - Qwen3 4096-d Embeddings

**Date:** 2025-10-18
**Target:** ~620 documents
**Estimated Time:** 13-15 hours
**Status:** ✅ **READY FOR PRODUCTION** - All validation complete

---

## Pre-Migration Checklist

### 1. Backup Current Collection ✅ CRITICAL

**Before starting migration:**
```bash
# Create Qdrant snapshot
curl -X POST "http://localhost:6333/collections/nomad_bms_documents/snapshots"

# List snapshots
curl "http://localhost:6333/collections/nomad_bms_documents/snapshots"

# Download snapshot
SNAPSHOT_NAME="<snapshot-name-from-list>"
curl "http://localhost:6333/collections/nomad_bms_documents/snapshots/$SNAPSHOT_NAME" \
  --output /workspace/backups/qdrant_nomad_bms_documents_$(date +%Y%m%d_%H%M%S).snapshot
```

**Verify backup:**
```bash
ls -lh /workspace/backups/qdrant_nomad_bms_documents_*.snapshot
```

### 2. Verify Current System State

**Check Qdrant:**
```bash
# Collection status
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result | {points_count, status}'

# Expected: ~1744 points (current 768-d collection)
```

**Check GPU:**
```bash
nvidia-smi

# Expected: GPU available, no out-of-memory errors
```

**Check Disk Space:**
```bash
df -h /workspace

# Expected: >50GB free (for new collection + backups)
```

**Check Document Count:**
```bash
ls /workspace/bms_data/incoming/*.pdf | wc -l

# Expected: ~620 documents
```

### 3. Verify Migration Script

**Check script version:**
```bash
grep "v5.0_qwen3_4096d" /workspace/001-bms-agent/scripts/migrate_to_qwen3_4096d_FIXED.py

# Expected: processing_version in metadata
```

**Verify all fixes present:**
```bash
# Check for chunk key fix
grep 'chunk_data.get("content"' /workspace/001-bms-agent/scripts/migrate_to_qwen3_4096d_FIXED.py

# Check for processor's Qdrant disable
grep 'self.processor.qdrant_client = None' /workspace/001-bms-agent/scripts/migrate_to_qwen3_4096d_FIXED.py

# Check for tensor filtering
grep 'torch.Tensor' /workspace/001-bms-agent/scripts/migrate_to_qwen3_4096d_FIXED.py

# All should return matching lines
```

---

## Migration Execution

### Step 1: Schedule Maintenance Window

**Recommended Window:**
- Duration: 15-16 hours (includes buffer)
- Timing: Overnight/weekend
- Start time: Evening (e.g., 18:00)
- Expected completion: Following morning (e.g., 09:00-10:00)

**User Communication:**
- Notify users 24-48 hours in advance
- BMS search will be unavailable during migration
- Provide estimated completion time

### Step 2: Pre-Migration Setup

**Set up monitoring:**
```bash
# Terminal 1: Migration script (will show progress)
cd /workspace/001-bms-agent
export NLTK_DATA=/workspace/nltk_data
source /workspace/bms-api-venv/bin/activate

# Terminal 2: GPU monitoring
watch -n 60 nvidia-smi

# Terminal 3: Qdrant collection monitoring
watch -n 300 'curl -s http://localhost:6333/collections/nomad_bms_documents | jq ".result.points_count"'
```

**Verify virtual environment:**
```bash
source /workspace/bms-api-venv/bin/activate
python --version  # Should be 3.11+
pip list | grep qdrant-client  # Should be 1.15.1
```

### Step 3: Run Migration

**Command:**
```bash
cd /workspace/001-bms-agent
export NLTK_DATA=/workspace/nltk_data
source /workspace/bms-api-venv/bin/activate

# Use tmux or screen for session persistence
tmux new -s migration

# Run migration with 16-hour timeout
timeout 57600 python scripts/migrate_to_qwen3_4096d_FIXED.py --recreate <<EOF
YES
EOF

# Detach from tmux: Ctrl+B, then D
```

**Progress Monitoring:**
```bash
# Reattach to tmux session
tmux attach -t migration

# Or tail logs
tail -f /workspace/logs/migration_*.log
```

**Expected Output Pattern:**
```
Processing: document_001.pdf
  Generated 15 chunks
  ✓ Completed in 68.3s: 15 high-quality, 0 low-quality, 0 failed uploads

Processing: document_002.pdf
  Generated 22 chunks
  ✓ Completed in 79.1s: 22 high-quality, 0 low-quality, 0 failed uploads

...

Progress: 620/620 documents
Chunks: ~10000 total
Failed: 0 documents, 0 uploads
Elapsed: 13.2 hours | Avg: 76.8s/doc
```

### Step 4: Monitor During Migration

**Check every 1-2 hours:**

1. **Progress:**
   ```bash
   # Reattach to tmux
   tmux attach -t migration
   ```

2. **GPU Status:**
   ```bash
   nvidia-smi
   # Expected: GPU utilized but not maxed out
   ```

3. **Collection Size:**
   ```bash
   curl -s http://localhost:6333/collections/nomad_bms_documents | \
     jq '{points_count: .result.points_count, status: .result.status}'

   # Expected: Points count steadily increasing
   ```

4. **Disk Space:**
   ```bash
   df -h /workspace
   # Expected: Decreasing but >10GB remaining
   ```

**Warning Signs:**
- ❌ GPU out-of-memory errors → Stop and investigate
- ❌ Disk space <5GB → Free up space immediately
- ❌ Points count not increasing for >1 hour → Check logs
- ❌ Many "Failed to process" errors → Stop and investigate

---

## Post-Migration Validation

### Step 1: Verify Completion

**Check final stats:**
```bash
# Migration script output should show:
# Processed: 620/620 (100.0%)
# Quality rate: >99%
# Upload success: >98%
```

**Check collection:**
```bash
curl -s http://localhost:6333/collections/nomad_bms_documents | \
  jq '{
    points_count: .result.points_count,
    status: .result.status,
    vectors: .result.config.params.vectors | to_entries | map({name: .key, size: .value.size})
  }'

# Expected:
# - points_count: ~10000-12000 (depending on chunking)
# - status: "green"
# - All vectors: size 4096
```

### Step 2: Dimension Verification

**Verify all 4 vector types are 4096-d:**
```bash
curl -s http://localhost:6333/collections/nomad_bms_documents | \
  jq '.result.config.params.vectors | to_entries[] | {name: .key, size: .value.size}'

# Expected output:
# {"name": "chunk_embedding", "size": 4096}
# {"name": "parent_embedding", "size": 4096}
# {"name": "child_embedding", "size": 4096}
# {"name": "full_doc_embedding", "size": 4096}
```

### Step 3: Sample Query Testing

**Test basic search:**
```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "railway safety procedures",
    "limit": 5,
    "min_score": 0.7
  }' | jq

# Expected: Results with relevance scores >0.7
```

**Test hybrid search:**
```bash
curl -X POST http://localhost:8000/api/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "emergency brake system",
    "limit": 5
  }' | jq

# Expected: Results with mixed semantic + keyword matching
```

### Step 4: Quality Validation

**Check migration report:**
```bash
cat /workspace/logs/migration_report_4096d_FIXED.json | jq '{
  processed_documents,
  failed_documents,
  total_chunks,
  high_quality_chunks,
  upload_success_rate: (.total_chunks - .failed_uploads) / .total_chunks * 100
}'

# Expected:
# - processed_documents: ~620
# - failed_documents: 0-5 (< 1%)
# - upload_success_rate: > 98%
```

**Sample document verification:**
```bash
# Pick 5 random documents and verify chunks stored
for i in 1 2 3 4 5; do
  echo "Document $i:"
  curl -s "http://localhost:6333/collections/nomad_bms_documents/points/scroll" \
    -H "Content-Type: application/json" \
    -d "{\"limit\": 1, \"with_payload\": true}" | \
    jq '.result.points[0].payload | {file_name, processing_version, vector_count: (.vectors | length)}'
  echo ""
done

# Expected: processing_version: "v5.0_qwen3_4096d"
```

---

## Rollback Procedure (If Needed)

### When to Rollback

Rollback if ANY of the following occur:
- Upload success rate < 95%
- More than 10 failed documents
- GPU out-of-memory errors preventing completion
- Collection corruption or data loss

### Rollback Steps

1. **Stop migration:**
   ```bash
   # Kill migration process
   tmux attach -t migration
   # Ctrl+C to stop
   ```

2. **Delete new collection:**
   ```bash
   curl -X DELETE "http://localhost:6333/collections/nomad_bms_documents"
   ```

3. **Restore from backup:**
   ```bash
   # Upload snapshot
   SNAPSHOT_FILE="/workspace/backups/qdrant_nomad_bms_documents_YYYYMMDD_HHMMSS.snapshot"
   curl -X PUT "http://localhost:6333/collections/nomad_bms_documents/snapshots/upload" \
     --data-binary @$SNAPSHOT_FILE

   # Restore collection
   SNAPSHOT_NAME="<snapshot-name>"
   curl -X PUT "http://localhost:6333/collections/nomad_bms_documents/snapshots/$SNAPSHOT_NAME/recover"
   ```

4. **Verify restoration:**
   ```bash
   curl http://localhost:6333/collections/nomad_bms_documents | \
     jq '.result | {points_count, status}'

   # Expected: Original ~1744 points, status "green"
   ```

5. **Investigate issues:**
   - Check logs: `/workspace/logs/migration_*.log`
   - Review error messages
   - Contact support if needed

---

## Post-Migration Tasks

### Immediate (Within 24 hours)

1. **Enable search service:**
   ```bash
   # Restart BMS API to use new collection
   ./scripts/manage_services.sh restart
   ```

2. **Verify search quality:**
   - Run 10-20 test queries
   - Compare results with expectations
   - Check relevance scores

3. **Monitor performance:**
   ```bash
   # Check p95 latency
   curl http://localhost:8000/metrics/uplink | grep search_latency_p95

   # Expected: < 200ms (MVP target)
   ```

4. **User communication:**
   - Notify users migration complete
   - Request feedback on search quality
   - Monitor for reported issues

### Short-term (Within 1 week)

1. **Generate validation queries (T012):**
   - 70 production-style queries
   - 30 edge cases
   - Document expected results

2. **Run accuracy comparison (FR-012):**
   ```bash
   cd /workspace/001-bms-agent
   python scripts/evaluate_retrieval_enhanced.py

   # Compare 4096-d vs 768-d baseline
   # Target: ≥95% retrieval accuracy
   ```

3. **Deploy monitoring (T018):**
   - 24-hour performance tracking
   - Query volume monitoring
   - Error rate tracking
   - User satisfaction metrics

4. **Document results:**
   - Create comparison report
   - Highlight improvements
   - Note any regressions
   - Share with stakeholders

### Long-term (Within 1 month)

1. **Delete old backups:**
   ```bash
   # After confirming migration success
   rm /workspace/backups/qdrant_nomad_bms_documents_*_pre_migration.snapshot
   ```

2. **Update documentation:**
   - Update deployment guides
   - Document new vector dimensions
   - Update performance baselines

3. **Performance optimization:**
   - Tune Qdrant index parameters if needed
   - Adjust quality thresholds based on results
   - Optimize query patterns

---

## Success Criteria

Migration is considered successful if ALL of the following are met:

### Critical ✅
- [ ] Upload success rate ≥ 98%
- [ ] All vectors are 4096-dimensional
- [ ] Zero collection corruption
- [ ] Search service operational
- [ ] Zero data loss

### Important ⚠️
- [ ] Failed documents < 1% (≤6 out of 620)
- [ ] All high-priority documents migrated
- [ ] p95 search latency < 200ms
- [ ] No user-reported search quality regressions

### Nice-to-have 🟢
- [ ] Migration completes within 13-15 hours
- [ ] Zero manual interventions needed
- [ ] Checkpoint saves working (datetime fix)

---

## Contact & Support

**Primary Contact:** System Administrator
**Escalation:** DevOps Team
**Emergency Rollback Authority:** Product Owner

**Documentation:**
- Migration Success Report: `/workspace/specs/004-migrate-qdrant-collection/MIGRATION_SUCCESS_2025-10-18.md`
- Validation Test Report: `/workspace/specs/004-migrate-qdrant-collection/VALIDATION_TEST_REPORT_2025-10-18.md`
- GPU Contention Analysis: `/workspace/specs/004-migrate-qdrant-collection/GPU_CONTENTION_ANALYSIS_2025-10-18.md`

---

## Quick Reference

**Start Migration:**
```bash
cd /workspace/001-bms-agent
export NLTK_DATA=/workspace/nltk_data
source /workspace/bms-api-venv/bin/activate
tmux new -s migration
timeout 57600 python scripts/migrate_to_qwen3_4096d_FIXED.py --recreate
```

**Monitor Progress:**
```bash
tmux attach -t migration
```

**Check Collection:**
```bash
curl -s http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'
```

**Emergency Stop:**
```bash
tmux attach -t migration
# Ctrl+C
```

---

**Status:** ✅ **READY FOR PRODUCTION MIGRATION**
**Confidence Level:** VERY HIGH (100% validation success)
**Recommended Date:** Next scheduled maintenance window
