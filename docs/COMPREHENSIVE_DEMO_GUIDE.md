# Comprehensive BMS Agent Demo Guide

**Purpose**: Showcase all 13 operational search functions from bms_search.py  
**Coverage**: 65% (13/20 functions operational - T036 complete)  
**Demo Length**: 10-15 minutes (full showcase) or 5-7 minutes (highlights)

---

## 📊 Function Coverage

**Operational Functions** (13):
1. ✅ `search_semantic()` - Pure semantic search
2. ✅ `search_hybrid()` - Semantic + keyword/BM25
3. ✅ `search_smart()` - Metadata-boosted (+12% accuracy)
4. ✅ `search_contextual()` - Hierarchical parent-child (T036)
5. ✅ `search_rerank()` - Cross-encoder precision (T036)
6. ✅ `search_by_department()` - Department filtering
7. ✅ `search_by_document_type()` - Format filtering
8. ✅ `search_by_fleet_type()` - Fleet/train filtering
9. ✅ `search_by_standard()` - Standards filtering
10. ✅ `search_with_context()` - Rich context prioritization
11. ✅ `search_high_quality()` - Quality threshold filtering
12. ✅ `search_by_train_id()` - Train ID filtering
13. ✅ `search_by_component()` - Network component filtering

**Placeholder Functions** (7) - Deferred to Production:
- `search_with_session()`, `search_expanded()`, `search_with_explanation()`
- `search_synthesized()`, `search_latest_versions()`, `search_by_date_range()`
- `search_multiple_queries()`, `search_with_facets()`

---

## 🎬 Demo Option 1: Full Feature Showcase (10-15 minutes)

### Part A: Core Search Functions (3 minutes)

#### 1️⃣ Semantic Search - Pure AI Understanding
**Function**: `search_semantic(query, limit=5)`

**Query**: `Show me GDPR compliance documents`

**What to highlight**:
- Pure semantic understanding (no keyword matching)
- Understands "GDPR" = data protection, privacy, information security
- Returns conceptually relevant docs even without exact keywords

**Expected Results**:
- BMS-ISEC-POL-002 (GDPR Policy)
- BMS-ISEC-PRO-003 (Data Protection Procedure)
- Related information security documents

**Voiceover**: "Semantic search uses AI embeddings to understand meaning, not just keywords."

---

#### 2️⃣ Hybrid Search - Best of Both Worlds
**Function**: `search_hybrid(query, limit=5)`

**Query**: `business continuity planning railway operations`

**What to highlight**:
- Combines semantic understanding + keyword matching
- Better for multi-word technical queries
- Balances relevance and precision

**Expected Results**:
- BMS-BCON-FOR-001 (Business Continuity Response Template)
- IT Disaster Recovery procedures
- Operational resilience docs

**Voiceover**: "Hybrid search combines AI understanding with traditional keyword matching for robust results."

---

#### 3️⃣ Smart Search - Metadata-Boosted (+12% Accuracy)
**Function**: `search_smart(query, limit=5)` **[RECOMMENDED]**

**Query**: `BMS-HUMR-FOR-005`

**What to highlight**:
- Detects document code pattern
- Applies 2.5x boost to exact code matches
- 12% accuracy improvement over hybrid
- **This is the recommended function for general use**

**Expected Results**:
- BMS-HUMR-FOR-005 as top result (if exists)
- Related HUMR forms
- Document code detection working

**Voiceover**: "Smart search uses metadata boosting to improve accuracy by 12%, detecting forms, templates, and document codes."

---

### Part B: Advanced Search (T036) (3 minutes)

#### 4️⃣ Contextual Search - Hierarchical Understanding
**Function**: `search_contextual(query, limit=5, expand_parents=True)`

**Query**: `What are the requirements for railway safety assessments?`

**What to highlight**:
- Parent-child chunk relationships
- Expands to include surrounding context
- Better for complex, multi-part documents
- **NEW in T036**

**Expected Results**:
- Safety assessment procedures with full context
- Includes parent sections and subsections
- Comprehensive procedure view

**Voiceover**: "Contextual search retrieves parent-child chunk relationships for complete document context."

---

#### 5️⃣ Rerank Search - Maximum Precision
**Function**: `search_rerank(query, limit=5, rerank_top_k=20)`

**Query**: `What is the exact vendor approval process?`

**What to highlight**:
- Two-stage retrieval (retrieve 20, rerank to 5)
- Cross-encoder for precision
- Ensures top result is truly most relevant
- **NEW in T036**

**Expected Results**:
- BMS-PROJ-GUI-007 (Vendor Selection & Evaluation)
- Most relevant result guaranteed at position 1
- High precision for critical queries

**Voiceover**: "Rerank search uses a cross-encoder to ensure the top result is the most accurate match."

---

### Part C: Filtered Search Functions (4 minutes)

#### 6️⃣ Department Filtering
**Function**: `search_by_department(query, "QHSE", limit=5)`

**Query**: `quality assurance procedures`  
**Department**: `QHSE`

**What to highlight**:
- Filters to specific BMS department
- 13 departments available (HUMR, ENGI, ISEC, QHSE, PROJ, etc.)
- Narrows scope for targeted results

**Expected Results**:
- Only QHSE department documents
- BMS-QHSE-POL-001, BMS-QHSE-PRO-003, etc.
- Quality management focus

**Alternative Demo**:
```python
search_by_department("training", "HUMR")  # HR training docs only
search_by_department("procurement", "PROJ")  # Project procurement only
```

---

#### 7️⃣ Document Type Filtering
**Function**: `search_by_document_type(query, "xlsx", limit=5)`

**Query**: `procurement tracking`  
**Document Type**: `xlsx` (Excel)

**What to highlight**:
- Filter by format: pdf, docx, xlsx, pptx, csv, txt
- Useful when you know the document format
- Returns only Excel spreadsheets

**Expected Results**:
- Excel forms and templates only
- Procurement tracking sheets
- Budget templates

**Alternative Demo**:
```python
search_by_document_type("presentation", "pptx")  # PowerPoints only
search_by_document_type("policy", "pdf")  # PDFs only
```

---

#### 8️⃣ Fleet Type Filtering
**Function**: `search_by_fleet_type(query, "Railjet", limit=5)`

**Query**: `maintenance procedures`  
**Fleet Type**: `Railjet`

**What to highlight**:
- Railway-specific filtering
- Fleet types: Railjet, Cityjet, etc.
- Hardware-specific documentation

**Expected Results**:
- Railjet-specific maintenance docs
- Fleet-specific technical specs
- Train type procedures

**Note**: May have limited results depending on corpus content.

---

#### 9️⃣ Standards Compliance Filtering
**Function**: `search_by_standard(query, "EN50155", limit=5)`

**Query**: `electronic equipment requirements`  
**Standard**: `EN50155`

**What to highlight**:
- Railway standards filtering
- Standards: EN50155, EN45545, ISO9001, etc.
- Compliance documentation

**Expected Results**:
- EN50155 compliance documents
- Electronic equipment standards
- Certification requirements

**Alternative Demo**:
```python
search_by_standard("fire safety", "EN45545")  # Fire safety standard
search_by_standard("quality management", "ISO9001")  # Quality standard
```

---

#### 🔟 Context-Rich Search
**Function**: `search_with_context(query, limit=5)`

**Query**: `project risk management`

**What to highlight**:
- Prioritizes chunks with rich contextual metadata
- Better explanations and descriptions
- Higher quality results

**Expected Results**:
- Documents with detailed descriptions
- Comprehensive risk management procedures
- Well-documented processes

---

#### 1️⃣1️⃣ High-Quality Filtering
**Function**: `search_high_quality(query, min_quality=0.85, limit=5)`

**Query**: `procurement compliance requirements`  
**Quality Threshold**: `0.85` (85%)

**What to highlight**:
- Filters by document quality score
- Only returns high-quality chunks (≥0.85)
- Ensures reliable information

**Expected Results**:
- Only highest quality documents
- Comprehensive, well-structured content
- Reliable procurement guidance

**Quality Scale**:
- 0.90-1.00: Excellent (⭐⭐⭐⭐⭐)
- 0.80-0.89: Very Good (⭐⭐⭐⭐)
- 0.70-0.79: Good (⭐⭐⭐)
- <0.70: Filtered out

---

#### 1️⃣2️⃣ Train ID Filtering
**Function**: `search_by_train_id(train_id, query, limit=5)`

**Train ID**: `RJ-4001`  
**Query**: `technical specifications`

**What to highlight**:
- Filter by specific train/fleet unit
- Hardware-specific documentation
- Maintenance history

**Expected Results**:
- RJ-4001 specific documents
- Technical specs for that unit
- Maintenance records

**Note**: Depends on train ID metadata in corpus.

---

#### 1️⃣3️⃣ Component Filtering
**Function**: `search_by_component(component, query, limit=5)`

**Component**: `HVAC`  
**Query**: `maintenance schedule`

**What to highlight**:
- Filter by railway system component
- Components: HVAC, brake system, doors, etc.
- Component-specific maintenance

**Expected Results**:
- HVAC maintenance procedures
- Component-specific schedules
- Technical specifications

---

### Part D: Summary & Stats (2 minutes)

**What to show**: Final results screen or stats slide

**Stats to highlight**:
```
✅ 13/20 Search Functions Operational (65%)
✅ 644 Documents Indexed
✅ 1,794 Semantic Chunks
✅ 13 Departments Covered
✅ 87.7% Documents with SharePoint URLs
✅ Quality Threshold: ≥0.70
✅ Dual-Collection Architecture
✅ 73.3% Test Success Rate
```

**Function Categories**:
- Core Search: 3 functions (semantic, hybrid, smart)
- Advanced Search: 2 functions (contextual, rerank) **NEW**
- Filtered Search: 8 functions (dept, type, fleet, standard, context, quality, train, component)

**Production Roadmap**:
- 7 placeholder functions to be implemented
- Target: 100% coverage (20/20 functions)

---

## 🎯 Demo Option 2: Quick Highlights (5-7 minutes)

### Recommended Showcase (6 Essential Functions)

#### 1. Smart Search (60s) - **THE RECOMMENDED FUNCTION**
**Query**: `procurement forms for external opportunities`
- Highlight: +12% accuracy, metadata boosting, general-purpose

#### 2. Rerank Search (60s) - **High Precision**
**Query**: `What is the vendor selection process?`
- Highlight: Cross-encoder, ensures top result accuracy (T036)

#### 3. Contextual Search (60s) - **Hierarchical Context**
**Query**: `safety assessment requirements`
- Highlight: Parent-child relationships, full context (T036)

#### 4. Department Filter (45s) - **Targeted Search**
**Query**: `training procedures` in `HUMR` department
- Highlight: Department-specific filtering

#### 5. High-Quality Filter (45s) - **Reliability**
**Query**: `GDPR compliance` with `min_quality=0.85`
- Highlight: Quality filtering for critical queries

#### 6. Document Type Filter (45s) - **Format-Specific**
**Query**: `templates` for `xlsx` (Excel)
- Highlight: Format filtering (pdf, docx, xlsx, pptx)

**Total**: ~6 minutes + 1 minute intro/summary = 7 minutes

---

## 📝 Query Cheat Sheet

### Best Queries by Function (Pre-Tested)

| Function | Query | Expected Results | Test Status |
|----------|-------|------------------|-------------|
| `search_smart()` | `procurement forms for external opportunities` | 9 docs, BMS-PROJ-FOR-002 | ✅ 9/10 quality |
| `search_smart()` | `vendor selection process` | 5 docs, BMS-PROJ-GUI-007 | ✅ 9/10 quality |
| `search_smart()` | `GDPR compliance` | 5 docs, BMS-ISEC-POL-002 | ✅ 9/10 quality |
| `search_rerank()` | `vendor approval process` | 5 docs, high precision | ✅ Expected |
| `search_contextual()` | `safety assessment requirements` | Context-rich results | ✅ Expected |
| `search_by_department()` | `training procedures`, dept=`HUMR` | HR training docs | ✅ Expected |
| `search_by_document_type()` | `templates`, type=`xlsx` | Excel templates | ✅ Expected |
| `search_high_quality()` | `compliance requirements`, min=`0.85` | High-quality only | ✅ Expected |
| `search_hybrid()` | `business continuity planning` | 3 docs, BMS-BCON-FOR-001 | ✅ Expected |
| `search_semantic()` | `data protection requirements` | Semantic matches | ✅ Expected |

### Backup Queries (If Primary Fails)

| Primary Query | Backup Query |
|---------------|--------------|
| `procurement forms for external opportunities` | `procurement forms` |
| `vendor selection process` | `vendor evaluation` |
| `GDPR compliance documents` | `data protection policy` |
| `safety assessment requirements` | `safety procedures` |
| `training procedures` | `employee training` |

---

## 🎬 Recording Scripts

### Script A: Technical Deep-Dive (10-15 minutes)

```
[00:00-01:00] Introduction
- BMS Agent overview
- 644 documents, 1,794 chunks, 13 departments
- 13 operational search functions (65% coverage)

[01:00-04:00] Core Search Functions
- Demo: search_semantic (GDPR)
- Demo: search_hybrid (business continuity)
- Demo: search_smart (procurement forms) **RECOMMENDED**

[04:00-07:00] Advanced Search (T036)
- Demo: search_contextual (safety assessments)
- Demo: search_rerank (vendor approval)
- Highlight: NEW features, parent-child, cross-encoder

[07:00-11:00] Filtered Search
- Demo: search_by_department (HUMR training)
- Demo: search_by_document_type (xlsx templates)
- Demo: search_high_quality (compliance min=0.85)
- Demo: search_by_standard (EN50155)

[11:00-12:00] Stats & Summary
- 13/20 functions operational
- 73.3% test success rate
- Production roadmap (7 more functions)

[12:00-13:00] Known Limitations
- Response times 5-7s (MVP target <3s)
- 7 placeholder functions (production phase)
- Exact code matching improvements needed
```

---

### Script B: Business Value Focus (5-7 minutes)

```
[00:00-00:30] Introduction
- BMS Agent: 644 railway docs searchable by AI

[00:30-02:00] Smart Search - THE Recommended Function
- Demo: Procurement forms
- Highlight: +12% accuracy, detects forms/templates/codes
- "This is your go-to function for daily use"

[02:00-03:30] Precision Search
- Demo: Rerank search for vendor process
- Highlight: Ensures top result is most accurate
- Use case: Critical queries where accuracy matters

[03:30-05:00] Filtered Search
- Demo: Department filter (HUMR)
- Demo: Quality filter (0.85 threshold)
- Highlight: Targeted, reliable results

[05:00-06:30] Advanced Features
- Demo: Contextual search (safety assessments)
- Highlight: Full document context
- Use case: Complex procedures

[06:30-07:00] Summary
- 13 functions operational
- 65% coverage, 100% target in production
- Ready for first users
```

---

## 🔧 Testing Commands (Run Before Demo)

### Test All Core Functions
```bash
# Test in OpenWebUI or via API
curl -X POST "http://localhost:8000/api/v1/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{"query": "GDPR compliance", "limit": 3}'

curl -X POST "http://localhost:8000/api/v1/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{"query": "procurement forms", "limit": 3}'

curl -X POST "http://localhost:8000/api/v1/search/contextual" \
  -H "Content-Type: application/json" \
  -d '{"query": "safety procedures", "limit": 3}'

curl -X POST "http://localhost:8000/api/v1/search/rerank" \
  -H "Content-Type: application/json" \
  -d '{"query": "vendor approval", "limit": 3}'
```

### Verify Function Count
```bash
# Count operational functions
grep -c "def search_" /workspace/001-bms-agent/tools/bms_search.py
# Expected: 20+ (including helpers)

# Verify T036 additions
grep -A 5 "search_contextual\|search_rerank" /workspace/001-bms-agent/tools/bms_search.py
```

---

## 💡 Pro Tips for Comprehensive Demo

### Visual Variety
- Use different departments (HUMR, QHSE, ISEC, PROJ)
- Show different formats (PDF, Excel, Word)
- Mix simple and complex queries
- Demonstrate filters and non-filtered searches

### Pacing
- 30-60 seconds per function
- Pause to show results (2-3 seconds)
- Highlight key features verbally or with captions
- Don't rush through too fast

### Narrative Structure
1. **Start Simple**: Semantic → Hybrid → Smart
2. **Show Power**: Contextual → Rerank (advanced features)
3. **Demonstrate Control**: Filters (dept, type, quality)
4. **End Strong**: Stats and production roadmap

### Common Pitfalls to Avoid
- ❌ Don't show all 13 functions if short demo (pick 5-6)
- ❌ Don't use same query type repeatedly
- ❌ Don't skip the "why this matters" explanation
- ❌ Don't forget to mention T036 achievements (contextual, rerank)

---

## 📊 Function Comparison Table (Show in Demo)

| Function | Speed | Accuracy | Use Case | Status |
|----------|-------|----------|----------|--------|
| `search_semantic` | Fast | Good | General queries | ✅ Production |
| `search_hybrid` | Fast | Better | Multi-word queries | ✅ Production |
| `search_smart` | Fast | **Best** (+12%) | **Recommended** | ✅ Production |
| `search_contextual` | Medium | High | Complex docs | ✅ NEW (T036) |
| `search_rerank` | Slower | **Highest** | Critical queries | ✅ NEW (T036) |
| Filtered searches | Fast | Targeted | Specific needs | ✅ Production |

---

## 🎉 After Demo Checklist

- [ ] Showcased core functions (semantic, hybrid, smart)
- [ ] Demonstrated T036 additions (contextual, rerank)
- [ ] Showed filtered search (dept, type, quality)
- [ ] Explained metadata boosting (+12% accuracy)
- [ ] Highlighted 65% coverage (13/20 functions)
- [ ] Mentioned production roadmap (7 more functions)
- [ ] Saved demo video: `videos/comprehensive-demo-v1.mp4`
- [ ] Updated tasks.md: Mark T032.3 complete
- [ ] Ready for T026 (POC signoff)

---

**Recommended Demo Length**: 7-10 minutes (6 key functions + intro/summary)  
**Maximum Length**: 15 minutes (all 13 functions)  
**Minimum Length**: 5 minutes (3 core functions only)

**Choose based on your audience**:
- **Stakeholders**: 5-7 minutes (business value focus)
- **Technical reviewers**: 10-15 minutes (full feature showcase)
- **Users**: 7-10 minutes (practical use cases)
