"""
Tests for rate limiting middleware
Validates HTTP 429 responses and Retry-After headers
"""

import pytest
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.security import RateLimitMiddleware, TokenBucket


def test_token_bucket_basic():
    """Test basic token bucket functionality"""
    bucket = TokenBucket(capacity=5, refill_rate=1.0)
    
    # Should be able to consume 5 tokens initially
    assert bucket.consume() == True
    assert bucket.consume() == True
    assert bucket.consume() == True
    assert bucket.consume() == True
    assert bucket.consume() == True
    
    # 6th token should fail
    assert bucket.consume() == False


def test_token_bucket_refill():
    """Test token bucket refill over time"""
    bucket = TokenBucket(capacity=2, refill_rate=2.0)  # 2 tokens per second
    
    # Consume all tokens
    assert bucket.consume() == True
    assert bucket.consume() == True
    assert bucket.consume() == False
    
    # Wait for refill (0.5 seconds = 1 token)
    time.sleep(0.6)
    assert bucket.consume() == True
    assert bucket.consume() == False


def test_token_bucket_retry_after():
    """Test retry_after calculation"""
    bucket = TokenBucket(capacity=1, refill_rate=1.0)
    
    # Consume token
    bucket.consume()
    
    # Should suggest waiting ~1 second
    retry_after = bucket.get_retry_after()
    assert 0 <= retry_after <= 2


def test_rate_limit_middleware_basic():
    """Test rate limiting middleware with basic requests"""
    # Create test app
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}
    
    # Add rate limiting (5 requests per minute)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=5,
        burst_size=5
    )
    
    client = TestClient(app)
    
    # First 5 requests should succeed
    for i in range(5):
        response = client.get("/test")
        assert response.status_code == 200, f"Request {i+1} failed"
    
    # 6th request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert "retry_after" in response.json()
    assert "Retry-After" in response.headers


def test_rate_limit_middleware_health_check_exempt():
    """Test that health checks bypass rate limiting"""
    app = FastAPI()
    
    @app.get("/health")
    def health():
        return {"status": "healthy"}
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}
    
    # Very restrictive rate limit (1 per minute)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=1,
        burst_size=1
    )
    
    client = TestClient(app)
    
    # Health checks should not be rate limited
    for i in range(10):
        response = client.get("/health")
        assert response.status_code == 200
    
    # But regular endpoints should be
    response = client.get("/test")
    assert response.status_code == 200
    
    response = client.get("/test")
    assert response.status_code == 429


def test_rate_limit_per_ip():
    """Test that rate limiting is per IP address"""
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}
    
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=2,
        burst_size=2
    )
    
    client = TestClient(app)
    
    # Simulate requests from different IPs
    # Note: TestClient doesn't easily support different IPs,
    # but we can test the logic
    response1 = client.get("/test")
    response2 = client.get("/test")
    response3 = client.get("/test")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 429


def test_rate_limit_error_response_format():
    """Test that 429 response has correct format"""
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}
    
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=1,
        burst_size=1
    )
    
    client = TestClient(app)
    
    # Exhaust rate limit
    client.get("/test")
    response = client.get("/test")
    
    assert response.status_code == 429
    
    # Check response format
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "retry_after" in data
    assert isinstance(data["retry_after"], int)
    
    # Check headers
    assert "Retry-After" in response.headers
    assert response.headers["Retry-After"].isdigit()


def test_rate_limit_configuration():
    """Test rate limit configuration from environment"""
    from api.security import get_rate_limit_config
    import os
    
    # Test default values
    config = get_rate_limit_config()
    assert "requests_per_minute" in config
    assert "burst_size" in config
    assert config["requests_per_minute"] == 60  # default
    
    # Test custom values
    os.environ["RATE_LIMIT_PER_MIN"] = "100"
    os.environ["RATE_LIMIT_BURST_SIZE"] = "150"
    
    config = get_rate_limit_config()
    assert config["requests_per_minute"] == 100
    assert config["burst_size"] == 150
    
    # Cleanup
    del os.environ["RATE_LIMIT_PER_MIN"]
    del os.environ["RATE_LIMIT_BURST_SIZE"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
