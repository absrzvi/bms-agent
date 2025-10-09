# 002-n8n MS Teams Bot Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

**MANDATE**: All production code MUST be preceded by failing tests.

- Write tests → User approval → Tests fail → Then implement
- Red-Green-Refactor cycle strictly enforced
- Contract tests validate API schemas (BMS API, MS Teams Bot Framework)
- Integration tests validate end-to-end workflows (user message → bot response)
- **POC Exception**: Test coverage minimum 60% (relaxed from 80% production standard)
- **Production Gate**: 80% test coverage required before production deployment

**Violations**: Any implementation without preceding tests requires explicit documentation and remediation plan.

### II. n8n Workflow-First Architecture

**MANDATE**: Core bot logic MUST be implemented as n8n workflows, not standalone services.

- All bot interactions flow through n8n workflows (no direct service-to-service calls)
- Workflows exported as JSON files for version control
- Reusable logic extracted to shared modules (`/workspace/002-n8n/lib/`)
- **Architectural Decision**: MS Teams integration uses webhook + Bot Framework REST API (bypassing n8n MS Teams node due to credential configuration issues)

**Rationale**: n8n provides visual workflow debugging, non-developer maintenance access, and rapid iteration.

### III. Redis-Backed State Management

**MANDATE**: All conversation state MUST use Redis with TTL enforcement.

- 7-day TTL for conversation history (FR-027, FR-028)
- 60-second cache for whitelist configuration
- Automatic cleanup via TTL expiration (no manual purge required for conversations)
- Retry logic: 3 attempts, exponential backoff (100ms → 200ms → 400ms)
- **Fallback**: Stateless mode if Redis unavailable (NFR-002)

**Storage Requirements**:
- Conversation entity: 7-day TTL (604800s)
- DocumentUploadJob entity: 7-day TTL (604800s)
- Query history: 7-day TTL (604800s)
- Whitelist cache: 60-second refresh

### IV. Code Quality & Testing

**POC Phase Standards**:
- Test coverage: ≥60% (statements, branches, functions)
- Linting: ESLint with recommended config
- Contract tests for all external API dependencies (BMS API, MS Teams Bot Framework)
- Integration tests for all user-facing scenarios (16 acceptance scenarios from spec.md)
- Performance validation: p95 < 3000ms end-to-end

**Production Phase Standards**:
- Test coverage: ≥80% (statements, branches, functions)
- Load testing: 5x POC volume (250-500 queries/day)
- Security scanning: Bandit/ESLint security rules
- Dependency auditing: npm audit clean

### V. Monitoring & Observability

**POC Phase Requirements** (NFR-006):
- Health endpoint: `/health` returning component statuses (Redis, BMS API, Ollama, n8n)
- Structured logging: JSON format (timestamp, level, component, message)
- Log retention: 30 days minimum
- n8n execution logs for workflow debugging

**Production Phase Requirements** (deferred):
- Prometheus metrics export
- Grafana dashboards
- Alert thresholds (error rate >5%, p95 >3s)

**Decision Gate**: Implement advanced monitoring when user count >100 OR query volume >1000/day.

### VI. Security & Access Control

**MANDATE**: POC operates with channel whitelist; production requires OAuth integration.

- Channel whitelist enforced at bot handler entry point (before query processing)
- Admin privileges: First-user-admin model with reset mechanism
- Admin reset secret: 32+ character random string (generated via `openssl rand -hex 32`)
- Audit logging: All admin actions and reset attempts logged
- File upload validation: Only allowed types (PDF, CSV, XLSX, XLS, TXT, MD, DOCX, PPTX)
- Query length validation: Max 1000 UTF-8 characters (enforced at bot layer, not BMS API)

### VII. Documentation-First

**MANDATE**: User-facing features MUST have setup guides before deployment.

- Setup guide: `/workspace/002-n8n/docs/setup-ms-teams.md` (Bot Framework registration)
- Troubleshooting guide: `/workspace/002-n8n/docs/troubleshooting.md` (common errors)
- Workflow implementation guide: `/workspace/002-n8n/docs/workflow-implementation-guide.md` (n8n UI instructions)
- Architecture decision records: Documented in `research.md` (e.g., webhook vs n8n MS Teams node)

## Development Workflow

### Phase Gate Requirements

**Phase 0 (Research)**: PASS
- All technical unknowns resolved (documented in research.md)
- Architectural decisions justified (e.g., webhook approach for MS Teams)
- Technology choices validated (n8n 1.x, Redis 7, Mistral Nemo via Ollama)

**Phase 1 (Design)**: PASS
- Data model documented (data-model.md with 6 entities)
- API contracts defined (contracts/ directory with 3 contract files)
- Quickstart guide created (quickstart.md with 8 setup steps + 5 test scenarios)

**Phase 2 (Tasks)**: PASS
- Task list generated (tasks.md with 43 tasks)
- Dependencies mapped (critical path and parallel groups identified)
- File paths specified (no ambiguous task descriptions)

**Phase 3 (Implementation)**: IN PROGRESS
- All tests written and failing BEFORE implementation
- TDD cycle enforced for each task
- Code review for tasks modifying shared modules (`lib/`)

**Phase 4 (Validation)**: PENDING
- Test coverage ≥60% verified
- Performance targets met (p95 < 3000ms)
- Quickstart guide executed successfully
- All acceptance scenarios passing

### Validation Gates

**Test Coverage Gate** (MANDATORY before deployment):
```bash
npm test -- --coverage
# Assert: Overall coverage ≥60% for POC, ≥80% for production
```

**Performance Gate** (MANDATORY before deployment):
```bash
npm test tests/performance/load-test.js
# Assert: p95 < 3000ms, error rate <5%, 20 concurrent users
```

**Integration Gate** (MANDATORY before deployment):
```bash
npm test tests/integration/
# Assert: All 16 acceptance scenarios passing
```

## Complexity Tracking

| Architectural Decision | Justification | Simpler Alternative Rejected Because |
|------------------------|---------------|-------------------------------------|
| Webhook + Bot Framework API instead of n8n MS Teams node | n8n MS Teams node credential configuration repeatedly failed; webhook approach provides full control over authentication | n8n MS Teams node: Credential UI issues blocked progress; webhook approach allows OAuth 2.0 client credentials flow via HTTP Request nodes |
| Polling for document upload completion (30s intervals) | BMS API does not provide webhook callback for async upload status | Webhook callback: BMS API /documents/upload/async endpoint does not support callback URLs; polling balances notification latency with API load |
| 60% test coverage for POC (vs 80% production) | POC prioritizes velocity to validate user value proposition | 80% coverage for POC: Would delay user feedback by ~8-10 hours; POC is time-boxed; production deployment enforces 80% |

## Governance

**Constitution Authority**: This constitution is NON-NEGOTIABLE within the project scope.

- All pull requests MUST verify compliance with these principles
- Deviations MUST be documented in Complexity Tracking section with justification
- Amendments require explicit approval and version increment

**Amendment Process**:
1. Propose amendment with rationale (document in PR description)
2. Update Complexity Tracking with deviation justification
3. Obtain approval from project stakeholders
4. Update constitution version and Last Amended date

**Compliance Verification**:
- `/analyze` command validates spec/plan/tasks against constitution
- Critical violations block deployment
- High/medium violations require remediation plan

**Version**: 1.0.0 | **Ratified**: 2025-10-07 | **Last Amended**: 2025-10-07
