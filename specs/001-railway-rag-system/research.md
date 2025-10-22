# Technical Research: BMS Agent RAG System

**Date**: 2025-10-22
**Feature**: Railway Documentation RAG System
**Purpose**: Document technology choices, best practices, and design decisions for implementation

## Research Topics

### 1. Embedding Model Selection

**Decision**: Dual support for sentence-transformers and Ollama with runtime configuration

**Rationale**:
- **sentence-transformers** (`all-mpnet-base-v2`, 768d):
  - Faster batch processing (no API overhead)
  - Smaller model footprint (2GB RAM)
  - Deterministic embeddings (no model server variability)
  - Best for: Batch document ingestion, consistent quality

- **Ollama** (`snowflake-arctic-embed2`, 1024d):
  - Higher dimensional embeddings (potentially better semantic capture)
  - Unified interface with LLM workflows
  - Model updates without code changes
  - Best for: Real-time search, integration with existing Ollama infrastructure

**Implementation Strategy**:
```python
class EmbeddingService:
    def __init__(self, provider: str = "sentence-transformers"):
        if provider == "sentence-transformers":
            self.model = SentenceTransformer('all-mpnet-base-v2')
            self.dimension = 768
        elif provider == "ollama":
            self.endpoint = os.getenv("EMBEDDING_URL", "http://localhost:11434/api/embeddings")
            self.model_name = "snowflake-arctic-embed2"
            self.dimension = 1024

    async def embed(self, texts: List[str]) -> List[List[float]]:
        # Provider-specific implementation
        pass
```

**Alternatives Considered**:
- OpenAI embeddings (rejected: external dependency, cost, network latency)
- BGE models (rejected: similar performance to all-mpnet, less mature ecosystem)
- Cohere embeddings (rejected: external dependency, cost)

### 2. Quality Validation Metrics (RAGAS-Style)

**Decision**: Implement simplified RAGAS-style metrics for chunk quality scoring

**Approach**:
```python
def compute_quality_score(chunk: dict) -> dict:
    """
    Returns: {
        'faithfulness': 0-100,      # Text coherence, no truncation artifacts
        'answer_relevancy': 0-100,   # Semantic density, topical consistency
        'context_precision': 0-100,  # Information specificity
        'context_recall': 0-100,     # Parent-child overlap verification
        'overall': 0-100             # Weighted average
    }
    """
    faithfulness = check_faithfulness(chunk['text'])
    relevancy = check_relevancy(chunk['text'], chunk['parent_text'])
    precision = check_precision(chunk['text'], chunk['chapter_title'])
    recall = check_recall(chunk['text'], chunk['parent_text'])

    overall = (faithfulness * 0.3 + relevancy * 0.3 + precision * 0.2 + recall * 0.2)
    return {'overall': overall, ...}
```

**Faithfulness Checks**:
- No truncated sentences (last sentence has ending punctuation)
- No orphaned bullets/lists (checks for matching open/close markers)
- Minimum word count (>30 words)
- No excessive whitespace or formatting artifacts

**Relevancy Checks**:
- Embedding similarity between chunk and parent (>0.7 cosine)
- Topic consistency (keyword overlap with chapter title)
- No generic boilerplate text (checks against patterns like "Table of Contents", "Page N")

**Precision Checks**:
- Information density (unique tokens / total tokens > 0.4)
- Sentence completeness (no sentence fragments)
- Technical term presence (railway vocabulary check)

**Recall Checks**:
- Parent-child overlap verification (>10% token overlap)
- Context window coverage (chunk + overlap contains key parent information)

**Threshold Tuning**:
- Default: 85% overall score
- Railway-specific: May need lowering to 80% for highly structured/tabular content
- Can be overridden per deployment via `BMS_QUALITY_THRESHOLD` env var

**Best Practices**:
- Log all filtered chunks with scores for threshold tuning
- Provide quality score in search results for user transparency
- Allow quality threshold override in search API for power users

**Alternatives Considered**:
- Full RAGAS implementation (rejected: requires LLM for evaluation, too slow)
- Perplexity-based quality (rejected: requires language model, computational cost)
- Rule-based only (rejected: insufficient signal for edge cases)

### 3. Hybrid Search with Reciprocal Rank Fusion (RRF)

**Decision**: Implement RRF to combine dense and sparse vector search results

**Algorithm**:
```python
def reciprocal_rank_fusion(
    dense_results: List[ScoredPoint],
    sparse_results: List[ScoredPoint],
    alpha: float = 0.5,  # Weight for dense vs sparse (0=sparse only, 1=dense only)
    k: int = 60          # RRF constant (typical range: 60-100)
) -> List[ScoredPoint]:
    """
    RRF formula: score(d) = α * (1/(k + rank_dense(d))) + (1-α) * (1/(k + rank_sparse(d)))
    """
    # Create rank dictionaries
    dense_ranks = {result.id: rank for rank, result in enumerate(dense_results, 1)}
    sparse_ranks = {result.id: rank for rank, result in enumerate(sparse_results, 1)}

    # Collect all unique doc IDs
    all_ids = set(dense_ranks.keys()) | set(sparse_ranks.keys())

    # Compute RRF scores
    fused_scores = {}
    for doc_id in all_ids:
        dense_rank = dense_ranks.get(doc_id, len(dense_results) + 1)
        sparse_rank = sparse_ranks.get(doc_id, len(sparse_results) + 1)

        rrf_score = alpha * (1 / (k + dense_rank)) + (1 - alpha) * (1 / (k + sparse_rank))
        fused_scores[doc_id] = rrf_score

    # Sort by fused score descending
    return sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
```

**Alpha Tuning Recommendations**:
- **α = 0.7-0.8**: Semantic-heavy (natural language queries, concept search)
- **α = 0.5**: Balanced (default, works well for mixed queries)
- **α = 0.2-0.3**: Keyword-heavy (model numbers, acronyms, exact terms)

**RRF Constant (k) Tuning**:
- **k = 60**: Standard, gives top-ranked results more weight
- **k = 100**: Flatter ranking, more democratic fusion
- Recommendation: k=60 for most use cases

**Best Practices**:
- Expose `alpha` as query parameter for power users
- Default to α=0.5 for general search endpoint
- Log alpha values with search queries for analytics/tuning
- Consider per-department alpha tuning (technical docs may benefit from higher keyword weight)

**Alternatives Considered**:
- Linear combination of scores (rejected: requires score normalization, less robust)
- Borda count (rejected: doesn't leverage rank position information as effectively)
- CombSUM/CombMNZ (rejected: score distribution assumptions don't hold across dense/sparse)

### 4. Chapter Extraction Patterns

**Decision**: Multi-strategy chapter detection with hierarchical fallback

**Strategies** (applied in order):

1. **Markdown Headers**:
```python
def extract_markdown_chapters(text: str) -> List[Chapter]:
    patterns = [
        r'^#{1,6}\s+(.+)$',          # # Header, ## Subheader, etc.
        r'^(.+)\n[=-]{3,}$'          # Underline-style headers
    ]
    # Parse into hierarchical structure based on # count
```

2. **Numbered Sections**:
```python
def extract_numbered_chapters(text: str) -> List[Chapter]:
    patterns = [
        r'^(\d+(?:\.\d+)*)\s+(.+)$',          # 1.2.3 Title
        r'^([A-Z]\d+(?:\.\d+)*)\s+(.+)$',     # A1.2 Title (appendices)
        r'^(?:Chapter|Section)\s+(\d+)[:\s]+(.+)$'  # Chapter 5: Title
    ]
    # Build chapter_path: "1 > 1.2 > 1.2.3"
```

3. **Word-Style Headings**:
```python
def extract_styled_chapters(docx_doc) -> List[Chapter]:
    # Use python-docx to detect heading styles
    for para in docx_doc.paragraphs:
        if para.style.name.startswith('Heading'):
            level = int(para.style.name.replace('Heading ', ''))
            # Extract chapter info
```

4. **Fallback (No Detectable Structure)**:
```python
def create_pseudo_chapters(text: str, chunk_size: int = 1500) -> List[Chapter]:
    # Divide into logical sections based on double newlines or page breaks
    # Assign sequential numbers: "Section 1", "Section 2", etc.
```

**Hierarchical Path Construction**:
```python
def build_chapter_path(chapter_number: str) -> str:
    """
    Input: "1.2.3"
    Output: "1 > 1.2 > 1.2.3"
    """
    parts = chapter_number.split('.')
    path_elements = ['.'.join(parts[:i+1]) for i in range(len(parts))]
    return ' > '.join(path_elements)
```

**Best Practices**:
- Run all strategies and merge results (strategy priority order if conflicts)
- Store chapter metadata in chunk payload for filtering
- Log detection statistics per document (useful for accuracy tracking)
- Provide manual chapter override via metadata file (chapter_overrides.json)

**Accuracy Targets**:
- Well-structured docs (markdown, numbered): 95%+ detection accuracy
- Unstructured docs (plain text): Fallback to pseudo-chapters (100% coverage, lower semantic accuracy)

**Alternatives Considered**:
- ML-based heading detection (rejected: requires training data, overkill for structured docs)
- PDF table-of-contents extraction only (rejected: not all PDFs have TOC metadata)
- Page-based chunking only (rejected: loses semantic boundaries)

### 5. Metrics Collection Without Distributed Tracing

**Decision**: In-memory metrics with periodic aggregation and health endpoint exposure

**Architecture**:
```python
class MetricsCollector:
    def __init__(self):
        self.request_count = 0
        self.latencies = []  # Rolling window of last 1000 latencies
        self.error_count = 0
        self.queue_depth = 0  # Current ingestion queue size

    def record_request(self, latency_ms: float, error: bool = False):
        self.request_count += 1
        self.latencies.append(latency_ms)
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-1000:]  # Keep last 1000
        if error:
            self.error_count += 1

    def get_metrics(self) -> dict:
        return {
            'request_count': self.request_count,
            'latency_p50': np.percentile(self.latencies, 50),
            'latency_p95': np.percentile(self.latencies, 95),
            'latency_p99': np.percentile(self.latencies, 99),
            'error_rate': self.error_count / max(self.request_count, 1),
            'queue_depth': self.queue_depth
        }
```

**Health Endpoint Implementation**:
```python
@app.get("/metrics")
async def get_metrics():
    metrics = metrics_collector.get_metrics()
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'bms-agent-api',
        'metrics': metrics,
        'thresholds': {
            'latency_p95_threshold_ms': 2000,
            'error_rate_threshold': 0.01,  # 1%
        },
        'health': 'healthy' if metrics['latency_p95'] < 2000 and metrics['error_rate'] < 0.01 else 'degraded'
    }
```

**Prometheus-Compatible Format** (optional):
```python
@app.get("/metrics/prometheus")
async def get_prometheus_metrics():
    metrics = metrics_collector.get_metrics()
    return f"""
# HELP bms_requests_total Total number of requests
# TYPE bms_requests_total counter
bms_requests_total {metrics['request_count']}

# HELP bms_request_latency_milliseconds Request latency percentiles
# TYPE bms_request_latency_milliseconds summary
bms_request_latency_milliseconds{{quantile="0.5"}} {metrics['latency_p50']}
bms_request_latency_milliseconds{{quantile="0.95"}} {metrics['latency_p95']}
bms_request_latency_milliseconds{{quantile="0.99"}} {metrics['latency_p99']}

# HELP bms_errors_total Total number of errors
# TYPE bms_errors_total counter
bms_errors_total {metrics['error_count']}
"""
```

**Best Practices**:
- Reset counters on service restart (in-memory only, no persistence needed)
- Use middleware to automatically instrument all endpoints
- Log metrics to file every 5 minutes for historical analysis
- Expose metrics in both JSON (default) and Prometheus format

**Limitations Accepted**:
- No cross-service tracing (can't track request through FastAPI → Qdrant → Ollama)
- No distributed aggregation (single node metrics only)
- No long-term metric storage (file logs only)

**Alternatives Considered**:
- OpenTelemetry with Jaeger (rejected: too complex for minimal observability requirement)
- StatsD + Graphite (rejected: requires additional infrastructure)
- Prometheus + Grafana (rejected: overkill for basic metrics, but format kept for future compatibility)

### 6. FastAPI Best Practices

**Async Processing for Long-Running Ingestion**:
```python
from fastapi import BackgroundTasks

@app.post("/api/v1/upload")
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    department: str
):
    # Save file immediately
    file_path = await save_upload(file, department)

    # Queue processing as background task
    background_tasks.add_task(process_document, file_path, department)

    # Return immediately with job ID
    return {
        'status': 'accepted',
        'file_path': file_path,
        'job_id': generate_job_id(),
        'message': 'Document uploaded, processing in background'
    }

async def process_document(file_path: str, department: str):
    # Long-running: extract, chunk, embed, index
    try:
        processor.process(file_path, department)
        metrics_collector.record_request(latency, error=False)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        metrics_collector.record_request(latency, error=True)
```

**File Upload Handling for 100MB Documents**:
```python
from fastapi import File, UploadFile, HTTPException

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    # Stream file to disk to avoid memory overflow
    file_path = f"/workspace/bms-agent/upload-files/temp/{file.filename}"

    size = 0
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(8192):  # 8KB chunks
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                await f.close()
                os.remove(file_path)
                raise HTTPException(413, f"File exceeds {MAX_FILE_SIZE} byte limit")
            await f.write(chunk)

    return {'file_path': file_path, 'size': size}
```

**CORS Configuration for OpenWebUI Integration**:
```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           # OpenWebUI dev
        "http://localhost:8080",           # OpenWebUI prod
        os.getenv("OPENWEBUI_URL", "*")    # Configurable
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**Request Validation**:
```python
from pydantic import BaseModel, Field, validator

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    department: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)
    alpha: float = Field(0.5, ge=0.0, le=1.0)  # Hybrid search weight

    @validator('query')
    def sanitize_query(cls, v):
        # Remove potential injection patterns
        v = re.sub(r'[<>{}\\]', '', v)
        return v.strip()
```

**Best Practices**:
- Use `async def` for all I/O-bound endpoints (Qdrant queries, file I/O)
- Use `def` (sync) for CPU-bound operations (embedding generation if synchronous)
- Stream large responses with `StreamingResponse`
- Use dependency injection for shared resources (Qdrant client, embedding service)
- Implement lifespan events for startup/shutdown (load models, close connections)

### 7. Qdrant Multi-Vector Indexing

**Collection Creation with Named Vectors**:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

client = QdrantClient(url="http://localhost:6333")

client.create_collection(
    collection_name="nomad_bms_documents",
    vectors_config={
        "chunk_embedding": VectorParams(size=768, distance=Distance.COSINE),
        "parent_embedding": VectorParams(size=768, distance=Distance.COSINE),
        "child_embedding": VectorParams(size=768, distance=Distance.COSINE),
        "full_doc_embedding": VectorParams(size=768, distance=Distance.COSINE),
    },
    sparse_vectors_config={
        "keyword_sparse": {}  # BM25-style sparse vector
    }
)
```

**Keyword Index Setup for Metadata Filtering**:
```python
from qdrant_client.models import PayloadSchemaType

# Create keyword indexes for fast filtering
client.create_payload_index(
    collection_name="nomad_bms_documents",
    field_name="department",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="nomad_bms_documents",
    field_name="chapter_number",
    field_schema=PayloadSchemaType.KEYWORD
)

# Text indexes for search within fields
client.create_payload_index(
    collection_name="nomad_bms_documents",
    field_name="document_name",
    field_schema=PayloadSchemaType.TEXT
)
```

**Point Insertion with Multi-Vector**:
```python
from qdrant_client.models import PointStruct, SparseVector

point = PointStruct(
    id=chunk_id,
    vector={
        "chunk_embedding": chunk_vector,      # [768] floats
        "parent_embedding": parent_vector,    # [768] floats
        "child_embedding": child_vector,      # [768] floats
        "full_doc_embedding": doc_vector,     # [768] floats
        "keyword_sparse": SparseVector(
            indices=[12, 45, 67, ...],        # Token IDs
            values=[0.8, 0.6, 0.5, ...]       # TF-IDF weights
        )
    },
    payload={
        "document_name": "Safety_Manual_2024.pdf",
        "department": "Safety",
        "chapter_number": "1.2.3",
        "chapter_title": "Emergency Procedures",
        "chunk_text": "...",
        "quality_score": 92.5,
        # ... other metadata
    }
)

client.upsert(collection_name="nomad_bms_documents", points=[point])
```

**Search with Specific Vector**:
```python
# Semantic search using chunk embeddings
results = client.search(
    collection_name="nomad_bms_documents",
    query_vector=("chunk_embedding", query_embedding),
    limit=10,
    query_filter={
        "must": [
            {"key": "department", "match": {"value": "Safety"}}
        ]
    }
)

# Hybrid search (dense + sparse)
results = client.search(
    collection_name="nomad_bms_documents",
    query_vector=("chunk_embedding", query_embedding),
    sparse_vector=("keyword_sparse", query_sparse_vector),
    limit=20  # Get more for RRF fusion
)
```

**Best Practices**:
- Create collection with `force_recreate=False` to avoid accidental data loss
- Use UUIDs for point IDs (avoid collisions)
- Batch upserts (100-1000 points per batch) for performance
- Use `scroll` API for iterating over large result sets
- Monitor collection size and reindex if schema changes needed

**Performance Considerations**:
- 768d vectors: ~3KB per chunk (4 vectors)
- Sparse vectors: ~200 bytes per chunk (typical)
- Metadata: ~500 bytes per chunk
- Total: ~3.7KB per chunk
- 10,000 chunks: ~37MB (fits in RAM)
- 100,000 chunks: ~370MB (still reasonable)

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Web Framework | FastAPI | 0.104+ | Async support, auto OpenAPI, Pydantic validation |
| Vector DB | Qdrant | 1.15.5+ | Multi-vector, sparse vector support, self-hosted |
| Embeddings | sentence-transformers / Ollama | 2.2+ / Latest | Dual support for flexibility |
| Document Processing | PyMuPDF, python-docx | Latest | Mature, reliable text extraction |
| NLP | NLTK, spaCy | 3.8+ / 3.7+ | Tokenization, entity recognition |
| Testing | pytest, pytest-asyncio | 7.4+ / 0.21+ | Async test support, fixtures |
| Metrics | Custom in-memory | N/A | Minimal complexity, Prometheus-compatible export |

## Open Questions & Future Research

1. **Embedding Model Benchmarking**:
   - Need to compare sentence-transformers vs. Ollama on railway domain queries
   - Metrics: Precision@10, Recall@10, MRR (Mean Reciprocal Rank)
   - Dataset: 100+ railway queries with ground truth documents

2. **Quality Threshold Tuning**:
   - Current default 85% based on general RAG best practices
   - Railway domain may have different characteristics (tabular data, appendices)
   - Recommend A/B testing 80%, 85%, 90% thresholds

3. **Hybrid Search Alpha Optimization**:
   - Default α=0.5 is generic
   - Could train per-department alpha values (Safety vs. HR vs. Technical)
   - Requires query log analysis and relevance feedback

4. **Caching Strategy**:
   - Not in MVP scope, but common queries could benefit from result caching
   - Redis or in-memory LRU cache for top-100 queries
   - Invalidation strategy on document updates

5. **Backup & Disaster Recovery**:
   - Current: Manual Qdrant data backup
   - Future: Automated snapshots, S3/MinIO backup target
   - RTO/RPO requirements undefined (assume 24-hour RTO, 1-hour RPO for internal system)

## References

- [Qdrant Multi-Vector Documentation](https://qdrant.tech/documentation/concepts/vectors/#multivectors)
- [RAGAS Framework](https://docs.ragas.io/en/latest/concepts/metrics/faithfulness.html)
- [Reciprocal Rank Fusion Paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [sentence-transformers Documentation](https://www.sbert.net/docs/pretrained_models.html)
