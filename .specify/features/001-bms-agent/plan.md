# BMS Agent RunPod Deployment Plan

## Overview
Single-pod deployment on RunPod.io with direct binary installations (no Docker/containers) for maximum performance, simplicity, and /workspace persistence per constitution §11. This deployment model ensures all data survives pod restarts by storing everything in /workspace.

## Priority Order
1. Qdrant vector database setup
2. Document processor integration
3. Slack bot implementation
4. OpenWebUI integration

## Deployment Environment
- **Platform**: Runpod.io single pod (no Docker/Kubernetes)
- **Hardware**: 8-16 vCPUs, 32-64GB RAM, 200-500GB NVMe SSD
- **Existing Services**: Ollama, n8n, OpenWebUI (already installed)
- **Persistent Storage**: /workspace/ for all data

## Tech Stack & Models

### Core Services
- **Qdrant v1.7.4** (application) with **v4.0 schema** (document processor): Direct binary installation (no Docker)
  - Multi-vector schema: `chunk_embedding`, `parent_embedding`, `child_embedding`, `full_doc_embedding` (768-d for sentence-transformers/all-mpnet-base-v2)
  - Sparse vectors for BM25 keyword search with complete hybrid search support
  - On-disk storage for memory efficiency and persistence under `/workspace/qdrant_storage`
  - **Dual-Collection Architecture** (R1.6, Q24, T037 verified 2025-10-05):
    - Primary: `nomad_bms_documents` (high-quality chunks ≥0.70 quality score) - 1794 points
    - Low-Quality: `nomad_bms_documents_low_quality` (low-quality chunks <0.70 for admin review) - 0 points
    - Both collections use identical v4.0 schema with 768-dimensional multi-vector embeddings
    - Future: `include_low_quality=true` parameter for admin access to low-quality chunks
  - **CORRECTED**: All vectors are 768-dimensional (not 1024-d) to match sentence-transformers/all-mpnet-base-v2 model output

- **Embedding Model**:
  - Primary: sentence-transformers/all-mpnet-base-v2 (768 dimensions) for document embeddings and search
  - LLM: qwen2.5:14b or llama3.1:8b via Ollama (for future answer generation and summarization; not required for MVP semantic search)
  - **Model Size Guidelines** (per constitution §11):
    - 32GB RAM: 7B-8B parameter models (e.g., llama3.1:8b, mistral:7b)
    - 64GB RAM: 12B-14B parameter models (e.g., qwen2.5:14b, mistral-nemo:12b)
    - GPU VRAM: Reserve 8-12GB for model inference, remainder for embeddings cache

- **Python 3.11+**: Direct installation with venv
  - No containerization, runs as system process
  - FastAPI on port 8000 for API endpoints
  - Persistent data in /workspace/bms_data/

- **Slack Integration**:
  - Direct FastAPI integration (primary)
  - Slack slash commands and event handlers
  - POC: no authentication required; Production: signature verification

- **n8n Integration**:
  - Optional workflow orchestration (secondary/post-MVP)
  - Webhook endpoints for document processing automation
  - POC: basic webhook support; Production: full workflow integration

- **OpenWebUI**:
  - Custom Qdrant tool integration (Priority 2)
  - Railway expertise prompts

## Implementation Plan

### Phase 0 – Specification & Planning (`T000`)
- Author the MVP specification (`.specify/features/001-bms-agent/spec.md`) to capture user stories, functional/non-functional requirements, and constitution mapping.
- Review constitution (§1–§4) to ensure acceptance criteria include standards compliance, basic monitoring, and testing thresholds (POC: simplified security and performance requirements).
- Establish Git flow branching strategy (feature/release branches) and document workflow expectations in `README.md`.
- Create `docs/migrations.md` to track any manual data/schema changes executed during the MVP.

### Phase 1 – Environment & Qdrant (`T001–T005`)
1. Provision project directories and persistent storage (`tasks.md` `T001`) sized for ≥1 TB to support multi-GB uploads and indexes.
2. Create Python virtual environment and install dependencies as per `reqs/requirements.txt` (`T002`).
3. Install Qdrant binary 1.7.4 locally (no Docker) and place logs under `/workspace/logs` (`T003`).
4. Generate `scripts/start_qdrant.sh` with optimized settings (on-disk vectors/payloads) and start the service (`T004`).
5. Initialize the `nomad_bms_documents` collection using `scripts/init_qdrant.py` with 768-d vector schema (matching sentence-transformers/all-mpnet-base-v2) plus sparse vector support for hybrid search (`T005`).

### Phase 2 – Core Application (`T006`, `T007`, `T011`)
1. Author `api/processor_wrapper.py` that wraps Enhanced Document Processor v4.0 with complete multi-format support (PDF, DOCX, PPTX, XLSX, CSV, TXT), quality optimization (0.718 score, 100% pass rate), perfect data cleaning, and enterprise-grade processing.
2. Generate comprehensive test suite including `scripts/test_processor.py`, format-specific tests (test_docx_*.py, test_pptx_*.py, test_xlsx_*.py, test_csv_*.py), and quality validation scripts for end-to-end verification.
3. Create `api/main.py` (FastAPI) exposing:
   - `POST /api/v1/documents/upload`
   - `POST /api/v1/search/semantic`
   - `POST /api/v1/search/hybrid`
   - `GET /health` and `GET /health/detailed`
   - Root endpoint summarising capabilities
4. Ensure all endpoints load configuration from environment variables with reasonable defaults for local development.
5. Implement streaming upload pipeline capable of handling 1 GB files without exhausting memory and persist both dense and sparse (keyword/BM25) payloads for each chunk.
6. Expose hybrid search utilities in the wrapper (query fusion, keyword extraction) for reuse by future endpoints.
7. Implement admin-only `include_low_quality` query flag that routes search requests to the `nomad_bms_documents_low_quality` collection when true, including regression tests and documentation updates.

### Phase 3 – Integrations (`T017`, `T018`)
- Implement direct FastAPI Slack integration (`api/slack_integration.py`) with slash command handlers and Block Kit formatting.
- Create OpenWebUI tool (`tools/bms_search.py`) to query the Qdrant collection via BMS API HTTP endpoints.

### Phase 4 – Security & Compliance (`T015`, `T016`)
1. **MVP REQUIREMENT**: Basic security implementation:
   - No JWT validation required for MVP (deferred to production)
   - No API key authentication for MVP (deferred to production)
   - **Rate limiting deferred to Production** per `spec.md` R3.2; capture remediation plan for Production sprint (T015)
   - Basic security headers middleware (X-Frame-Options, X-Content-Type-Options)
2. Ensure error handling (400/413) is covered by automated tests (T016); 429 responses remain production-only alongside rate limiting.
3. Document security roadmap in `docs/security-notes.md` for Production implementation (JWT, API key enforcement, rate limiting rollout).

### Phase 5 – Documentation, Tooling & CI/CD (`T015`, `T016`, `T023`, `T024` – post-MVP optional)
- Configure GitHub Actions (`.github/workflows/ci-cd.yml`) to run tests, coverage, basic security scans (Bandit, Safety - even for POC per constitution §5), pre-commit hooks (Black, Ruff, mypy), and provide deployment automation for RunPod binary releases.
- Document required secrets (`BMS_API_KEY`, `DEPLOY_KEY`, optional `CODECOV_TOKEN`, `SAFETY_API_KEY`, future `RUNPOD_USER/HOST` for SSH deployment).
- Generate and publish the OpenAPI 3.0 schema at `/openapi.json`, including CI checks that ensure the spec stays in sync with implemented endpoints and documentation.
- **Database Migration Note**: Alembic not required for Qdrant (NoSQL vector database). Manual schema changes tracked in `docs/migrations.md` per Phase 0. Future SQL databases (if added) will require Alembic implementation per constitution §9.
- **Deployment Model**: Direct binary installation in /workspace (not containerized) per constitution §11 persistence requirements for RunPod pods.

### Phase 6 – Testing & Evaluation (`T010`, `T017`, `T019`, `T020`)
1. Use `scripts/run_tests.sh` to orchestrate integration tests (processor, API smoke checks).
3. Create evaluation dataset (`data/evaluation/ground_truth.jsonl`) and `scripts/evaluate_retrieval.py` to compute top-5 accuracy ≥95 %.
4. Add hybrid retrieval regression tests validating keyword enrichment and dense/sparse fusion logic (leveraging `/api/v1/search/hybrid`).
5. Integrate evaluation into CI (report accuracy figure and fail if below threshold) and surface performance/hybrid results in pipeline artifacts.
6. Update `DEPLOYMENT_CHECKLIST.md` to include manual alert runbooks for latency, ingestion, and dependency degradation.

## Logging & Monitoring
1. Configure structured logging with correlation IDs and appropriate log levels for all components (API, Qdrant, processing pipeline).
2. Implement `/metrics/uplink` endpoint exposing latency histogram, request counts, and error totals for scraping.
3. Expose Prometheus metrics (FastAPI + Qdrant exporters) and provision Grafana dashboards aligned to 99.99 % availability (`T021`, included in MVP) with documented manual alert runbooks for latency, ingestion, and dependency degradation.
4. Note automated paging/notification delivery as post-MVP follow-up; document monitoring routine, log rotation, manual escalation steps, and incident response in `DEPLOYMENT_CHECKLIST.md`.

## File Structure
```
/workspace/
│   ├── qdrant_storage/            # Qdrant data files
│   ├── bms_data/
│   │   ├── uploads/               # Source documents
│   │   ├── processed/             # Processed artifacts (optional cache)
│   │   └── evaluations/           # Ground-truth/reference material
│   └── logs/
│       ├── qdrant.log
│       └── api.log
│
└── 001-bms-agent/
    ├── api/
    │   ├── main.py                # FastAPI entry point
    │   ├── processor_wrapper.py
    │   ├── security.py            # Rate limiting, headers
    │   └── slack_integration.py   # Direct Slack integration
    ├── tools/
    │   └── bms_search.py          # OpenWebUI tool
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
WORKSPACE_ROOT=/workspace
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
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
GENERATION_MODEL=mistral-nemo:12b-instruct

# Integrations
SLACK_BOT_TOKEN=your-token
SLACK_SIGNING_SECRET=your-secret
OPENWEBUI_URL=http://localhost:8080
N8N_WEBHOOK_JWT=...
```

## API Endpoints (MVP)

- `POST /api/v1/documents/upload` – Upload and process a single document (≤1 GB streaming, chunked write).
- `POST /api/v1/search/semantic` – Semantic vector search (POC: no authentication; Production: JWT + API key protected, rate limited).
- `GET /health` – Lightweight service heartbeat.
- `GET /health/detailed` – Extended health report (Qdrant collection state, Ollama status, n8n/OpenWebUI reachability).
- `GET /` – API overview and endpoint discovery.

## Testing & Validation Workflow

1. `./scripts/run_tests.sh` – Ensures Qdrant running, processor ingestion works, API responsive.
2. `pytest -v --cov=./ --cov-report=term-missing` – Unit/integration coverage (≥80 %).
3. `locust -f tests/performance/load/test_locust.py --headless -u 20 -r 5 -t 5m --host http://localhost:8000` – Establishes baseline performance metrics. See `spec.md` Performance Targets for phase-specific thresholds (POC: <500ms baseline, MVP: <200ms, Production: ≤100ms p95).
4. `python scripts/evaluate_retrieval.py` – Computes top-5 accuracy vs `data/evaluation/ground_truth.jsonl` (≥95 %).
5. Manual smoke tests via Slack bot and OpenWebUI to ensure integrations operate correctly.

## Performance & Reliability Targets

See `spec.md` Performance Targets section for complete phase-specific requirements.

**Summary**:
- **POC**: p95 <500ms baseline (escalate if >1000ms), ≥5 docs/min, best-effort availability
  - **⚠️ CRITICAL ESCALATION TRIGGER**: p95 >1000ms **BLOCKS MVP PROGRESSION** - requires optimization work before MVP phase can begin
  - Baseline establishment: p95 <500ms acceptable for POC completion
- **MVP**: p95 <200ms for 20-50 users, ≥10 docs/min, 99.9% availability
- **Production**: p95 ≤100ms for 20-100 users, ≥20 docs/min, 99.99% availability
- Storage efficiency: ≤100 GB for 10k documents using on-disk vectors/payloads

## Monitoring & Backup Strategy

- Health script scheduled via cron/systemd on RunPod to log status snapshots.
- Log rotation for `/workspace/logs/*.log` using `logrotate` or custom cron with 30-day retention (per R7.4).
- **MVP REQUIREMENT**: Implement Prometheus/Grafana integration as part of MVP per constitution §8; configure basic dashboards and metrics scraping via `/metrics/uplink` endpoint.

## Success Criteria & Priority Order

1. Qdrant installed, collection initialized (`nomad_bms_documents`).
2. Documents ingest via API and are searchable with relevant top results.
3. Slack integration returns contextual answers; OpenWebUI tool surfaces matching chunks.
4. **POC**: Document rate limiting deferment and remediation plan; **Production**: Implement and verify JWT + API key security plus 60 req/min rate limiting.
5. Retrieval accuracy evaluation ≥95 %; performance benchmarks within target.
6. Monitoring scripts and health endpoints provide actionable status.
7. CI pipeline green (tests, coverage, security scans) on main branch.

Priority sequence aligns with tasks: Setup (T000–T005) → Core (T006–T011) → Integrations (T008–T009) → Security (T014) → Documentation & CI (T015–T016) → Testing & Evaluation (T010, T017, T019) → Operations (T012, T013, T018).
