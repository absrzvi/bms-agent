# BMS Agent OpenWebUI Tool

Custom tool for integrating BMS Agent search capabilities into OpenWebUI chat interface.

## Overview

The BMS Search tool provides seamless access to railway documentation through OpenWebUI's chat interface, enabling users to search 448+ indexed documents using semantic and hybrid search.

## Features

- ✅ **Semantic Search**: AI-powered search using 768-d embeddings
- ✅ **Hybrid Search**: Combined semantic + keyword (BM25) search
- ✅ **Document Type Filtering**: Search within specific file types
- ✅ **Quality Filtering**: Filter by document quality scores
- ✅ **Configurable**: Adjustable search parameters via Valves
- ✅ **Health Monitoring**: Check BMS API status

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

```bash
# Copy tool to OpenWebUI tools directory
mkdir -p /workspace/openwebui/data/tools
cp /root/CascadeProjects/windsurf-project/001-bms-agent/tools/bms_search.py \
   /workspace/openwebui/data/tools/

# Or create symlink
ln -s /root/CascadeProjects/windsurf-project/001-bms-agent/tools/bms_search.py \
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

### Valve Settings

Configure the tool through OpenWebUI's interface or by editing the Valves:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `BMS_API_URL` | `http://localhost:8000` | BMS Agent API base URL |
| `DEFAULT_LIMIT` | `5` | Default number of results |
| `SEARCH_TYPE` | `semantic` | Default search type |
| `HYBRID_WEIGHT_DENSE` | `0.7` | Dense vector weight (hybrid) |
| `HYBRID_WEIGHT_SPARSE` | `0.3` | Sparse vector weight (hybrid) |
| `QUALITY_THRESHOLD` | `0.0` | Minimum quality score filter |
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

#### `search_documents(query, limit, search_type, filters)`
General search with full configuration options.

**Example:**
```python
search_documents(
    query="safety procedures",
    limit=10,
    search_type="hybrid",
    filters={"document_type": "pdf", "quality_score_min": 0.7}
)
```

#### `search_semantic(query, limit)`
Semantic search using AI embeddings.

**Example:**
```python
search_semantic("business continuity", limit=5)
```

#### `search_hybrid(query, limit)`
Hybrid search combining semantic and keyword matching.

**Example:**
```python
search_hybrid("railway maintenance", limit=5)
```

#### `search_by_document_type(query, document_type, limit)`
Search within specific document types.

**Example:**
```python
search_by_document_type("safety", "pdf", limit=5)
```

#### `get_api_status()`
Check BMS API health.

**Example:**
```python
get_api_status()
```

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
