# BMS Agent Deployment Checklist

## Pre-Deployment

### System Requirements
- [ ] RunPod pod with 8-16 vCPUs, 32-64GB RAM, 200-500GB NVMe SSD
- [ ] GPU support enabled (for Ollama) - NVIDIA GPU recommended
- [ ] `/workspace` directory with persistent storage
- [ ] Internet connectivity for initial setup

### RunPod Configuration
- [ ] Copy `scripts/runpod_init_v2.sh` to RunPod startup script field
- [ ] SSH keys stored in `/workspace/config/authorized_keys` (optional)
- [ ] Ollama models pre-downloaded to `/workspace/data/ollama_models`
- [ ] Environment variables configured (if needed)

### Dependencies
- [ ] Python 3.11+ installed
- [ ] All packages from `requirements.txt` installed
- [ ] Qdrant binary v1.7.4+ installed
- [ ] Ollama installed with GPU support
- [ ] sentence-transformers model downloaded

### Configuration Files
- [ ] `.env` or `config/env.sh` configured with:
  - `RATE_LIMIT_PER_MIN` (default: 60)
  - `QDRANT_HOST` and `QDRANT_PORT`
  - `OLLAMA_URL`
  - `EMBEDDING_MODEL` (sentence-transformers/all-mpnet-base-v2)

## Deployment Steps

### 0. RunPod Pod Initialization (Automatic)
The `scripts/runpod_init_v2.sh` script runs automatically on pod boot and:
- Restores SSH keys from `/workspace/config/authorized_keys`
- Installs system packages (jq, htop, tmux, vim, etc.)
- Restores/installs Ollama with GPU support
- Verifies GPU availability
- Starts all BMS Agent services
- Performs comprehensive health checks
- Logs to `/workspace/logs/runpod_init.log` and `/workspace/logs/startup.log`

**Verification:**
```bash
# Check initialization log
tail -100 /workspace/logs/runpod_init.log

# Verify all services started
tail -50 /workspace/logs/startup.log | grep "services operational"
```

### 1. Initialize Qdrant
```bash
# Start Qdrant service
./scripts/start_qdrant.sh

# Initialize collection
python scripts/init_qdrant.py

# Verify collection
curl http://localhost:6333/collections/nomad_bms_documents
```

### 2. Start Services
```bash
# Start all services
./scripts/start_all_services.sh

# Verify services
./scripts/health_check.sh
```

### 3. Configure Automated Backups
```bash
# Setup backup cron job (requires root)
sudo ./scripts/setup_backup_cron.sh

# Test backup manually
./scripts/backup_system.sh

# Verify backups
./scripts/verify_backup.sh
```

### 4. Load Initial Data
```bash
# Process documents from incoming directory
python scripts/batch_process_incoming.py

# Verify Qdrant collection
curl http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'
```

### 5. Verify API
```bash
# Check health endpoint
curl http://localhost:8000/health | jq '.'

# Test search endpoint
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 5}' | jq '.'
```

## Post-Deployment Verification

### Functional Tests
- [ ] Health endpoint returns 200 OK
- [ ] Semantic search returns relevant results
- [ ] Hybrid search works correctly
- [ ] Document upload succeeds
- [ ] Rate limiting triggers at configured threshold
- [ ] Security headers present on all responses

### Performance Tests
- [ ] p95 latency < 500ms (POC) / < 200ms (MVP) / ≤ 100ms (Production)
- [ ] Document processing ≥ 5 docs/min (POC) / ≥ 10 docs/min (MVP)
- [ ] Concurrent users: 20 (POC) / 50 (MVP) / 100 (Production)

### Integration Tests
- [ ] Slack integration responds to commands
- [ ] OpenWebUI tool returns search results
- [ ] Metrics endpoint exposes Prometheus metrics

## Backup & Recovery

### Automated Backups
**Schedule:** Daily at 2:00 AM (configured via cron)

**Backup Locations:**
- Qdrant: `/workspace/backups/qdrant/`
- BMS Data: `/workspace/backups/bms_data/`
- Logs: `/workspace/backups/logs/`

**Retention Policies:**
- Logs: 30 days
- Data backups: 90 days

**Verification:**
```bash
# Verify all backups
./scripts/verify_backup.sh

# Check backup logs
tail -100 /workspace/logs/backup.log
```

### Restoration Procedures

**Restore Qdrant:**
```bash
# Stop Qdrant service
./scripts/start_qdrant.sh stop

# Restore from backup
./scripts/restore_backup.sh qdrant

# Start Qdrant service
./scripts/start_qdrant.sh start
```

**Restore BMS Data:**
```bash
./scripts/restore_backup.sh bms_data
```

**Restore Both:**
```bash
./scripts/restore_backup.sh all
```

## Monitoring

### Health Checks
```bash
# Manual health check
./scripts/health_check.sh

# API health endpoint
curl http://localhost:8000/health/detailed
```

### Metrics Collection
```bash
# Prometheus metrics endpoint
curl http://localhost:8000/metrics/uplink

# Qdrant metrics
curl http://localhost:6333/metrics
```

### Log Locations
- API: `/workspace/logs/api.log`
- Qdrant: `/workspace/logs/qdrant.log`
- Ollama: `/workspace/logs/ollama.log`
- Backup: `/workspace/logs/backup.log`
- Startup: `/workspace/logs/startup.log`

## Incident Response

### API Latency > 100ms p95

**Detection:**
- Monitor `/metrics/uplink` endpoint
- Check Grafana dashboard (if configured)

**Response:**
1. Check system resources: `htop`, `nvidia-smi`
2. Review API logs: `tail -100 /workspace/logs/api.log`
3. Check Qdrant performance: `curl http://localhost:6333/metrics`
4. Verify embedding model loaded: `curl http://localhost:11434/api/tags`

**Escalation:**
- If latency > 500ms for > 5 minutes: Restart services
- If latency > 1000ms: Investigate root cause before restart

### Document Ingestion Failure

**Detection:**
- Check processing logs
- Monitor upload endpoint errors

**Response:**
1. Verify Qdrant connection: `curl http://localhost:6333/health`
2. Check disk space: `df -h /workspace`
3. Review document processor logs
4. Test with sample document

**Escalation:**
- If > 10% failure rate: Pause ingestion, investigate
- If Qdrant unavailable: Restart Qdrant service

### Qdrant/Ollama Dependency Outage

**Detection:**
- Health check failures
- 503 Service Unavailable responses

**Response:**
1. Check service status: `./scripts/health_check.sh`
2. Review service logs
3. Restart affected service: `./scripts/start_all_services.sh`

**Escalation:**
- If restart fails: Check system resources
- If persistent: Restore from backup

### Rate Limiting Abuse

**Detection:**
- High volume of 429 responses
- Sustained traffic from single IP

**Response:**
1. Review API logs for abusive IPs
2. Verify legitimate vs malicious traffic
3. Adjust rate limits if needed: `RATE_LIMIT_PER_MIN` env var
4. Consider IP blocking for persistent abuse

## Contact Matrix

### On-Call Engineer
- **Response Time:** Immediate
- **Responsibilities:** First response, initial triage
- **Escalation:** If issue unresolved in 30 minutes

### Security Team
- **Contact:** security@example.com
- **Response Time:** Within 1 hour for security incidents
- **Escalation:** For data breaches, unauthorized access

### Infrastructure Team
- **Contact:** infrastructure@example.com
- **Response Time:** Within 2 hours for infrastructure issues
- **Escalation:** For RunPod pod issues, network problems

## Rollback Procedures

### API Rollback
```bash
# Stop current API
pkill -f "uvicorn api.main:app"

# Checkout previous version
git checkout <previous-commit>

# Restart API
./scripts/start_all_services.sh
```

### Database Rollback
```bash
# Restore from backup
./scripts/restore_backup.sh qdrant

# Restart Qdrant
./scripts/start_qdrant.sh restart
```

## Security Checklist

### MVP Phase
- [x] Rate limiting enabled (60 req/min per IP)
- [x] Security headers on all responses
- [x] Error handling (400/413/429)
- [ ] Automated backups configured
- [ ] Log rotation configured

### Production Phase (TODO)
- [ ] JWT authentication enabled
- [ ] API key validation
- [ ] RBAC implementation
- [ ] Audit logging
- [ ] Encryption at rest
- [ ] Security scanning in CI/CD
- [ ] Penetration testing completed

## Maintenance Windows

### Scheduled Maintenance
- **Backup Window:** Daily 2:00-2:30 AM
- **Log Rotation:** Daily 3:00 AM
- **System Updates:** Monthly, first Sunday 2:00-4:00 AM

### Emergency Maintenance
- Notify users via Slack #bms-agent channel
- Post status updates every 30 minutes
- Document all changes in incident log

## Documentation

### Required Documentation
- [x] README.md with setup instructions
- [x] DEPLOYMENT_CHECKLIST.md (this file)
- [x] docs/security-notes.md with security roadmap
- [ ] TESTING.md with test procedures
- [ ] API documentation (OpenAPI spec at /openapi.json)

### Operational Runbooks
- [x] Backup and restoration procedures
- [x] Service startup and health checks
- [ ] Performance troubleshooting guide
- [ ] Incident response playbook

## Sign-Off

### Pre-Production
- [ ] All functional tests passed
- [ ] Performance benchmarks met
- [ ] Security requirements satisfied
- [ ] Backup system verified
- [ ] Monitoring configured
- [ ] Documentation complete

**Approved by:** ________________  
**Date:** ________________

### Production
- [ ] MVP requirements met
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Disaster recovery tested
- [ ] On-call rotation established

**Approved by:** ________________  
**Date:** ________________
