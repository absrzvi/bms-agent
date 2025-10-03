# BMS Agent Security Roadmap

## Current Status (MVP)

### ✅ Implemented (MVP Phase)

**Rate Limiting**:
- Token bucket algorithm for per-IP rate limiting
- Default: 60 requests/minute per IP address
- Configurable via `RATE_LIMIT_PER_MIN` environment variable
- Burst size configurable via `RATE_LIMIT_BURST_SIZE`
- HTTP 429 responses with `Retry-After` header
- Health check endpoints exempt from rate limiting
- In-memory implementation (suitable for single-instance deployment)

**Security Headers**:
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - Enables XSS filter
- `Strict-Transport-Security` - Enforces HTTPS (31536000s = 1 year)
- `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer information

**Error Handling**:
- Automated tests for 400 (Bad Request) responses
- Automated tests for 413 (Payload Too Large) responses
- Automated tests for 429 (Too Many Requests) responses
- Proper error messages and status codes

### ⚠️ NOT Implemented (Deferred to Production)

**Authentication & Authorization**:
- ❌ JWT token validation
- ❌ API key authentication
- ❌ Role-Based Access Control (RBAC)
- ❌ User identity management
- ❌ Admin-only endpoints

**Advanced Security**:
- ❌ Request signing/verification (except Slack signature verification)
- ❌ IP whitelisting/blacklisting
- ❌ Distributed rate limiting (Redis-based)
- ❌ Audit logging for sensitive operations
- ❌ Encryption at rest for sensitive data

---

## Production Security Roadmap

### Phase 1: Authentication (Post-MVP)

**JWT Implementation**:
```python
# Add to api/security.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def verify_jwt(credentials: HTTPAuthorizationCredentials):
    try:
        payload = jwt.decode(
            credentials.credentials,
            PUBLIC_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**API Key Implementation**:
```python
# Add to api/security.py
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

**Environment Variables**:
```env
# Production .env
BMS_JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."
BMS_JWT_ALGORITHM=RS256
BMS_API_KEYS=key1,key2,key3
```

### Phase 2: Authorization (Post-MVP)

**RBAC Implementation**:
- Define roles: `admin`, `user`, `readonly`
- Implement permission checks per endpoint
- Add role claims to JWT tokens
- Create admin-only endpoints for:
  - Document deletion (`DELETE /api/v1/documents/{id}`)
  - User management
  - System configuration

**Example**:
```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"

def require_role(required_role: Role):
    async def role_checker(token: dict = Depends(verify_jwt)):
        user_role = token.get("role")
        if user_role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return token
    return role_checker

# Usage
@app.delete("/api/v1/documents/{id}", dependencies=[Depends(require_role(Role.ADMIN))])
async def delete_document(id: str):
    ...
```

### Phase 3: Advanced Security (Production)

**Distributed Rate Limiting**:
- Replace in-memory token buckets with Redis
- Synchronize rate limits across multiple instances
- Add per-user rate limiting (in addition to per-IP)

**Audit Logging**:
```python
# Add to api/security.py
import logging
from datetime import datetime

audit_logger = logging.getLogger("audit")

async def log_audit_event(
    user_id: str,
    action: str,
    resource: str,
    status: str,
    ip_address: str
):
    audit_logger.info({
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "status": status,
        "ip_address": ip_address
    })
```

**Request Signing** (for sensitive operations):
- Implement HMAC-SHA256 request signing
- Verify request signatures for mutations
- Add timestamp validation to prevent replay attacks

**IP Whitelisting** (for admin endpoints):
```python
# Add to api/security.py
ADMIN_IP_WHITELIST = set(os.getenv("ADMIN_IP_WHITELIST", "").split(","))

async def verify_admin_ip(request: Request):
    client_ip = request.client.host
    if client_ip not in ADMIN_IP_WHITELIST:
        raise HTTPException(status_code=403, detail="Access denied")
```

### Phase 4: Data Protection (Production)

**Encryption at Rest**:
- Encrypt sensitive document metadata in Qdrant
- Use AES-256-GCM for encryption
- Implement key rotation strategy
- Store encryption keys in secure key management system

**GDPR Compliance**:
- Implement data retention policies
- Add data export functionality
- Implement right to be forgotten (document deletion with audit trail)
- Add consent management for personal data

**Secrets Management**:
- Migrate from environment variables to HashiCorp Vault or AWS Secrets Manager
- Implement secret rotation
- Add secret access auditing

---

## Security Testing

### Current Tests (MVP)

**Rate Limiting Tests** (`tests/security/test_rate_limiting.py`):
- ✅ Token bucket basic functionality
- ✅ Token bucket refill over time
- ✅ Retry-After calculation
- ✅ Rate limit middleware basic requests
- ✅ Health check exemption
- ✅ Per-IP rate limiting
- ✅ Error response format (429)
- ✅ Configuration from environment

**Security Headers Tests** (`tests/security/test_security_headers.py`):
- ✅ All required headers present
- ✅ Headers on all endpoints
- ✅ Headers on error responses
- ✅ Correct header values

**Error Handling Tests** (integrated in other test suites):
- ✅ 400 Bad Request (invalid input)
- ✅ 413 Payload Too Large (file size limits)
- ✅ 429 Too Many Requests (rate limiting)

### Production Tests (TODO)

**Authentication Tests**:
- JWT token validation (valid/invalid/expired)
- API key validation
- Token refresh flow
- Unauthorized access attempts

**Authorization Tests**:
- Role-based access control
- Admin-only endpoint protection
- Cross-user data access prevention

**Security Scanning**:
- OWASP ZAP automated security scans
- Dependency vulnerability scanning (Safety, Snyk)
- Static code analysis (Bandit)
- Penetration testing

---

## Configuration

### MVP Configuration

```env
# Rate Limiting
RATE_LIMIT_PER_MIN=60          # Requests per minute per IP
RATE_LIMIT_BURST_SIZE=60       # Maximum burst size

# Logging
LOG_LEVEL=INFO                  # INFO for production, DEBUG for development
```

### Production Configuration

```env
# Authentication
BMS_JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."
BMS_JWT_ALGORITHM=RS256
BMS_API_KEYS=comma,separated,keys

# Rate Limiting (distributed)
REDIS_URL=redis://localhost:6379
RATE_LIMIT_PER_MIN=100
RATE_LIMIT_PER_USER=200

# Security
ADMIN_IP_WHITELIST=10.0.0.1,10.0.0.2
ENCRYPTION_KEY_ID=prod-key-v1
VAULT_ADDR=https://vault.example.com

# Audit Logging
AUDIT_LOG_PATH=/var/log/bms-agent/audit.log
AUDIT_LOG_RETENTION_DAYS=365
```

---

## Incident Response

### Security Incident Procedures

**1. Rate Limit Abuse Detection**:
- Monitor for sustained 429 responses from single IPs
- Investigate patterns (distributed attacks, legitimate traffic spikes)
- Temporarily block abusive IPs if needed
- Adjust rate limits if legitimate traffic is affected

**2. Unauthorized Access Attempts** (Production):
- Monitor failed authentication attempts
- Alert on repeated failures from same IP/user
- Implement temporary account lockout after N failures
- Review audit logs for suspicious patterns

**3. Data Breach Response** (Production):
- Immediately revoke compromised credentials
- Rotate all API keys and JWT signing keys
- Audit access logs to determine scope
- Notify affected users per GDPR requirements
- Document incident and remediation steps

### Contact Information

**Security Team**:
- Email: security@example.com
- Slack: #security-incidents
- On-call: PagerDuty rotation

**Escalation Path**:
1. On-call engineer (immediate response)
2. Security team lead (within 1 hour)
3. CTO (critical incidents)

---

## Compliance

### Current Compliance Status

**MVP Phase**:
- ✅ Basic rate limiting (DoS protection)
- ✅ Security headers (OWASP best practices)
- ✅ Error handling (information disclosure prevention)
- ⚠️ No authentication (acceptable for POC/MVP)
- ⚠️ No encryption at rest (acceptable for MVP)
- ⚠️ No audit logging (acceptable for MVP)

**Production Requirements**:
- 🔴 JWT/API key authentication (REQUIRED)
- 🔴 RBAC authorization (REQUIRED)
- 🔴 Audit logging (REQUIRED for GDPR)
- 🔴 Encryption at rest (REQUIRED for sensitive data)
- 🔴 Data retention policies (REQUIRED for GDPR)
- 🔴 Security scanning in CI/CD (REQUIRED per constitution §5)

### Railway IT Standards Compliance

**EN50155 (Railway Electronics)**:
- Security requirements deferred to production
- MVP focuses on functional requirements

**GDPR (Data Protection)**:
- MVP: No personal data processing
- Production: Full GDPR compliance required
  - Right to access
  - Right to be forgotten
  - Data portability
  - Consent management

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [GDPR Compliance Guide](https://gdpr.eu/)
- Constitution §5: Security & Compliance requirements
