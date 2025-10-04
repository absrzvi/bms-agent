# OpenWebUI Tool Quick Reference

**Tool**: BMS Agent Search - Enhanced v3.0  
**Status**: POC Ready (80% Accuracy)  
**Working Functions**: 10/21 (Core + Filtered + Utility)

---

## 🚀 Quick Start

### 1. Install Tool in OpenWebUI

1. Open OpenWebUI admin panel
2. Navigate to **Admin Panel** → **Tools** (or **Functions**)
3. Click **Add Tool** or **Import**
4. Upload `tools/bms_search.py` or paste content
5. Configure valves (optional):
   - `BMS_API_URL`: Default `http://localhost:8000`
   - `DEFAULT_LIMIT`: Default `5` results
   - `SEARCH_TYPE`: Default `semantic`

### 2. Test Connection

In OpenWebUI chat:
```
@bms_search.get_api_status()
```

Expected: ✅ API status with Qdrant/Ollama connection info

---

## 📚 Function Reference (10 Working Functions)

### **RECOMMENDED: search_hybrid()** ⭐

Best overall accuracy (80% on POC evaluation)

```python
@bms_search.search_hybrid("Where is the employee onboarding form?", limit=5)
```

**Use for**:
- Natural language queries
- Document code lookups (BMS-HUMR-FOR-001)
- General searches

---

### **Core Search (4 functions)**

#### 1. `search_semantic(query, limit=5)`
Pure semantic search using AI embeddings

```python
@bms_search.search_semantic("railway safety procedures")
```

**Best for**: Conceptual queries, synonyms, natural language

---

#### 2. `search_hybrid(query, limit=5)` ⭐ RECOMMENDED
Semantic + keyword matching (pseudo-BM25)

```python
@bms_search.search_hybrid("BMS-ENGI-FOR-003")
```

**Best for**: All-purpose search, document codes, specific terms

---

#### 3. `search_documents(query, limit, search_type, filters)`
Advanced search with full configurability

```python
@bms_search.search_documents(
    "safety procedures",
    limit=5,
    search_type="hybrid",
    filters={"department": "ISEC", "quality_score_min": 0.80}
)
```

**Best for**: Power users, complex filtering

---

#### 4. `compare_search_types(query, limit=3)`
Side-by-side comparison of semantic vs hybrid

```python
@bms_search.compare_search_types("material management")
```

**Best for**: Understanding which search type works better

---

### **Filtered Search (6 functions)**

#### 5. `search_by_document_type(query, document_type, limit=5)`
Filter by file type

```python
@bms_search.search_by_document_type("quality forms", "xlsx", limit=5)
```

**Types**: pdf, docx, pptx, xlsx, csv, txt

---

#### 6. `search_by_department(query, department, limit=5)`
Filter by BMS department

```python
@bms_search.search_by_department("employee forms", "HUMR")
```

**Departments**: HUMR, ENGI, ISEC, QHSE, PROC, FINA, BUSDEV

---

#### 7. `search_by_fleet_type(query, fleet_type, limit=5)`
Filter by railway fleet/train type

```python
@bms_search.search_by_fleet_type("maintenance procedures", "Cityjet")
```

**Fleet Types**: Cityjet, Railjet, R4600, etc.

---

#### 8. `search_by_standard(query, standard, limit=5)`
Filter by compliance standard

```python
@bms_search.search_by_standard("fire protection", "EN45545")
```

**Standards**: EN50155, EN45545, TSI, etc.

---

#### 9. `search_with_context(query, limit=5)`
Prioritize chunks with rich contextual descriptions

```python
@bms_search.search_with_context("complex procurement process")
```

**Best for**: Complex queries needing detailed context

---

#### 10. `search_high_quality(query, min_quality=0.80, limit=5)`
Filter by quality score

```python
@bms_search.search_high_quality("safety procedures", min_quality=0.85)
```

**Quality Range**: 0.0 - 1.0 (higher = better quality)

---

### **Utility (1 function)**

#### 11. `get_api_status()`
Check BMS API health

```python
@bms_search.get_api_status()
```

---

## 💡 Usage Examples

### Example 1: Find a Specific Form

**Query**: "Where is the company credit card expense form?"

```python
@bms_search.search_hybrid("company credit card expense form")
```

**Expected**: BMS-FINA-FOR-006 Company Credit Card Expense Form.xlsx

---

### Example 2: Find Department Procedures

**Query**: "Show me all human resources procedures"

```python
@bms_search.search_by_department("procedures", "HUMR", limit=10)
```

---

### Example 3: Find High-Quality Safety Documents

**Query**: "Find high-quality safety management documents"

```python
@bms_search.search_high_quality("safety management", min_quality=0.85, limit=5)
```

---

### Example 4: Compare Search Methods

**Query**: "Which search works better for 'risk assessment'?"

```python
@bms_search.compare_search_types("risk assessment", limit=3)
```

---

## 📊 Performance

**POC Evaluation Results** (50 diverse queries):
- **Top-5 Accuracy**: 80%
- **Top-3 Accuracy**: 74%
- **Top-1 Accuracy**: 64%
- **Best Categories**: Finance (100%), Quality (100%), Procurement (100%), Business Dev (100%)

**Response Time**: Typically 1-3 seconds per query

---

## ⚠️ Known Limitations

### Advanced Functions (9) - Not Yet Available

These functions are **planned for MVP/Production** but currently fallback to hybrid search:

- `search_with_session()` - Conversational context
- `search_expanded()` - Query expansion
- `search_with_explanation()` - Score breakdowns
- `search_synthesized()` - Multi-document synthesis
- `search_by_train_id()` - Train-specific search
- `search_by_component()` - Component search
- `search_by_date_range()` - Temporal filtering
- `search_latest_versions()` - Version filtering
- `search_multiple_queries()` - Batch queries
- `search_with_facets()` - Faceted results

**Note**: These functions won't break - they gracefully fallback to hybrid search.

---

## 🔧 Troubleshooting

### Issue: "Cannot connect to BMS API"

**Solution**: Check that BMS API is running on `http://localhost:8000`

```bash
# Test API directly
curl http://localhost:8000/health

# Expected response: {"status": "healthy", "services": {...}}
```

---

### Issue: "No results found"

**Possible Causes**:
1. Query too specific - try broader terms
2. Document not indexed - check document inventory
3. Typo in document code - verify spelling

**Solution**: Try hybrid search with broader terms

---

### Issue: "Search timed out"

**Solution**: Increase timeout in valves (default 30s)

---

## 📋 POC Integration Testing (T023)

Run automated tests:

```bash
cd /workspace/001-bms-agent
python tests/integration/test_openwebui_tool.py
```

**Expected**: All 11 tests pass (100% pass rate)

**Pass Criteria**:
- ✅ API status check works
- ✅ All 4 core search functions return results
- ✅ All 6 filtered search functions work correctly
- ✅ Response time <5 seconds per query
- ✅ No crashes or exceptions

---

## 🎯 Best Practices

### 1. Use Hybrid Search by Default
```python
@bms_search.search_hybrid(query)  # 80% accuracy
```

### 2. Add Filters for Precision
```python
@bms_search.search_by_department(query, "HUMR")  # Only HR docs
```

### 3. Increase Limit for Exploration
```python
@bms_search.search_hybrid(query, limit=10)  # More results
```

### 4. Use Quality Filter for Important Queries
```python
@bms_search.search_high_quality(query, min_quality=0.85)  # Best quality only
```

### 5. Compare Search Types When Uncertain
```python
@bms_search.compare_search_types(query)  # See both methods
```

---

## 📈 Roadmap to 95% Accuracy

**Current**: 80% (POC Complete)  
**Target**: 95% (Production)

**Path Forward**:
1. **Missing Document Recovery** (+6-8%) - Recover 4 missing forms
2. **Full BM25 Integration** (+2-3%) - Complete keyword matching
3. **Metadata Boosting** (+3-5%) - Expose reranking to OpenWebUI
4. **Domain Fine-tuning** (+3-5%) - Railway-specific embeddings

**Estimated Effort**: 30-40 hours

---

## ✅ POC Signoff Checklist

- [x] Tool accuracy claims corrected (80% not 96%)
- [x] Working functions clearly marked (10/21)
- [x] Advanced functions documented as planned
- [x] Integration test script created
- [x] Quick reference guide complete
- [ ] All 11 tests pass (run test_openwebui_tool.py)
- [ ] Manual testing in OpenWebUI complete
- [ ] Response times acceptable (<5s)

---

**Last Updated**: 2025-10-04 20:20 UTC  
**Status**: Ready for T023 Integration Testing  
**Next**: Run automated tests and manual validation in OpenWebUI
