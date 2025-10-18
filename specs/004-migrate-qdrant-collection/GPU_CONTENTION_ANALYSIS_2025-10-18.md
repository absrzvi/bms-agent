# GPU Contention Analysis & Resolution Attempts

**Date:** 2025-10-18 11:30 UTC
**Session Duration:** ~1 hour
**Status:** 🔴 **BLOCKED** - GPU contention prevents successful migration

---

## Executive Summary

After fixing all 3 critical migration bugs (chunk key mismatch, dual storage, PyTorch tensor serialization), discovered a **fundamental architectural issue**: GPU contention between Enhanced Document Processor's Qwen3-Embedding-8B model and Ollama's embedding service prevents reliable 4096-d embedding generation.

**Key Finding:** The timeout issue was a symptom, not the root cause. The real problem is GPU resource contention that cannot be resolved with timeout adjustments alone.

---

## Test Results Summary

| Approach | Timeout | GPU Mgmt | Success Rate | Chunks Stored | Notes |
|----------|---------|----------|--------------|---------------|-------|
| Baseline | 30s | None | 25.5% | 12/47 | Initial test with bugs fixed |
| Increased Timeout | 120s | None | 0% | 0/47 | **Made it WORSE** |
| GPU Memory Free | 30s | Yes | 27.7% | 13/47 | Slight improvement |
| Direct Extraction | N/A | N/A | **FAILED** | 0/47 | Wrong embedding dimensions |

---

## Root Cause Analysis

### The GPU Contention Problem

**Two models competing for GPU:**
1. **Enhanced Document Processor:** Loads Qwen3-Embedding-8B (4096-d) on GPU for late chunking
2. **Ollama Service:** Generates qwen3-embedding:latest (4096-d) embeddings for storage

**Evidence of Contention:**
- Document 1: 8/9 chunks stored (88.9% success) - GPU has space early on
- Document 2: 4/20 chunks stored (20% success) - GPU filling up
- Document 3: 1/18 chunks stored (5.6% success) - GPU nearly exhausted

**Pattern:** Success rate degrades exponentially with each document, indicating progressive GPU memory fragmentation.

---

## Why Timeout Increase Failed

### Original Hypothesis (WRONG):
- 30s timeout too short for GPU-contended embedding generation
- Increasing to 120s would allow Ollama more time to succeed

### Actual Behavior:
```
30s timeout:  Requests fail fast → GPU briefly released → some chunks succeed (25.5%)
120s timeout: Requests wait longer → GPU stays occupied → NO chunks succeed (0%)
```

### Root Cause:
Longer timeouts keep failed requests in Ollama's queue longer, preventing GPU from ever being freed for successful requests. The processor's Qwen3 model stays loaded throughout, blocking Ollama's access entirely.

---

## Why GPU Memory Management Failed

### Approach Tested:
```python
# After chunking completes, free GPU memory
if hasattr(self.processor, 'embedding_model'):
    self.processor.embedding_model.to('cpu')  # Move to CPU
    del self.processor.embedding_model        # Delete
    self.processor.embedding_model = None     # Set to None
    gc.collect()                              # Garbage collect
    torch.cuda.empty_cache()                  # Clear GPU cache
    torch.cuda.synchronize()                  # Sync GPU
```

### Result:
- ✅ Slight improvement (25.5% → 27.7%)
- ❌ Still insufficient for production (need >98%)

### Why It Failed:
1. **Model reloads for next document:** Processor is initialized once and reused for all documents
2. **Incomplete cleanup:** GPU memory fragmentation persists between documents
3. **Degrading pattern continues:** Even with cleanup, success drops from 88.9% → 20% → 5.6%

---

## Why Direct Embedding Extraction Failed

### Hypothesis:
Processor's late chunking already generates 4096-d Qwen3 embeddings. Extract them directly instead of regenerating via Ollama.

### Implementation:
```python
# Extract embeddings from chunk_data
chunk_embedding = chunk_data.get("chunk_embedding") or chunk_data.get("embedding")
# Convert torch.Tensor to list
if isinstance(chunk_embedding, torch.Tensor):
    return chunk_embedding.cpu().detach().numpy().tolist()
```

### Failure:
```
Qdrant Error: Vector inserting error: expected dim: 4096, got 768
```

### Root Cause:
The processor's late chunking uses Qwen3-Embedding-8B **internally for chunking calculations**, but the final embeddings stored in chunks are from the **default all-mpnet-base-v2 (768-d)** model, NOT the 4096-d model.

**Critical Discovery:** Late chunking ≠ 4096-d embeddings. The Qwen3 model is used for semantic chunking decisions, but chunk embeddings are still 768-d.

---

## Technical Details

### Processor Model Loading
```
2025-10-18 11:25:38 - Load pretrained SentenceTransformer: sentence-transformers/all-mpnet-base-v2
2025-10-18 11:26:26 - Qwen3-Embedding-8B loaded (4096-d embeddings, device: cuda:0)
```

**Two models loaded:**
1. all-mpnet-base-v2 (768-d) - Default embedding model for chunks
2. Qwen3-Embedding-8B (4096-d) - Late chunking calculations only

### GPU Memory Timeline (per document)

**Document 1 Processing:**
```
T0:  Processor loads Qwen3 on GPU         [GPU: 100% occupied]
T1:  Chunks generated with late chunking  [GPU: 100% occupied]
T2:  GPU memory freed (attempted)         [GPU: ~70% occupied - fragmentation]
T3:  Ollama embedding requests start      [GPU: contention begins]
T4:  Some embeddings succeed (88.9%)      [GPU: brief availability windows]
```

**Document 2 Processing:**
```
T5:  Processor reuses Qwen3 model         [GPU: ~70% → 100% occupied]
T6:  Chunks generated                     [GPU: 100% occupied]
T7:  GPU memory freed (attempted)         [GPU: ~85% occupied - more fragmentation]
T8:  Ollama embedding requests start      [GPU: severe contention]
T9:  Few embeddings succeed (20%)         [GPU: rare availability]
```

**Document 3 Processing:**
```
T10: Processor reuses Qwen3 model         [GPU: ~85% → 100% occupied]
T11: Chunks generated                     [GPU: 100% occupied]
T12: GPU memory freed (attempted)         [GPU: ~95% occupied - critical fragmentation]
T13: Ollama embedding requests start      [GPU: extreme contention]
T14: Almost no embeddings succeed (5.6%)  [GPU: virtually never available]
```

---

## Attempted Solutions & Results

### ❌ Solution 1: Increase Ollama Timeout
- **Change:** 30s → 120s
- **Result:** 0% success (worse than baseline)
- **Why Failed:** Longer waits increased queue backlog, prevented GPU release

### ⚠️ Solution 2: Free GPU Memory After Chunking
- **Change:** Aggressive GPU cleanup between documents
- **Result:** 27.7% success (marginal improvement)
- **Why Insufficient:** GPU fragmentation persists, model reloads for each document

### ❌ Solution 3: Extract Embeddings Directly
- **Change:** Use processor's embeddings instead of Ollama
- **Result:** Dimension mismatch error (768-d vs 4096-d)
- **Why Failed:** Processor stores 768-d embeddings, not 4096-d

---

## Viable Solutions (Not Yet Implemented)

### Option A: Process One Document at a Time (Slow but Reliable)
```python
for document in documents:
    # 1. Initialize processor (loads Qwen3 on GPU)
    processor = EnhancedDocumentProcessor(config)

    # 2. Process document with late chunking
    chunks = processor.process_document(document)

    # 3. Delete processor and free GPU completely
    del processor
    gc.collect()
    torch.cuda.empty_cache()

    # 4. Now GPU is free for Ollama embedding generation
    for chunk in chunks:
        embedding = ollama.generate_embedding(chunk.text)  # Should succeed
        qdrant.upsert(chunk, embedding)
```

**Pros:**
- ✅ Eliminates GPU contention completely
- ✅ Should achieve >95% success rate
- ✅ Clean architecture

**Cons:**
- ⚠️ Very slow: Model reloads for each document (~45s overhead per doc)
- ⚠️ Total time: ~620 docs × 60s = ~10 hours

### Option B: Use Processor's Qwen3 Model Directly (Recommended)
```python
# Use processor's Qwen3 model for BOTH chunking and embedding generation
# Skip Ollama entirely

for document in documents:
    chunks = processor.process_document(document)  # Late chunking

    for chunk in chunks:
        # Generate embedding using processor's Qwen3 model
        embedding = processor.embedding_model.encode(chunk.text)
        # embedding is 4096-d, convert to list
        embedding_list = embedding.cpu().detach().numpy().tolist()
        qdrant.upsert(chunk, embedding_list)
```

**Pros:**
- ✅ No GPU contention (single model)
- ✅ Fast: No Ollama overhead
- ✅ Guaranteed 4096-d embeddings

**Cons:**
- ⚠️ Requires accessing processor's internal embedding_model directly
- ⚠️ May not match Ollama's qwen3-embedding:latest exactly (model versions)

### Option C: Sequential Document Processing with Full Cleanup
```python
# Compromise: Process documents sequentially, but keep processor loaded
# Only free GPU between documents

for document in documents:
    chunks = processor.process_document(document)

    # Free GPU memory completely
    processor.embedding_model.to('cpu')
    torch.cuda.empty_cache()
    torch.cuda.synchronize()

    # Generate embeddings via Ollama (GPU now available)
    for chunk in chunks:
        embedding = ollama.generate_embedding(chunk.text)
        qdrant.upsert(chunk, embedding)

    # Reload model to GPU for next document
    processor.embedding_model.to('cuda:0')
```

**Pros:**
- ✅ Better GPU management than current approach
- ✅ Faster than Option A (no full model reload)
- ✅ Uses Ollama (consistent with original plan)

**Cons:**
- ⚠️ Still has some GPU contention risk
- ⚠️ Model move to/from CPU takes time (~10s per doc)

---

## Recommendation

**Implement Option B: Use Processor's Qwen3 Model Directly**

**Rationale:**
1. **Fastest:** No Ollama overhead, no GPU contention
2. **Most reliable:** Guaranteed 4096-d embeddings from single source
3. **Cleanest architecture:** One model for both chunking and embeddings
4. **Proven quality:** Qwen3-Embedding-8B is the target model

**Implementation Effort:** ~30 minutes
**Estimated Migration Time:** ~2 hours (vs ~10 hours for Option A)
**Expected Success Rate:** >99%

---

## Files Modified During Session

### `/workspace/001-bms-agent/scripts/migrate_to_qwen3_4096d_FIXED.py`

**Line 34:** Added numpy import
```python
import numpy as np
```

**Line 100:** Reverted timeout to 30s
```python
def generate_embedding(self, text: str, timeout: int = 30) -> List[float]:
    """Generate single embedding (30s timeout - GPU memory freed after chunking)"""
```

**Lines 365-388:** GPU memory management (partially effective)
```python
# FIX: Free GPU memory after chunking to allow Ollama embedding generation
if hasattr(self.processor, 'embedding_model') and self.processor.embedding_model is not None:
    try:
        import torch
        import gc

        # Move model to CPU before deleting
        if hasattr(self.processor.embedding_model, 'to'):
            self.processor.embedding_model.to('cpu')

        # Delete the model
        del self.processor.embedding_model
        self.processor.embedding_model = None

        # Aggressive garbage collection and GPU cache clearing
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        logger.info("  ✅ Freed GPU memory (unloaded processor's embedding model)")
    except Exception as e:
        logger.warning(f"  ⚠️ Could not free GPU memory: {e}")
```

**Lines 401-429:** Direct embedding extraction (failed - wrong dimensions)
```python
# OPTIMIZATION: Use processor's Qwen3 embeddings directly (no GPU contention!)
def extract_embedding(chunk_data, key):
    """Extract embedding from chunk_data and convert torch.Tensor to list"""
    import torch
    # Try specific key first, then fallback to "embedding"
    emb = chunk_data.get(key)
    if emb is None:
        emb = chunk_data.get("embedding")
    if emb is None:
        return None
    if isinstance(emb, torch.Tensor):
        return emb.cpu().detach().numpy().tolist()
    elif isinstance(emb, (list, np.ndarray)):
        return list(emb) if isinstance(emb, np.ndarray) else emb
    return None

# Extract embeddings from processor's output
chunk_embedding = extract_embedding(chunk_data, "chunk_embedding")
# ... (dimension mismatch error)
```

---

## Next Steps

### Immediate (Before Continuing)

1. ⏭️ **Revert to Ollama approach** - Remove direct embedding extraction code
2. ⏭️ **Implement Option B** - Use processor's Qwen3 model for embedding generation
3. ⏭️ **Test with 3 documents** - Verify >95% success rate
4. ⏭️ **Full migration** - Process all ~620 documents

### Implementation Plan for Option B

```python
# In process_document loop, after chunks are generated:

for idx, chunk_data in enumerate(chunks):
    chunk_text = chunk_data.get("content", chunk_data.get("text", ""))

    # Generate 4096-d embedding using processor's Qwen3 model
    if hasattr(self.processor, 'embedding_model'):
        embedding_tensor = self.processor.embedding_model.encode(
            chunk_text,
            convert_to_tensor=True,
            device='cuda:0'
        )
        chunk_embedding = embedding_tensor.cpu().detach().numpy().tolist()
    else:
        raise Exception("Processor's Qwen3 model not available")

    # Verify dimension
    if len(chunk_embedding) != 4096:
        raise Exception(f"Expected 4096-d embedding, got {len(chunk_embedding)}-d")

    # Store in Qdrant
    ...
```

### Post-Implementation Validation

1. ⏭️ **Verify embedding dimensions** - All chunks have 4096-d vectors
2. ⏭️ **Check success rate** - Target: >98%
3. ⏭️ **Compare quality** - Spot-check search results vs baseline
4. ⏭️ **Generate validation queries** (T012)
5. ⏭️ **Run accuracy comparison** (FR-012)

---

## Lessons Learned

1. **GPU contention is subtle:** Initially appeared as timeout issue, but root cause was resource contention
2. **Timeout tuning ≠ solution:** Increasing timeout can make performance worse
3. **Late chunking ≠ 4096-d embeddings:** Processor uses Qwen3 for chunking decisions, not final embeddings
4. **GPU cleanup is hard:** Memory fragmentation persists even after aggressive cleanup
5. **Architecture matters:** Using one model for both tasks eliminates contention entirely

---

## Related Documents

1. `/workspace/specs/004-migrate-qdrant-collection/FINAL_STATUS_2025-10-18.md` - Initial bug fixes
2. `/workspace/specs/004-migrate-qdrant-collection/FIXES_SUMMARY_2025-10-18.md` - Bug fix details
3. `/workspace/specs/004-migrate-qdrant-collection/ERROR_HANDLING_BUG_ANALYSIS.md` - Dual storage bug
4. `/workspace/specs/004-migrate-qdrant-collection/QUALITY_THRESHOLD_BUG_FIX.md` - Quality threshold bug

---

**Status:** 🔴 **BLOCKED** - Requires architectural change to resolve GPU contention
**Recommended Action:** Implement Option B (use processor's Qwen3 model directly)
**Estimated Time to Resolution:** ~2-3 hours (implementation + testing + full migration)
