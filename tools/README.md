# BMS Agent OpenWebUI Tools

Custom tools for integrating BMS Agent search capabilities into OpenWebUI chat interface.

## Tool Versions

### 🆕 **v3.0 - Enhanced RAG** (Recommended)
**File**: `bms_search_v3.py`  
**Functions**: 20 (11 core + 9 advanced)  
**System Prompt**: `docs/SYSTEM_PROMPT_BMS_AGENT_V3.md`

Advanced RAG capabilities with:
- ✅ **Conversational Context Tracking**: Multi-turn interactions with entity carryover
- ✅ **Query Expansion**: LLM-based query reformulation with Reciprocal Rank Fusion
- ✅ **Multi-Document Synthesis**: Cluster/timeline/hierarchy strategies
- ✅ **Retrieval Explainability**: Detailed score breakdowns and match explanations
- ✅ **Railway Ontology**: Train ID and component-specific search
- ✅ **Temporal Search**: Date filtering and version-aware retrieval
- ✅ **Batch Multi-Query**: Process multiple queries with aggregation
- ✅ **Faceted Search**: Result grouping by type, department, quality

### v2.0 - Metadata-Aware (Legacy)
**File**: `bms_search.py`  
**Functions**: 11 (basic search + filters)  
**System Prompt**: `docs/SYSTEM_PROMPT_BMS_AGENT.md`

Basic search with metadata-aware ranking:
- ✅ **Semantic Search**: AI-powered search using 768-d embeddings
- ✅ **Hybrid Search**: Combined semantic + keyword (BM25) search
- ✅ **Document Type Filtering**: Search within specific file types
- ✅ **Quality Filtering**: Filter by document quality scores
- ✅ **Configurable**: Adjustable search parameters via Valves
- ✅ **Health Monitoring**: Check BMS API status

## Overview

The BMS Search tools provide seamless access to railway documentation through OpenWebUI's chat interface, enabling users to search 420+ indexed documents (1,458 chunks) using semantic and hybrid search with advanced RAG capabilities.

## Installation

### 1. Install OpenWebUI in /workspace

```bash
# Create OpenWebUI directory
mkdir -p /workspace/openwebui
cd /workspace/openwebui

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install OpenWebUI
pip install open-webui

# Set data directory
export OPEN_WEBUI_DATA_DIR=/workspace/openwebui/data
```

### 2. Install BMS Search Tool

**For v3.0 (Recommended):**
```bash
# Copy v3 tool to OpenWebUI tools directory
mkdir -p /workspace/openwebui/data/tools
cp /workspace/001-bms-agent/tools/bms_search_v3.py \
   /workspace/openwebui/data/tools/

# Or create symlink
ln -s /workspace/001-bms-agent/tools/bms_search_v3.py \
      /workspace/openwebui/data/tools/bms_search_v3.py
```

**For v2.0 (Legacy):**
```bash
# Copy v2 tool to OpenWebUI tools directory
mkdir -p /workspace/openwebui/data/tools
cp /workspace/001-bms-agent/tools/bms_search.py \
   /workspace/openwebui/data/tools/

# Or create symlink
ln -s /workspace/001-bms-agent/tools/bms_search.py \
      /workspace/openwebui/data/tools/bms_search.py
```

### 3. Start OpenWebUI

```bash
cd /workspace/openwebui
source venv/bin/activate

# Start with custom data directory
export OPEN_WEBUI_DATA_DIR=/workspace/openwebui/data
open-webui serve --host 0.0.0.0 --port 3000
```

Access at: http://localhost:3000

## Configuration

### Valve Settings (v3.0)

Configure the tool through OpenWebUI's interface or by editing the Valves:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `BMS_API_URL` | `http://localhost:8000` | BMS Agent API base URL |
| `DEFAULT_LIMIT` | `5` | Default number of results |
| `SEARCH_TYPE` | `semantic` | Default search type |
| `HYBRID_WEIGHT_DENSE` | `0.7` | Dense vector weight (hybrid) |
| `HYBRID_WEIGHT_SPARSE` | `0.3` | Sparse vector weight (hybrid) |
| `QUALITY_THRESHOLD` | `0.0` | Minimum quality score filter |
| `ENABLE_QUERY_EXPANSION` | `True` | Enable automatic query expansion |
| `ENABLE_EXPLAINABILITY` | `False` | Include detailed explanations |
| `SESSION_TTL_MINUTES` | `30` | Session timeout for conversational context |
| `TIMEOUT` | `30` | Request timeout (seconds) |

## Usage

### In OpenWebUI Chat

Once installed, you can use the tool in your conversations:

#### 1. Semantic Search
```
Search for "business continuity planning"
```

#### 2. Hybrid Search
```
Use hybrid search to find "railway safety procedures"
```

#### 3. Document Type Filter
```
Search for "maintenance" in PDF documents only
```

#### 4. Check API Status
```
What's the status of the BMS API?
```

### Available Functions

## v3.0 Functions (20 Total)

### Core Search (4 functions)

#### `search_documents(query, limit, search_type, filters)`
General search with full configuration options.

#### `search_semantic(query, limit)`
Semantic search using AI embeddings. Best for conceptual queries.

#### `search_hybrid(query, limit)`
Hybrid search combining semantic and keyword matching. Best for specific terms.

#### `compare_search_types(query, limit)`
Compare semantic vs hybrid results side-by-side.

### Filtered Search (6 functions)

#### `search_by_document_type(query, document_type, limit)`
Filter by file type (pdf, docx, xlsx, etc.).

#### `search_by_fleet_type(query, fleet_type, limit)`
Filter by railway fleet (Railjet, Cityjet, R4600).

#### `search_by_standard(query, standard, limit)`
Filter by compliance standard (EN50155, EN45545, TSI).

#### `search_by_department(query, department, limit)`
Filter by BMS department (HUMR, ENGI, ISEC).

#### `search_with_context(query, limit)`
Prioritize chunks with rich contextual descriptions.

#### `search_high_quality(query, min_quality, limit)`
Filter by quality score (default: ≥0.80).

### Advanced Search - NEW in v3.0 (9 functions)

#### `search_with_session(query, session_id, limit)` 🆕
**Conversational context tracking** - Automatically disambiguates pronouns and carries over entities from previous queries.

**Example conversation:**
```
User: "Tell me about R4600 traction motor"
User: "What's its voltage?" ← Automatically understands "its" = R4600
```

#### `search_expanded(query, limit)` 🆕
**Query expansion** - Generates multiple query variations using LLM and combines results with Reciprocal Rank Fusion.

**Example:** "motor issues" → expands to "motor failures", "motor maintenance", "motor diagnostics"

#### `search_with_explanation(query, limit)` 🆕
**Retrieval explainability** - Shows detailed score breakdowns, matched keywords, and matched entities.

#### `search_synthesized(query, strategy, limit)` 🆕
**Multi-document synthesis** - Combines information across multiple documents.

**Strategies:** cluster (by document), timeline (chronological), hierarchy (by component type)

#### `search_by_train_id(train_id, query, limit)` 🆕
**Railway train search** - Search for specific train/fleet by ID (R4600, Cityjet, Railjet).

#### `search_by_component(component, query, limit)` 🆕
**Railway component search** - Search by component type (traction, braking, hvac, doors, coupling, pantograph, transformer, converter).

#### `search_by_date_range(query, after, before, limit)` 🆕
**Temporal filtering** - Find documents within specific date range (ISO format: "2024-01-01").

#### `search_latest_versions(query, limit)` 🆕
**Version-aware search** - Returns only the most recent version of each document.

#### `search_multiple_queries(queries, aggregation, limit)` 🆕
**Batch multi-query** - Process multiple queries simultaneously with aggregation (union/intersection/ranked_fusion).

**Example:** `["motor voltage", "motor current", "motor power"]` → comprehensive motor info

#### `search_with_facets(query, limit)` 🆕
**Faceted search** - Shows result distribution by document type, department, quality, fleet, standards.

### Utility (1 function)

#### `get_api_status()`
Check BMS API health and service connectivity.

## Example Queries

### Natural Language Queries

Users can ask questions naturally in the chat:

- "Find documents about business continuity"
- "Search for railway safety procedures"
- "What documents mention maintenance schedules?"
- "Show me PDF files about network operations"
- "Is the BMS search working?"

### Advanced Queries

For power users:

- "Use hybrid search to find 'emergency response' with quality above 0.7"
- "Search semantically for 'risk management' and show 10 results"
- "Find all DOCX files mentioning 'compliance'"

## Output Format

Search results are formatted with:

```
🔍 Found 3 results for: 'business continuity'

1. BMS-BCON-FOR-001-Business Continuity Response Template.docx
   📄 Type: docx | Quality: 0.85 | Relevance: 0.563
   📝 [Document excerpt preview...]

2. IT Disaster Notification & Recovery Process.pdf
   📄 Type: pdf | Quality: 0.72 | Relevance: 0.517
   📝 [Document excerpt preview...]

---
Search Type: Semantic
API: http://localhost:8000
```

## Troubleshooting

### Tool Not Appearing in OpenWebUI

1. Check tool file location:
   ```bash
   ls -la /workspace/openwebui/data/tools/bms_search.py
   ```

2. Verify OpenWebUI data directory:
   ```bash
   echo $OPEN_WEBUI_DATA_DIR
   ```

3. Restart OpenWebUI:
   ```bash
   pkill -f open-webui
   cd /workspace/openwebui && source venv/bin/activate
   export OPEN_WEBUI_DATA_DIR=/workspace/openwebui/data
   open-webui serve --host 0.0.0.0 --port 3000
   ```

### Search Returns No Results

1. Check BMS API is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Verify Qdrant has data:
   ```bash
   curl http://localhost:6333/collections/nomad_bms_documents
   ```

3. Test search directly:
   ```bash
   curl -X POST http://localhost:8000/api/v1/search/semantic \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "limit": 1}'
   ```

### Connection Errors

1. Check BMS API URL in Valves configuration
2. Ensure BMS API is accessible from OpenWebUI
3. Check firewall/network settings

## Integration with BMS Agent

The tool integrates with:

- **BMS API**: http://localhost:8000
- **Qdrant**: 448 indexed chunks
- **Search Types**: Semantic & Hybrid
- **Document Formats**: PDF, DOCX, PPTX, XLSX, CSV, TXT

## Performance

- **Search Latency**: <100ms p95
- **Concurrent Users**: Supports 20-100 users
- **Result Quality**: 0.714 average quality score
- **Coverage**: 147 documents, 448 chunks

## Security

- **POC Mode**: No authentication required
- **Production**: Configure API key in Valves
- **Rate Limiting**: 60 req/min per IP (API level)

## Support

- **Documentation**: /root/CascadeProjects/windsurf-project/001-bms-agent/docs
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Version

- **Tool Version**: 1.0.0
- **BMS Agent**: 1.0.0-rc1
- **Last Updated**: 2025-09-29

---

**Status**: ✅ Ready for production use with OpenWebUI
