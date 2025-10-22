# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BMS Agent** is a retrieval-augmented generation (RAG) system for railway documentation. It combines FastAPI backend, Qdrant vector database, Ollama/sentence-transformers embeddings, and OpenWebUI integration to provide semantic search over 300+ documents across 21 departments.

### 🔴 CRITICAL: RunPod POD Environment

This system runs in a **RunPod POD** where **ONLY `/workspace` is persistent** across pod restarts. Everything outside `/workspace` is ephemeral.

**Persistent Storage Locations:**
- `/workspace/bms-agent/` - Main codebase and Qdrant binary
- `/workspace/qdrant-data/` - Qdrant vector database (auto-created)
- `/workspace/ollama/` - Ollama models (auto-managed by pre_start.sh)
- `/workspace/openwebui/` - OpenWebUI data and configurations (auto-managed)
- `/workspace/logs/` - All service logs (ollama.log, webui.log, qdrant.log)

**Auto-Starting Services:**
- Ollama and OpenWebUI start automatically via `/pre_start.sh` (managed by RunPod)
- Qdrant now starts automatically via updated `/pre_start.sh`
- FastAPI must be started manually (not auto-started)

**POD Startup Workflow:**
1. RunPod executes `/pre_start.sh` on pod boot
2. `/pre_start.sh` creates directories and starts: Ollama → Qdrant → OpenWebUI
3. All services use persistent storage in `/workspace/`
4. You must manually run `./init.sh` on first pod setup (installs dependencies)
5. You must manually start FastAPI each time you want to use the API

### Core Technology Stack
- **Vector Database**: Qdrant v1.15.5 with multi-vector support (4 dense + 1 sparse)
- **Embeddings**: sentence-transformers (`all-mpnet-base-v2`, 768d) or Ollama (`snowflake-arctic-embed2`, 1024d)
- **Document Processing**: EnhancedDocumentProcessor with hierarchical chunking, quality validation, chapter awareness
- **API**: FastAPI with async processing, CORS, API key authentication
- **Integrations**: n8n workflows, OpenWebUI custom tool
- **Development**: GitHub Spec Kit for spec-driven development workflow

## Repository Structure

```
bms-agent/
├── bms-agent/                  # Main package
│   ├── api/
│   │   ├── main.py            # FastAPI application (routes, health checks, upload)
│   │   └── processor_wrapper.py  # High-level orchestrator for ingestion
│   ├── scr/                   # Core processing modules
│   │   ├── enhanced_document_processor.py  # Document chunking, quality validation
│   │   ├── qdrant_schema_v4.py            # Vector DB schema & search utilities
│   │   ├── chapter_extractor.py           # Chapter/sub-chapter structure extraction
│   │   └── ultimate_processor_v4.py       # Legacy v4 processor (reference)
│   ├── tests/
│   │   ├── test_basic.py      # Core API endpoint tests
│   │   ├── integration/       # Hybrid search integration tests
│   │   └── performance/       # Performance & load tests
│   └── reqs/
│       └── requirements_file.txt  # Core dependencies
├── upload-files/              # 21 department folders with documents
├── ingest_documents_to_qdrant.py  # CLI for batch ingestion
├── batch_ingest_by_department.py  # Department-aware batch ingestion
├── bms_search.py              # OpenWebUI custom tool (v4.2 with artifacts)
└── tasks.md                   # Deployment task tracking
```

## Common Commands

### Initial Setup (First Time on New Pod)

```bash
# Run the initialization script (installs dependencies, starts Qdrant)
cd /workspace/bms-agent
./init.sh

# This script will:
# - Install all Python dependencies from requirements.txt
# - Download NLTK data and spaCy models
# - Create /workspace/qdrant-data directory
# - Start Qdrant service with persistent storage
# - Verify all services are running
```

### Starting Services

**Note:** Ollama, OpenWebUI, and Qdrant start automatically via `/pre_start.sh` on pod boot.

```bash
# Check if services are running
ps aux | grep -E "(ollama|qdrant|open-webui)"

# Manually start Qdrant (if needed)
cd /workspace/bms-agent && nohup ./qdrant --storage-path /workspace/qdrant-data > /workspace/logs/qdrant.log 2>&1 &

# Verify Qdrant health
curl -s http://localhost:6333/healthz

# Start FastAPI (THIS MUST BE STARTED MANUALLY)
cd /workspace/bms-agent/bms-agent
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Or run in background
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/api.log 2>&1 &

# Check API health
curl http://localhost:8000/health
```

### Document Ingestion

```bash
# Single document ingestion
python3 ingest_documents_to_qdrant.py path/to/document.pdf

# Batch ingestion by department
python3 batch_ingest_by_department.py --department HR --collection nomad_bms_documents

# Test processor pipeline
cd bms-agent && python3 api/processor_wrapper.py  # Has test harness in __main__
```

### Qdrant Collection Management

```bash
# Verify collection health (uses verify_qdrant.py)
cd /workspace/bms-agent
python3 verify_qdrant.py

# Reset collection (delete + recreate schema)
python3 reset_qdrant_collection.py

# Initialize collection from scratch
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'bms-agent' / 'scr'))
from qdrant_schema_v4 import QdrantSchemaV4, QdrantConfig
config = QdrantConfig(collection_name='nomad_bms_documents', dense_vector_size=768)
schema = QdrantSchemaV4(config)
schema.create_collection(force_recreate=True)
"

# Check Qdrant logs
tail -f /workspace/logs/qdrant.log
```

### Testing

```bash
# Run all tests
cd bms-agent && pytest -v

# Run specific test file
pytest tests/test_basic.py -v

# Run with coverage
pytest --cov=api --cov=scr --cov-report=term-missing

# Performance tests
pytest tests/performance/ -m performance

# Integration tests
pytest tests/integration/ -m integration
```

## Architecture & Key Concepts

### Multi-Vector Strategy

The system uses **4 dense vectors** per chunk for hierarchical retrieval:
- `chunk_embedding` (768d): Main semantic vector for standard search
- `parent_embedding` (768d): Parent chunk vector for context-aware retrieval
- `child_embedding` (768d): Child chunk vector for precise matching
- `full_doc_embedding` (768d): Document-level embedding (late chunking)

Plus **1 sparse vector**:
- `keyword_sparse`: BM25-style keyword vector for hybrid search

### Document Processing Pipeline

1. **File Reading** (`enhanced_document_processor.py`):
   - Supports PDF, DOCX, PPTX, XLSX, CSV, TXT, MD
   - Text extraction with OCR fallback (PyMuPDF + Pillow)

2. **Chapter Extraction** (`chapter_extractor.py`):
   - Detects markdown headers (`#`, `##`, `###`) and numbered sections
   - Builds hierarchical structure: `chapter_number`, `chapter_title`, `chapter_path`
   - Associates each chunk with its chapter/sub-chapter

3. **Hierarchical Chunking** (`enhanced_document_processor.py`):
   - Parent chunks (1500 chars) with child chunks (500 chars)
   - Chunk overlap (200 chars) for context preservation
   - Contextual retrieval: embeds chunks with surrounding context

4. **Quality Validation**:
   - RAGAS-style metrics: faithfulness, relevancy, precision, recall
   - Quality score threshold (default 85.0)
   - Filters low-quality chunks before indexing

5. **Embedding & Indexing** (`processor_wrapper.py`):
   - Generates embeddings via sentence-transformers or Ollama
   - Builds Qdrant point with all 4 dense vectors + sparse vector
   - Upserts to `nomad_bms_documents` collection with metadata

### Document Lifecycle Management

**Document Replacement** (via re-upload):
- When uploading a document with matching `document_name` + `department` combination
- System automatically deletes all existing chunks for that document from Qdrant
- Processes new document through full pipeline (extraction → chunking → validation → embedding)
- Indexes new chunks with fresh embeddings
- **No version history**: Old version is completely removed
- **Identity**: Documents are uniquely identified by `document_name` + `department`
  - Two departments can have identically named files without conflict

**Document Deletion** (`DELETE /api/v1/documents/{document_name}?department={dept}`):
- Hard delete only (no soft delete, no retention)
- Permanently removes all chunks for the document from vector database
- Returns 404 Not Found if document doesn't exist
- No rollback or recovery after deletion

**Rationale**: Ensures search results always reflect latest document versions, prevents duplicate results, maintains data consistency without version management complexity.

### Search Architecture

The system provides multiple search strategies:

**Semantic Search** (`/api/v1/search/semantic`):
- Pure vector similarity using `chunk_embedding`
- Filters by metadata (department, category, document_name)

**Hybrid Search** (in `qdrant_schema_v4.py`):
- Combines vector + keyword search with Reciprocal Rank Fusion (RRF)
- Configurable alpha weight (default 0.5)
- Uses sparse vectors for BM25-style keyword matching

**Hierarchical Search** (`search_hierarchical`):
- Search child chunks, return parent chunks
- Provides broader context for detailed queries

**Railway-Specific Search** (`search_railway_specific`):
- Filters by fleet_type, standard_compliance, network_component
- Optimized for railway domain queries

### Configuration System

All processor settings are controlled via environment variables with `BMS_*` prefix:

```bash
# Core settings
BMS_API_KEY=your-key-here
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=nomad_bms_documents

# Embedding configuration
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # or snowflake-arctic-embed2
EMBEDDING_URL=http://localhost:11434/api/embeddings

# Processing tuning
BMS_PROCESSING_PROFILE=RAILWAY  # or TECHNICAL, GENERAL
BMS_CHUNK_SIZE=1500
BMS_CHUNK_OVERLAP=200
BMS_ENABLE_HYBRID_SEARCH=true
BMS_ENABLE_QUALITY_VALIDATION=true
BMS_QUALITY_THRESHOLD=85.0
BMS_UPLOAD_MAX_BYTES=104857600  # 100MB
```

See `bms-agent/api/processor_wrapper.py` for all available `BMS_*` variables.

## Data Flow

### Ingestion Flow
```
Document Upload
    ↓
EnhancedDocumentProcessor (text extraction, chapter extraction)
    ↓
Hierarchical Chunking (parent/child chunks with overlap)
    ↓
Quality Validation (RAGAS metrics, threshold filtering)
    ↓
Embedding Generation (sentence-transformers or Ollama)
    ↓
Multi-Vector Point Construction (4 dense + 1 sparse)
    ↓
Qdrant Upsert (nomad_bms_documents collection)
```

### Search Flow
```
User Query
    ↓
Query Embedding (same model as ingestion)
    ↓
Qdrant Vector Search (with optional metadata filters)
    ↓
Result Ranking (cosine similarity or RRF for hybrid)
    ↓
Response with Chunks + Metadata (quality scores, chapter info, citations)
```

## Integration Points

### OpenWebUI Tool (`bms_search.py`)
- Version 4.2 with artifact support
- 25 search functions (semantic, department-filtered, chapter-based, etc.)
- Smart boosting algorithms (+5% accuracy)
- SVG chart generation, Mermaid diagrams, Python code execution

### n8n Workflow
- Slack integration for conversational search
- Workflow JSON in `bms-agent/n8n/workflows/`
- Queries FastAPI `/api/v1/search/semantic` endpoint
- LLM response generation with Ollama Mistral

### API Authentication
- Optional API key via `BMS_API_KEY` environment variable
- `X-API-Key` header required when key is configured
- Anonymous access allowed when key is unset (MVP mode)

### Visual Artifacts (Feature 002)
- **Status**: ✅ MVP Deployed (2025-10-22)
- **Purpose**: Extract images from PDFs/DOCX, render PPTX slides, display inline with search results
- **Storage**: `/workspace/visual-artifacts/` (persistent on RunPod)
- **Supported Formats**:
  - PDF: Image extraction via PyMuPDF
  - DOCX: Embedded image extraction via python-docx
  - PPTX: Slide rendering via LibreOffice headless
- **Features**:
  - OCR text extraction from images (Tesseract)
  - Proximity-based image-to-chunk association
  - Caption matching ("Figure 1", "Fig. 2", etc.)
  - Thumbnail generation for fast preview
  - Base64 encoding for OpenWebUI inline display
- **Performance**:
  - PDF extraction: ~10ms per page (target: <100ms) ⚡
  - PPTX rendering: ~12s for 50 slides (target: <300s) ⚡
- **Configuration**: See environment variables in `.env` file
- **Tests**: See `TEST_RESULTS_VISUAL_ARTIFACTS.md` for validation results

## Important Implementation Details

### Collection Naming
- **Current production collection**: `nomad_bms_documents`
- **Legacy/test collection**: `railway_documents_v4`
- Always verify collection name in environment variables before operations

### Embedding Model Compatibility
- **768-dimensional** models: `all-mpnet-base-v2` (sentence-transformers default)
- **1024-dimensional** models: `snowflake-arctic-embed2` (Ollama)
- Collection `dense_vector_size` must match model dimensions
- Check `QdrantConfig` in `qdrant_schema_v4.py` when switching models

### Chapter Awareness
- Automatically extracts chapter structure from markdown, numbered sections, Word-style headings
- Stores in payload: `chapter_number`, `chapter_title`, `chapter_level`, `chapter_path`, `sub_chapter`
- Indexed for fast chapter-based filtering
- See `CHAPTER_AWARENESS_GUIDE.md` for full feature documentation

### Quality Score System
- Overall score (0-100) computed from RAGAS metrics
- Components: faithfulness, answer_relevancy, context_precision, context_recall
- Default threshold: 85.0 (configurable via `BMS_QUALITY_THRESHOLD`)
- Low-quality chunks are logged but not indexed
- See `QUALITY_SCORES_EXPLAINED.md` for details

### Metadata Filtering
- All searches support filtering by: `department`, `category`, `document_name`, `document_type`, `chapter_number`
- Indexed fields for fast filtering (keyword indexes)
- Railway-specific fields: `fleet_type`, `train_id`, `standard_compliance`, `network_component`
- See `METADATA_FILTERING_FEATURE.md` for usage examples

## Development Workflow

### Code Style
- Python 3.11+
- Type hints encouraged (see `processor_wrapper.py` for reference)
- Async/await for I/O operations (FastAPI routes, embedding generation)
- Logging via Python `logging` module (INFO level default)

### Testing Strategy
- Core tests: `tests/test_basic.py` (API endpoints, health checks)
- Integration tests: `tests/integration/` (hybrid search, end-to-end flows)
- Performance tests: `tests/performance/` (latency benchmarks, load testing)
- Target: ≤100ms p95 latency @ 1,000 concurrent users
- See `TESTING.md` for full QA strategy

### Git Workflow
- Main branch: `main` (stable)
- Feature branches: `feature/<name>`
- Release branches: `release/<version>`
- Semantic commits preferred: `feat:`, `fix:`, `docs:`, `test:`

### Deployment
- Target platform: RunPod pods (8-16 vCPU, 32-64GB RAM)
- Persistent storage: `~/persistent/` (Qdrant data, uploaded documents, logs)
- Service management: see `tasks.md` for complete deployment checklist
- Manual deployment currently (rsync to RunPod, restart services)
- CI/CD automation in `.github/workflows/ci-cd.yml` (test + security scans)

## Common Pitfalls

1. **POD Persistence**: Remember that ONLY `/workspace` is persistent. Never store data outside this directory.

2. **Qdrant Data Loss**: Always ensure Qdrant uses `--storage-path /workspace/qdrant-data`. Check the running Qdrant process arguments with `ps aux | grep qdrant`.

3. **Collection Not Found**: Ensure Qdrant is running and collection exists. Run `cd /workspace/bms-agent && python3 verify_qdrant.py` to check.

4. **Embedding Dimension Mismatch**: If switching embedding models, recreate collection with correct `dense_vector_size`.

5. **Path Issues**: Many scripts assume execution from `/workspace/bms-agent` root. Check working directory if imports fail.

6. **Import Errors**: The `scr/` directory is added to `sys.path` dynamically. Use absolute imports from project root.

7. **Empty Search Results**: Check if documents are ingested (`collection.points_count > 0`). Verify embedding model is loaded.

8. **Quality Score Threshold**: If no chunks are indexed, quality scores may be below threshold. Lower `BMS_QUALITY_THRESHOLD` or check document quality.

9. **API Key Issues**: If testing locally, either set `BMS_API_KEY` or leave unset for anonymous access. Match key in requests.

10. **Service Not Starting**: Check logs in `/workspace/logs/` for errors. Ensure binaries and dependencies are in `/workspace/bms-agent/`.

## Key Files Reference

### Core Application Files
- **`bms-agent/api/main.py`**: FastAPI routes, request models, authentication logic
- **`bms-agent/api/processor_wrapper.py`**: High-level ingestion orchestrator, embedding generation, Qdrant interaction
- **`bms-agent/scr/enhanced_document_processor.py`**: Core document processing, chunking, quality validation, **visual artifacts extraction**
- **`bms-agent/scr/qdrant_schema_v4.py`**: Qdrant schema definition, multi-vector setup, search utilities
- **`bms-agent/scr/chapter_extractor.py`**: Chapter/sub-chapter structure detection and extraction
- **`ingest_documents_to_qdrant.py`**: CLI tool for single document ingestion with progress tracking
- **`batch_ingest_by_department.py`**: Department-aware batch ingestion for `upload-files/` folders
- **`bms_search.py`**: OpenWebUI v4.2 tool with 25 search functions and **artifact display support**
- **`tasks.md`**: Complete deployment task list with dependency order and verification commands

### Visual Artifacts Files (Feature 002)
- **`bms-agent/scr/image_extractor.py`**: PDF/DOCX image extraction, PPTX slide rendering (PyMuPDF, LibreOffice)
- **`bms-agent/scr/artifact_storage.py`**: File system storage manager for artifacts with metadata tracking
- **`bms-agent/scr/image_processor.py`**: Image resizing, optimization, thumbnail generation (Pillow)
- **`bms-agent/scr/ocr_processor.py`**: Tesseract OCR integration with preprocessing
- **`bms-agent/scr/proximity_associator.py`**: Image-to-chunk association via proximity and caption matching
- **`bms-agent/tests/test_visual_artifacts_integration.py`**: Integration test suite (14 tests, all passing)
- **`TEST_RESULTS_VISUAL_ARTIFACTS.md`**: Comprehensive test results and performance benchmarks
- **`.env`**: Visual artifacts configuration (storage dir, OCR settings, render DPI, etc.)

### POD-Specific Files
- **`/pre_start.sh`**: RunPod startup script (starts Ollama, OpenWebUI, Qdrant automatically)
- **`init.sh`**: First-time initialization script (dependencies, NLTK data, Qdrant setup)
- **`requirements.txt`**: Core Python dependencies
- **`qdrant`**: Qdrant binary (must be in `/workspace/bms-agent/`)

### Configuration & Logs
- **`/workspace/qdrant-data/`**: Qdrant persistent storage (CRITICAL for data persistence)
- **`/workspace/visual-artifacts/`**: Visual artifacts storage (images/, slides/, thumbnails/) (Feature 002)
- **`/workspace/logs/qdrant.log`**: Qdrant service logs
- **`/workspace/logs/ollama.log`**: Ollama service logs
- **`/workspace/logs/webui.log`**: OpenWebUI service logs
- **`/workspace/logs/api.log`**: FastAPI service logs (if running in background)

## Spec-Driven Development with Spec Kit

This project is configured with **GitHub Spec Kit** for structured feature development. Use these slash commands in Claude Code:

**Core Workflow:**
1. `/speckit.constitution` - Establish project principles
2. `/speckit.specify` - Define requirements (what & why)
3. `/speckit.plan` - Create technical plan (how)
4. `/speckit.tasks` - Generate actionable tasks
5. `/speckit.implement` - Execute implementation

**Enhancement Commands:**
- `/speckit.clarify` - Resolve ambiguities before planning
- `/speckit.checklist` - Validate requirements quality
- `/speckit.analyze` - Check cross-artifact consistency

See `SPEC_KIT_GUIDE.md` for detailed usage and workflow examples.

## Additional Documentation

- `README.md`: Setup instructions, API usage, environment configuration
- `SPEC_KIT_GUIDE.md`: GitHub Spec Kit integration and workflow
- `TESTING.md`: QA strategy, test fixtures, performance targets
- `CHAPTER_AWARENESS_GUIDE.md`: Chapter extraction features and usage
- `QUALITY_SCORES_EXPLAINED.md`: Quality metric computation and interpretation
- `METADATA_FILTERING_FEATURE.md`: Advanced filtering capabilities
- `TOOL_USAGE_INSTRUCTIONS.md`: OpenWebUI tool integration guide
- `SYSTEM_PROMPT_UPDATE_SUMMARY.md`: LLM prompt engineering for search quality

## Active Technologies
- Python 3.11+ + aiohttp>=3.9.0, pydantic>=2.0.0, base64 (stdlib), Pillow (for image handling) (003-search-tool-refactor)
- `/workspace/visual-artifacts/` (filesystem), Qdrant `nomad_bms_documents` collection (vector DB) (003-search-tool-refactor)

## Recent Changes
- 003-search-tool-refactor: Added Python 3.11+ + aiohttp>=3.9.0, pydantic>=2.0.0, base64 (stdlib), Pillow (for image handling)
