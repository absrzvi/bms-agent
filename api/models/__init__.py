"""
BMS Agent API Data Models

Pydantic models for the BMS Agent API based on data-model.md specification.
"""

from .documents import (
    Document,
    DocumentVersion,
    Chunk,
    ChunkEmbedding,
    DocumentStatus,
    ContentType,
    HierarchyType
)

from .search import (
    RetrievalQuery,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SemanticSearchRequest,
    HybridSearchRequest
)

from .health import (
    HealthStatus,
    HealthCheck,
    ServiceStatus,
    SystemHealth
)

# Audit and metrics modules not yet implemented (production tasks)
# from .audit import (
#     AuditLog,
#     UserIdentity,
#     EventType,
#     UserRole
# )

# from .metrics import (
#     OperationalMetrics,
#     MetricWindow,
#     LatencyMetrics,
#     IngestionMetrics,
#     ErrorMetrics
# )

# Upload status models for async queue
from .upload_status import (
    UploadStatus,
    UploadJobStatus,
    UploadJobCreate
)

__all__ = [
    # Documents
    "Document",
    "DocumentVersion", 
    "Chunk",
    "ChunkEmbedding",
    "DocumentStatus",
    "ContentType",
    "HierarchyType",
    
    # Search
    "RetrievalQuery",
    "SearchRequest",
    "SearchResponse", 
    "SearchResult",
    "SemanticSearchRequest",
    "HybridSearchRequest",
    
    # Health
    "HealthStatus",
    "HealthCheck",
    "ServiceStatus",
    "SystemHealth",
    
    # Audit (not yet implemented)
    # "AuditLog",
    # "UserIdentity",
    # "EventType",
    # "UserRole",
    
    # Metrics (not yet implemented)
    # "OperationalMetrics",
    # "MetricWindow",
    # "LatencyMetrics", 
    # "IngestionMetrics",
    # "ErrorMetrics",
    
    # Upload Status
    "UploadStatus",
    "UploadJobStatus",
    "UploadJobCreate"
]
