# Quickstart Guide: BMS Agent RAG System

**Target Audience**: Developers setting up the BMS Agent for the first time
**Time Required**: 30-60 minutes (depending on download speeds)
**Prerequisites**: Linux environment with Python 3.11+, 16GB+ RAM, 100GB+ storage

## Overview

This guide walks you through:
1. Installing dependencies
2. Starting required services (Qdrant, Ollama optional)
3. Uploading your first document
4. Performing your first search
5. Running tests
6. Troubleshooting common issues

## Prerequisites

**Required**:
- Python 3.11 or higher
- 16GB RAM minimum (32GB+ recommended)
- 100GB free disk space in `/workspace` (or equivalent persistent storage)
- Linux environment (Ubuntu 20.04+ recommended, or RunPod POD)

**Optional** (for full features):
- Ollama installed (for snowflake-arctic-embed2 embeddings)
- OpenWebUI (for conversational interface)

## Step 1: Clone and Setup

```bash
# If not already in the project directory
cd /workspace/bms-agent

# Run the initialization script (first-time setup)
./init.sh
```

**What `init.sh` does**:
- Installs Python dependencies from `requirements.txt`
- Downloads NLTK data (punkt, stopwords)
- Downloads spaCy model (`en_core_web_sm`)
- Creates `/workspace/qdrant-data` directory
- Starts Qdrant service with persistent storage
- Verifies all services are running

**Expected output**:
```
✓ Python dependencies installed
✓ NLTK data downloaded
✓ spaCy model downloaded
✓ Qdrant started on http://localhost:6333
✓ Initialization complete!
```

## Step 2: Verify Services

Check that all required services are running:

```bash
# Check Qdrant health
curl http://localhost:6333/healthz
# Expected: OK

# Check if Qdrant collection exists (should return 200 or 404 if not created yet)
curl http://localhost:6333/collections/nomad_bms_documents

# Optional: Check Ollama (if installed)
curl http://localhost:11434/api/tags
# Expected: JSON list of models

# Check Python environment
python3 --version
# Expected: Python 3.11.x or higher
```

## Step 3: Create Qdrant Collection

Initialize the vector database collection with multi-vector schema:

```bash
cd /workspace/bms-agent/bms-agent

python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'scr'))
from qdrant_schema_v4 import QdrantSchemaV4, QdrantConfig

config = QdrantConfig(
    collection_name='nomad_bms_documents',
    dense_vector_size=768  # For sentence-transformers all-mpnet-base-v2
)
schema = QdrantSchemaV4(config)
schema.create_collection(force_recreate=False)
print('✓ Collection created successfully')
"
```

**Expected output**:
```
✓ Collection created successfully
```

**Verify collection creation**:
```bash
curl http://localhost:6333/collections/nomad_bms_documents | jq .
```

## Step 4: Configure Environment Variables

Create a `.env` file in `/workspace/bms-agent/` or set environment variables:

```bash
# Core settings
export BMS_API_KEY=your-secret-key-here  # Optional, leave unset for anonymous access
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export QDRANT_COLLECTION=nomad_bms_documents

# Embedding configuration (choose one)
# Option 1: sentence-transformers (default, faster, 768d)
export EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# Option 2: Ollama (requires Ollama installed, 1024d)
# export EMBEDDING_MODEL=snowflake-arctic-embed2
# export EMBEDDING_URL=http://localhost:11434/api/embeddings

# Processing configuration
export BMS_PROCESSING_PROFILE=RAILWAY  # or TECHNICAL, GENERAL
export BMS_CHUNK_SIZE=1500
export BMS_CHUNK_OVERLAP=200
export BMS_ENABLE_HYBRID_SEARCH=true
export BMS_ENABLE_QUALITY_VALIDATION=true
export BMS_QUALITY_THRESHOLD=85.0
export BMS_UPLOAD_MAX_BYTES=104857600  # 100MB

# Logging
export LOG_LEVEL=INFO
```

**For quick testing without environment file**:
```bash
# Use defaults (sentence-transformers, no API key, localhost Qdrant)
# No configuration needed!
```

## Step 5: Start FastAPI Server

```bash
cd /workspace/bms-agent/bms-agent

# Start in development mode (auto-reload)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Or start in background for production
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/api.log 2>&1 &
```

**Verify API is running**:
```bash
curl http://localhost:8000/health | jq .
```

**Expected output**:
```json
{
  "status": "healthy",
  "timestamp": "2024-10-22T10:30:00Z",
  "services": {
    "api": "up",
    "qdrant": "up",
    "embedding": "up"
  },
  "metrics": {
    "request_count": 1,
    "latency_p95_ms": 0,
    "error_rate": 0.0
  }
}
```

## Step 6: Upload Your First Document

**Option A: Using CLI tool (recommended for first test)**

```bash
cd /workspace/bms-agent

# Upload a single PDF
python3 ingest_documents_to_qdrant.py /path/to/your/document.pdf
```

**Option B: Using HTTP API**

```bash
# Upload via curl
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/path/to/your/document.pdf" \
  -F "department=Safety" \
  -F "category=Manuals"
```

**Option C: Using Python requests**

```python
import requests

# Upload document
with open('/path/to/document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/upload',
        files={'file': f},
        data={
            'department': 'Safety',
            'category': 'Manuals',
            'fleet_type': 'EMU'  # Optional
        }
    )

print(response.json())
# Expected: {'status': 'accepted', 'document_id': '...', 'job_id': '...'}
```

**Expected processing time**:
- Small PDF (10-20 pages): 30-60 seconds
- Medium PDF (50-100 pages): 2-4 minutes
- Large PDF (200+ pages): 5-10 minutes

**Monitor processing**:
```bash
# Watch Qdrant logs
tail -f /workspace/logs/qdrant.log

# Watch API logs (if running in background)
tail -f /workspace/logs/api.log

# Check collection size
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'
```

## Step 7: Perform Your First Search

**Semantic search (pure vector similarity)**:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "emergency braking procedures",
    "limit": 10
  }' | jq .
```

**Hybrid search (semantic + keyword)**:

```bash
curl -X POST http://localhost:8000/api/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "EMU-750 maintenance schedule",
    "alpha": 0.5,
    "limit": 10
  }' | jq .
```

**Filtered search (by department)**:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "safety protocols",
    "filter_department": "Safety",
    "limit": 10
  }' | jq .
```

**Expected output**:
```json
{
  "query": "emergency braking procedures",
  "results": [
    {
      "chunk_id": "...",
      "chunk_text": "Emergency braking procedures must be followed...",
      "relevance_score": 0.89,
      "ranking_position": 1,
      "source_document": "Safety_Manual_2024.pdf",
      "chapter_context": {
        "chapter_number": "5.2.1",
        "chapter_title": "Emergency Procedures",
        "chapter_path": "5 > 5.2 > 5.2.1"
      },
      "quality_score": 92.5
    }
  ],
  "total_results": 10,
  "search_time_ms": 145.2
}
```

## Step 8: Run Tests

Verify everything is working correctly:

```bash
cd /workspace/bms-agent/bms-agent

# Run all tests
pytest -v

# Run specific test suites
pytest tests/test_basic.py -v  # API endpoint tests
pytest tests/integration/ -v  # Integration tests
pytest tests/performance/ -v  # Performance tests

# Run with coverage
pytest --cov=api --cov=scr --cov-report=term-missing
```

**Expected output**:
```
tests/test_basic.py::test_health_endpoint PASSED
tests/test_basic.py::test_upload_endpoint PASSED
tests/test_basic.py::test_search_semantic PASSED
...
==================== 25 passed in 15.2s ====================
```

## Step 9: Batch Document Ingestion (Optional)

If you have multiple documents in the `upload-files/` directory structure:

```bash
cd /workspace/bms-agent

# Ingest all documents from the Safety department
python3 batch_ingest_by_department.py --department Safety --collection nomad_bms_documents

# Check progress
# The script will show progress bars and log processing status
```

**Expected output**:
```
Processing Safety department...
[====================] 42/42 documents processed
✓ Successfully indexed 3580 chunks
✗ 2 documents failed (check logs)
```

## Troubleshooting

### Issue: "Collection not found"

**Symptom**: `404 Not Found` when searching or `Collection nomad_bms_documents does not exist`

**Solution**:
```bash
# Create the collection (Step 3)
cd /workspace/bms-agent/bms-agent
python3 -c "
from scr.qdrant_schema_v4 import QdrantSchemaV4, QdrantConfig
config = QdrantConfig(collection_name='nomad_bms_documents', dense_vector_size=768)
schema = QdrantSchemaV4(config)
schema.create_collection(force_recreate=False)
"
```

### Issue: "Embedding service unavailable"

**Symptom**: `503 Service Unavailable` from `/health/embedding` or search fails

**Solution for sentence-transformers**:
```bash
# Verify model is downloaded
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

# If it downloads successfully, restart API server
```

**Solution for Ollama**:
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull the embedding model
ollama pull snowflake-arctic-embed2

# Restart API server
```

### Issue: "Qdrant connection refused"

**Symptom**: `Connection refused` to `localhost:6333`

**Solution**:
```bash
# Check if Qdrant is running
ps aux | grep qdrant

# If not running, start it
cd /workspace/bms-agent
nohup ./qdrant --storage-path /workspace/qdrant-data > /workspace/logs/qdrant.log 2>&1 &

# Wait a few seconds and check health
curl http://localhost:6333/healthz
```

### Issue: "File size exceeds limit"

**Symptom**: `413 Payload Too Large` when uploading

**Solution**:
```bash
# Increase limit via environment variable
export BMS_UPLOAD_MAX_BYTES=209715200  # 200MB

# Restart API server
```

### Issue: "No results returned" for queries

**Symptom**: Search returns empty results `{"results": [], "total_results": 0}`

**Possible causes and solutions**:

1. **No documents indexed yet**:
   ```bash
   # Check collection size
   curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'
   # If 0, upload documents first (Step 6)
   ```

2. **Quality threshold too high**:
   ```bash
   # Lower quality threshold temporarily
   export BMS_QUALITY_THRESHOLD=75.0
   # Re-process documents
   ```

3. **Wrong embedding dimension**:
   ```bash
   # Check collection config
   curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.config.params.vectors'
   # If dimension mismatch, recreate collection with correct size
   ```

### Issue: "Import errors" (e.g., `ModuleNotFoundError`)

**Symptom**: `ModuleNotFoundError: No module named 'fastapi'` or similar

**Solution**:
```bash
# Reinstall dependencies
cd /workspace/bms-agent
pip install -r requirements.txt

# Or run init.sh again
./init.sh
```

### Issue: "Out of memory" during processing

**Symptom**: Process killed or OOM errors in logs

**Solution**:
```bash
# Reduce batch size for embedding generation
export BMS_EMBEDDING_BATCH_SIZE=16  # Default is 32

# Or reduce chunk sizes
export BMS_CHUNK_SIZE=1000  # Default is 1500

# Restart API and re-process
```

## Next Steps

**For Development**:
1. Review API documentation: `/workspace/bms-agent/specs/001-railway-rag-system/contracts/api.openapi.yaml`
2. Explore data model: `/workspace/bms-agent/specs/001-railway-rag-system/data-model.md`
3. Read implementation plan: `/workspace/bms-agent/specs/001-railway-rag-system/plan.md`
4. Review technical research: `/workspace/bms-agent/specs/001-railway-rag-system/research.md`

**For Deployment**:
1. Configure API key authentication (`BMS_API_KEY` environment variable)
2. Set up log rotation for `/workspace/logs/`
3. Configure automated backups for `/workspace/qdrant-data/`
4. Set up monitoring for health endpoints
5. Review scaling considerations in plan.md

**For Integration**:
1. **OpenWebUI**: Install custom tool from `bms_search.py`
2. **n8n**: Import workflow from `n8n/workflows/` (if available)
3. **Custom Applications**: Use OpenAPI schema to generate client SDKs

## Useful Commands Reference

```bash
# Service Management
./init.sh                          # First-time setup
uvicorn api.main:app --reload      # Start API (dev mode)
ps aux | grep -E "(qdrant|ollama)" # Check services

# Document Operations
python3 ingest_documents_to_qdrant.py <file>                 # Upload single doc
python3 batch_ingest_by_department.py --department <name>     # Batch upload
python3 verify_qdrant.py                                     # Verify collection health
python3 reset_qdrant_collection.py                           # Reset collection (destructive!)

# Testing
pytest -v                          # Run all tests
pytest tests/test_basic.py -v      # Run API tests
pytest --cov=api --cov-report=html # Generate coverage report

# Monitoring
curl http://localhost:8000/health                # API health
curl http://localhost:8000/metrics               # Operational metrics
curl http://localhost:6333/collections/nomad_bms_documents | jq . # Qdrant status
tail -f /workspace/logs/api.log                  # Watch API logs
tail -f /workspace/logs/qdrant.log               # Watch Qdrant logs
```

## Support

**Documentation**:
- Specification: `/workspace/bms-agent/specs/001-railway-rag-system/spec.md`
- Implementation Plan: `/workspace/bms-agent/specs/001-railway-rag-system/plan.md`
- API Contract: `/workspace/bms-agent/specs/001-railway-rag-system/contracts/api.openapi.yaml`

**Common Issues**: See CLAUDE.md section "Common Pitfalls"

**Logs Location**: `/workspace/logs/`
- `api.log` - FastAPI application logs
- `qdrant.log` - Qdrant service logs
- `ollama.log` - Ollama service logs (if used)
- `webui.log` - OpenWebUI logs (if used)

**Need Help?**: Check logs first, then review troubleshooting section above.
