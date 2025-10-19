# Open WebUI MVP Limitations

## Overview

This document describes the known limitations of the current MVP deployment of Open WebUI for BMS Agent. These limitations are intentional decisions to validate the concept before investing in full production hardening.

## MVP Limitations

### 1. Authentication Disabled

**Current State:**
- `WEBUI_AUTH=False` - No login required
- Anyone with network access can use the interface

**Rationale:**
- Simplifies MVP validation
- Allows quick testing without user management overhead

**Production Plan:**
- Phase 2: Enable `WEBUI_AUTH=True`
- Implement user registration and access control
- Timeline: After MVP validates usage patterns (4+ hours)

### 2. Basic Logging Only

**Current State:**
- Simple file logging to `/workspace/logs/openwebui.log`
- No structured log aggregation
- No alerting

**Rationale:**
- Sufficient for MVP troubleshooting
- Defers complexity until proven necessary

**Production Plan:**
- Phase 3: Add Prometheus metrics
- Phase 3: Add Grafana dashboards
- Phase 3: Configure alerting rules
- Timeline: When usage shows monitoring is needed

### 3. No Performance Optimization

**Current State:**
- No specific latency targets enforced
- Best-effort performance (measured: 37ms p95)
- No caching beyond existing BMS API semantic cache

**Rationale:**
- Aspirational target is <100ms p95
- MVP shows we're already meeting it (37ms)
- Optimization deferred until usage shows p95 >200ms

**Production Plan:**
- Optimize only if real usage shows p95 latency >200ms
- Consider: query caching, connection pooling, async improvements

### 4. Limited Citation Format

**Current State:**
- Results show document names
- No expandable citation UI
- No direct links to source documents

**Rationale:**
- Core search functionality works
- Citation enhancements are UI improvements, not blockers

**Production Plan:**
- Phase 3+: Expandable citations with document previews
- Phase 3+: Direct links to SharePoint sources (if available)
- Timeline: Based on user feedback

### 5. Manual Service Management

**Current State:**
- Services started manually via `start_openwebui.sh`
- No systemd service files
- No automatic restart on failure

**Rationale:**
- RunPod environment already handles pod initialization via `runpod_init.sh`
- Manual start sufficient for MVP testing

**Production Plan:**
- Optional: Create systemd service for auto-restart
- Consider: supervisord or similar process manager
- Timeline: If uptime becomes critical

### 6. Single Instance Only

**Current State:**
- No load balancing
- Single Open WebUI process
- Limited to one RunPod pod

**Rationale:**
- MVP targets 20-100 concurrent users
- Single instance sufficient for validation

**Production Plan:**
- Phase 3+: Multi-instance deployment with load balancer
- Phase 3+: Redis session storage for session persistence
- Timeline: Only if user load exceeds single-instance capacity

### 7. Browser Compatibility Testing

**Current State:**
- Tested: Chrome, Firefox (latest versions)
- Untested: Safari, Edge, mobile browsers

**Rationale:**
- Core browsers covered
- Railway IT environment typically uses Chrome/Firefox

**Production Plan:**
- Expand testing based on actual user browser data
- Add browser compatibility warnings if needed

## Deferred Features

The following features were scoped out of MVP and deferred to future phases:

### Phase 2 (Production Hardening - 4 hours)
- [ ] Enable authentication (`WEBUI_AUTH=True`)
- [ ] Configure user access control
- [ ] Production .env configuration
- [ ] Verify RunPod auto-start (already configured in `runpod_init.sh:331`)

### Phase 3+ (Advanced Features - Future)
- [ ] Prometheus/Grafana monitoring dashboards
- [ ] Performance optimization (if needed)
- [ ] Expandable citations UI
- [ ] Multi-instance deployment
- [ ] Advanced search features (faceted search, filters)
- [ ] A/B testing framework
- [ ] Analytics and usage tracking

## What Works in MVP

Despite limitations, the following are fully functional:

✅ **Core Search:** Semantic and hybrid search via BMS Agent API
✅ **Performance:** 37ms average latency (under 100ms target)
✅ **Scale:** Handles current document corpus (4,733 chunks)
✅ **Quality:** Search results filtered by quality score (≥0.70)
✅ **Integration:** BMS Search Tool integrated with Open WebUI
✅ **Reliability:** All services running and responding
✅ **Documentation:** Full operational guides and troubleshooting

## Constitutional Compliance

Per `/workspace/.specify/memory/constitution.md` POC/MVP Exception Framework:

| Requirement | MVP Status | Justification |
|------------|-----------|---------------|
| Testing (Section 4) | Manual UI validation | Integration tests deferred to Phase 3 |
| Security (Section 5) | No authentication | Development/validation phase |
| Monitoring (Section 8) | Basic logging | Full observability in Phase 3 |
| Performance (Section 7) | No specific targets | Best-effort (37ms measured) |

All MVP decisions documented and approved per constitution Section 4, 5, 7, 8 POC/MVP provisions.

## Reference

For full feature specification and phasing decisions, see:
- `/workspace/specs/006-production-rag-interface/spec.md`
- `/workspace/specs/006-production-rag-interface/plan.md`
- `/workspace/specs/006-production-rag-interface/quickstart.md`
