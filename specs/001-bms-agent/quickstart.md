---
description: "Phase 1 quickstart guide for BMS Agent MVP"
---

# Quickstart – BMS Agent MVP

## Prerequisites
- RunPod pod with Ubuntu 22.04+, 8–16 vCPU, 32–64 GB RAM, 200–500 GB NVMe.
- Python 3.11 virtual environment on the pod.
- Qdrant binary 1.7.4 installed (no Docker).
- Ollama installed with access to `snowflake-arctic-embed2` and `mistral-nemo:12b-instruct` models.
- Environment variables configured (`BMS_API_KEY`, `BMS_JWT_PUBLIC_KEY`, `QDRANT_HOST`, etc.).
- `bms-agent/` repository synced to the pod.

## 1. Bootstrap Environment
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt
```

## 2. Start Qdrant
```bash
./scripts/start_qdrant.sh
./scripts/init_qdrant.py
```
Confirm collection creation via:
```bash
curl http://localhost:6333/collections | jq
```

## 3. Launch API Service
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
Verify health:
```bash
curl http://localhost:8000/health
```

## 4. Upload Test Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
     -H "X-API-Key: ${BMS_API_KEY}" \
     -F "file=@data/sample_docs/railway_sops.pdf"
```
Check processing logs and confirm chunk count via Qdrant.

## 5. Semantic Search Smoke Test
```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
     -H "Content-Type: application/json" \
     -H "X-API-Key: ${BMS_API_KEY}" \
     -d '{"query": "emergency brake procedure", "limit": 5}'
```
Expect response payload containing `results` with dense scores and snippets.

## 6. Hybrid Search Test
```bash
curl -X POST http://localhost:8000/api/v1/search/hybrid \
     -H "Content-Type: application/json" \
     -H "X-API-Key: ${BMS_API_KEY}" \
     -d '{"query": "trackside repeater", "candidate_multiplier": 3, "vector_weight": 0.6, "keyword_weight": 0.4}'
```
Verify `score_dense`, `score_sparse`, and `score_fused` fields.

## 7. Integrations
- **Slack (n8n workflow)**: Import `n8n/workflows/slack_bot.json`, set JWT/API key secrets, confirm `/search` command returns top chunks.
- **OpenWebUI tool**: Place `~/.openwebui/tools/bms_search.py`, configure API key, and test queries from the UI.

## 8. Observability Checks
- Access Grafana dashboard (URL TBD) to view latency and ingestion panels.
- Follow manual alert runbooks if latency >100 ms p95 or ingestion failures occur.

## 9. Performance Validation
```bash
locust -f tests/performance/load/test_locust.py --headless -u 1000 -r 50 -t 7m --host http://localhost:8000
```
Ensure ≤100 ms p95 latency and capture JSON stats for documentation.

## 10. Retrieval Accuracy
```bash
python scripts/evaluate_retrieval.py --ground-truth data/evaluation/ground_truth.jsonl
```
Confirm ≥95 % top-5 accuracy. Store results in `reports/performance-baseline.md`.

## 11. Security Verification
```bash
pytest tests/security/test_auth.py -m security
pytest tests/security/test_rate_limit.py
```
Validate JWT + API key enforcement, rate limiting, and audit logging hooks.

## 12. Shutdown & Cleanup
```bash
./scripts/manage_services.sh stop
./scripts/start_qdrant.sh stop
```
Persist logs under `~/persistent/logs/` and back up Qdrant storage if necessary.
