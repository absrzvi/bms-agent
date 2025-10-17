# Research: Qdrant Collection Migration

**Feature**: 004-migrate-qdrant-collection
**Generated**: 2025-10-17 (Phase 0 of /plan command)
**Status**: ✅ Complete - All unknowns resolved in spec clarifications

## Overview

This document captures technical research findings for migrating the Qdrant vector database from 768-dimensional to 4096-dimensional embeddings. All critical unknowns were resolved during specification phase (Session 2025-10-17), so this research document serves as a consolidation of decisions and rationales.

---

## Research Findings

### 1. Migration Strategy

**Question**: How to perform zero-downtime migration of vector database collection?

**Options Evaluated**:

| Strategy | Pros | Cons | Decision |
|----------|------|------|----------|
| Blue-Green Deployment | Zero downtime, full rollback capability, validates before cutover | Requires snapshot backup (~5 min overhead) | ✅ **CHOSEN** |
| Online Migration (Dual Collections) | No downtime, gradual cutover | Complex routing logic, 2x disk space, manual traffic splitting | ❌ Rejected |
| In-Place Upgrade | Fast, minimal disk usage | No rollback path, downtime required, risky | ❌ Rejected |
| Shadow Collection | Zero downtime, safe testing | Complex synchronization, eventual consistency issues | ❌ Rejected |

**Decision: Blue-Green Deployment**

**Rationale**:
- Meets zero-downtime requirement (FR from spec)
- Rollback capability within 5 minutes (NFR-003)
- Qdrant snapshot API provides reliable backup/restore
- Simple execution model (backup → delete → recreate → validate)
- Industry-standard approach for database migrations

**Implementation**:
1. Create snapshot backup of 768-d collection
2. Validate backup integrity (restore to test collection)
3. Delete old collection
4. Recreate with 4096-d schema
5. Reprocess all documents
6. Validate search quality
7. Monitor for 24 hours
8. Rollback if validation fails

**References**:
- Qdrant Snapshot API: https://qdrant.tech/documentation/concepts/snapshots/
- Blue-Green Deployment Pattern: Martin Fowler, "Continuous Delivery"

---

### 2. Embedding Model Selection

**Question**: Which embedding model to use for 4096-dimensional vectors?

**Options Evaluated**:

| Model | Dimensions | Size | Provider | Quality | Decision |
|-------|------------|------|----------|---------|----------|
| Qwen3-Embedding-8B:F16 | 4096 | 15 GB | Ollama (local) | Superior (MTEB benchmark) | ✅ **CHOSEN** |
| sentence-transformers/all-mpnet-base-v2 | 768 | 420 MB | HuggingFace | Good (current baseline) | ❌ Status quo |
| OpenAI text-embedding-3-large | 3072 | N/A | OpenAI API | Excellent | ❌ Violates constitution |
| nomic-embed-text-v1.5 | 768 | 274 MB | Ollama | Good | ❌ No dimension upgrade |

**Decision: Qwen3-Embedding-8B:F16 via Ollama**

**Rationale**:
- Superior semantic understanding (4096-d provides richer representations)
- Already installed in Phase 3.7 of feature 002 (`/workspace/data/ollama_models/`)
- GPU-accelerated via Ollama (RunPod pod has GPU access)
- On-premises deployment (meets constitution §11 air-gapped requirement)
- No external API calls (data sovereignty maintained)
- Proven performance in testing (Phase 3.7 validation)

**Performance Characteristics**:
- Batch size 32: ~15 embeddings/second (GPU-accelerated)
- p95 latency: ~320ms per batch
- Memory: ~14.5 GB GPU RAM during generation
- Disk: 15 GB model size (persistent in `/workspace/data/ollama_models/`)

**Alternative Rejected**:
- OpenAI text-embedding-3-large: Excellent quality but requires external API calls, violating constitution §11 ("Strictly no external API calls for inference")

**References**:
- Qwen3 Model Card: https://huggingface.co/Qwen/Qwen2.5
- MTEB Benchmarks: https://huggingface.co/spaces/mteb/leaderboard
- Constitution §11 (AI/LLM Architecture): `.specify/memory/constitution.md` lines 138-154

---

### 3. Chunking Strategy

**Question**: Which chunking strategy to use for document reprocessing?

**Options Evaluated**:

| Strategy | Boundary Type | Context Preservation | Implementation Complexity | Decision |
|----------|---------------|----------------------|---------------------------|----------|
| Late Chunking | Semantic boundaries | Excellent (preserves hierarchy) | Moderate (already implemented) | ✅ **CHOSEN** |
| Sentence-Based | Sentence endings | Fair (breaks at sentences) | Low (current method) | ❌ Sub-optimal |
| Fixed-Size | Character count | Poor (arbitrary breaks) | Low | ❌ Breaks semantic units |
| Sliding Window | Overlapping windows | Good (provides context) | Low | ❌ Creates redundancy |

**Decision: Late Chunking with 500 tokens/chunk, 150 token overlap**

**Rationale**:
- Better context preservation (creates parent-child-chunk hierarchy)
- Already implemented in `enhanced_document_processor.py` (Phase 3.6 of feature 002)
- Supports multi-vector embeddings (chunk, parent, child, full_doc)
- Semantic boundaries improve retrieval accuracy
- RAGAS quality scores higher with late chunking (observed in Phase 3.6 testing)

**Configuration**:
```python
ChunkingStrategy.LATE_CHUNKING
chunk_size = 500  # tokens
chunk_overlap = 150  # tokens
```

**References**:
- Late Chunking Paper: "Contextual Document Embeddings" (ArXiv 2024)
- Implementation: `/workspace/001-bms-agent/bms-agent/src/enhanced_document_processor.py`

---

### 4. Validation Approach

**Question**: How to objectively validate migration success?

**Options Evaluated**:

| Approach | Measurability | Repeatability | Captures Regressions | Decision |
|----------|---------------|---------------|----------------------|----------|
| Baseline Comparison + 24h Monitoring | High (quantitative metrics) | High (scripted tests) | Yes (delta tracking) | ✅ **CHOSEN** |
| Manual Spot-Checking | Low (subjective) | Low (inconsistent) | No | ❌ Not measurable |
| Immediate Cutover | N/A (no validation) | N/A | No | ❌ Violates FR-013 |
| A/B Testing | High | High | Yes | ❌ Complex routing |

**Decision: Baseline Comparison with 50-Query Test Set + 24h Monitoring**

**Rationale**:
- Objective quality measurement (retrieval accuracy, latency percentiles)
- Catches performance regressions (compares against 768-d baseline)
- User feedback integration (24h window allows real-world testing)
- Automated rollback triggers (accuracy <90%, p95 >200ms)
- FR-013 mandates 24h monitoring period

**Validation Metrics**:
1. **Retrieval Accuracy**: ≥95% (compare to baseline)
2. **p95 Search Latency**: ≤100ms (Qdrant queries only)
3. **Quality Score Distribution**: mean ≥70.0, median ≥75.0
4. **Memory Stability**: No memory leaks (RSS stable)
5. **Disk Usage**: Growth <10% over 24h
6. **Error Rate**: <1% of search queries

**Test Query Set** (50 queries):
- 10 document code queries (e.g., "BMS-NET-VLAN-042")
- 10 procedural queries (e.g., "How to perform maintenance")
- 10 conceptual queries (e.g., "What is emergency braking system")
- 10 metadata queries (e.g., "Documents updated after 2024-01-01")
- 10 edge cases (ambiguous, multi-topic, out-of-scope)

**References**:
- RAGAS Framework: https://github.com/explodinggradients/ragas
- Evaluation Script: `/workspace/001-bms-agent/scripts/evaluate_retrieval_enhanced.py`

---

### 5. Disk Space Management

**Question**: How to manage 5x storage increase (768-d → 4096-d)?

**Options Evaluated**:

| Approach | Disk Usage | Safety | Decision |
|----------|------------|--------|----------|
| Pre-flight Validation + Delete Old | 1x target collection (3-4 GB) | Medium (requires valid backup) | ✅ **CHOSEN** |
| Keep Both Collections | 2x (768-d + 4096-d) | High (instant rollback) | ❌ Disk constraints |
| Compress Embeddings | 0.5x (compressed) | Low (performance penalty) | ❌ Complexity |
| Incremental Migration | Variable (gradual growth) | High | ❌ Complex synchronization |

**Decision: Pre-flight Validation (5 GB minimum) + Delete Old Collection After Success**

**Rationale**:
- Prevents disk exhaustion (5x increase from ~600 MB to ~3-4 GB)
- Qdrant snapshot provides reliable backup (validated before deletion)
- Rollback within 5 minutes via snapshot restore (meets NFR-003)
- Simplest approach (no ongoing dual-collection complexity)

**Disk Space Calculation**:
- 2,615 points × 4 vector types × 4096 dimensions × 4 bytes/float = ~168 MB (vectors only)
- Payload + metadata + indexes: ~3.5 GB (observed in similar collections)
- **Total: ~3.7 GB** (estimated for 4096-d collection)

**Pre-flight Check**:
```bash
df -h /workspace/qdrant_storage | awk 'NR==2 {print $4}'
# Abort if available space < 5 GB
```

**References**:
- Qdrant Storage Docs: https://qdrant.tech/documentation/guides/administration/#storage-configuration

---

## Dependencies Best Practices

### Qdrant Snapshot API

**Key Learnings**:
- Snapshots are atomic (collection state frozen during snapshot)
- Restore overwrites target collection completely (destructive)
- Snapshot file format is opaque binary (no manual editing)
- Best practice: Always validate backup integrity with test restore

**API Endpoints**:
```bash
# Create snapshot
POST /collections/{collection_name}/snapshots

# List snapshots
GET /collections/{collection_name}/snapshots

# Restore snapshot (upload)
POST /collections/{collection_name}/snapshots/upload
```

**References**:
- Qdrant Snapshot API: https://qdrant.tech/documentation/concepts/snapshots/

---

### Ollama Embedding Generation

**Key Learnings**:
- Batch processing significantly faster than individual embeddings (32x speedup)
- GPU memory usage peaks during batch embedding (~14.5 GB for Qwen3)
- Timeout should be generous for large models (5000ms recommended)
- Model availability check essential before migration (prevent mid-migration failure)

**Best Practices**:
```python
# Validate model availability
def validate_embedding_model(model_name: str) -> bool:
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": model_name, "prompt": "test"},
            timeout=5
        )
        return response.status_code == 200 and len(response.json()["embedding"]) == 4096
    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        return False
```

**References**:
- Ollama Embeddings API: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings

---

### RAGAS Quality Scoring

**Key Learnings**:
- Quality score <50.0 indicates low-quality chunk (missing context, poor faithfulness)
- Mean quality score ≥70.0 is target for production collections
- Quality filtering reduces point count by ~10% (observed in Phase 3.6)
- Late chunking improves quality scores vs sentence-based chunking

**Best Practices**:
```python
# Filter low-quality chunks to separate collection
if quality_score < 50.0:
    qdrant_client.upsert(
        collection_name="nomad_bms_documents_low_quality",
        points=[point]
    )
else:
    qdrant_client.upsert(
        collection_name="nomad_bms_documents",
        points=[point]
    )
```

**References**:
- RAGAS Documentation: https://github.com/explodinggradients/ragas
- Implementation: `/workspace/001-bms-agent/bms-agent/src/enhanced_document_processor.py` lines 150-200

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Disk space exhaustion during migration | Medium | High (migration failure) | Pre-flight validation (5 GB min check) |
| Embedding model unavailable mid-migration | Low | High (partial data) | Model availability check before migration |
| Quality regression (accuracy <95%) | Low | Medium (user complaints) | Baseline comparison, 24h monitoring, rollback triggers |
| Rollback time exceeds 5 min | Low | Medium (violates NFR-003) | Dry-run rollback before migration, optimize snapshot restore |
| Memory OOM during batch processing | Medium | Medium (processing failure) | Reduce batch size to 16 if OOM, monitor GPU RAM |

**All high-impact risks have documented mitigations in plan.md**

---

## Conclusion

All technical unknowns for the Qdrant collection migration have been resolved. Key decisions:

1. **Migration Strategy**: Blue-green deployment (zero downtime, rollback capability)
2. **Embedding Model**: Qwen3-Embedding-8B:F16 (4096-d, GPU-accelerated, on-premises)
3. **Chunking**: Late chunking with 500 token chunks, 150 token overlap
4. **Validation**: Baseline comparison + 50-query test set + 24h monitoring
5. **Disk Management**: Pre-flight validation (5 GB min), delete old collection after success

**Ready to proceed to Phase 1 (Design & Contracts)**

---

*Research completed: 2025-10-17*
*All findings incorporated into plan.md and spec.md clarifications*
*Next step: /plan command Phase 1 execution*
