# BMS Agent API Reference

## Overview
Railway documentation retrieval system using RAG (Retrieval-Augmented Generation) with vector search, document processing, and LLM-based answer generation.

**Base URL:** `http://localhost:8000`
**Docs:** `http://localhost:8000/docs`

---

## Core Endpoints

### Health & Status
```
GET  /health                        # Basic health check
GET  /health/detailed               # Detailed service status
```

### Document Management
```
POST   /api/v1/documents/upload           # Upload document (sync)
POST   /api/v1/documents/upload/async     # Upload document (async, returns job_id)
GET    /api/v1/documents/status/{job_id}  # Check async upload status
GET    /api/v1/documents/queue/stats      # Queue statistics
DELETE /api/v1/documents/{document_id}    # Delete document
```

**Supported formats:** PDF, CSV, XLSX, XLS, TXT, MD, DOCX, PPTX
**Max file size:** 1GB
**Profiles:** general, technical, legal, medical, financial, railway

### Search Endpoints
```
POST /api/v1/search/semantic     # Vector-based semantic search
POST /api/v1/search/hybrid       # Combines semantic + keyword search
POST /api/v1/search/contextual   # Search with parent-child relationships
POST /api/v1/search/rerank       # Two-stage search with cross-encoder reranking
POST /api/v1/search/batch        # Batch search for multiple queries
```

**Common parameters:**
- `query`: Search text
- `limit`: Max results (1-100)
- `min_score`: Relevance threshold (0.0-1.0)
- `min_quality`: Quality score threshold (0.0-1.0)
- `filters`: Document type, profile, etc.

### Question Answering
```
POST /api/v1/ask    # Ask question, get LLM-generated answer with citations
```

**Parameters:**
- `query`: Question text
- `max_chunks`: Context chunks (1-10)
- `include_citations`: Include source references
- `temperature`: LLM temperature (0.0-1.0)
- `max_tokens`: Max answer length (50-2000)

### Monitoring & Metrics
```
GET  /metrics/uplink                    # Operational metrics
GET  /api/v1/monitoring/quality         # Real-time quality metrics
GET  /api/v1/monitoring/health          # Quality health report
GET  /api/v1/monitoring/alerts          # Quality alerts
GET  /api/v1/monitoring/trends          # Quality trends over time
GET  /api/v1/monitoring/prometheus      # Prometheus-formatted metrics
POST /api/v1/monitoring/baseline        # Set quality baseline
```

### Cache Management
```
GET  /api/v1/cache/stats                 # Cache statistics
POST /api/v1/cache/clear                 # Clear cache
POST /api/v1/cache/invalidate-expired    # Remove expired entries
```

---

## Key Features

### Search Capabilities
- **Semantic Search**: 768-d embeddings (sentence-transformers/all-mpnet-base-v2)
- **Hybrid Search**: Combines vector + keyword matching with weighted scoring
- **Contextual Search**: Leverages document hierarchy (parent-child chunks)
- **Reranking**: Cross-encoder refinement for improved relevance
- **Batch Search**: Process multiple queries efficiently

### Document Processing
- Multi-format support with Enhanced Document Processor v4.0
- RAGAS quality scoring (0-1 scale)
- Automatic chunking with configurable strategies
- Metadata extraction (keywords, entities, technical terms)
- GPU-accelerated embeddings

### Answer Generation
- LLM-based answers using Ollama (mistral-nemo:12b-instruct)
- Citation tracking with source references
- Confidence scoring
- Answer validation

### Quality & Performance
- Semantic caching (95% similarity threshold)
- Rate limiting (60 req/min default)
- Quality monitoring with alerts
- CORS enabled (configurable)
- p95 latency target: <100ms (production)

---

## Example Usage

### Search for documents
```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "emergency brake procedures",
    "limit": 5,
    "min_score": 0.7
  }'
```

### Upload document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@document.pdf" \
  -F "profile=railway"
```

### Ask question
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the safety requirements for VLAN configuration?",
    "max_chunks": 5,
    "include_citations": true
  }'
```

---

## Response Format

All responses follow this structure:
```json
{
  "status": "success",
  "results": [...],
  "search_metadata": {
    "total_results": 5,
    "search_time_ms": 45
  }
}
```

**Search results include:**
- `content`: Chunk text
- `score`: Relevance score
- `metadata`: Document name, type, quality score, keywords, entities
- `document_url`: SharePoint URL (if available)

---

## Authentication & Security
- Optional API key via `X-API-Key` header
- Rate limiting per IP address
- Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- File size validation
- CORS middleware

---

## Integration Notes for n8n/MS Teams

### Recommended Workflow
1. **Incoming Message** → Trigger on MS Teams message
2. **Search/Ask** → Call `/api/v1/ask` or `/api/v1/search/semantic`
3. **Format Response** → Extract answer + citations
4. **Reply** → Send formatted response to MS Teams

### Best Endpoints for Chat Bot
- `/api/v1/ask` - Get direct answers with citations
- `/api/v1/search/semantic` - Find relevant documents
- `/api/v1/search/hybrid` - Better for keyword-specific queries

### Response Time
- Semantic search: ~45ms (p50)
- Ask endpoint: ~500-2000ms (includes LLM generation)
- Consider async pattern for document uploads
