"""
Health check related Pydantic models for BMS Agent API
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceStatus(BaseModel):
    """Individual service status"""
    name: str = Field(..., description="Service name")
    status: HealthStatus = Field(..., description="Service health status")
    response_time_ms: Optional[int] = Field(None, description="Service response time")
    details: Optional[str] = Field(None, description="Additional status details")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last health check time")


class SystemHealth(BaseModel):
    """Overall system health status"""
    status: HealthStatus = Field(..., description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    services: Dict[str, ServiceStatus] = Field(default_factory=dict, description="Individual service statuses")
    uptime_seconds: Optional[int] = Field(None, description="System uptime in seconds")
    version: str = Field(default="1.0.0", description="API version")


class HealthCheck(BaseModel):
    """Basic health check response"""
    status: str = Field(default="ok", description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(default="1.0.0", description="API version")
