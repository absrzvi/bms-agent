# BMS Agent Deployment Checklist

**Deployment Target:** RunPod Pods (NOT Docker)

## Pre-Deployment

### System Requirements
- [ ] RunPod pod (NOT Docker container) with 8-16 vCPUs, 32-64GB RAM, 200-500GB NVMe SSD
- [ ] GPU support enabled (for Ollama) - NVIDIA GPU recommended
- [ ] `/workspace` volume with persistent storage (200+ GB)
- [ ] Internet connectivity for initial setup and pod restarts
- [ ] Understanding: Only `/workspace` persists across pod restarts

### RunPod Configuration
- [ ] Copy `scripts/runpod_init.sh` to RunPod startup script field
- [ ] SSH keys stored in `/workspace/config/authorized_keys` (optional)
- [ ] Ollama models pre-downloaded to `/workspace/data/ollama_models`
- [ ] Environment variables configured (if needed)

### Installation Architecture (Constitution §11 - RunPod Pod Specific)
**CRITICAL: Persistent Storage Requirements (RunPod Pods Only Persist `/workspace`)**
- [ ] **All applications/libraries** → `/workspace` (ONLY persistent location in RunPod pods)
- [ ] **Python virtual environment** → `/workspace/bms-api-venv` (CRITICAL for persistence)
- [ ] **Qdrant data** → `/workspace/qdrant_storage`
- [ ] **BMS data** → `/workspace/bms_data`
- [ ] **Ollama models** → `/workspace/data/ollama_models` (models persist, binary does not)
- [ ] **Logs** → `/workspace/logs`
- [ ] **Backups** → `/workspace/backups`
- [ ] **EXCEPTION: Ollama binary** → `/root` (EPHEMERAL - reinstalled on each pod start for GPU compatibility)
- [ ] **Understanding:** Everything outside `/workspace` is wiped on pod restart

### Dependencies (Auto-installed by runpod_init.sh on EVERY pod start)

**Persistent (installed once, survives restarts):**
- [ ] Python virtual environment created in `/workspace/bms-api-venv`
- [ ] All packages from `requirements.txt` installed in venv (in `/workspace`)
- [ ] Qdrant binary v1.7.4+ installed in `/workspace`
- [ ] Ollama models pulled to `/workspace/data/ollama_models` (large files, persist)
- [ ] **NLTK data downloaded to `/workspace/nltk_data`** ✨ (NEW - now persistent!)

**Ephemeral (reinstalled on EVERY pod start):**
- [ ] Ollama binary installed in `/root` with GPU support (reinstalled each start)
- [ ] System packages installed (jq, etc.) (reinstalled each start)

**Note:** Only Ollama binary and system packages need reinstallation on pod restart. NLTK data now persists!

### Configuration Files
- [ ] `.env` or `config/env.sh` configured with:
  - `RATE_LIMIT_PER_MIN` (default: 60)
  - `QDRANT_HOST` and `QDRANT_PORT`
  - `OLLAMA_URL`
  - `EMBEDDING_MODEL` (sentence-transformers/all-mpnet-base-v2)

## Deployment Steps

### 0. RunPod Pod Initialization (Automatic)
The `scripts/runpod_init.sh` script runs automatically on pod boot and:
- Creates directory structure in `/workspace` (logs, data, qdrant_storage, bms_data, backups)
- Installs Ollama in `/root` (for GPU compatibility)
- Configures Ollama to use `/workspace/data/ollama_models` for model storage
- Creates Python virtual environment in `/workspace/bms-api-venv`
- Installs all dependencies from `requirements.txt`
- Downloads required NLTK data files
- Installs system packages (jq, etc.)
- Pulls Ollama models (nomic-embed-text, mistral)
- Starts all BMS Agent services
- Performs comprehensive health checks
- Logs to `/workspace/logs/runpod_init.log`

**Verification:**
```bash
# Check initialization log
tail -100 /workspace/logs/runpod_init.log

# Verify virtual environment
ls -la /workspace/bms-api-venv/

# Verify requirements installed
source /workspace/bms-api-venv/bin/activate && pip list

# Verify all services started
tail -50 /workspace/logs/runpod_init.log | grep "✅"
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

### Prometheus & Grafana Setup

**Prometheus Configuration:**
```bash
# Prometheus config location
cat prometheus/prometheus.yml

# Start Prometheus (if installed)
prometheus --config.file=prometheus/prometheus.yml --storage.tsdb.path=/workspace/prometheus_data
```

**Grafana Dashboard:**
- Dashboard JSON: `grafana/dashboards/bms-agent.json`
- Import into Grafana UI: Configuration → Dashboards → Import
- Panels included:
  - API Latency (p50/p95/p99)
  - Request Throughput
  - Error Rate (4xx/5xx)
  - Service Health (BMS API, Qdrant)
  - Document Processing Stats

**Alert Rules:**
- Alert configuration: `prometheus/alerts.yml`
- Alerts configured for:
  - High API latency (>100ms p95)
  - Critical API latency (>500ms p95)
  - High error rate (>1%)
  - Service downtime (Qdrant, Ollama)
  - Document processing failures
  - Low disk space
  - High memory usage

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
