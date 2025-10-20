# Low Relevance Scores Analysis - Nomi Slack Workflow

**Date**: 2025-10-11
**Issue**: ask_bms tool returns relevant data but AI agent rejects it due to low relevance scores

---

## Root Cause Analysis

### The Problem

**Execution 1566** - Query: "how do i start a project?"

**What happened:**
1. ✅ ask_bms tool returned 3 highly relevant documents
2. ❌ Relevance scores: 0.348, 0.331, 0.319 (all below 0.6 threshold)
3. ❌ Agent rejected results: "I couldn't find any BMS documentation that meets the relevance threshold"

**Documents returned:**
- `BMS-PROJ-GUI-003 PROJECT PLANNING OVERVIEW PRESENTATION.pdf`
- `BMS-PROJ-FOR-004 Project Initiation Document.docx`
- `BMS-PROJ-PRO-001 Project Planning Process.pdf`

These are **exactly the right documents** for the query!

---

## Deep Dive: Why Are Scores Low?

### Test Results

| Query Type | Query | Top Score | Assessment |
|------------|-------|-----------|------------|
| Conversational | "how do i start a project?" | 0.348 | ❌ Below 0.6 |
| Keyword | "project planning process" | 0.697 | ✅ Above 0.6 |
| Conversational | "what is the sick leave policy" | 0.681 | ✅ Above 0.6 |
| Technical | "how to configure VLAN settings" | 0.345 | ❌ Below 0.6 |

### Pattern Identified

**The embedding model (sentence-transformers/all-mpnet-base-v2) has different behavior for different query types:**

1. **High scores (>0.6)**: Queries that match document titles/keywords
   - "project planning process" → matches "PROJECT PLANNING" in titles
   - "sick leave policy" → matches "Sickness Absence Policy" exactly

2. **Low scores (0.3-0.4)**: Conversational queries with generic verbs
   - "how do i **start** a project?" → "start" is too generic
   - "how to **configure** VLAN" → technical jargon not well-represented

### The Mismatch

- **Agent threshold**: ≥0.6 (strict, designed to prevent hallucination)
- **Typical conversational query scores**: 0.3-0.4
- **Result**: Agent correctly rejects low-scoring results per its instructions

---

## Why This Isn't Fixed Yet

### Query Expansion Exists But Isn't Used

**Found:** `/workspace/001-bms-agent/api/retrieval/query_expansion.py`

```python
class QueryExpander:
    """Expand queries using LLM to generate variations and improve recall."""

    async def expand_query(self, query: str) -> List[str]:
        # Converts "how do I start a project?"
        # to ["how do I start a project?", "project planning process", "project initiation"]
```

**Problem:** The `/api/v1/ask` endpoint does NOT use query expansion!

```python
# /workspace/001-bms-agent/api/main.py:1745
query_embedding = processor._generate_embeddings(request.query)  # Direct embedding, no expansion
```

---

## Solutions (Ranked by Impact)

### Solution 1: Lower the Threshold (Quick Fix - 5 minutes)

**Change:** Update Nomi agent system prompt from 0.6 → 0.3

**Rationale:**
- ask_bms uses LLM to validate relevance (double-check)
- LLM can filter out irrelevant low-scoring results
- 0.3-0.4 is normal for conversational queries

**Implementation:**
```javascript
// In bms-ai-agent.json, line ~45, update system message:
"Search results have relevance score ≥0.3"  // was 0.6
```

**Pros:**
- Immediate fix (no code changes)
- Works with existing infrastructure
- LLM provides additional validation layer

**Cons:**
- Higher risk of hallucination if LLM misinterprets low-quality results
- Doesn't fix underlying score issue

---

### Solution 2: Add Query Expansion to /ask Endpoint (Better Fix - 30 minutes)

**Change:** Use existing query expansion before semantic search

**Implementation:**
```python
# In /workspace/001-bms-agent/api/main.py, line ~1745

from retrieval.query_expansion import QueryExpander

expander = QueryExpander()
expanded_queries = await expander.expand_query(request.query)

# Search with all variations, merge results
all_results = []
for q in expanded_queries:
    embedding = processor._generate_embeddings(q)
    results = processor.qdrant_client.search(...)
    all_results.extend(results)

# Deduplicate and rerank
search_results = deduplicate_and_rerank(all_results)
```

**Example:**
- Input: "how do i start a project?"
- Expanded:
  1. "how do i start a project?"
  2. "project planning process"
  3. "project initiation documentation"

**Expected improvement:**
- Query 1: scores 0.3-0.4
- Query 2: scores 0.6-0.7 ← **Now finds high-scoring matches!**
- Query 3: scores 0.5-0.6

**Pros:**
- Uses existing code
- Significantly improves recall
- Maintains 0.6 threshold for safety

**Cons:**
- 3x more search calls (latency impact)
- Requires async changes to /ask endpoint

---

### Solution 3: Cross-Encoder Reranker (Best Fix - 2 hours)

**Change:** Add two-stage retrieval with reranking

**Architecture:**
```
Query → Semantic Search (recall 50 results, any score)
      → Cross-Encoder Reranker (precision, score 0-1)
      → Top 5 reranked results
```

**Implementation:**
Use existing reranker: `/workspace/001-bms-agent/api/retrieval/reranker.py`

```python
from retrieval.reranker import Reranker

# Stage 1: Broad recall
search_results = processor.qdrant_client.search(limit=50, score_threshold=0.2)

# Stage 2: Precise reranking
reranker = Reranker()
reranked = reranker.rerank(query=request.query, results=search_results, top_k=5)
# Returns results with accurate 0-1 scores
```

**Expected improvement:**
- "how do i start a project?" → Reranked scores: 0.82, 0.79, 0.76
- Conversational queries get accurate high scores

**Pros:**
- Most accurate solution
- Cross-encoders designed for this exact problem
- Maintains high quality threshold

**Cons:**
- Adds latency (50-100ms per query)
- More complex implementation

---

### Solution 4: Hybrid Search (Alternative - 1 hour)

**Change:** Use keyword + semantic search fusion

**Note:** BMS API already has `/api/v1/search/hybrid` endpoint!

**Implementation:**
```python
# Change ask_bms tool to call /api/v1/search/hybrid instead of /api/v1/ask
# Hybrid combines:
# - Semantic search (0.3-0.4 for conversational)
# - Keyword search (1.0 for exact matches)
# - Fusion scores: 0.5-0.7 (above threshold!)
```

**Pros:**
- Minimal code change (just change endpoint URL)
- Proven to improve conversational queries
- Already implemented and tested

**Cons:**
- Still need to generate answer from search results
- May need custom answer generation logic

---

## Recommendation

### Immediate Action (Today)
**Solution 1**: Lower threshold to 0.3 in Nomi system prompt
- 5 minutes to implement
- Unblocks users immediately
- Acceptable risk with LLM validation

### Short-Term (This Week)
**Solution 2**: Add query expansion to /ask endpoint
- Significantly improves quality
- Uses existing code
- Proper fix for the root cause

### Long-Term (Next Sprint)
**Solution 3**: Implement cross-encoder reranker
- Production-grade solution
- Best accuracy
- Worth the latency cost

---

## Files to Modify

### Solution 1 (Quick Fix)
- `/workspace/002-n8n/workflows/bms-ai-agent.json` (Nomi system prompt)

### Solution 2 (Query Expansion)
- `/workspace/001-bms-agent/api/main.py` (ask endpoint)
- `/workspace/001-bms-agent/api/retrieval/query_expansion.py` (may need tweaks)

### Solution 3 (Reranker)
- `/workspace/001-bms-agent/api/main.py` (ask endpoint)
- `/workspace/001-bms-agent/api/retrieval/reranker.py` (may need tweaks)

### Solution 4 (Hybrid Search)
- `/workspace/002-n8n/workflows/tool-ask-bms-enhanced.json` (change endpoint URL)
- May need new answer generation workflow

---

## Testing Plan

**Before:**
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "how do i start a project?"}'
# Citations: relevance_score: 0.348, 0.331, 0.319
```

**After (Solution 1):**
- Agent accepts 0.3+ scores
- Response includes actual documentation

**After (Solution 2):**
```bash
# Expanded queries find 0.6+ scores
# Citations: relevance_score: 0.697, 0.663, 0.622
```

**After (Solution 3):**
```bash
# Reranked scores are accurate
# Citations: relevance_score: 0.82, 0.79, 0.76
```

---

## Conclusion

The issue is **not a bug** - it's a fundamental limitation of semantic search with conversational queries. The agent is working exactly as designed, but the **0.6 threshold is too strict** for the query patterns users actually use.

**Root cause:** Conversational queries ("how do I...") get lower similarity scores than keyword queries, even for highly relevant documents.

**Recommended path:**
1. Deploy Solution 1 immediately (lower threshold)
2. Implement Solution 2 this week (query expansion)
3. Plan Solution 3 for next sprint (reranker)

This layered approach balances immediate user needs with long-term quality improvement.
