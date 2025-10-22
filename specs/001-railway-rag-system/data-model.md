# Data Model: BMS Agent RAG System

**Date**: 2025-10-22
**Feature**: Railway Documentation RAG System
**Purpose**: Define entity schemas, relationships, validation rules, and state transitions

## Entity Relationship Diagram

```
┌─────────────┐
│ Department  │
└──────┬──────┘
       │ 1:N
       │
┌──────▼───────────┐
│    Document      │
└──────┬───────────┘
       │ 1:N
       │
┌──────▼───────────┐       ┌──────────────┐
│     Chapter      │───────│ Chunk        │
└──────────────────┘  1:N  └──────┬───────┘
                                  │
                                  │ Parent-Child (1:N)
                                  │
                            ┌─────▼──────┐
                            │Embedding   │
                            │Model Config│
                            └────────────┘

┌─────────────┐
│Search Query │
└──────┬──────┘
       │ 1:N
       │
┌──────▼──────────┐
│ Search Result   │
└─────────────────┘

┌──────────────────┐
│Processing Profile│
└──────────────────┘
```

## Entity Definitions

### 1. Document

Represents an uploaded railway technical document with processing status and metadata.

**Schema**:
```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    PPTX = "PPTX"
    XLSX = "XLSX"
    CSV = "CSV"
    TXT = "TXT"
    MD = "MD"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(BaseModel):
    document_id: str = Field(..., description="UUID for document")
    document_name: str = Field(..., min_length=1, max_length=255)
    document_type: DocumentType
    department: str = Field(..., description="One of 21 departments")
    category: Optional[str] = Field(None, max_length=100)
    file_path: str = Field(..., description="Path in /workspace/bms-agent/upload-files/")
    file_size_bytes: int = Field(..., ge=0, le=104857600)  # Max 100MB
    total_pages: Optional[int] = Field(None, ge=1)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    indexed_chunks_count: int = Field(0, ge=0)
    upload_timestamp: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_error: Optional[str] = None

    # Railway-specific metadata (optional)
    fleet_type: Optional[str] = Field(None, description="DMU, EMU, Locomotive, etc.")
    train_id: Optional[str] = None
    standard_compliance: Optional[List[str]] = Field(None, description="e.g., EN 50126, ISO 9001")
    network_component: Optional[str] = Field(None, description="signaling, track, overhead_line, etc.")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "document_name": "Safety_Manual_2024.pdf",
                "document_type": "PDF",
                "department": "Safety",
                "category": "Manuals",
                "file_path": "/workspace/bms-agent/upload-files/Safety/Safety_Manual_2024.pdf",
                "file_size_bytes": 5242880,
                "total_pages": 120,
                "processing_status": "completed",
                "indexed_chunks_count": 85,
                "upload_timestamp": "2024-10-22T10:30:00Z",
                "fleet_type": "EMU",
                "standard_compliance": ["EN 50126", "ISO 9001"]
            }
        }
```

**Validation Rules**:
- `document_name` must be unique within department
- `file_size_bytes` <= 104857600 (100MB)
- `department` must be one of 21 valid departments (enum or validated list)
- `processing_status` transitions: PENDING → PROCESSING → (COMPLETED | FAILED)
- `indexed_chunks_count` only updated when status = COMPLETED

**State Transitions**:
```
PENDING ──upload──> PROCESSING ──success──> COMPLETED
                         │
                         └──error──> FAILED
```

**Indexes** (for search/filtering):
- Primary key: `document_id`
- Indexes: `department`, `document_type`, `processing_status`, `upload_timestamp`

---

### 2. Chunk

Represents a processed segment of a document with embeddings and quality metrics.

**Schema**:
```python
class Chunk(BaseModel):
    chunk_id: str = Field(..., description="UUID for chunk")
    document_id: str = Field(..., description="Foreign key to Document")
    chunk_text: str = Field(..., min_length=50, max_length=2000)
    chunk_size: int = Field(..., ge=50, description="Character count")
    chunk_index: int = Field(..., ge=0, description="Sequential position in document")

    # Hierarchical relationships
    parent_chunk_id: Optional[str] = Field(None, description="Parent chunk for hierarchical retrieval")
    parent_text: Optional[str] = Field(None, max_length=2000, description="Parent context for quality validation")
    child_chunk_ids: List[str] = Field(default_factory=list, description="Child chunks if this is a parent")

    # Chapter information
    chapter_number: Optional[str] = Field(None, max_length=50, description="e.g., 1.2.3")
    chapter_title: Optional[str] = Field(None, max_length=200)
    chapter_level: Optional[int] = Field(None, ge=1, le=6, description="Nesting depth")
    chapter_path: Optional[str] = Field(None, max_length=500, description="e.g., 1 > 1.2 > 1.2.3")
    sub_chapter: Optional[str] = Field(None, max_length=100)

    # Quality metrics
    quality_score: float = Field(..., ge=0, le=100, description="Overall quality (RAGAS-style)")
    quality_metrics: dict = Field(
        ...,
        description="faithfulness, answer_relevancy, context_precision, context_recall"
    )

    # Embeddings (stored in Qdrant, referenced here)
    embeddings_stored: bool = Field(False, description="Whether vectors are in Qdrant")
    vector_names: List[str] = Field(
        default_factory=lambda: ["chunk_embedding", "parent_embedding", "child_embedding", "full_doc_embedding", "keyword_sparse"]
    )

    # Metadata
    position_in_document: int = Field(..., ge=0, description="Character offset in original document")
    created_at: datetime

    # Source document metadata (denormalized for fast retrieval)
    document_name: str
    department: str
    category: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "660e8400-e29b-41d4-a716-446655440001",
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "chunk_text": "Emergency braking procedures must be followed...",
                "chunk_size": 512,
                "chunk_index": 42,
                "parent_chunk_id": "660e8400-e29b-41d4-a716-446655440040",
                "chapter_number": "5.2.1",
                "chapter_title": "Emergency Procedures",
                "chapter_level": 3,
                "chapter_path": "5 > 5.2 > 5.2.1",
                "quality_score": 92.5,
                "quality_metrics": {
                    "faithfulness": 95.0,
                    "answer_relevancy": 90.0,
                    "context_precision": 92.0,
                    "context_recall": 93.0
                },
                "embeddings_stored": True,
                "document_name": "Safety_Manual_2024.pdf",
                "department": "Safety"
            }
        }
```

**Validation Rules**:
- `chunk_text` must have minimum 50 characters (configurable)
- `quality_score` >= threshold (default 85) to be indexed
- `chapter_level` corresponds to depth (1 = top level, 2 = subsection, etc.)
- `parent_chunk_id` must reference existing chunk (if not None)
- `quality_metrics` must contain all 4 required keys

**Relationships**:
- **Many-to-One** with Document (`document_id`)
- **Parent-Child** with self (`parent_chunk_id`, `child_chunk_ids`)
- **Many-to-One** with Chapter (logical, via `chapter_number`)

---

### 3. Chapter

Represents a hierarchical section of a document with structural metadata.

**Schema**:
```python
class Chapter(BaseModel):
    chapter_id: str = Field(..., description="UUID for chapter")
    document_id: str = Field(..., description="Foreign key to Document")
    chapter_number: str = Field(..., max_length=50, description="e.g., 1.2.3, A.1, Chapter 5")
    chapter_title: str = Field(..., min_length=1, max_length=200)
    chapter_level: int = Field(..., ge=1, le=6, description="1=top, 2=section, 3=subsection, etc.")
    chapter_path: str = Field(..., max_length=500, description="Full hierarchy, e.g., 1 > 1.2 > 1.2.3")

    # Hierarchical relationships
    parent_chapter_id: Optional[str] = Field(None, description="Parent chapter (if not root)")
    child_chapter_ids: List[str] = Field(default_factory=list, description="Immediate children")

    # Position in document
    start_position: int = Field(..., ge=0, description="Character offset where chapter starts")
    end_position: Optional[int] = Field(None, ge=0, description="Character offset where chapter ends")

    # Statistics
    chunk_count: int = Field(0, ge=0, description="Number of chunks in this chapter")

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_id": "770e8400-e29b-41d4-a716-446655440002",
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "chapter_number": "5.2",
                "chapter_title": "Emergency Response",
                "chapter_level": 2,
                "chapter_path": "5 > 5.2",
                "parent_chapter_id": "770e8400-e29b-41d4-a716-446655440001",
                "child_chapter_ids": ["770e8400-...", "770e8400-..."],
                "start_position": 12500,
                "end_position": 18200,
                "chunk_count": 12
            }
        }
```

**Validation Rules**:
- `chapter_level` must match depth in `chapter_path` (level 3 → 3 elements in path)
- `parent_chapter_id` must reference chapter with `chapter_level` = this.level - 1
- `chapter_number` must be unique within document
- `end_position` >= `start_position`

---

### 4. Search Query

Represents a user search request with filters and configuration.

**Schema**:
```python
class SearchMode(str, Enum):
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    HIERARCHICAL = "hierarchical"
    RAILWAY_SPECIFIC = "railway_specific"

class SearchQuery(BaseModel):
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query_text: str = Field(..., min_length=3, max_length=1000)
    query_embedding: Optional[List[float]] = Field(None, description="Generated from query_text")

    # Search configuration
    search_mode: SearchMode = SearchMode.SEMANTIC
    result_limit: int = Field(10, ge=1, le=100)
    alpha_weight: float = Field(0.5, ge=0.0, le=1.0, description="Hybrid search: semantic vs keyword weight")

    # Filters
    filter_department: Optional[str] = None
    filter_category: Optional[str] = None
    filter_document_name: Optional[str] = None
    filter_document_type: Optional[DocumentType] = None
    filter_chapter_number: Optional[str] = None

    # Railway-specific filters
    filter_fleet_type: Optional[str] = None
    filter_train_id: Optional[str] = None
    filter_standard_compliance: Optional[str] = None
    filter_network_component: Optional[str] = None

    # Metadata
    user_id: Optional[str] = Field(None, description="Optional API key or user identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field("api", description="api, openwebui, n8n, etc.")

    class Config:
        json_schema_extra = {
            "example": {
                "query_text": "emergency braking procedures for EMU trains",
                "search_mode": "hybrid",
                "result_limit": 10,
                "alpha_weight": 0.7,
                "filter_department": "Safety",
                "filter_fleet_type": "EMU",
                "source": "openwebui"
            }
        }
```

**Validation Rules**:
- `query_text` sanitized (remove special characters: `<>{}\\`)
- `alpha_weight` only applies when `search_mode` = HYBRID
- At least one of: `query_text`, filters must be provided
- `filter_chapter_number` validated against chapter number format (regex)

---

### 5. Search Result

Represents a retrieved chunk matching a query with ranking information.

**Schema**:
```python
class SearchResult(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query_id: str = Field(..., description="Foreign key to SearchQuery")
    chunk_id: str = Field(..., description="Foreign key to Chunk")

    # Chunk content (denormalized for convenience)
    chunk_text: str
    chunk_reference: dict = Field(..., description="document_name, chapter_number, chunk_index")

    # Scoring
    relevance_score: float = Field(..., ge=0, le=1, description="Cosine similarity or RRF score")
    ranking_position: int = Field(..., ge=1, description="1 = top result")

    # Source information
    source_document: str = Field(..., description="Document name")
    chapter_context: Optional[dict] = Field(None, description="chapter_number, chapter_title, chapter_path")
    quality_score: float = Field(..., ge=0, le=100, description="Chunk quality score")

    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional chunk metadata")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "880e8400-e29b-41d4-a716-446655440003",
                "chunk_id": "660e8400-e29b-41d4-a716-446655440001",
                "chunk_text": "Emergency braking procedures must be followed...",
                "chunk_reference": {
                    "document_name": "Safety_Manual_2024.pdf",
                    "chapter_number": "5.2.1",
                    "chunk_index": 42
                },
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
        }
```

**Validation Rules**:
- `relevance_score` range depends on search mode (cosine: [0, 1], RRF: [0, 1] normalized)
- `ranking_position` must be unique within query results
- `chunk_reference` must contain: document_name, chapter_number (if available), chunk_index

---

### 6. Department

Represents an organizational unit owning documents.

**Schema**:
```python
class Department(BaseModel):
    department_id: str = Field(..., description="UUID or short code (e.g., 'HR', 'SAFETY')")
    department_name: str = Field(..., min_length=1, max_length=100, description="Human-readable name")
    document_count: int = Field(0, ge=0, description="Total documents in department")
    total_indexed_chunks: int = Field(0, ge=0, description="Total chunks across all documents")
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "department_id": "SAFETY",
                "department_name": "Safety & Compliance",
                "document_count": 42,
                "total_indexed_chunks": 3580
            }
        }
```

**Validation Rules**:
- `department_name` must be unique
- `department_id` should use uppercase, no spaces (e.g., "HR", "OPERATIONS")
- Supported departments (21 total): HR, Safety, Operations, Maintenance, Engineering, Finance, IT, Procurement, Legal, Quality, Training, Facilities, Security, Communications, Planning, Projects, CustomerService, Assets, Performance, Risk, Compliance

---

### 7. Embedding Model Config

Represents embedding service configuration and status.

**Schema**:
```python
class ServiceType(str, Enum):
    SENTENCE_TRANSFORMERS = "sentence-transformers"
    OLLAMA = "ollama"

class ModelStatus(str, Enum):
    LOADED = "loaded"
    UNLOADED = "unloaded"
    ERROR = "error"

class EmbeddingModelConfig(BaseModel):
    config_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str = Field(..., description="e.g., all-mpnet-base-v2, snowflake-arctic-embed2")
    embedding_dimension: int = Field(..., ge=384, le=2048, description="768 or 1024 for supported models")
    service_type: ServiceType
    service_url: Optional[str] = Field(None, description="URL for Ollama service")
    model_status: ModelStatus = ModelStatus.UNLOADED
    is_active: bool = Field(False, description="Currently selected model")

    # Performance metrics
    avg_embedding_time_ms: Optional[float] = Field(None, ge=0)
    last_health_check: Optional[datetime] = None

    # Configuration
    batch_size: int = Field(32, ge=1, le=256, description="Batch size for embedding generation")

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "all-mpnet-base-v2",
                "embedding_dimension": 768,
                "service_type": "sentence-transformers",
                "model_status": "loaded",
                "is_active": True,
                "avg_embedding_time_ms": 45.2,
                "batch_size": 32
            }
        }
```

**Validation Rules**:
- Only one config can have `is_active` = True at a time
- `embedding_dimension` must match Qdrant collection vector size
- `service_url` required if `service_type` = OLLAMA
- `model_status` = LOADED required before use

---

### 8. Processing Profile

Represents document processing configuration for different use cases.

**Schema**:
```python
class ProfileName(str, Enum):
    RAILWAY = "RAILWAY"
    TECHNICAL = "TECHNICAL"
    GENERAL = "GENERAL"

class ProcessingProfile(BaseModel):
    profile_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_name: ProfileName
    description: str = Field(..., max_length=500)

    # Chunking parameters
    parent_chunk_size: int = Field(1500, ge=500, le=3000)
    child_chunk_size: int = Field(500, ge=100, le=1000)
    chunk_overlap: int = Field(200, ge=0, le=500)

    # Quality validation
    quality_threshold: float = Field(85.0, ge=0, le=100)
    enable_quality_validation: bool = True

    # Search configuration
    enable_hybrid_search: bool = True
    default_alpha: float = Field(0.5, ge=0, le=1)

    # Feature flags
    enable_chapter_extraction: bool = True
    enable_railway_metadata: bool = False

    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "profile_name": "RAILWAY",
                "description": "Optimized for railway technical documentation with chapter awareness",
                "parent_chunk_size": 1500,
                "child_chunk_size": 500,
                "chunk_overlap": 200,
                "quality_threshold": 85.0,
                "enable_quality_validation": True,
                "enable_hybrid_search": True,
                "enable_chapter_extraction": True,
                "enable_railway_metadata": True,
                "is_default": True
            }
        }
```

**Validation Rules**:
- `parent_chunk_size` > `child_chunk_size`
- `chunk_overlap` < `child_chunk_size`
- Only one profile can have `is_default` = True
- `profile_name` must be unique

---

## Relationships Summary

| Parent | Child | Relationship | Cascade |
|--------|-------|--------------|---------|
| Department | Document | 1:N | No (preserve department on doc delete) |
| Document | Chapter | 1:N | Yes (delete chapters when doc deleted) |
| Document | Chunk | 1:N | Yes (delete chunks when doc deleted) |
| Chapter | Chunk | 1:N (logical) | No (chunks reference chapter, not owned by it) |
| Chunk | Chunk (parent-child) | 1:N | No (keep orphaned chunks, mark parent_id = null) |
| SearchQuery | SearchResult | 1:N | Yes (delete results when query logged out) |

## Storage Strategy

### Qdrant (Vector Storage)

**Collection**: `nomad_bms_documents`

**Stored Fields**:
- **Vectors**: chunk_embedding, parent_embedding, child_embedding, full_doc_embedding (all 768d), keyword_sparse
- **Payload**: All Chunk fields (excluding embeddings themselves) + denormalized Document/Chapter metadata

**Access Pattern**:
- Write: Upsert after chunk processing (batch 100-1000 points)
- Read: Search queries with filters
- Update: Re-index specific documents (delete old chunks, insert new)
- Delete: Remove all points with `document_id` filter

### PostgreSQL / SQLite (Metadata Storage - Optional)

**Purpose**: Store Document, Department, EmbeddingModelConfig, ProcessingProfile for relational queries

**Why Optional**: Qdrant payload can store all metadata, but relational DB provides:
- Better query performance for document listing, filtering by status
- Transaction support for multi-document operations
- Easier reporting and analytics

**Decision**: For MVP, use Qdrant-only (simpler). Add PostgreSQL if complex relational queries needed.

### File System (Document Storage)

**Path Structure**:
```
/workspace/bms-agent/upload-files/
├── HR/
│   ├── doc1.pdf
│   └── doc2.docx
├── Safety/
│   ├── manual1.pdf
│   └── procedures.md
└── [19 more departments]/
```

**Access Pattern**:
- Write: On upload, stream to department folder
- Read: During processing, read-once then discard from memory
- Delete: Manual cleanup or automated retention policy (out of scope)

## Migration Considerations

**Adding New Fields**:
- Qdrant: Add to payload, no schema migration needed (schema-less JSON)
- PostgreSQL (if used): Standard ALTER TABLE migrations

**Changing Vector Dimensions**:
- Requires full collection recreation (Qdrant doesn't support dimension changes)
- Process: Create new collection → Re-process all documents → Switch collection name → Delete old collection

**Data Retention**:
- Documents: Manual deletion only (no automated retention in MVP)
- Search queries/results: Optional logging (not required for core functionality)
- Logs: Rotate every 30 days (handled by external log rotation)

## Validation Summary

**Input Validation** (FastAPI Pydantic models):
- All API requests validated against schemas above
- Custom validators for department names, chapter numbers, file types

**Business Logic Validation**:
- Quality score thresholds before indexing
- Parent-child chunk relationships (parent must exist before child)
- Document size limits (100MB hard limit)
- Concurrent processing limits (prevent OOM with large batch uploads)

**Data Integrity**:
- Foreign key relationships maintained via UUIDs
- Orphaned chunk handling (mark parent_id=null if parent deleted)
- Collection existence check before Qdrant operations

## Performance Considerations

**Estimated Data Sizes**:
- **Document**: ~1KB per record (metadata only)
- **Chunk**: ~4KB in Qdrant (vectors + payload)
- **Chapter**: ~500 bytes per record
- **SearchQuery**: ~500 bytes per record
- **SearchResult**: ~2KB per result (with denormalized chunk text)

**Scaling**:
- **300 documents** × 50 chunks/doc = **15,000 chunks**
- 15,000 chunks × 4KB = **60MB** in Qdrant
- Acceptable for single-node deployment

**Bottlenecks**:
- Embedding generation (CPU-bound, 2-5ms per chunk)
- Qdrant indexing (fast, <1ms per point)
- File I/O during processing (disk-bound for large PDFs)

**Optimization Strategies**:
- Batch embedding generation (32-64 chunks at once)
- Async document processing (background tasks)
- Qdrant batch upsert (100-1000 points per request)
- In-memory caching for frequently accessed documents (future enhancement)
