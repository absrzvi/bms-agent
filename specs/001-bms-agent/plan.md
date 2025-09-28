---
description: "Implementation plan template for feature development"
scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

# Implementation Plan: BMS Agent MVP

**Branch**: `001-bms-agent` | **Date**: 2025-09-28 | **Spec**: `specs/001-bms-agent/spec.md`
**Input**: Feature specification from `specs/001-bms-agent/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
- **Goal**: Deliver a RunPod-hosted retrieval-augmented assistant for railway network documentation with Slack, n8n, and OpenWebUI integrations.
- **Scope**: Stream up to 1 GB documents, chunk and embed into Qdrant, expose FastAPI endpoints (`/api/v1/documents/upload`, `/api/v1/search/semantic`, `/api/v1/search/hybrid`, health, metrics), ensure ≥95 % top-5 retrieval accuracy and ≤100 ms p95 latency.
- **Approach**: Python 3.11 FastAPI service orchestrating EnhancedDocumentProcessor, Ollama (snowflake-arctic-embed2 + mistral-nemo:12b-instruct), self-hosted Qdrant, n8n workflow, OpenWebUI custom tool, GitHub Actions CI with security and performance gates.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, Qdrant client, Ollama, EnhancedDocumentProcessor stack, n8n workflows, OpenWebUI toolchain  
**Storage**: RunPod-managed encrypted NVMe volume; Qdrant collections for embeddings; local filesystem under `~/persistent/`  
**Testing**: pytest with coverage, Locust load tests, custom evaluation scripts, Bandit/Safety scans  
**Target Platform**: Single RunPod pod (Ubuntu) with 8–16 vCPU, 32–64 GB RAM, 200–500 GB NVMe  
**Project Type**: Single backend service with supporting automation  
**Performance Goals**: ≤100 ms p95 search latency @ 1,000 concurrent requests; ≥95 % top-5 retrieval accuracy  
**Constraints**: 1 GB document ingestion, JWT+API key auth, rate limiting 60 req/min, observability mandate (Prometheus + Grafana), 99.99 % availability  
**Scale/Scope**: Initial deployment serving railway engineering team; document corpus up to 10 k files and 1 TB storage envelope

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
- **§1 Railway Standards**: Architecture maintains on-prem RunPod deployment with high availability and performance targets (≤100 ms, 99.99 % uptime) documented in spec. No violation.
- **§2 RAG Architecture**: Uses Python 3.11+, EnhancedDocumentProcessor, Qdrant hybrid retrieval, 1 GB ingestion, Ollama embeddings—meets all mandates.
- **§3 n8n Integration**: REST endpoints with JWT+API key, structured errors, rate limiting, OpenAPI exposure align with requirements.
- **§4 Code Quality & Testing**: Plan enforces ≥80 % coverage, pytest, pre-commit (Black, Ruff, mypy), performance benchmarking.
- **§5 Security & Compliance**: Encryption at rest via RunPod-managed volume, RBAC, audit logging, GDPR alignment via data handling policies.
- **§7/§8 Performance & Observability**: Locust load tests, Prometheus metrics, Grafana dashboards, alerting for latency/ingestion/dependencies; document manual alert runbooks for latency, ingestion, and dependency degradation with clear escalation steps.
4. Call out automated pager/notification delivery as post-MVP scope; include monitoring routine, log rotation, alert response playbooks, and incident response in `DEPLOYMENT_CHECKLIST.md`.
- **§9 Workflow**: Git flow, semantic versioning, CI/CD defined; plan includes migration logging.
- **§10–§12 Architecture**: Modular service architecture with repository/service layers, hybrid retrieval via Qdrant.
- **§11 AI/LLM**: Local Ollama models only, no external inference calls, embedding versioning captured in research tasks.

**Status**: PASS – proceed to Phase 0.

### Documentation (this feature)
```
specs/001-bms-agent/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-search.yaml
│   └── api-documents.yaml
└── tasks.md
```

### Source Code (repository root)
```
bms-agent/
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── processor_wrapper.py
│   └── security.py
├── data/
│   └── evaluation/ground_truth.jsonl (generated)
├── docs/
│   ├── migrations.md
│   └── security-notes.md
├── n8n/
│   └── workflows/slack_bot.json
├── scripts/
│   ├── start_qdrant.sh
│   ├── init_qdrant.py
│   ├── manage_services.sh
│   ├── health_check.sh
│   ├── run_tests.sh
│   └── evaluate_retrieval.py
├── tests/
│   ├── __init__.py
│   ├── test_basic.py
│   ├── integration/test_hybrid_search.py
│   └── performance/load/test_locust.py
├── requirements.txt
├── requirements-test.txt
└── README.md

.github/
└── workflows/ci-cd.yml
```

**Structure Decision**: Single-service backend in `bms-agent/` with supporting scripts, tests, and CI under `.github/`. No separate frontend/mobile components required.

## Phase 0: Outline & Research
1. **Targets**
   - Confirm RunPod-managed encryption approach (Clarification Session 1).
   - Validate Qdrant schema sizing for hybrid vectors and retention requirements.
   - Document Ollama model resource footprint and fallback models.
   - Capture data ingestion safeguards (streaming, file validation, rate limits).
2. **Research Tasks**
   - R0.1: Gather RunPod encryption + key rotation operational playbook.
   - R0.2: Benchmark Qdrant multi-vector collection at target corpus scale.
   - R0.3: Profile `snowflake-arctic-embed2` + `mistral-nemo:12b-instruct` on target hardware; document resource thresholds and fallback triggers.
   - R0.4: Review EnhancedDocumentProcessor configuration for 1 GB streaming ingestion and memory backpressure.
3. **Consolidation**
   - Summaries recorded in `research.md` with decision/rationale/alternatives.
   - Mark unresolved risks for follow-up during Phase 1.

**Output**: `research.md` with all critical unknowns resolved or flagged.

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Data Model Extraction** → `data-model.md`
   - Entities: Document, DocumentVersion, Chunk, ChunkEmbedding, RetrievalQuery, AuditLog, UserIdentity.
   - Capture validation (file type whitelist, size ≤1 GB), lifecycle states (ingested → processed → indexed), retention (90-day audit logs).
2. **API Contracts** → `contracts/`
   - `api-documents.yaml`: Upload endpoint schema (streamed multipart), validation errors.
   - `api-search.yaml`: Semantic/hybrid search endpoints, response payload with dense/sparse scores, trace IDs.
   - Include `/health`, `/health/detailed`, `/metrics/uplink` response structures.
3. **Contract Tests**
   - Map each contract to placeholder pytest modules (fail-first) under `tests/contract/` (created in later implementation phase).
4. **Integration Scenarios** → `quickstart.md`
   - Slack n8n workflow invocation sequence.
   - OpenWebUI tool usage and expected responses.
   - Performance validation steps (Locust, evaluation script).
5. **Agent Context Update**
   - Run `scripts/bash/update-agent-context.sh github-copilot` once design changes introduce new tech (kept for future automation hook).

**Output**: `data-model.md`, `/contracts/*`, `quickstart.md`, notes for contract tests.

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base.
- Create tasks for: environment/bootstrap scripts, Qdrant setup, processor integration, API endpoints, security enforcement, observability wiring, integrations (n8n/OpenWebUI), tests (unit/integration/performance/security).
- Derive contract tasks from `/contracts/` definitions (one task per endpoint + error cases).
- Map data model entities to persistence/schema tasks (Qdrant indexes, metadata).
- Include operational documentation updates (`README.md`, `DEPLOYMENT_CHECKLIST.md`, `docs/security-notes.md`).

**Ordering Strategy**:
- TDD-first: write/extend tests (including Locust configuration) before implementation where feasible.
- Storage and ingestion foundation before API surface (Qdrant install → collection init → processor wrapper → API routes).
- Security/observability tasks blocked on API scaffolding; mark parallelizable tasks `[P]` when touching independent files (e.g., docs vs. code).

**Estimated Output**: 28–32 ordered tasks.

**IMPORTANT**: This phase is executed by the `/tasks` command, NOT by `/plan`.

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No deviations from constitution identified; table intentionally left blank.*


## Progress Tracking
*Updated as phases complete*

- **Phase Status**:
- [X] Phase 0: Research complete (/plan command)
- [X] Phase 1: Design complete (/plan command)
- [X] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

- **Gate Status**:
- [X] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS
- [ ] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
