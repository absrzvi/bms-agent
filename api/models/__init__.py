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

from .audit import (
    AuditLog,
    UserIdentity,
    EventType,
    UserRole
)

from .metrics import (
    OperationalMetrics,
    MetricWindow,
    LatencyMetrics,
    IngestionMetrics,
    ErrorMetrics
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
    
    # Audit
    "AuditLog",
    "UserIdentity",
    "EventType",
    "UserRole",
    
    # Metrics
    "OperationalMetrics",
    "MetricWindow",
    "LatencyMetrics", 
    "IngestionMetrics",
    "ErrorMetrics"
]
