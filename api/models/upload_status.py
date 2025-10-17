"""
Upload Status Models for Async Document Processing
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class UploadStatus(str, Enum):
    """Upload processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadJobStatus(BaseModel):
    """Status of an upload job"""
    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original filename")
    status: UploadStatus = Field(..., description="Current processing status")
    created_at: str = Field(..., description="Job creation timestamp (ISO 8601)")
    started_at: Optional[str] = Field(None, description="Processing start timestamp")
    completed_at: Optional[str] = Field(None, description="Processing completion timestamp")
    progress_percent: int = Field(0, ge=0, le=100, description="Processing progress percentage")
    
    # Result fields (populated on completion)
    document_id: Optional[str] = Field(None, description="Generated document ID (on success)")
    chunks_created: Optional[int] = Field(None, description="Number of chunks created")
    quality_score: Optional[float] = Field(None, description="Document quality score")
    processing_time_ms: Optional[int] = Field(None, description="Total processing time in milliseconds")
    replaced_existing: bool = Field(False, description="Whether an existing document was replaced")
    deleted_chunks: int = Field(0, description="Number of chunks deleted from previous version")
    
    # Error fields (populated on failure)
    error: Optional[str] = Field(None, description="Error message (on failure)")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")
    
    class Config:
        use_enum_values = True


class UploadJobCreate(BaseModel):
    """Response when creating a new upload job"""
    job_id: str = Field(..., description="Unique job identifier")
    status: UploadStatus = Field(UploadStatus.QUEUED, description="Initial status (queued)")
    message: str = Field(..., description="Status message")
    status_url: str = Field(..., description="URL to check job status")
    
    class Config:
        use_enum_values = True
