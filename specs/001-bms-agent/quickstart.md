---
description: "Production quickstart guide for BMS Agent v1.0"
---

# Quickstart – BMS Agent v1.0

## Prerequisites
- RunPod pod with Ubuntu 22.04+, 8–16 vCPU, 32–64 GB RAM, 200–500 GB NVMe
- NVIDIA GPU (for Ollama)
- Python 3.11+
- All services installed via RunPod initialization (automatic)
- Repository cloned to `/workspace/001-bms-agent`

## 1. Automatic Setup (RunPod)

The RunPod initialization script handles everything automatically:
- SSH key restoration
- System packages installation
- Python requirements installation
- Ollama GPU setup
- Service startup

**Verify initialization:**
```bash
tail -100 /workspace/logs/runpod_init.log
```

## 2. Manual Service Management (if needed)

**Start all services:**
```bash
cd /workspace/001-bms-agent
./scripts/manage_services.sh start
```

**Check service status:**
```bash
./scripts/manage_services.sh status
```

**Run health checks:**
```bash
./scripts/health_check.sh
```

## 3. Verify Qdrant Collection

**Check collection exists:**
```bash
curl http://localhost:6333/collections/nomad_bms_documents | jq
```

**Expected output:** Collection with 1,744 points (chunks)

## 4. Verify API Health

**Basic health check:**
```bash
curl http://localhost:8000/health
```

**Detailed health check:**
```bash
curl http://localhost:8000/health/detailed | jq
```

## 5. Upload Test Document (Optional)

**Upload a document:**
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
     -F "file=@/path/to/document.pdf" \
     -F "profile=railway"
```

**Expected response:** Processing status with document ID

## 6. Semantic Search Test

**Basic semantic search:**
```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
     -H "Content-Type: application/json" \
     -d '{"query": "railway safety procedures", "limit": 5}'
```

**With quality filtering:**
```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
     -d '{"query": "train control systems", "limit": 5, "min_quality": 0.95, "min_score": 0.7}'
```
**Expected response:** JSON with `results` array containing chunks with scores and metadata

## 7. Hybrid Search Test

**Hybrid search with custom weights:**
```bash
curl -X POST http://localhost:8000/api/v1/search/hybrid \
     -H "Content-Type: application/json" \
     -d '{"query": "network maintenance", "limit": 5, "vector_weight": 0.6, "keyword_weight": 0.4}'
```

**With quality and relevance filtering:**
```bash
curl -X POST http://localhost:8000/api/v1/search/hybrid \
     -H "Content-Type: application/json" \
     -d '{"query": "emergency procedures", "limit": 5, "min_quality": 0.95, "min_score": 0.6}'
```

**Expected response:** JSON with `hybrid_score`, `semantic_score`, and `keyword_score` fields

## 8. Integration Tests

**Slack Integration:**
- Endpoints available at `/api/v1/slack/search` and `/api/v1/slack/events`
- See `api/main.py` for implementation details

**OpenWebUI Tool:**
- Tool script: `tools/bms_search.py`
- 7/7 tests passing
- See `tools/README.md` for installation

## 9. Service Management

**Restart a specific service:**
```bash
./scripts/manage_services.sh restart api
```

**Stop all services:**
```bash
./scripts/manage_services.sh stop
```

**View logs:**
```bash
tail -f /workspace/logs/api.log
tail -f /workspace/logs/qdrant.log
tail -f /workspace/logs/ollama.log
```

## 10. Security Features

**Rate limiting:** 60 requests/minute per IP (configurable via `RATE_LIMIT_PER_MIN`)

**Security headers:** Automatic (X-Content-Type-Options, X-Frame-Options, etc.)

**Test rate limiting:**
```bash
# Run 100 requests rapidly
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/search/semantic \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "limit": 1}' &
done
```

**Expected:** Some requests return HTTP 429 (Too Many Requests)

## 11. Backup & Recovery

**Run manual backup:**
```bash
./scripts/backup_system.sh
```

**Verify backup:**
```bash
./scripts/verify_backup.sh
```

**Restore from backup:**
```bash
./scripts/restore_backup.sh
```

**Backups location:** `/workspace/backups/`

## 12. Troubleshooting

**Check service health:**
```bash
./scripts/health_check.sh
```

**View initialization logs:**
```bash
cat /workspace/logs/runpod_init.log
cat /workspace/logs/startup.log
```

**Restart all services:**
```bash
./scripts/manage_services.sh restart
```

## Next Steps

- See [DEPLOYMENT_CHECKLIST.md](../../DEPLOYMENT_CHECKLIST.md) for complete deployment procedures
- See [README.md](../../README.md) for architecture details
- See [docs/security-notes.md](../../docs/security-notes.md) for security roadmap
