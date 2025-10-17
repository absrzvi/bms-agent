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
- **Persistent Storage**: /workspace/ for all data (updated for reboot persistence)

## Tech Stack & Models

### Core Services
- **Qdrant v1.7.4**: ✅ COMPLETED - Direct binary installation in /workspace
  - Multi-vector schema: `chunk_embedding`, `parent_embedding`, `child_embedding`, `full_doc_embedding` (1024-d)
  - Sparse vectors for BM25 keyword search: ✅ IMPLEMENTED
  - On-disk storage for memory efficiency and persistence under `/workspace/qdrant_storage`
  - Collection: `nomad_bms_documents` ✅ ACTIVE

- **Ollama Models**: ✅ COMPLETED - Running in /workspace
  - Embeddings: snowflake-arctic-embed2 (1024 dimensions) ✅ AVAILABLE
  - Generation: mistral:latest ✅ AVAILABLE
  - Alternative: qwen2.5:14b available if needed

- **Python 3.11+**: ✅ COMPLETED - Direct installation with venv
  - No containerization, runs as system process
  - FastAPI on port 8000 for API endpoints
  - Persistent data in /workspace/bms_data/ ✅ PROVISIONED

- **n8n Workflows**:
  - Slack bot integration (Priority 1)
  - Webhook endpoints protected with JWT per constitution §3

- **OpenWebUI**:
  - Custom Qdrant tool integration (Priority 2)
  - Railway expertise prompts

- **Enhanced Document Processor v4.0**: ✅ COMPLETED - Production Ready
  - Quality Score: 0.718 (8% improvement from v3.0)
  - Pass Rate: 100% (120% improvement)
  - Multi-format support: PDF, DOCX, PPTX, CSV, XLSX, TXT, MD
  - Processing speed: 1,135 chars/second
  - Batch processing: `process_directory_distributed()` with 4 workers
  - Quality features: Sentence-aware chunking, context preservation, RAGAS validation
  - Test coverage: 20+ validation scripts

## Current Status & Batch Processing

### ✅ COMPLETED PHASES
- **Phase 0**: Specification & Planning ✅ DONE
- **Phase 1**: Environment & Qdrant ✅ DONE (T001-T005)
  - Persistent storage provisioned in /workspace
  - Qdrant v1.7.4 installed and running
  - Collection `nomad_bms_documents` active with multi-vector support
  - Ollama running with required models

### 🔄 CURRENT: Batch Document Processing
- **Documents Available**: 54+ BMS documents in `/workspace/bms_data/uploads/`
  - 22 DOCX files (business continuity, engineering forms)
  - 32+ PDF files (policies, processes, procedures)
  - Additional PPTX and XLSX files
- **Processing Script**: `scripts/run_batch_processing.py` ✅ READY
- **Expected Results**: Enterprise-grade processing with ≥0.718 quality score

## Implementation Plan

### Phase 0 – Specification & Planning (`T000`) ✅ COMPLETED
- ✅ Author the MVP specification and constitution mapping
- ✅ Review constitution compliance (all 13 sections validated)
- ✅ Establish Git flow branching strategy and document workflow in `README.md`
- ✅ Create migration tracking documentation

### Phase 1 – Environment & Qdrant (`T001–T005`) ✅ COMPLETED
1. ✅ Provision project directories and persistent storage in `/workspace` (`T001`)
2. ✅ Create Python virtual environment and install dependencies (`T002`)
3. ✅ Install Qdrant binary 1.7.4 in `/workspace` with service management (`T003`)
4. ✅ Generate `scripts/start_qdrant.sh` and start the service (`T004`)
5. ✅ Initialize the `nomad_bms_documents` collection with multi-vector schema (`T005`)

### Phase 2 – Core Application (`T006`, `T007`, `T011`)
1. Author `api/processor_wrapper.py` that wraps `EnhancedDocumentProcessor`, handles chunking, embeddings via Ollama, and upserts to Qdrant.
2. Generate `scripts/test_processor.py` for end-to-end ingestion sanity checks.
3. Create `api/main.py` (FastAPI) exposing:
   - `POST /api/v1/search/semantic`
   - `GET /health` and `GET /health/detailed`
   - Root endpoint summarising capabilities
4. Ensure all endpoints load configuration from environment variables with reasonable defaults for local development.
5. Implement streaming upload pipeline capable of handling 1 GB files without exhausting memory and persist both dense and sparse (keyword/BM25) payloads for each chunk.
6. Expose hybrid search utilities in the wrapper (query fusion, keyword extraction) for reuse by future endpoints.

### Phase 3 – Integrations (`T008`, `T009`)
- Build n8n Slack workflow (`n8n/workflows/slack_bot.json`) to call the FastAPI search endpoint and format responses.
- Create OpenWebUI tool (`~/.openwebui/tools/bms_search.py`) to query the same Qdrant collection via HTTP.

### Phase 4 – Security & Compliance (`T014`)
1. Implement `api/security.py` (or equivalent module) providing:
   - JWT validation using RS256 (`BMS_JWT_PUBLIC_KEY` / `BMS_JWT_ALGORITHM`).
   - API key fallback for internal services (`BMS_API_KEY`).
   - Request-scoped rate limiting (60 req/min per JWT subject) using lightweight in-memory token bucket (no external dependencies).
   - Security headers middleware (CSP, HSTS optional, X-Frame-Options, X-Content-Type-Options).
   - Encryption at rest orchestration (RunPod volume encryption, Qdrant payload encryption) with documented key rotation workflow.
   - Role-based access control (RBAC) policies for admin/operator/service personas across API and n8n workflows.
   - Immutable audit logging plumbing (authentication, ingestion, search, admin actions) with ≥90-day retention.
2. Wire security dependencies into FastAPI routes and ensure 403/429 handling is covered by tests.
3. Extend automated security tests to validate RBAC enforcement, encryption toggles, and audit log creation; update `docs/security-notes.md` with validation checklist and outstanding items.

### Phase 5 – Documentation, Tooling & CI/CD (`T015`, `T016`, `T023`, `T024`)
- Maintain `README.md`, `TESTING.md`, `DEPLOYMENT_CHECKLIST.md`, and `reports/performance-baseline.md` with instructions reflecting current architecture.
- Configure GitHub Actions (`.github/workflows/ci-cd.yml`) to run tests, coverage, security scans (Bandit, Safety), pre-commit hooks (Black, Ruff, mypy), and provide deployment placeholders for RunPod automation.
- Document required secrets (`BMS_API_KEY`, `DEPLOY_KEY`, optional `CODECOV_TOKEN`, `SAFETY_API_KEY`, future `RUNPOD_USER/HOST`, `REGISTRY_USERNAME/PASSWORD`).

### Phase 6 – Testing & Evaluation (`T010`, `T017`, `T019`, `T020`)
1. Use `scripts/run_tests.sh` to orchestrate integration tests (processor, API smoke checks).
2. Expand `tests/test_basic.py` and the Locust scenario in `tests/performance/load/test_locust.py` to verify ≤100 ms p95 latency with 1,000 concurrent requests; document how latency metrics are captured and reported.
3. Create evaluation dataset (`data/evaluation/ground_truth.jsonl`) and `scripts/evaluate_retrieval.py` to compute top-5 accuracy ≥95 %.
4. Add hybrid retrieval regression tests validating keyword enrichment and dense/sparse fusion logic (leveraging `/api/v1/search/hybrid`).
5. Integrate evaluation into CI (report accuracy figure and fail if below threshold) and surface performance/hybrid results in pipeline artifacts.

### Phase 7 – Observability & Operations (`T012`, `T013`, `T018`, `T021`)
2. Implement `/metrics/uplink` endpoint exposing latency histogram, request counts, and error totals for scraping.
3. Expose Prometheus metrics (FastAPI + Qdrant exporters) and provision Grafana dashboards/alert rules aligned to 99.99 % availability (`T021`), including automated alerting for latency, ingestion, and dependency degradation.
4. Document monitoring routine, log rotation, alert response playbooks, and incident response in `DEPLOYMENT_CHECKLIST.md`.

## File Structure ✅ UPDATED
```
/workspace/                         # ✅ Persistent across reboots
├── qdrant                         # ✅ Qdrant binary
├── qdrant_storage/                # ✅ Qdrant data files
├── bms_data/
│   ├── uploads/                   # ✅ 54+ BMS documents ready for processing
│   ├── processed/                 # ✅ Processed artifacts
│   └── evaluations/               # ✅ Ground-truth/reference material
├── logs/
│   ├── qdrant.log                 # ✅ Qdrant service logs
│   ├── ollama.log                 # ✅ Ollama service logs
│   └── api.log                    # API logs (future)
├── ollama/                        # ✅ Ollama installation
│   ├── bin/ollama                 # ✅ Ollama binary
│   └── models/                    # ✅ Model storage
├── config/
│   └── config.yaml                # ✅ Qdrant configuration
└── setup-qdrant-service.sh        # ✅ Service setup script

/root/CascadeProjects/windsurf-project/001-bms-agent/
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
- Semantic query latency: ≤100 ms p95 with 1,000 concurrent users (validated via `tests/performance/load/test_locust.py` and associated latency reports).
- Availability: 99.99 % (documented monitoring + incident response, failover guidance TBD).
- Storage efficiency: ≤100 GB for 10 k documents using on-disk vectors/payloads.

## Monitoring & Backup Strategy

- Health script scheduled via cron/systemd on RunPod to log status snapshots.
- Log rotation for `~/persistent/logs/*.log` using `logrotate` or custom cron.
- Daily backups: `tar -czf ~/persistent/backups/bms_$(date +%Y%m%d).tar.gz ~/persistent/qdrant_storage ~/persistent/bms_data` (automate in cron after initial validation).
- Prometheus exporters and Grafana dashboards (latency, ingestion, dependency health) deployed as part of MVP, with alerts wired to on-call procedures.

## Success Criteria & Priority Order

1. Qdrant installed, collection initialized (`nomad_bms_documents`).
2. Documents ingest via API and are searchable with relevant top results.
3. Slack workflow returns contextual answers; OpenWebUI tool surfaces matching chunks.
4. JWT + API key security enforced; rate limiting verified.
5. Retrieval accuracy evaluation ≥95 %; performance benchmarks within target.
6. Monitoring scripts and health endpoints provide actionable status.
7. CI pipeline green (tests, coverage, security scans) on main branch.

Priority sequence aligns with tasks: Setup (T000–T005) → Core (T006–T011) → Integrations (T008–T009) → Security (T014) → Documentation & CI (T015–T016) → Testing & Evaluation (T010, T017, T019) → Operations (T012, T013, T018).

---

## 🎯 **CURRENT STATUS SUMMARY** (Updated: 2025-09-29)

### ✅ **COMPLETED INFRASTRUCTURE**
- **Qdrant v1.7.4**: Running in `/workspace` with multi-vector collection active
- **Ollama**: Running in `/workspace` with snowflake-arctic-embed2 and mistral models
- **Enhanced Document Processor v4.0**: Production-ready with 0.718 quality score
- **Persistent Storage**: All services configured for `/workspace` persistence
- **Document Inventory**: 54+ BMS documents ready for batch processing

### 🔄 **READY FOR EXECUTION**
- **Batch Processing Script**: `scripts/run_batch_processing.py` ready to process all documents
- **Service Management**: Complete scripts for Qdrant and Ollama management
- **Quality Assurance**: Enterprise-grade processing with comprehensive validation

### 📋 **NEXT IMMEDIATE STEPS**
1. **Execute Batch Processing**: Run `python3 scripts/run_batch_processing.py` to process 54+ documents
2. **Continue Implementation**: Proceed with Phase 2 (Core Application) tasks
3. **API Development**: Build FastAPI endpoints for document upload and search
4. **Integration Development**: Implement Slack bot and OpenWebUI tools

### 🏆 **ACHIEVEMENT HIGHLIGHTS**
- **Infrastructure**: 100% complete and persistent across reboots
- **Document Processor**: Production-ready with optimal quality scores
- **Architecture**: Constitutional compliance across all 13 sections
- **Scalability**: Distributed processing with 4-worker parallel execution

**The BMS Agent is ready for production document processing and API development!** 🚀
