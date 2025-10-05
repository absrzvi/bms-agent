# Explainability Feature Guide

**Feature**: `ENABLE_EXPLAINABILITY` valve  
**Added**: 2025-10-05  
**Type**: Global toggle for detailed search explanations

---

## 🎯 Purpose

Enable detailed explanations for every search result showing:
- **Score breakdown** (relevance + quality)
- **Matched entities** (people, places, organizations, dates)
- **Technical terms** found in the document
- **Metadata tags** (Form, Template, Process, etc.)
- **Chunk position** (chunk index, hierarchy level)

This helps users understand **WHY** a document was retrieved and **HOW** the relevance score was calculated.

---

## 🔧 How to Enable

### Option 1: OpenWebUI Admin Panel (Recommended)

1. Open OpenWebUI at http://localhost:3000
2. Go to **Admin Panel** → **Tools**
3. Find **BMS Agent Search - Enhanced v3.0**
4. Click **Settings** (⚙️ icon)
5. Find **ENABLE_EXPLAINABILITY** valve
6. Set to **`True`**
7. Click **Save**
8. **Reload tool** in the admin panel

### Option 2: Edit Tool File Directly

Edit `/workspace/openwebui/data/tools/bms_search.py`:

```python
ENABLE_EXPLAINABILITY: bool = Field(
    default=True,  # Change False to True
    description="Include detailed explanations in results"
)
```

Then restart OpenWebUI.

---

## 📊 What You'll See

### Before (ENABLE_EXPLAINABILITY = False)
```
**1. Visitor Management Process**
   📋 ID: BMS-QHSE-PRO-007
   📄 Type: PDF
   ✨ Quality: ⭐⭐⭐⭐☆ 85% (Very Good)
   🎯 Relevance: 94% (Very High)
   🏢 QHSE
   🔑 visitor, management, security, badge, escort
   🔗 URL: https://nomadrail.sharepoint.com/qms/...
   
   📝 All visitors must be pre-registered...
```

### After (ENABLE_EXPLAINABILITY = True)
```
**1. Visitor Management Process**
   📋 ID: BMS-QHSE-PRO-007
   📄 Type: PDF
   ✨ Quality: ⭐⭐⭐⭐☆ 85% (Very Good)
   🎯 Relevance: 94% (Very High)
   🏢 QHSE
   🔑 visitor, management, security, badge, escort
   🔗 URL: https://nomadrail.sharepoint.com/qms/...
   
   📝 All visitors must be pre-registered...
   
   ──────────────────────────────────────────────────
   📊 **EXPLANATION**:
   📈 Score Breakdown:
      • Relevance Score: 0.942 (94% - Excellent match)
      • Quality Score: 0.850 (85%)
   🎯 Matched Entities: Organization: Nomad Digital, Location: Reception
   🔬 Technical Terms: pre-registration, security clearance, visitor badge
   ⚡ Metadata Tags: Process, Rich Context
   📍 Position: Chunk #3 | Level: section
   ──────────────────────────────────────────────────
```

---

## 🔍 Explanation Components

### 📈 Score Breakdown
- **Relevance Score**: How well the document matches your query (0.0-1.0)
  - 0.90+ = Excellent match
  - 0.80-0.89 = Very good match
  - 0.70-0.79 = Good match
  - 0.60-0.69 = Decent match
  - 0.50-0.59 = Fair match
  - <0.50 = Weak match
- **Quality Score**: Document processing quality (0.70-1.0)
  - All documents pass ≥0.70 threshold
  - Higher = better text extraction, cleaner data

### 🎯 Matched Entities
Named entities found in the document:
- **Organization**: Company names (Nomad Digital, Bombardier, Siemens)
- **Location**: Places (Reception, Vienna, Austria)
- **Person**: Roles (visitor, employee, manager)
- **Date**: Time references (pre-2023, quarterly, annual)
- **Identifier**: Document codes, IDs

### 🔬 Technical Terms
Domain-specific terminology:
- Safety terms: risk assessment, PPE, hazard
- Railway terms: rolling stock, traction, braking system
- IT terms: encryption, authentication, firewall
- Business terms: procurement, vendor, approval

### ⚡ Metadata Tags
Document characteristics:
- **Form**: Official forms requiring completion
- **Template**: Reusable document templates
- **Process**: Process/procedure documents
- **Rich Context**: Has detailed contextual descriptions

### 📍 Position
Where in the document this chunk appears:
- **Chunk #X**: Sequential position (0-indexed)
- **Level**: Hierarchy (header, section, subsection, paragraph)

---

## 💡 Use Cases

### 1. Debugging Search Results
**Problem**: "Why did this document appear in my results?"  
**Solution**: Enable explanations to see matched keywords, entities, and score breakdown

### 2. Improving Query Quality
**Problem**: "My searches aren't finding what I need"  
**Solution**: See which terms are matching and adjust your query

### 3. Understanding Relevance
**Problem**: "Why is Document A ranked higher than Document B?"  
**Solution**: Compare score breakdowns and matched entities

### 4. Training Users
**Problem**: "Users don't know how to search effectively"  
**Solution**: Show explanations during training to teach search behavior

### 5. Quality Assurance
**Problem**: "Is the search working correctly?"  
**Solution**: Verify that high-quality, relevant documents score higher

---

## ⚙️ Performance Impact

**Minimal** - The valve only adds formatting logic:
- ✅ No additional API calls
- ✅ No database queries
- ✅ No computation overhead
- ✅ Same metadata already returned by API
- ⚠️ Slightly longer output (more text to read)

**Recommendation**: 
- **Enable** for: Training, debugging, QA testing, demos
- **Disable** for: Normal daily use (cleaner output)

---

## 🔄 Works With All Search Functions

Explanations work with **all 13 operational search functions**:

✅ Core Searches:
- `search_semantic()`
- `search_hybrid()`

✅ Smart Search:
- `search_smart()` (includes metadata boosts explanation)

✅ Connected Endpoints:
- `search_contextual()`
- `search_rerank()`

✅ Filtered Searches:
- `search_by_department()`
- `search_by_document_type()`
- `search_by_fleet_type()`
- `search_by_standard()`
- `search_with_context()`
- `search_high_quality()`
- `search_by_train_id()`
- `search_by_component()`

---

## 🚨 Important Notes

### 1. Tool Must Be Reloaded
After changing the valve setting, you MUST reload the tool in OpenWebUI:
- Admin Panel → Tools → BMS Agent Search → Reload/Refresh

### 2. Affects All Searches Globally
Once enabled, **every search** in **every chat** will show explanations.
- This is a global setting, not per-query
- Use for debugging/training sessions
- Disable for normal operations

### 3. LLM Still Summarizes
The LLM will still receive and process all this information, then provide a natural language answer with citations. The detailed explanations help the LLM understand the results better.

---

## 📝 Example Queries to Try

With explanations enabled, try these queries to see different aspects:

1. **"GDPR compliance documents"**
   - See: How entities and technical terms match
   - Expect: High relevance scores, Form/Process tags

2. **"BMS-ISEC-POL-002"**
   - See: Exact document code matching
   - Expect: Perfect 100% relevance score

3. **"employee onboarding forms"**
   - See: Metadata boosts (Form tag = 1.5x boost)
   - Expect: Form documents ranked higher

4. **"safety procedures for railway operations"**
   - See: Multiple technical terms, entity matches
   - Expect: Mix of QHSE and RENG documents

5. **"vendor selection process"**
   - See: Process tag, procurement-related entities
   - Expect: PROJ department documents

---

## 🎓 Training Tip

For new users, enable explanations for their first week, then disable once they're comfortable. This helps them learn:
- What makes a "good" search query
- How the system interprets their questions
- Why certain documents are more relevant

---

## 📚 References

- **Implementation**: `tools/bms_search.py` lines 1249-1304
- **Valve Definition**: `tools/bms_search.py` line 110-113
- **API Metadata**: All metadata comes from existing API response
- **No API Changes**: Uses existing `/api/v1/search/*` endpoints

---

**Status**: ✅ Fully implemented and ready to use  
**Version**: v3.0 (Enhanced BMS Agent Search)  
**Date**: 2025-10-05
