# Enhanced N8N Workflows for BMS Agent Integration

## Overview

Created 5 enhanced n8n workflows that leverage the full power of the BMS Agent API and Qdrant vector database with 1,794 searchable chunks across 420 documents.

## Available Workflows

### 1. Tool: Ask BMS (Enhanced)
**File:** `tool-ask-bms-enhanced.json`
**Webhook:** POST `/webhook/tool-ask-bms`
**Purpose:** Get LLM-generated answers with citations

**Features:**
- Full RAG pipeline (retrieval + generation)
- Citation tracking with source documents
- Confidence scoring
- Temperature control (0.0-1.0)
- Configurable chunk count (1-10)
- Metadata-rich responses

**Input Parameters:**
```json
{
  "query": "What are the brake safety procedures?",
  "max_chunks": 5,
  "temperature": 0.7,
  "min_score": 0.7,
  "filters": {
    "department": "QHSE",
    "is_process": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "answer": "Generated answer text...",
  "citations": [
    {
      "document_name": "BMS-QHSE-PRO-007.pdf",
      "document_type": "pdf",
      "department": "QHSE",
      "relevance_score": 0.92,
      "content_preview": "...",
      "document_url": "https://sharepoint.com/...",
      "quality_score": 0.98
    }
  ],
  "metadata": {
    "confidence": 0.85,
    "chunks_used": 3,
    "generation_time_ms": 1250
  }
}
```

---

### 2. Tool: Search Semantic
**File:** `tool-search-semantic.json`
**Webhook:** POST `/webhook/tool-search-semantic`
**Purpose:** Pure semantic/vector similarity search

**Features:**
- 768-dimensional embeddings (sentence-transformers/all-mpnet-base-v2)
- Quality score filtering (RAGAS scores 0.94-1.0)
- Relevance score threshold
- Rich metadata extraction
- Entity and keyword extraction
- Railway-specific filters

**Input Parameters:**
```json
{
  "query": "train brake configuration",
  "limit": 10,
  "min_score": 0.7,
  "min_quality": 0.95,
  "filters": {
    "department": "Engineering",
    "fleet_type": "Class 395",
    "document_type_category": "process"
  }
}
```

**Response Includes:**
- Document metadata (name, type, department, category)
- Content with preview
- Relevance and quality scores
- Hierarchy information (parent/child chunks)
- Railway-specific fields (fleet_type, train_id, network_component)
- Document flags (is_process, is_form, is_template)
- ISO standard compliance
- Extracted entities, keywords, technical terms
- SharePoint URLs

---

### 3. Tool: Search Hybrid
**File:** `tool-search-hybrid.json`
**Webhook:** POST `/webhook/tool-search-hybrid`
**Purpose:** Combined vector + keyword search

**Features:**
- Weighted combination of semantic and lexical search
- Configurable vector/keyword balance
- Candidate multiplier for precision
- Best for technical terms and acronyms

**Input Parameters:**
```json
{
  "query": "VLAN configuration procedure",
  "limit": 10,
  "vector_weight": 0.7,
  "keyword_weight": 0.3,
  "candidate_multiplier": 3,
  "filters": {
    "network_component": "VLAN"
  }
}
```

**Response:**
- Separate vector and keyword scores
- Combined relevance score
- Weight distribution used
- Keyword matches highlighted

---

### 4. Tool: Search by Metadata Filters
**File:** `tool-search-by-metadata.json`
**Webhook:** POST `/webhook/tool-search-metadata`
**Purpose:** Search filtered by document attributes

**Supported Filters:**

**Department:**
- QHSE
- Engineering
- Operations
- Finance
- HR

**Document Type Category:**
- process
- form
- template
- policy
- procedure
- manual

**Boolean Flags:**
- `is_process`: true/false
- `is_form`: true/false
- `is_template`: true/false

**Railway-Specific:**
- `fleet_type`: "Class 395", "Class 707", etc.
- `train_id`: Specific train identifier
- `network_component`: "VLAN", "Brake System", etc.
- `configuration_type`: Technical configuration

**Standards:**
- `standard_compliance`: "ISO 27001", "ISO 9001", etc.

**Processing:**
- `processing_profile`: "railway", "technical", "general"

**Example:**
```json
{
  "query": "safety procedures",
  "filters": {
    "department": "QHSE",
    "is_process": true,
    "standard_compliance": "ISO 45001"
  },
  "limit": 20
}
```

---

### 5. Tool: Contextual Search
**File:** `tool-contextual-search.json`
**Webhook:** POST `/webhook/tool-contextual-search`
**Purpose:** Search with hierarchical parent-child context

**Features:**
- Leverages Qdrant's parent-child chunk relationships
- Returns surrounding context from document
- Maintains document hierarchy
- Better for understanding document structure

**Qdrant Hierarchy:**
- **full_doc_embedding**: Complete document (768-dim, on-disk)
- **parent_embedding**: Major sections (768-dim)
- **child_embedding**: Subsections (768-dim, on-disk)
- **chunk_embedding**: Individual chunks (768-dim)

**Input Parameters:**
```json
{
  "query": "emergency procedures",
  "context_window": 2,
  "limit": 5
}
```

**Response Includes:**
- Main chunk content
- Parent chunk ID and content
- Surrounding context (±2 chunks)
- Contextual description
- Hierarchy level (parent/child/chunk)
- Full document structure

---

## Qdrant Metadata Schema

### Available Metadata Fields:

**Document Identification:**
- `document_id`: Unique document identifier
- `document_name`: Full filename
- `document_type`: pdf, docx, xlsx
- `document_type_category`: process, form, template, policy, procedure
- `document_url`: SharePoint URL
- `document_version`: Version number

**Organization:**
- `department`: QHSE, Engineering, Operations, etc.
- `standard_compliance`: ISO standards (27001, 9001, 14001, 45001)

**Content Structure:**
- `chunk_id`: Unique chunk identifier
- `chunk_index`: Position in document
- `chunk_size`: Character count
- `chunk_type`: parent/child/chunk
- `hierarchy_level`: Structural level
- `parent_chunk_id`: Reference to parent
- `has_context`: Boolean flag

**Content Analysis:**
- `entities`: Extracted named entities
- `keywords`: Top keywords
- `technical_terms`: Domain-specific terms
- `contextual_description`: Context summary
- `surrounding_context`: Adjacent content

**Railway-Specific:**
- `fleet_type`: Train class/model
- `train_id`: Specific train
- `network_component`: System component
- `configuration_type`: Technical config

**Document Properties:**
- `is_process`: Boolean
- `is_form`: Boolean
- `is_template`: Boolean

**Quality Metrics:**
- `quality_score`: RAGAS score (0-1)
- `processing_version`: "v4.0_enhanced"
- `processing_profile`: railway/technical/general
- `processing_timestamp`: ISO timestamp

**Search Configuration:**
- `search_type`: hybrid/semantic
- `late_chunking_applied`: Boolean
- `context_type`: document_aware/section_aware

---

## BMS API Endpoints Summary

### Core Search Endpoints:
- `/api/v1/ask` - RAG with answer generation
- `/api/v1/search/semantic` - Pure vector search
- `/api/v1/search/hybrid` - Vector + keyword
- `/api/v1/search/contextual` - With document hierarchy
- `/api/v1/search/rerank` - Re-rank results

### Document Management:
- `/api/v1/documents/upload` - Sync upload
- `/api/v1/documents/upload/async` - Async upload
- `/api/v1/documents/status/{job_id}` - Check status
- `/api/v1/documents/{document_id}` - Get document
- `/api/v1/documents/queue/stats` - Queue statistics

### Monitoring:
- `/api/v1/monitoring/health` - System health
- `/api/v1/monitoring/quality` - Quality metrics
- `/api/v1/monitoring/alerts` - Active alerts
- `/api/v1/monitoring/trends` - Performance trends
- `/api/v1/monitoring/prometheus` - Prometheus metrics

### Cache:
- `/api/v1/cache/stats` - Cache statistics
- `/api/v1/cache/clear` - Clear cache
- `/api/v1/cache/invalidate-expired` - Cleanup

---

## Performance Characteristics

**Current BMS Agent Stats:**
- **1,794 searchable chunks**
- **420 documents processed**
- **100% success rate**
- **RAGAS scores: 0.94-1.0** (exceeds ≥0.70 target)
- **p95 latency: ≤100ms** (production target)
- **Retrieval accuracy: ≥95%**

**Qdrant Vector Embeddings:**
- 4 embedding types (full_doc, parent, child, chunk)
- 768 dimensions (all-mpnet-base-v2)
- Cosine distance metric
- Mixed on-disk/in-memory storage

---

## Usage in LangChain Agent

Upload these 5 workflows to n8n and configure them as tools in the LangChain agent:

**Tool Descriptions for Agent:**

1. **ask_bms** - "Get a direct answer to a question about railway systems, brake procedures, or technical documentation. Returns LLM-generated answer with source citations. Use when user wants a specific answer, not just documents."

2. **search_semantic** - "Search for relevant documents using semantic similarity. Returns ranked list of documents with metadata. Use when user wants to find documents or explore topics broadly."

3. **search_hybrid** - "Search using both semantic meaning and exact keyword matching. Best for technical terms, acronyms, or specific terminology. Use when query contains technical jargon."

4. **search_metadata** - "Filter documents by specific attributes like department, document type, fleet, or standards. Use when user specifies document characteristics (e.g., 'find all QHSE processes' or 'show Class 395 manuals')."

5. **search_contextual** - "Search with surrounding document context. Returns chunks with their hierarchical context (parent sections, surrounding content). Use when understanding document structure is important."

---

## Example Agent Queries

**Query:** "What are the emergency brake procedures for Class 395 trains?"
**Tools Used:**
1. `search_metadata` (filters: fleet_type="Class 395", is_process=true)
2. `ask_bms` (with results from metadata search)

**Query:** "Show me all QHSE forms related to visitor management"
**Tools Used:**
1. `search_metadata` (filters: department="QHSE", is_form=true, query="visitor management")

**Query:** "Explain VLAN configuration in the network"
**Tools Used:**
1. `search_hybrid` (good for technical term "VLAN")
2. `search_contextual` (to get surrounding context)
3. `ask_bms` (generate comprehensive answer)

**Query:** "Find ISO 27001 compliant security procedures"
**Tools Used:**
1. `search_metadata` (filters: standard_compliance="ISO 27001", is_process=true)

---

## Next Steps

1. **Upload workflows to n8n** - All 5 JSON files
2. **Activate workflows** - Enable webhook triggers
3. **Update LangChain agent** - Replace existing tools with these enhanced versions
4. **Test with complex queries** - Verify metadata filtering works
5. **Monitor performance** - Check BMS API metrics endpoint

## Files Created

- `tool-ask-bms-enhanced.json` - Enhanced RAG with citations
- `tool-search-semantic.json` - Semantic search with full metadata
- `tool-search-hybrid.json` - Hybrid vector+keyword search
- `tool-search-by-metadata.json` - Metadata-filtered search
- `tool-contextual-search.json` - Hierarchical context search

All workflows include comprehensive error handling, timeout configuration, and structured responses.
