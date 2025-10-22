# BMS Search Metadata Filtering Feature

## Overview

The BMS Search system now supports comprehensive metadata filtering across all search functions. This allows users to filter search results by department, category, document type, and other metadata fields.

## Implementation Status

✅ **COMPLETE** - All components have been implemented and tested

## Changes Made

### 1. API Layer (`bms-agent/api/processor_wrapper.py`)

**Updated Methods:**
- `search_documents()` - Added `filters` parameter to accept metadata filters
- `_build_filter()` - New method to convert filter dict to Qdrant Filter objects

**Filter Logic:**
- Single values: `{"department": "QHSE"}` → Exact match filter
- Multiple values (OR): `{"department": ["QHSE", "HR"]}` → Matches any value
- Multiple fields (AND): `{"department": "QHSE", "category": "Form"}` → All conditions must match

**Code Example:**
```python
# Single department filter
results = await processor.search_documents(
    query="safety procedures",
    limit=10,
    filters={"department": "QHSE"}
)

# Multiple departments (OR logic)
results = await processor.search_documents(
    query="risk assessment",
    limit=10,
    filters={"department": ["QHSE", "Projects"]}
)

# Combined filters (AND logic)
results = await processor.search_documents(
    query="template",
    limit=10,
    filters={
        "department": "Bid Development",
        "category": "Form"
    }
)
```

### 2. API Endpoints (`bms-agent/api/main.py`)

**Updated:**
- `SemanticSearchRequest` - Added `filters` field to request model
- `/api/v1/search/semantic` - Passes filters to processor
- `/api/v1/search/hybrid` - Passes filters to processor

**Fixed:**
- Changed relative import to absolute import to fix startup issues
- API now starts correctly with `python3 -m uvicorn main:app`

### 3. OpenWebUI Tool (`bms_search.py`)

**Updated Functions:**
All three search functions now accept a `filters` parameter:
- `search_smart(query, limit, filters, ...)`
- `search_semantic(query, limit, filters, ...)`
- `search_hybrid(query, limit, filters, ...)`

**Filter Merging:**
- Explicit filters passed to the function take precedence
- User preference filters (from UserValves) are applied only if no explicit filter exists
- Example: If user has preferred_departments=["HR"] but calls with filters={"department": "QHSE"}, QHSE is used

**Code Example:**
```python
# OpenWebUI tool call with filters
result = await tools.search_smart(
    query="safety procedures",
    filters={"department": "QHSE"},
    limit=10
)
```

### 4. System Prompt (`SYSTEM_PROMPT_ADDITION.md`)

**Added Sections:**
- Metadata Filtering overview and available fields
- Filter usage examples (single, multiple, combined)
- When to use filters vs. when to answer from knowledge
- Quick reference guide with filter examples

## Available Filter Fields

The following metadata fields are available for filtering:

| Field | Description | Example Values |
|-------|-------------|----------------|
| `department` | Department that owns the document | "QHSE", "HR", "Bid Development", "Projects" |
| `category` | Document category | "Policy", "Procedure", "Form", "Template" |
| `document_name` | Document filename or code | "BMS-QHSE-FOR-035", "Risk Register" |
| `document_type` | File extension | "PDF", "XLSX", "DOCX" |
| `chunk_type` | Type of content chunk | "text", "table", "image" |

Additional fields available in metadata (50+ fields total):
- `file_name`, `document_id`, `chunk_index`
- `quality_score`, `has_context`, `context_similarity`
- `railway_metadata` (for railway-specific documents)
- `entities` (extracted entities like locations, organizations)

## Testing Results

### Test 1: Single Department Filter
```bash
Filter: {"department": "Bid Development"}
Query: "template"
Results: ✅ All 10 results from Bid Development
```

### Test 2: Multiple Departments (OR Logic)
```bash
Filter: {"department": ["Bid Development", "QHSE"]}
Query: "safety"
Results: ✅ Results only from specified departments
```

### Test 3: Combined Filters (AND Logic)
```bash
Filter: {"department": "QHSE", "category": "Form"}
Query: "assessment"
Results: ✅ Only QHSE documents with category=Form
```

## Usage Guidelines

### When to Use Metadata Filters

**DO use filters when:**
- User asks for department-specific documents: "show me QHSE safety procedures"
- User wants to narrow results: "find bid development risk templates"
- User specifies document type: "find HR forms about training"
- User mentions document codes: "find BMS-QHSE-FOR-035"

**DON'T use filters when:**
- User asks meta-questions: "which docs are available"
- User wants broad semantic search: "what are safety best practices"
- User asks general knowledge: "what is QHSE"

### Filter Syntax Examples

**Single Value:**
```python
{"department": "QHSE"}
```

**Multiple Values (OR):**
```python
{"department": ["QHSE", "HR", "Projects"]}
```

**Multiple Fields (AND):**
```python
{
    "department": "Bid Development",
    "category": "Form",
    "document_type": "XLSX"
}
```

**Partial Match (document_name):**
```python
{"document_name": "BMS-QHSE"}  # Matches all QHSE documents
```

## Architecture

```
┌─────────────────┐
│  OpenWebUI LLM  │
└────────┬────────┘
         │ User query + intent detection
         ▼
┌─────────────────────────────────┐
│  bms_search.py Tool             │
│  - search_smart()               │
│  - search_semantic()            │
│  - search_hybrid()              │
│  + filters parameter            │
└────────┬────────────────────────┘
         │ HTTP POST with filters
         ▼
┌─────────────────────────────────┐
│  BMS Agent API (FastAPI)        │
│  - /api/v1/search/semantic      │
│  - /api/v1/search/hybrid        │
│  + filters in request body      │
└────────┬────────────────────────┘
         │ filters → Qdrant Filter
         ▼
┌─────────────────────────────────┐
│  processor_wrapper.py           │
│  - search_documents()           │
│  - _build_filter()              │
│  + Filter construction logic    │
└────────┬────────────────────────┘
         │ Qdrant search with filter
         ▼
┌─────────────────────────────────┐
│  Qdrant Vector Database         │
│  Collection: nomad_bms_documents│
│  9,348 chunks, 311 documents    │
│  + Metadata-filtered search     │
└─────────────────────────────────┘
```

## Benefits

1. **Precision**: Filter results to specific departments or categories
2. **Performance**: Reduce search space by filtering before semantic search
3. **User Intent**: Better handle user queries like "show me QHSE docs about X"
4. **Flexibility**: Support both broad semantic search and targeted filtering
5. **Compatibility**: Backward compatible - filters are optional

## Files Modified

| File | Changes | Lines Changed |
|------|---------|---------------|
| `bms-agent/api/processor_wrapper.py` | Added filter support to search_documents(), added _build_filter() | ~50 |
| `bms-agent/api/main.py` | Added filters to request model, fixed imports | ~10 |
| `bms_search.py` | Added filters parameter to all 3 search functions | ~30 |
| `SYSTEM_PROMPT_ADDITION.md` | Added filter documentation and examples | ~40 |

## Next Steps

The metadata filtering feature is complete and ready to use. To enable it:

1. **API**: Already running with filter support on port 8000
2. **Tool**: bms_search.py updated with filter parameters
3. **LLM**: Add SYSTEM_PROMPT_ADDITION.md to OpenWebUI system prompt
4. **Testing**: Test with queries like "show me QHSE safety docs"

## Example User Queries

| User Query | Tool Call |
|------------|-----------|
| "Show me QHSE safety procedures" | `search_smart("safety procedures", filters={"department": "QHSE"})` |
| "Find bid development risk templates" | `search_smart("risk template", filters={"department": "Bid Development"})` |
| "HR training forms" | `search_smart("training", filters={"department": "HR", "category": "Form"})` |
| "Find BMS-QHSE-FOR-035" | `search_smart("risk assessment", filters={"document_name": "BMS-QHSE-FOR-035"})` |
| "Projects and QHSE risk docs" | `search_smart("risk", filters={"department": ["Projects", "QHSE"]})` |

---

**Implementation Date**: 2025-10-21
**Status**: ✅ Complete and tested
**Version**: BMS Search v4.3 (with metadata filtering)
