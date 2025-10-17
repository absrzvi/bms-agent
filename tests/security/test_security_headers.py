"""
Tests for security headers middleware
Validates that all responses include required security headers
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.security import SecurityHeadersMiddleware


def test_security_headers_present():
    """Test that all required security headers are present"""
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}
    
    app.add_middleware(SecurityHeadersMiddleware)
    
    client = TestClient(app)
    response = client.get("/test")
    
    # Check all required security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    
    assert "X-XSS-Protection" in response.headers
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    
    assert "Strict-Transport-Security" in response.headers
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    
    assert "Referrer-Policy" in response.headers
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_security_headers_on_all_endpoints():
    """Test that security headers are applied to all endpoints"""
    app = FastAPI()
    
    @app.get("/endpoint1")
    def endpoint1():
        return {"id": 1}
    
    @app.post("/endpoint2")
    def endpoint2():
        return {"id": 2}
    
    @app.get("/health")
    def health():
        return {"status": "healthy"}
    
    app.add_middleware(SecurityHeadersMiddleware)
    
    client = TestClient(app)
    
    # Test GET endpoint
    response = client.get("/endpoint1")
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    
    # Test POST endpoint
    response = client.post("/endpoint2")
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    
    # Test health endpoint
    response = client.get("/health")
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers


def test_security_headers_on_errors():
    """Test that security headers are present even on error responses"""
    app = FastAPI()
    
    @app.get("/error")
    def error_endpoint():
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Test error")
    
    app.add_middleware(SecurityHeadersMiddleware)
    
    client = TestClient(app)
    response = client.get("/error")
    
    # Even on 500 errors, security headers should be present
    assert response.status_code == 500
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers


def test_security_headers_values():
    """Test specific security header values"""
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}
    
    app.add_middleware(SecurityHeadersMiddleware)
    
    client = TestClient(app)
    response = client.get("/test")
    
    # Verify specific header values
    headers = response.headers
    
    # X-Content-Type-Options prevents MIME sniffing
    assert headers["X-Content-Type-Options"] == "nosniff"
    
    # X-Frame-Options prevents clickjacking
    assert headers["X-Frame-Options"] == "DENY"
    
    # X-XSS-Protection enables XSS filter
    assert headers["X-XSS-Protection"] == "1; mode=block"
    
    # HSTS enforces HTTPS
    hsts = headers["Strict-Transport-Security"]
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts
    
    # Referrer-Policy controls referrer information
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
