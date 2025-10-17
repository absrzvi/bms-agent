"""
BMS Agent Security Module
Implements rate limiting and security headers for MVP deployment
"""

import time
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import os

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket algorithm for rate limiting
    In-memory implementation suitable for single-instance MVP deployment
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum number of tokens (requests) in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from bucket
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens consumed successfully, False if insufficient tokens
        """
        with self.lock:
            now = time.time()
            # Refill tokens based on time elapsed
            time_passed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + (time_passed * self.refill_rate)
            )
            self.last_refill = now
            
            # Check if enough tokens available
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_retry_after(self) -> int:
        """
        Calculate seconds until next token available
        
        Returns:
            Seconds to wait before retry
        """
        with self.lock:
            if self.tokens >= 1:
                return 0
            tokens_needed = 1 - self.tokens
            return int(tokens_needed / self.refill_rate) + 1


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm
    Limits requests per IP address
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiting middleware
        
        Args:
            app: ASGI application
            requests_per_minute: Maximum requests per minute per IP
            burst_size: Maximum burst size (defaults to requests_per_minute)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(self.burst_size, self.refill_rate)
        )
        self.cleanup_interval = 300  # Clean up old buckets every 5 minutes
        self.last_cleanup = time.time()
        logger.info(
            f"Rate limiting initialized: {requests_per_minute} req/min, "
            f"burst: {self.burst_size}"
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request
        Handles X-Forwarded-For header for proxy scenarios
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (for proxies/load balancers)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP in chain
            return forwarded.split(",")[0].strip()
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _cleanup_old_buckets(self):
        """Remove inactive buckets to prevent memory leak"""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            # Remove buckets that haven't been accessed recently
            inactive_threshold = now - self.cleanup_interval
            to_remove = [
                ip for ip, bucket in self.buckets.items()
                if bucket.last_refill < inactive_threshold
            ]
            for ip in to_remove:
                del self.buckets[ip]
            
            if to_remove:
                logger.debug(f"Cleaned up {len(to_remove)} inactive rate limit buckets")
            
            self.last_cleanup = now
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response or 429 error
        """
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/detailed"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Get or create token bucket for this IP
        bucket = self.buckets[client_ip]
        
        # Attempt to consume token
        if not bucket.consume():
            # Rate limit exceeded
            retry_after = bucket.get_retry_after()
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {request.url.path}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please retry after {retry_after} seconds.",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Periodic cleanup
        self._cleanup_old_buckets()
        
        # Process request
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    Implements basic security best practices
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize security headers middleware"""
        super().__init__(app)
        logger.info("Security headers middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """
        Add security headers to response
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


def get_rate_limit_config() -> Dict[str, int]:
    """
    Load rate limiting configuration from environment
    
    Returns:
        Configuration dictionary with requests_per_minute and burst_size
    """
    requests_per_minute = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))
    burst_size = int(os.getenv("RATE_LIMIT_BURST_SIZE", str(requests_per_minute)))
    
    return {
        "requests_per_minute": requests_per_minute,
        "burst_size": burst_size
    }
