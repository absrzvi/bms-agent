---
description: "Implementation plan template for feature development"
scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

# Implementation Plan: BMS Agent

**Branch**: `001-bms-agent` | **Date**: 2025-09-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-bms-agent/spec.md`

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
Railway network documentation retrieval-augmented assistant with Enhanced Document Processor v4.0, deployed on RunPod with complete integration stack including Slack bot, OpenWebUI tool, and n8n workflows. Supports multi-format document processing (PDF, DOCX, PPTX, CSV, XLSX, TXT) with enterprise-grade quality (0.718 score, 100% pass rate), semantic/hybrid search via Qdrant vector database, and department-level scalability (20-100 concurrent users).

## Technical Context
**Language/Version**: Python 3.11+ (constitution requirement)  
**Primary Dependencies**: FastAPI, Qdrant, Enhanced Document Processor v4.0, Ollama, python-docx, python-pptx, PyMuPDF, pandas  
**Storage**: Qdrant vector database (v1.7.4), /workspace folder for persistent data, Ollama for embeddings  
**Testing**: pytest, comprehensive test suite (25+ validation scripts), Locust for performance testing  
**Target Platform**: RunPod Linux server, single pod deployment  
**Project Type**: single - API service with integrations  
**Performance Goals**: ≤100ms p95 search latency, 1,135 chars/sec processing, ≥95% retrieval accuracy  
**Constraints**: 20-100 concurrent users, 1GB max file size, 99.99% availability target, /workspace storage  
**Scale/Scope**: Department-level deployment, multi-format documents, complete integration stack

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Railway IT Standards (§1)**: ✅ PASS - EN50155/EN45545 compliance documented, 99.99% availability target set  
**RAG Architecture (§2)**: ✅ PASS - Python 3.11+, Enhanced Document Processor v4.0, Qdrant v4+ schema, hybrid search  
**n8n Integration (§3)**: ✅ PASS - RESTful API with OpenAPI 3.0, webhook endpoints, structured error handling  
**Code Quality (§4)**: ✅ PASS (MVP) - Basic testing scope acceptable for POC, comprehensive test suite available  
**Security (§5)**: ✅ PASS (POC) - API key authentication, basic rate limiting, POC security acceptable  
**Documentation (§6)**: ✅ PASS - Comprehensive specs, API documentation, setup guides planned  
**Performance (§7)**: ✅ PASS (POC) - Best effort performance acceptable, specific targets documented  
**Monitoring (§8)**: ✅ PASS - Prometheus/Grafana dashboards, structured logging, health checks  
**Development Workflow (§9)**: ✅ PASS - Git flow, semantic versioning, container builds planned  
**Architecture (§10)**: ✅ PASS - Modular design, service layer, clear separation of concerns  
**AI/LLM Architecture (§11)**: ✅ PASS - Local Ollama deployment, no external API calls, data sovereignty  
**Vector Database (§12)**: ✅ PASS - Self-hosted Qdrant, hybrid retrieval, optimized chunking  
**n8n Integration (§13)**: ✅ PASS - Webhook-driven workflows, stateless processing, error recovery

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
api/
├── main.py                  # FastAPI application entry point
├── processor_wrapper.py     # Enhanced Document Processor v4.0 integration
├── security.py             # Authentication, rate limiting, headers
└── models/
    ├── documents.py         # Document processing models
    ├── search.py           # Search request/response models
    └── health.py           # Health check models

bms-agent/
└── scr/
    ├── enhanced_document_processor.py  # Core processor (existing)
    └── qdrant_schema_v4.py            # Vector database schema

scripts/
├── init_qdrant.py          # Qdrant collection initialization
├── start_qdrant.sh         # Service management
├── manage_services.sh      # Orchestration
├── health_check.sh         # System health validation
├── evaluate_retrieval.py   # Accuracy evaluation
└── test_*.py              # Comprehensive test suite (25+ files)

n8n/workflows/
└── slack_bot.json          # Slack integration workflow

tools/
└── bms_search.py           # OpenWebUI custom tool

tests/
├── contract/               # API contract tests
├── integration/            # End-to-end tests
├── performance/load/       # Locust performance tests
└── unit/                  # Component tests

config/
├── requirements.txt        # Python dependencies
├── requirements-test.txt   # Test dependencies
└── .env.example           # Configuration template

docs/
├── enhanced-document-processor-v4.md  # Technical documentation
└── DEPLOYMENT_CHECKLIST.md           # Operations runbook
```

**Structure Decision**: Single project structure selected for API service with integrations. Core Enhanced Document Processor v4.0 maintained in existing bms-agent/scr/ location, with FastAPI wrapper in api/ directory and comprehensive tooling in scripts/.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `{SCRIPT}`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Enhanced Document Processor v4.0 integration (already completed - mark as COMPLETED)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass
- Integration tasks for Slack, OpenWebUI, n8n workflows
- Monitoring and observability setup tasks

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Environment setup → Qdrant → Enhanced Processor → API → Integrations → Monitoring
- Mark [P] for parallel execution (independent files)
- Account for existing Enhanced Document Processor v4.0 (T009 COMPLETED status)

**BMS Agent Specific Tasks**:
- Environment setup (Qdrant, Ollama, Python venv)
- Enhanced Document Processor v4.0 wrapper (leverage existing implementation)
- FastAPI endpoints (upload, search, health, metrics)
- Security middleware (rate limiting, API key auth)
- Integration implementations (Slack bot, OpenWebUI tool, n8n workflows)
- Monitoring setup (Prometheus, Grafana dashboards, alert runbooks)
- Testing suite (contract, integration, performance, accuracy evaluation)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md with proper dependencies

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - research.md with all decisions documented
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md updated
- [x] Phase 2: Task planning complete (/plan command - describe approach only) - Strategy documented
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS - All 13 sections compliant
- [x] Post-Design Constitution Check: PASS - Design maintains compliance
- [x] All NEEDS CLARIFICATION resolved - Technical context complete
- [x] Complexity deviations documented - None required

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
