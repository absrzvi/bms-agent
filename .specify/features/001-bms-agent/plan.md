# BMS Agent RunPod Deployment Plan

## Overview
Single-pod deployment on RunPod.io with direct binary installations (no Docker) for maximum performance and simplicity.

## Priority Order
1. Qdrant vector database setup
2. Document processor integration
3. Slack bot implementation
4. OpenWebUI integration

## Deployment Environment
- **Platform**: Runpod.io single pod (no Docker/Kubernetes)
- **Hardware**: 8-16 vCPUs, 32-64GB RAM, 200-500GB NVMe SSD
- **Existing Services**: Ollama, n8n, OpenWebUI (already installed)
- **Persistent Storage**: ~/persistent/ for all data

## Tech Stack & Models

### Core Services
- **Qdrant v1.7.4** (application) with **v4.0 schema** (document processor): Direct binary installation (no Docker)
  - Multi-vector schema: `chunk_embedding`, `parent_embedding`, `child_embedding`, `full_doc_embedding` (1024-d for snowflake-arctic-embed2)
  - Sparse vectors for BM25 keyword search with complete hybrid search support
  - On-disk storage for memory efficiency and persistence under `~/persistent/qdrant_storage`
  - Collection: `nomad_bms_documents`

- **Ollama Models**:
  - Embeddings: snowflake-arctic-embed2 (1024 dimensions)
  - Alternative: qwen2.5:14b or llama3.1:8b if needed

- **Python 3.11+**: Direct installation with venv
  - No containerization, runs as system process
  - FastAPI on port 8000 for API endpoints
  - Persistent data in ~/persistent/bms_data/

- **n8n Workflows**:
  - Slack bot integration (Priority 1)
  - Webhook endpoints (POC: no authentication required)

- **OpenWebUI**:
  - Custom Qdrant tool integration (Priority 2)
  - Railway expertise prompts

## Implementation Plan

### Phase 0 – Specification & Planning (`T000`)
- Author the MVP specification (`.specify/specs/001-bms-agent/spec.md`) to capture user stories, functional/non-functional requirements, and constitution mapping.
- Review constitution (§1–§4) to ensure acceptance criteria include standards compliance, basic monitoring, and testing thresholds (POC: simplified security and performance requirements).
- Establish Git flow branching strategy (feature/release branches) and document workflow expectations in `README.md`.
- Create `docs/migrations.md` to track any manual data/schema changes executed during the MVP.

### Phase 1 – Environment & Qdrant (`T001–T005`)
1. Provision project directories and persistent storage (`tasks.md` `T001`) sized for ≥1 TB to support multi-GB uploads and indexes.
2. Create Python virtual environment and install dependencies as per `reqs/requirements.txt` (`T002`).
3. Install Qdrant binary 1.7.4 locally (no Docker) and place logs under `~/persistent/logs` (`T003`).
4. Generate `scripts/start_qdrant.sh` with optimized settings (on-disk vectors/payloads) and start the service (`T004`).
5. Initialize the `nomad_bms_documents` collection using `scripts/init_qdrant.py` with 1024-d vector schema plus sparse vector support for hybrid search (`T005`).

### Phase 2 – Core Application (`T006`, `T007`, `T011`)
1. Author `api/processor_wrapper.py` that wraps `EnhancedDocumentProcessor`, handles chunking, embeddings via Ollama, and upserts to Qdrant.
2. Generate `scripts/test_processor.py` for end-to-end ingestion sanity checks.
3. Create `api/main.py` (FastAPI) exposing:
   - `POST /api/v1/documents/upload`
   - `POST /api/v1/search/semantic`
   - `GET /health` and `GET /health/detailed`
   - Root endpoint summarising capabilities
4. Ensure all endpoints load configuration from environment variables with reasonable defaults for local development.
5. Implement streaming upload pipeline capable of handling 1 GB files without exhausting memory and persist both dense and sparse (keyword/BM25) payloads for each chunk.
6. Expose hybrid search utilities in the wrapper (query fusion, keyword extraction) for reuse by future endpoints.

### Phase 3 – Integrations (`T008`, `T009`)
- Build n8n Slack workflow (`n8n/workflows/slack_bot.json`) to call the FastAPI search endpoint and format responses.
- Create OpenWebUI tool (`~/.openwebui/tools/bms_search.py`) to query the same Qdrant collection via HTTP.

### Phase 4 – Security & Compliance (`T014` - POC Simplified)
1. **POC DECISION**: Skip authentication implementation for development phase:
   - No JWT validation required
   - No API key authentication 
   - Basic rate limiting (60 req/min per IP) using lightweight in-memory token bucket
   - Basic security headers middleware (X-Frame-Options, X-Content-Type-Options)
2. Ensure basic error handling (400/413/429) is covered by tests.
3. Document security roadmap in `docs/security-notes.md` for production implementation.

### Phase 5 – Documentation, Tooling & CI/CD (`T015`, `T016`, `T023`, `T024` – post-MVP optional)
- Configure GitHub Actions (`.github/workflows/ci-cd.yml`) to run tests, coverage, security scans (Bandit, Safety), pre-commit hooks (Black, Ruff, mypy), and provide deployment placeholders for RunPod automation.
- Document required secrets (`BMS_API_KEY`, `DEPLOY_KEY`, optional `CODECOV_TOKEN`, `SAFETY_API_KEY`, future `RUNPOD_USER/HOST`, `REGISTRY_USERNAME/PASSWORD`).

### Phase 6 – Testing & Evaluation (`T010`, `T017`, `T019`, `T020`)
1. Use `scripts/run_tests.sh` to orchestrate integration tests (processor, API smoke checks).
2. Expand `tests/test_basic.py` and the Locust suite in `tests/performance/load/test_locust.py` to validate best effort performance (no specific latency targets) and capture baseline JSON stats for analysis.
3. Create evaluation dataset (`data/evaluation/ground_truth.jsonl`) and `scripts/evaluate_retrieval.py` to compute top-5 accuracy ≥95 %.
4. Add hybrid retrieval regression tests validating keyword enrichment and dense/sparse fusion logic (leveraging `/api/v1/search/hybrid`).
5. Integrate evaluation into CI (report accuracy figure and fail if below threshold) and surface performance/hybrid results in pipeline artifacts.
6. Update `DEPLOYMENT_CHECKLIST.md` to include manual alert runbooks for latency, ingestion, and dependency degradation.

{{ ... }}
2. Implement `/metrics/uplink` endpoint exposing latency histogram, request counts, and error totals for scraping.
3. Expose Prometheus metrics (FastAPI + Qdrant exporters) and provision Grafana dashboards aligned to 99.99 % availability (`T021`, scheduled post-MVP) with documented manual alert runbooks for latency, ingestion, and dependency degradation.
4. Note automated paging/notification delivery as post-MVP follow-up; document monitoring routine, log rotation, manual escalation steps, and incident response in `DEPLOYMENT_CHECKLIST.md`.

## File Structure
```
~
├── persistent/
│   ├── qdrant_storage/            # Qdrant data files
│   ├── bms_data/
│   │   ├── uploads/               # Source documents
│   │   ├── processed/             # Processed artifacts (optional cache)
│   │   └── evaluations/           # Ground-truth/reference material
│   └── logs/
│       ├── qdrant.log
│       └── api.log
│
└── bms-agent/
    ├── api/
    │   ├── main.py                # FastAPI entry point
    │   ├── processor_wrapper.py
    │   └── security.py            # JWT, rate limiting, headers
    ├── n8n/workflows/slack_bot.json
    ├── scripts/
    │   ├── start_qdrant.sh
    │   ├── init_qdrant.py
    │   ├── manage_services.sh
    │   ├── run_tests.sh
    │   ├── health_check.sh
    │   └── evaluate_retrieval.py
    ├── tests/
    │   ├── test_basic.py
    │   ├── integration/test_hybrid_search.py
    │   └── performance/load/test_locust.py
    ├── reports/performance-baseline.md
    ├── README.md
    ├── TESTING.md
    └── requirements-*.txt
```

## Service Management

- Primary orchestration via `scripts/manage_services.sh` (`start`, `stop`, `status`, `restart`).
- Health verification with `scripts/health_check.sh` covering Qdrant, API, Ollama, n8n, OpenWebUI, and embedding availability.
- API served with `uvicorn api.main:app --host 0.0.0.0 --port 8000` (managed inside scripts).

## Configuration (`.env` or `config/env.sh`)
```env
# Core paths & logging
PERSISTENT_PATH=~/persistent
LOG_LEVEL=INFO

# Security
BMS_API_KEY=change-me
BMS_JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."
BMS_JWT_ALGORITHM=RS256
RATE_LIMIT_PER_MIN=60

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=nomad_bms_documents

# Ollama
OLLAMA_URL=http://localhost:11434
EMBEDDING_MODEL=snowflake-arctic-embed2
GENERATION_MODEL=mistral-nemo:12b-instruct

# Integrations
SLACK_BOT_TOKEN=your-token
SLACK_SIGNING_SECRET=your-secret
OPENWEBUI_URL=http://localhost:8080
N8N_WEBHOOK_JWT=...
```

## API Endpoints (MVP)

- `POST /api/v1/documents/upload` – Upload and process a single document (≤1 GB streaming, chunked write).
- `POST /api/v1/search/semantic` – Semantic vector search (JWT + API key protected, rate limited).
- `GET /health` – Lightweight service heartbeat.
- `GET /health/detailed` – Extended health report (Qdrant collection state, Ollama status, n8n/OpenWebUI reachability).
- `GET /metrics/uplink` – Operational metrics (latency, throughput, error counters) in JSON.
- `GET /` – API overview and endpoint discovery.

## Testing & Validation Workflow

1. `./scripts/run_tests.sh` – Ensures Qdrant running, processor ingestion works, API responsive.
2. `pytest -v --cov=./ --cov-report=term-missing` – Unit/integration coverage (≥80 %).
3. `locust -f tests/performance/load/test_locust.py --headless -u 1000 -r 50 -t 7m --host http://localhost:8000` – Validates ≤100 ms p95 and ≤50 ms average latency under 1,000 concurrent users.
4. `python scripts/evaluate_retrieval.py` – Computes top-5 accuracy vs `data/evaluation/ground_truth.jsonl` (≥95 %).
5. Manual smoke tests via Slack bot and OpenWebUI to ensure integrations operate with current API key/JWT configuration.

## Performance & Reliability Targets

- Document processing throughput: ≥10 documents/minute (using EnhancedDocumentProcessor).
- Semantic query latency: ≤100 ms p95 with 1,000 concurrent users (validated via `tests/performance/load/test_locust.py`).
- Availability: 99.99 % (documented monitoring + incident response, failover guidance TBD).
- Storage efficiency: ≤100 GB for 10 k documents using on-disk vectors/payloads.

## Monitoring & Backup Strategy

- Health script scheduled via cron/systemd on RunPod to log status snapshots.
- Log rotation for `~/persistent/logs/*.log` using `logrotate` or custom cron.
- Daily backups: `tar -czf ~/persistent/backups/bms_$(date +%Y%m%d).tar.gz ~/persistent/qdrant_storage ~/persistent/bms_data` (automate in cron after initial validation).
- Consider Prometheus/Grafana integration post-MVP; maintain placeholders in `/metrics/uplink` response for future scrape format.

## Success Criteria & Priority Order

1. Qdrant installed, collection initialized (`nomad_bms_documents`).
2. Documents ingest via API and are searchable with relevant top results.
3. Slack workflow returns contextual answers; OpenWebUI tool surfaces matching chunks.
4. JWT + API key security enforced; rate limiting verified.
5. Retrieval accuracy evaluation ≥95 %; performance benchmarks within target.
6. Monitoring scripts and health endpoints provide actionable status.
7. CI pipeline green (tests, coverage, security scans) on main branch.

Priority sequence aligns with tasks: Setup (T000–T005) → Core (T006–T011) → Integrations (T008–T009) → Security (T014) → Documentation & CI (T015–T016) → Testing & Evaluation (T010, T017, T019) → Operations (T012, T013, T018).
