"""
Document-related Pydantic models for BMS Agent API

Based on data-model.md specification with Enhanced Document Processor v4.0 features.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class ContentType(str, Enum):
    """Supported document content types"""
    PDF = "pdf"
    DOCX = "docx" 
    PPTX = "pptx"
    CSV = "csv"
    XLSX = "xlsx"
    TXT = "txt"


class DocumentStatus(str, Enum):
    """Document processing status"""
    INGESTED = "ingested"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class HierarchyType(str, Enum):
    """Chunk hierarchy types"""
    PARENT = "parent"
    CHILD = "child"


class Document(BaseModel):
    """Document entity model"""
    document_id: UUID = Field(default_factory=uuid4, description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    source_path: str = Field(..., description="Source file path")
    content_type: ContentType = Field(..., description="Document content type")
    ingested_at: datetime = Field(default_factory=datetime.utcnow, description="Ingestion timestamp")
    checksum: str = Field(..., description="File checksum for integrity")
    size_bytes: int = Field(..., ge=0, le=1073741824, description="File size in bytes (max 1GB)")
    version: int = Field(default=1, ge=1, description="Document version number")
    
    @validator('size_bytes')
    def validate_size(cls, v):
        if v > 1073741824:  # 1GB limit
            raise ValueError('File size exceeds 1GB limit')
        return v
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class DocumentVersion(BaseModel):
    """Document version entity model"""
    version_id: UUID = Field(default_factory=uuid4, description="Unique version identifier")
    document_id: UUID = Field(..., description="Parent document ID")
    version_number: int = Field(..., ge=1, description="Sequential version number")
    status: DocumentStatus = Field(default=DocumentStatus.INGESTED, description="Processing status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Version creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    notes: Optional[str] = Field(None, description="Processing notes or error messages")
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class Chunk(BaseModel):
    """Document chunk entity model"""
    chunk_id: UUID = Field(default_factory=uuid4, description="Unique chunk identifier")
    version_id: UUID = Field(..., description="Parent document version ID")
    chunk_index: int = Field(..., ge=0, description="Zero-based chunk index")
    text: str = Field(..., description="Chunk text content")
    token_count: int = Field(..., ge=0, le=1500, description="Token count (max 1500)")
    hierarchy: HierarchyType = Field(..., description="Chunk hierarchy type")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Chunk creation timestamp")
    
    @validator('token_count')
    def validate_token_count(cls, v):
        if v > 1500:
            raise ValueError('Token count exceeds 1500 limit')
        return v
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ChunkEmbedding(BaseModel):
    """Chunk embedding entity model with Enhanced Document Processor v4.0 features"""
    chunk_id: UUID = Field(..., description="Parent chunk ID")
    
    # Multi-vector embeddings (1024-d each)
    chunk_embedding: List[float] = Field(..., description="Primary chunk embedding (1024-d)")
    parent_embedding: List[float] = Field(..., description="Parent context embedding (1024-d)")
    child_embedding: List[float] = Field(..., description="Child context embedding (1024-d)")
    full_doc_embedding: List[float] = Field(..., description="Full document embedding (1024-d)")
    
    # Sparse vector for BM25/keyword search
    keyword_sparse: Dict[str, float] = Field(default_factory=dict, description="Sparse keyword vector")
    
    # Standard metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    embedding_model: str = Field(default="snowflake-arctic-embed2", description="Embedding model used")
    embedding_version: str = Field(..., description="Model version")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Embedding creation timestamp")
    
    # Enhanced Document Processor v4.0 features
    contextual_description: Optional[str] = Field(None, description="Contextual description of chunk")
    surrounding_context: Optional[str] = Field(None, description="Surrounding context information")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score (≥0.70 for production)")
    faithfulness: Optional[float] = Field(None, ge=0.0, le=1.0, description="RAGAS faithfulness score")
    relevancy: Optional[float] = Field(None, ge=0.0, le=1.0, description="RAGAS relevancy score")
    precision: Optional[float] = Field(None, ge=0.0, le=1.0, description="RAGAS precision score")
    recall: Optional[float] = Field(None, ge=0.0, le=1.0, description="RAGAS recall score")
    has_context: bool = Field(default=False, description="Whether chunk has contextual information")
    context_type: Optional[str] = Field(None, description="Type of context preserved")
    late_chunking_applied: bool = Field(default=False, description="Whether late chunking was applied")
    processing_version: str = Field(default="v4.0", description="Document processor version")
    technical_terms: List[str] = Field(default_factory=list, description="Extracted technical terms")
    entity_types: List[str] = Field(default_factory=list, description="Identified entity types")
    
    @validator('chunk_embedding', 'parent_embedding', 'child_embedding', 'full_doc_embedding')
    def validate_embedding_dimension(cls, v):
        if len(v) != 1024:
            raise ValueError('Embedding must be 1024-dimensional')
        return v
    
    @validator('quality_score')
    def validate_quality_score(cls, v):
        if v < 0.70:
            raise ValueError('Quality score must be ≥0.70 for production use')
        return v
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
