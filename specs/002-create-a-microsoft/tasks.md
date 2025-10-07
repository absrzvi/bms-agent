# Tasks: MS Teams Chat Bot for BMS Agent

**Input**: Design documents from `/workspace/specs/002-create-a-microsoft/`
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✓ Tech stack: n8n 1.x, Redis 7, Node.js 18+, Mistral Nemo via Ollama
   → ✓ Structure: Single project with n8n workflows + supporting scripts
2. Load optional design documents:
   → ✓ data-model.md: 6 entities extracted
   → ✓ contracts/: 3 contract files found
   → ✓ research.md: 8 technical decisions extracted
   → ✓ quickstart.md: 8 deployment steps + 5 test scenarios
3. Generate tasks by category:
   → Setup: 6 tasks (Redis, n8n, config, storage)
   → Tests: 10 tasks (3 contract tests + 5 integration tests + 1 load test + 1 POST-POC)
   → Core: 8 tasks (6 n8n workflows + 3 supporting scripts + similar query detection)
   → Integration: 5 tasks (Redis connection, whitelist, file upload, typing, proactive notifications)
   → Polish: 8 tasks (unit tests, docs, cleanup, validation, coverage enforcement)
4. Apply task rules:
   → 15 tasks marked [P] for parallel execution
   → Tests before implementation (TDD)
   → Infrastructure before workflows
5. Number tasks sequentially (T001-T034)
6. Generate dependency graph below
7. Create parallel execution examples
8. Validate task completeness:
   → ✓ All 3 contracts have tests
   → ✓ All 6 entities have storage schema tasks
   → ✓ All 6 workflows have implementation tasks
9. Return: SUCCESS (39 tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- File paths use `/workspace/002-n8n/` as project root

## Path Conventions
Project structure from plan.md:
```
/workspace/002-n8n/
├── workflows/       # n8n workflow JSON exports
├── scripts/         # Shell scripts for deployment/maintenance
├── config/          # Configuration files (whitelist.json, env)
├── tests/           # Integration tests (Jest)
└── docs/            # Setup guides
```

---

## Phase 3.1: Setup & Infrastructure

- [x] **T001** Create project directory structure at `/workspace/002-n8n/` with subdirs: workflows/, scripts/, config/, tests/, docs/

- [x] **T002** Install Redis with persistent storage in /workspace (RunPod-compatible)
  - Path: `/workspace/redis` (binary) and `/workspace/redis_data` (data directory)
  - **REQUIRED**: Build from source in /workspace for RunPod persistence (OPTION 1)
  - Installation steps:
    1. **Recommended (RunPod)**: Build from source in /workspace
       ```bash
       cd /workspace && \
       wget http://download.redis.io/releases/redis-7.0.15.tar.gz && \
       tar xzf redis-7.0.15.tar.gz && \
       cd redis-7.0.15 && \
       make && \
       make PREFIX=/workspace/redis install
       ```
    2. Alternative (development only): Use system package manager with custom data dir
       ```bash
       apt-get install redis-server
       # Then configure data dir to `/workspace/redis_data` in redis.conf
       ```
  - Configuration: Edit `/workspace/redis/redis.conf` to set `dir /workspace/redis_data` and `appendonly yes`
  - Start command: `/workspace/redis/bin/redis-server /workspace/redis/redis.conf --daemonize yes` (add to startup script)
  - Verify: `redis-cli ping` returns PONG
  - NOTE: Must use /workspace for persistence across RunPod pod restarts (per CLAUDE.md RunPod deployment architecture)

- [x] **T003** [P] Initialize whitelist configuration file
  - Path: `/workspace/002-n8n/config/whitelist.json`
  - Schema: `{"admins": [], "channels": []}`
  - Must be JSON-formatted, empty arrays

- [x] **T004** [P] Create environment variables template
  - Path: `/workspace/002-n8n/config/env.example`
  - Include: BOT_APP_ID, BOT_APP_PASSWORD, BMS_API_URL, REDIS_URL, OLLAMA_URL
  - Add comments explaining each variable

- [x] **T005** [P] Write init-storage.sh script
  - Path: `/workspace/002-n8n/scripts/init-storage.sh`
  - Creates config/whitelist.json if not exists
  - Tests Redis connectivity
  - Make executable: `chmod +x`

- [x] **T006** [P] Install Node.js test dependencies
  - Path: `/workspace/002-n8n/package.json`
  - Dependencies: jest@29.x, axios, redis
  - Run: `npm install`

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY workflow implementation**

### Contract Tests (Parallel - Different Files)

- [x] **T007** [P] Contract test for MS Teams webhook schema ✅
  - Path: `/workspace/002-n8n/tests/contract/test-ms-teams-webhook.js`
  - Test: Validate incoming message structure per contracts/ms-teams-webhook.json
  - Assert: type, id, from.id, conversation.id, text fields present
  - ✅ FAILING as expected (ECONNREFUSED - no workflow exists)

- [x] **T008** [P] Contract test for BMS API /ask endpoint ✅
  - Path: `/workspace/002-n8n/tests/contract/test-bms-ask-integration.js`
  - Test: POST http://localhost:8000/api/v1/ask with valid query
  - Assert: Response has status, answer, citations[], confidence
  - ✅ FAILING as expected (no integration exists)

- [x] **T009** [P] Contract test for conversation storage API ✅
  - Path: `/workspace/002-n8n/tests/contract/test-context-storage.js`
  - Test: GET /context/{conversation_id} returns Conversation schema
  - Test: POST /context/{conversation_id} stores Message
  - Assert: 7-day TTL set on Redis keys
  - ✅ FAILING as expected (no storage logic exists)

### Integration Tests (Parallel - Different Test Scenarios)

- [x] **T010** [P] Integration test: Natural language question in personal chat ✅
  - Path: `/workspace/002-n8n/tests/integration/test-message-flow.js`
  - Scenario: User asks "What are emergency brake procedures?"
  - Assert: Bot responds with answer + citations within 3s
  - Mock: MS Teams webhook trigger
  - ✅ FAILING as expected (ECONNREFUSED)

- [x] **T011** [P] Integration test: Slash command execution ✅
  - Path: `/workspace/002-n8n/tests/integration/test-commands.js`
  - Scenarios:
    1. User types `/help` → Assert response contains all 7 commands from response-templates.json
    2. User types `/status [doc_id]` → Assert returns DocumentUploadJob status (queued/processing/completed/failed)
    3. User types `/history` → Assert returns last 7 days of queries with timestamps
    4. User types `/search [query]` → Assert returns search results without generated answer
    5. User types `/ask [question]` → Assert returns answer with citations
    6. (FR-031) User types query with 1001 UTF-8 characters → Assert error "Query too long. Please limit to 1000 characters."
    7. (FR-031) User types query with exactly 1000 characters including emoji → Assert query processed successfully
  - ✅ FAILING as expected

- [x] **T012** [P] Integration test: Document upload with file attachment ✅
  - Path: `/workspace/002-n8n/tests/integration/test-file-upload.js`
  - Scenario 1: User attaches PDF file
    - Assert: BMS API /upload called, returns document_id
    - Assert: Confirmation message sent to user
  - Scenario 2 (NFR-010): User attaches non-whitelisted file type (e.g., .exe, .zip)
    - Assert: File rejected before BMS API call
    - Assert: Error message from response-templates.json "file_type_invalid"
    - Assert: Validation checks against allowed types: PDF, CSV, XLSX, XLS, TXT, MD, DOCX, PPTX
  - ✅ FAILING as expected

- [x] **T013** [P] Integration test: Admin whitelist management ✅
  - Path: `/workspace/002-n8n/tests/integration/test-admin-commands.js`
  - Scenario: Admin types `/admin allow #ops-team`
  - Assert: Channel added to whitelist.json
  - Assert: Response "Access granted to #ops-team"
  - Mock: User with is_admin=true
  - ✅ FAILING as expected (ECONNREFUSED)

- [x] **T014** [P] Integration test: Context storage failure fallback ✅
  - Path: `/workspace/002-n8n/tests/integration/test-storage-failure.js`
  - Scenario: Redis unavailable, user asks question
  - Assert: Bot responds with warning + answer (stateless mode)
  - Assert: Warning text matches NFR-002 spec
  - ✅ FAILING as expected

### Performance Test

- [x] **T015** [P] Load test: 20 concurrent users, 100 queries ✅
  - Path: `/workspace/002-n8n/tests/performance/load-test.js`
  - Test: Simulate 20 users sending queries simultaneously
  - Assert: p95 response time < 3000ms
  - Assert: Error rate < 5%
  - ✅ FAILING as expected (no workflows deployed)

- [ ] **T015b** [POST-POC] Load test: 5x scale validation (NFR-005a)
  - Path: `/workspace/002-n8n/tests/performance/load-test-5x.js`
  - Test: Simulate 50-100 users with 250-500 queries per day
  - Distribution: Spread queries over simulated 8-hour workday
  - Assert: p95 response time < 3000ms maintained at 5x scale
  - Assert: Error rate < 5%
  - Assert: Redis memory usage < 2GB
  - NOTE: Execute during post-POC phase before production deployment

---

## Phase 3.2a: n8n Installation (Required before 3.3)

- [x] **T015a** Install n8n locally without Docker ✅
  - Install location: `/workspace/n8n` (for RunPod persistence)
  - Installation method: npm global install
  - Steps completed:
    1. ✅ Installed n8n globally (version 1.113.3)
    2. ✅ Created n8n data directories at `/workspace/n8n/.n8n` and `/workspace/n8n/workflows`
    3. ✅ Created environment config: `/workspace/002-n8n/config/n8n.env`
    4. ✅ Created startup script: `/workspace/002-n8n/scripts/start-n8n.sh`
    5. ✅ Made script executable
    6. ✅ Started n8n and verified running on port 5678
    7. ✅ Verified HTTP 200 response from http://localhost:5678
  - Configuration:
    - `N8N_USER_FOLDER=/workspace/n8n`
    - `N8N_HOST=0.0.0.0`, `N8N_PORT=5678`
    - `WEBHOOK_URL=http://localhost:5678/`
    - Security settings enabled (file permissions, git bare repos disabled)
    - Performance tuning (SQLite pool=5, task runners enabled)
  - n8n Editor: http://0.0.0.0:5678
  - Status: ✅ n8n running (PID visible in ps aux)

---

## Phase 3.3: Core Implementation (ONLY after T007-T015a complete)

### n8n Workflows (Parallel - Different Workflow Files)

- [ ] **T016** [P] Create main bot handler workflow ⚠️ MANUAL IN n8n UI
  - Path: `/workspace/002-n8n/workflows/main-bot-handler.json`
  - **Status**: Implementation guide and helper utilities ready
  - **Action Required**: Create workflow in n8n UI following `/workspace/002-n8n/docs/workflow-implementation-guide.md`
  - **Helper Module**: `/workspace/002-n8n/lib/workflow-helpers.js` available for Function nodes
  - Components:
    1. Webhook Trigger (MS Teams Bot Framework webhook incoming message)
    2. Extract message data (from, conversation, text, attachments)
    3. **Input Validation (FR-031)**: Check query length (UTF-8 character count)
       - If text.length > 1000 characters → return error from response-templates.json
       - Error template: "query_too_long"
       - Do NOT send to BMS API (fail fast at bot layer)
    4. **Malformed Command Handling**: Validate command syntax
       - If command detected (text starts with /) but no recognized pattern → return error "Unknown command. Type /help for available commands."
       - If recognized command but missing required parameters (e.g., `/admin` with no action) → return error with usage example
    5. Whitelist check (call /whitelist/check)
    6. Route to appropriate sub-workflow or command handler
    7. Send typing indicator
    8. Format and send response to MS Teams
       - NOTE: response-templates.json contains message templates for n8n workflow logic
       - Final Teams message is rendered as plain text with citations (per NFR-004)
       - Templates provide structured content that workflows convert to plain text before sending
  - Command Handlers (FR-007 to FR-015):
    - `/ask [question]` → Route to query-analyzer (T017) → bms-api-caller (T018)
    - `/search [query]` → Route to bms-api-caller (T018) with search intent
    - `/upload` → Prompt user to attach file (handled by T026)
    - `/help` → Return formatted help from response-templates.json
    - `/status [document_id]` → Query Redis for DocumentUploadJob, return status from response-templates.json
    - `/history` → Query Redis for Conversation entity history, return last 7 days queries from response-templates.json
    - `/admin [action] [target]` → Route to admin-commands workflow (T020)
  - Natural language (no command prefix) → Route to query-analyzer (T017) for intent detection
  - Export as JSON for n8n import

- [ ] **T017** [P] Create query analyzer workflow ⚠️ MANUAL IN n8n UI
  - Path: `/workspace/002-n8n/workflows/query-analyzer.json`
  - **Status**: Implementation guide ready (Section 2 of workflow-implementation-guide.md)
  - Components:
    1. HTTP Request to Ollama (Mistral Nemo)
    2. Prompt: Intent classification (ASK vs SEARCH vs COMMAND)
    3. Parse LLM response
    4. Return intent + confidence
  - Use prompts from research.md section 4
  - Export as JSON

- [ ] **T018** [P] Create BMS API caller workflow ⚠️ MANUAL IN n8n UI
  - Path: `/workspace/002-n8n/workflows/bms-api-caller.json`
  - **Status**: Implementation guide ready (Section 3 of workflow-implementation-guide.md)
  - Components:
    1. If intent=ASK → POST /api/v1/ask
    2. If intent=SEARCH → POST /api/v1/search/semantic
    3. Error handling (503 → "BMS-search tool cannot be accessed")
    4. Timeout: 2.5s max
    5. Format response with citations
  - Export as JSON

- [ ] **T019** [P] Create context manager workflow ⚠️ MANUAL IN n8n UI
  - Path: `/workspace/002-n8n/workflows/context-manager.json`
  - **Status**: Implementation guide ready (Section 4), Redis client module available
  - **Dependencies**: Uses `/workspace/002-n8n/lib/redis-client.js` ✓
  - Components:
    1. GET /context/{conversation_id} from Redis
    2. If not found → create new Conversation
    3. POST message to conversation
    4. Update context_summary (last 5 messages)
    5. Set 7-day TTL (604800s)
    6. **Restoration Detection (NFR-003)**: Track Redis availability state
       - If previous request failed (503) and current request succeeds → set flag `storage_restored=true`
       - Return `storage_restored` flag to main-bot-handler
       - Main handler sends notification using response-templates.json "storage_restored" template
  - Schema from data-model.md
  - Export as JSON

- [x] **T019a** [P] Create similar query detection workflow (FR-017) ✅
  - Path: `/workspace/002-n8n/workflows/similar-query-detector.json`
  - Components:
    1. Called from main-bot-handler before query processing
    2. Retrieve user's query history from Redis (user:{user_id}:history)
    3. **Generate embedding for new query**: Use BMS API embedding endpoint
       - POST http://localhost:8000/api/v1/embeddings with query text
       - Returns 768-dimensional vector (sentence-transformers/all-mpnet-base-v2)
       - **Rationale**: Use same model as document embeddings for consistency (per CLAUDE.md line 43)
    4. Compare with stored query embeddings using cosine similarity
    5. If similarity ≥ 0.85 threshold → return previous query and response
    6. Format suggestion using response-templates.json "similar_query" template
    7. Store new query with embedding: {query: string, embedding: float[768], timestamp: string, result_id: string}
  - Integration: Called by T016 main-bot-handler after whitelist check, before query-analyzer
  - Export as JSON

- [ ] **T020** [P] Create admin commands workflow ⚠️ MANUAL IN n8n UI
  - Path: `/workspace/002-n8n/workflows/admin-commands.json`
  - **Status**: Implementation guide ready (Section 5), whitelist module available
  - **Dependencies**: Uses `/workspace/002-n8n/lib/whitelist.js` ✓
  - Components:
    1. Parse command (/admin allow|revoke #channel)
    2. Verify user is admin (check whitelist.json admins array)
    3. Update whitelist.json (add/remove channel)
    4. Return confirmation message
  - Handle commands: /admin allow, /admin revoke, /admin list
  - Export as JSON

### Supporting Scripts (Parallel - Different Script Files)

- [x] **T021** [P] Write deploy-workflows.sh script ✅
  - Path: `/workspace/002-n8n/scripts/deploy-workflows.sh`
  - Function: Import all workflow JSON files to n8n instance
  - Use n8n CLI or API to import workflows
  - Make executable: `chmod +x`
  - ✅ COMPLETE: Script created with n8n health check and workflow import logic

- [x] **T022** [P] Write cleanup-expired.sh script ✅
  - Path: `/workspace/002-n8n/scripts/cleanup-expired.sh`
  - Function: Remove Redis keys for conversations > 7 days old
  - Logic from data-model.md retention policy section
  - Make executable: `chmod +x`
  - ✅ COMPLETE: Script created with dry-run mode, handles conversations, history, and upload jobs

- [x] **T023** [P] Write manage-services.sh script ✅
  - Path: `/workspace/002-n8n/scripts/manage-services.sh`
  - Commands: start, stop, restart, status
  - Manages: Redis container, n8n workflows
  - Health checks for all services
  - Make executable: `chmod +x`
  - ✅ COMPLETE: Script created with start/stop/restart/status/health commands for all services

---

## Phase 3.4: Integration & Connection

- [x] **T024** Implement Redis connection with retry logic ✅
  - Path: Shared module `/workspace/002-n8n/lib/redis-client.js` (create if needed)
  - Connection string from env: REDIS_URL
  - Retry strategy: 3 attempts, exponential backoff (base delay: 100ms, max delay: 2s, factor: 2x)
  - Retry timing: Attempt 1 → 0ms, Attempt 2 → 100ms, Attempt 3 → 200ms
  - Fallback: Return error for stateless mode (NFR-002)
  - Used by: context-manager workflow, admin-commands workflow
  - ✅ COMPLETE: Module created with singleton pattern, exponential backoff, and NFR-003 restoration detection

- [x] **T025** Implement whitelist validation logic ✅
  - Path: Shared module `/workspace/002-n8n/lib/whitelist.js` (create if needed)
  - Functions: isChannelAllowed(channelId), isAdmin(userId), invalidateCache()
  - Cache whitelist in memory (refresh every 60s per data-model.md)
  - **Cache Invalidation**: Immediately invalidate cache after `/admin allow` or `/admin revoke` commands (called by T020 admin-commands workflow)
  - Used by: main-bot-handler workflow, admin-commands workflow
  - ✅ COMPLETE: Module created with 60s cache, add/revoke channel methods, admin verification, immediate invalidation support

- [ ] **T026** Implement file upload handler
  - Path: Extension to main-bot-handler workflow
  - Components:
    1. Detect attachments array in message
    2. Download file from attachment.contentUrl
    3. Validate file type (FR-011)
    4. POST multipart/form-data to /api/v1/documents/upload/async
    5. Store job_id in Redis (DocumentUploadJob entity)
    6. Return confirmation with document_id
  - File type validation from data-model.md

- [ ] **T027** Implement typing indicator support
  - Path: Extension to main-bot-handler workflow
  - Components:
    1. Extract serviceUrl from incoming message
    2. POST typing activity to MS Teams Bot Framework API
    3. Set type: "typing", duration: ~3s
    4. Send before query processing starts
  - Implementation from research.md section 7

- [ ] **T026a** Implement proactive document completion notification (FR-014)
  - Path: Extension to main-bot-handler workflow + new polling workflow
  - **Approach**: Polling-based (BMS API does not provide webhook callback)
  - Components:
    1. Create polling workflow: `/workspace/002-n8n/workflows/document-status-poller.json`
       - Triggered every 30 seconds (n8n Schedule node)
       - **Rationale for 30s interval**: Balances user notification latency (acceptable for async upload) with BMS API load (max 2 requests/minute for status checks)
       - Query Redis for jobs with status "processing"
       - For each job: GET /api/v1/documents/status/{job_id} from BMS API
       - **Error Handling**: On BMS API failure, retry with exponential backoff (base delay 100ms, max delay 2s, 3 attempts max per NFR-011) before skipping job and retrying on next polling cycle
       - If status changed to "completed" or "failed":
         - Update Redis job record
         - Send proactive message to user in conversation_id using response-templates.json "upload_complete"
         - Remove job from polling queue
    2. Update T026 file upload handler to write job record to Redis with:
       - `job_id`, `conversation_id`, `user_id`, `status: "processing"`, `timestamp`
    3. Use Redis sorted set: `upload_jobs:pending` with score = timestamp for efficient polling
  - Alternative (deferred to production): BMS API webhook callback when processing completes

- [ ] **T027a** Implement BMS API embeddings endpoint (FR-017 dependency)
  - Path: `/workspace/001-bms-agent/api/main.py`
  - **Prerequisite**: Required for similar query detection (T019a)
  - Components:
    1. Create endpoint: POST /api/v1/embeddings
    2. Request schema: `{"query": "string"}`
    3. Response schema: `{"embedding": [768 floats], "model": "sentence-transformers/all-mpnet-base-v2"}`
    4. Use existing processor._generate_embeddings() method
    5. Add error handling and validation (query length, encoding)
  - **Rationale**: Clarification from Session 2025-10-07 - implement endpoint as part of this project

- [ ] **T027b** Create enhanced search workflows for new BMS API endpoints
  - Path: Create 4 new workflow files in `/workspace/002-n8n/workflows/`
  - **New Workflows**:
    1. `batch-search.json` - Multi-query batch search workflow
       - Trigger: Webhook or called from main-bot-handler
       - POST to /api/v1/search/batch with query array
       - Support union/intersection aggregation modes
       - Format combined results for MS Teams
    2. `faceted-search.json` - Faceted search workflow
       - POST to /api/v1/search/facets
       - Parse facet breakdown by document_type, department, fleet_type, compliance
       - Format faceted results with counts
    3. `explained-search.json` - Search with score explanations
       - POST to /api/v1/search/explain
       - Display semantic similarity, quality boost, relevance factors
       - Useful for debugging and user transparency
    4. `latest-versions-search.json` - Latest document versions only
       - POST to /api/v1/search/latest
       - Filter results to is_latest_version=True documents
       - Default mode for production queries
  - Export as JSON for n8n import

- [ ] **T027c** [P] Add command handlers for enhanced search features
  - Path: Extend `/workspace/002-n8n/workflows/main-bot-handler.json`
  - **New Commands**:
    1. `/search-batch [query1] | [query2] | ...` → Route to batch-search workflow
    2. `/search-facets [query]` → Route to faceted-search workflow
    3. `/search-explain [query]` → Route to explained-search workflow (admin/debug)
    4. `/search-latest [query]` → Route to latest-versions-search workflow
  - Add help text entries for new commands in response-templates.json
  - **POC Decision**: /search-explain restricted to admins only

- [ ] **T027d** [P] Update integration tests for new search capabilities
  - Path: `/workspace/002-n8n/tests/integration/test-enhanced-search.js`
  - Test scenarios:
    1. Batch search with 3 queries returns union of results
    2. Faceted search groups results by metadata
    3. Explained search includes score breakdown
    4. Latest search filters to newest document versions
    5. Invalid queries handled gracefully
  - Assert response schemas match BMS API contracts
  - Verify error handling for BMS API failures

---

## Phase 3.5: Polish & Validation

### Unit Tests (Parallel - Different Test Files)

- [ ] **T028** [P] Unit tests for whitelist validation
  - Path: `/workspace/002-n8n/tests/unit/test-whitelist.js`
  - **Prerequisite**: T025 (whitelist.js module) must be complete
  - Test: isChannelAllowed returns true for active channels
  - Test: isAdmin returns true for whitelisted admins
  - Test: Cache refresh works after 60s
  - Test: invalidateCache() immediately clears cache
  - Test: Cache invalidation triggers reload on next access

- [ ] **T029** [P] Unit tests for Redis TTL enforcement
  - Path: `/workspace/002-n8n/tests/unit/test-redis-ttl.js`
  - Test: New conversation has 7-day TTL
  - Test: Expired conversations auto-deleted
  - Test: TTL refreshed on message update

### Documentation & Validation

- [x] **T030** [P] Create MS Teams bot setup guide ✅
  - Path: `/workspace/002-n8n/docs/setup-ms-teams.md`
  - Content: Bot Framework registration steps from quickstart.md section 2
  - Include: Screenshots, webhook URL configuration

- [x] **T031** [P] Create troubleshooting guide ✅
  - Path: `/workspace/002-n8n/docs/troubleshooting.md`
  - Content: Common issues from quickstart.md section 7
  - Include: Redis errors, webhook failures, timeout issues

- [ ] **T032** Run full quickstart validation
  - Path: Manual execution of `/workspace/specs/002-create-a-microsoft/quickstart.md`
  - Execute: All 8 setup steps
  - Validate: All 5 test scenarios pass (T010-T014 integration tests)
  - Document: Any deviations or issues

- [ ] **T033** Performance validation and optimization
  - Path: Run load test from T015
  - Target: p95 < 3000ms, p50 < 1500ms
  - Optimize: If needed, tune Redis connection pooling, Ollama batch size
  - Document: Final performance metrics in quickstart.md

- [x] **T033a** [P] Create basic monitoring and health checks ✅
  - Path: `/workspace/002-n8n/workflows/health-check.json` (n8n workflow)
  - Components:
    1. HTTP endpoint: GET /health (via n8n webhook)
    2. Check Redis connectivity (ping)
    3. Check BMS API availability (GET /health)
    4. Check Ollama availability (GET /api/tags)
    5. Return JSON health status with component statuses
  - Additional: Document monitoring approach in `/workspace/002-n8n/docs/monitoring.md`
  - Constitution: Addresses §8 Monitoring & Observability (POC-appropriate level)
  - POC Decision: Use n8n execution logs + basic health endpoint (Prometheus deferred to production)

- [ ] **T034** Validate test coverage meets 60% POC threshold (NFR-012)
  - Path: Run from `/workspace/002-n8n/`
  - Command: `npm test -- --coverage`
  - Assert: Overall coverage ≥60% (lines, branches, functions, statements)
  - Generate: `coverage/lcov-report/index.html` for detailed report
  - Document: Final coverage percentage in `/workspace/specs/002-create-a-microsoft/quickstart.md`
  - Constitution: Enforces §4 Code Quality & Testing (line 49 - POC minimum 60%)
  - Validation Gate: Must pass before production deployment (80% required per §4 line 48)

---

## Dependencies

### Critical Path (Must be Sequential)
```
T001 (project structure)
  ↓
T002 (Redis) → T024 (Redis client) → T019 (context manager)
  ↓
T003, T004, T005, T006 (config & setup)
  ↓
T007-T015 (ALL TESTS MUST FAIL)
  ↓
T015a (n8n installation) ⚠️ REQUIRED BEFORE WORKFLOWS
  ↓
T016-T020 (workflows) ← depends on T015a, T024, T025
  ↓
T026, T027, T026a (advanced integrations)
  ↓
T027a (BMS embeddings endpoint) → T027b, T027c, T027d (enhanced search features)
  ↓
T028-T034 (polish & validation)
```

### Parallel Groups

**Group 1: Initial Setup (after T001, T002)** [P]
- T003 (whitelist.json)
- T004 (env.example)
- T005 (init-storage.sh)
- T006 (npm install)

**Group 2: Contract Tests (TDD Phase)** [P]
- T007 (MS Teams webhook contract)
- T008 (BMS API contract)
- T009 (storage API contract)

**Group 3: Integration Tests (TDD Phase)** [P]
- T010 (message flow)
- T011 (commands)
- T012 (file upload)
- T013 (admin commands)
- T014 (storage failure)
- T015 (load test)

**Group 4: Core Workflows (after tests fail)** [P]
- T016 (main bot handler)
- T017 (query analyzer)
- T018 (BMS API caller)
- T019 (context manager) ← needs T024 (Redis client)
- T019a (similar query detection) ← depends on T019
- T020 (admin commands)

**Group 5: Supporting Scripts (after workflows)** [P]
- T021 (deploy-workflows.sh)
- T022 (cleanup-expired.sh)
- T023 (manage-services.sh)

**Group 5a: Enhanced Search Features (after T027a)** [P]
- T027b (enhanced search workflows) ← needs T027a (embeddings endpoint)
- T027c (command handlers for enhanced search)
- T027d (integration tests for enhanced search)

**Group 6: Polish (final phase)** [P]
- T028 (whitelist unit tests)
- T029 (Redis TTL unit tests)
- T030 (setup guide)
- T031 (troubleshooting guide)
- T033a (health checks & monitoring)
- T034 (test coverage validation) ← Run after all tests complete

---

## Parallel Execution Examples

### Launch Contract Tests Together (T007-T009)
```bash
# All contract tests can run in parallel (different files, no shared state)
npm test tests/contract/test-ms-teams-webhook.js &
npm test tests/contract/test-bms-ask-integration.js &
npm test tests/contract/test-context-storage.js &
wait
```

### Launch Integration Tests Together (T010-T015)
```bash
# All integration tests are independent
npm test tests/integration/ --maxWorkers=6
```

### Deploy Workflows in Parallel (T016-T020)
Since these are separate JSON files, they can be created simultaneously:
```bash
# Task agent commands (run in parallel)
Task: "Create main bot handler workflow in /workspace/002-n8n/workflows/main-bot-handler.json"
Task: "Create query analyzer workflow in /workspace/002-n8n/workflows/query-analyzer.json"
Task: "Create BMS API caller workflow in /workspace/002-n8n/workflows/bms-api-caller.json"
Task: "Create context manager workflow in /workspace/002-n8n/workflows/context-manager.json"
Task: "Create admin commands workflow in /workspace/002-n8n/workflows/admin-commands.json"
```

---

## Notes

### TDD Enforcement
- **T007-T015 MUST fail before any implementation starts**
- Run `npm test` after writing tests to confirm failures
- Each test should have clear assertion errors showing what's missing

### File Isolation for Parallelism
- [P] tasks modify different files → safe for parallel execution
- Non-[P] tasks may modify same workflow or shared module → must be sequential

### Commit Strategy
- Commit after each completed task
- Use task ID in commit message: `git commit -m "T016: Create main bot handler workflow"`

### Validation Gates
- After T015: All tests must fail
- After T027: All tests must pass
- After T033: Performance targets met (p95 < 3s)

---

## Task Validation Checklist
*Applied during task generation*

- [x] All 3 contracts have corresponding tests (T007-T009)
- [x] All 6 entities have storage/model tasks (covered in T019 context manager)
- [x] All 5 workflows have implementation tasks (T016-T020)
- [x] All tests come before implementation (T007-T015 before T016-T020)
- [x] Parallel tasks are truly independent (verified file paths)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] User stories mapped to integration tests (T010-T014 from spec scenarios)

---

## Total Task Count: 43

- Setup: 6 tasks (T001-T006)
- n8n Installation: 1 task (T015a)
- Tests: 10 tasks (T007-T015, T015b POST-POC)
- Core Workflows: 6 tasks (T016-T020, T019a)
- Scripts: 3 tasks (T021-T023)
- Integration: 5 tasks (T024-T027, T026a)
- Enhanced Search: 4 tasks (T027a-T027d) ⭐ NEW
- Polish: 8 tasks (T028-T034)

**Estimated Effort**: 56-68 hours (POC phase) + 3-4 hours (T015b POST-POC)
**Critical Path**: ~16-20 hours (sequential dependencies)
**Parallelizable**: ~36-48 hours (if 5-6 parallel workers)

---

*Tasks generated from design artifacts: research.md, data-model.md, contracts/, quickstart.md*
*Ready for execution - Start with T001 or use parallel groups above*
