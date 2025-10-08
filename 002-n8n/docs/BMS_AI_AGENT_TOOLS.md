# BMS AI Agent Tools Reference

Quick reference for the 8 search tools available in the BMS AI Agent workflow.

## Tool Overview

| Tool | Purpose | Best For |
|------|---------|----------|
| ask_bms | General question answering | Natural language queries about railway docs |
| search_semantic | Vector similarity search | Conceptual/meaning-based queries |
| search_hybrid | Combined vector + keyword | Specific terms + conceptual understanding |
| search_contextual | Parent-child relationship search | Finding related sections/context |
| search_metadata | Filter by document properties | Department, type, version, date filters |
| search_version | Latest version retrieval | Getting most recent document revisions |
| search_faceted | Aggregated category results | Exploring documents by groupings |
| search_explained | Transparent scoring | Understanding why results match |

## Detailed Descriptions

### 1. ask_bms
**Purpose**: General-purpose question answering with conversational context
**Use When**: User asks natural language questions about railway documentation
**Data Searched**: All 1,794 BMS documents across departments (QHSE, HUMR, FINA, ISEC, RENG, SERV)
**Example**: "What are the safety procedures for emergency brake systems?"

### 2. search_semantic
**Purpose**: Pure vector similarity search using 768-dimensional embeddings
**Use When**: Looking for conceptually similar content, synonyms, related topics
**Data Searched**: Vector embeddings of all document chunks (7,936 vectors)
**Example**: "risk assessment methodologies" (finds "hazard evaluation", "safety analysis")

### 3. search_hybrid
**Purpose**: Combines semantic similarity with keyword matching
**Use When**: Need both exact term matches AND conceptual understanding
**Data Searched**: Dense vectors + sparse keyword vectors
**Example**: "VLAN configuration for emergency brake" (matches both "VLAN" keyword + brake concepts)

### 4. search_contextual
**Purpose**: Retrieves parent documents and related chunks for comprehensive context
**Use When**: Need full section context around a specific passage
**Data Searched**: Parent-child relationships in document hierarchy
**Example**: "show me the full section about this procedure" (gets surrounding context)

### 5. search_metadata
**Purpose**: Filter documents by structural properties
**Use When**: Looking for specific document types, departments, or versions
**Data Searched**: Document metadata (department, type, version, dates)
**Example Filters**:
- Department: QHSE, HUMR, FINA, ISEC, RENG, SERV
- Type: PROC (procedure), FORM, PLAN, SPEC, GUIDE
- Document codes: BMS-QHSE-PROC-001, etc.

### 6. search_version
**Purpose**: Returns only the latest version of matching documents
**Use When**: Ensuring users get current, not outdated information
**Data Searched**: Version-controlled document metadata
**Example**: "latest incident reporting procedure" (filters out v1.0, returns v2.1)

### 7. search_faceted
**Purpose**: Groups results by categories (department, type, topic)
**Use When**: Exploring document landscape, understanding coverage
**Data Searched**: Aggregations across all metadata fields
**Example**: "show me all QHSE documents grouped by type" (returns counts per category)

### 8. search_explained
**Purpose**: Returns results with detailed scoring explanations
**Use When**: Need transparency on why documents matched
**Data Searched**: Full scoring breakdown (vector score, keyword score, quality score)
**Example**: Shows "matched with 0.87 similarity, 3 keyword matches, quality 0.95"

## Tool Selection Decision Tree

The AI agent automatically selects the appropriate tool based on user intent:

```
User Query → Parse Intent → Select Tool:
├── General question? → ask_bms
├── Conceptual search? → search_semantic
├── Specific term + concept? → search_hybrid
├── Need full context? → search_contextual
├── Filter by properties? → search_metadata
├── Latest version only? → search_version
├── Explore categories? → search_faceted
└── Want scoring details? → search_explained
```

## Available Document Data

**Total Documents**: 1,794
**Total Vectors**: 7,936 (768-dimensional)
**Departments**: QHSE, HUMR, FINA, ISEC, RENG, SERV
**Document Types**: PROC, FORM, PLAN, SPEC, GUIDE, CHEC
**Naming Pattern**: BMS-[DEPT]-[TYPE]-[###]

**Sample Documents**:
- BMS-QHSE-PROC-004: Safety inspection procedures
- BMS-HUMR-FORM-012: Personnel evaluation form
- BMS-FINA-PLAN-007: Budget planning template
- BMS-ISEC-SPEC-003: Security system specifications
- BMS-RENG-PROC-018: Railway engineering standards
- BMS-SERV-GUID-021: Service maintenance guidelines

## Performance Characteristics

| Tool | Avg Latency | Result Count | Accuracy |
|------|-------------|--------------|----------|
| ask_bms | ~200ms | 3-5 results | High |
| search_semantic | ~100ms | 5-10 results | High |
| search_hybrid | ~150ms | 5-10 results | Very High |
| search_contextual | ~180ms | 1 parent + chunks | High |
| search_metadata | ~80ms | Variable | Exact |
| search_version | ~120ms | 1 per doc | Exact |
| search_faceted | ~200ms | Aggregations | N/A |
| search_explained | ~120ms | 5-10 results | High |

## Quality Filtering

All tools (except metadata/faceted) apply dual filtering:
- **Relevance Score** (min_score): Typically ≥ 0.7
- **Quality Score** (min_quality): RAGAS quality ≥ 0.95

This ensures high-quality, relevant results from the 1,794 document collection.
