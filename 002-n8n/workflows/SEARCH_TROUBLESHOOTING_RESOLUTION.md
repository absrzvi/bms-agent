# Search Troubleshooting Resolution

**Date**: 2025-10-08
**Issue**: n8n workflows returning 0 results for all queries
**Root Cause**: Multiple configuration mismatches

---

## Problems Identified

### 1. **Wrong Collection Name** ❌
- **Workflow Configuration**: `bms_documents`
- **Actual Qdrant Collection**: `nomad_bms_documents`
- **Impact**: All searches failed with "Collection not found" error

### 2. **Quality Score Filtering** ❌
- **All Documents**: `quality_score: 0` (not populated during processing)
- **Workflow Default**: `min_quality: 0.5` (later lowered to 0.5)
- **BMS API Behavior**: Filters out documents with `quality_score < min_quality`
- **Impact**: 100% of documents filtered out

### 3. **Relevance Score Threshold Too High** ⚠️
- **Original Threshold**: `min_score: 0.7`
- **Actual Document Scores**: 0.58-0.65 range for relevant results
- **Impact**: Most relevant results filtered out

---

## Solutions Applied

### ✅ Fix 1: Updated Collection Name
**File**: `tool-search-semantic.json`
```javascript
// Before
let collection_name = 'bms_documents';

// After
let collection_name = 'nomad_bms_documents';
```

### ✅ Fix 2: Removed min_quality Default
**File**: `tool-search-hybrid.json`
```javascript
// Before
const params = {
  query: item.json.query || "",
  min_score: 0.7,
  min_quality: 0.65  // ❌ Filters out all docs with quality_score=0
};

// After
const params = {
  query: item.json.query || "",
  min_score: 0.3
};

// Only add min_quality if explicitly provided
if (item.json.min_quality !== undefined) {
  params.min_quality = parseFloat(item.json.min_quality);
}
```

### ✅ Fix 3: Lowered Relevance Threshold
**Files**: All `tool-*.json` workflows
```javascript
// Before
min_score: 0.7   // Too high - missed relevant results

// After
min_score: 0.3   // More permissive - returns 0.58-0.65 scored results
```

---

## Verification Test

**Query**: "sick leave policy"

### Before Fixes
```json
{
  "status": "success",
  "results": [],
  "results_count": 0
}
```

### After Fixes
```json
{
  "status": "success",
  "results_count": 10,
  "top_results": [
    {
      "document": "BMS-HUMR-POL-028 AUSTRALIA - Sickness Absence Policy",
      "score": 0.647
    },
    {
      "document": "BMS-HUMR-POL-010 Sickness Absence Policy",
      "score": 0.633
    }
  ]
}
```

---

## Files Modified

1. ✅ `tool-search-hybrid.json` - Removed min_quality default, lowered min_score to 0.3
2. ✅ `tool-search-semantic.json` - Fixed collection name, lowered threshold to 0.3
3. ✅ `tool-contextual-search.json` - Lowered thresholds to 0.5
4. ✅ `tool-search-by-metadata.json` - Lowered thresholds to 0.5
5. ✅ `tool-latest-versions-search.json` - Lowered thresholds to 0.5
6. ✅ `tool-faceted-search.json` - Lowered thresholds to 0.5
7. ✅ `tool-explained-search.json` - Lowered thresholds to 0.5
8. ✅ `tool-batch-search.json` - Lowered threshold to 0.5
9. ✅ `bms-ai-agent.json` - Updated system message with new thresholds

---

## Recommendations

### For Production Deployment

1. **Re-process Documents with Quality Scoring**
   ```bash
   # Enable RAGAS quality validation in BMS API
   export BMS_ENABLE_QUALITY_VALIDATION=true

   # Re-process all documents
   python scripts/reindex_documents.py
   ```

2. **Optimal Threshold Settings** (once quality scores populated):
   - **Exploratory queries**: `min_score: 0.3, min_quality: 0.0`
   - **Standard queries**: `min_score: 0.5, min_quality: 0.7`
   - **Safety-critical (QHSE/RENG)**: `min_score: 0.7, min_quality: 0.9`

3. **Collection Naming Convention**
   - Use consistent naming across all configs
   - Document in `CLAUDE.md` and environment variables

### For Better Search Quality

1. **Dynamic Threshold Adjustment**
   ```javascript
   // Adjust based on results count
   if (results.length === 0 && min_score > 0.3) {
     min_score -= 0.1;  // Retry with lower threshold
   }
   ```

2. **Query-Specific Tuning**
   - Exact term searches: Lower vector weight, higher keyword weight
   - Conceptual searches: Higher vector weight
   - Multi-term searches: Balanced weights (0.5/0.5)

3. **Monitor Score Distributions**
   ```bash
   # Check actual score ranges in your data
   curl http://localhost:8000/api/v1/search/explained \
     -d '{"query": "test", "limit": 100}' | jq '.results[].score' | sort -n
   ```

---

## Quality Score Population (Future Task)

The `quality_score` field is currently 0 for all documents. To populate:

1. **Option A**: Re-run Enhanced Document Processor v4.0 with RAGAS enabled
   ```python
   from bms_agent.scr.enhanced_document_processor import EnhancedDocumentProcessor

   processor = EnhancedDocumentProcessor(
       enable_quality_validation=True,  # Enable RAGAS
       processing_profile="RAILWAY"
   )
   ```

2. **Option B**: Batch update existing points with quality scores
   ```python
   # Generate quality scores for existing chunks
   from api.monitoring.quality_monitor import QualityMonitor

   monitor = QualityMonitor()
   # Iterate over points and update quality_score field
   ```

---

## Testing Checklist

- [x] Semantic search returns results
- [x] Hybrid search returns results
- [x] Collection name correct in all workflows
- [x] min_quality optional (not blocking results)
- [x] min_score threshold appropriate (0.3 for broad recall)
- [ ] Test with 20+ different queries across departments
- [ ] Validate precision/recall trade-off
- [ ] Benchmark response times (<150ms target)

---

## Contact

For questions about this resolution:
- See: `/workspace/CLAUDE.md` (BMS Agent Architecture)
- See: `/workspace/002-n8n/docs/` (n8n workflow documentation)
