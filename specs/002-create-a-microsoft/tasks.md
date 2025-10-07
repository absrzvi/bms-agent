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
    8. (FR-032) User receives similar query suggestion → User replies "dismiss" or clicks dismiss button → Assert suggestion dismissed, query processing continues normally
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
    7. If query-analyzer returns intent="UNCLEAR" → Send query_unclear template from response-templates.json and stop
    8. Send typing indicator
    9. Format and send response to MS Teams
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

  **Acceptance Criteria** (Mark task complete when ALL checked):
  - [ ] Workflow created in n8n UI with all nodes documented above
  - [ ] Exported as JSON to `/workspace/002-n8n/workflows/main-bot-handler.json`
  - [ ] JSON schema valid (test: `n8n import:workflow --input main-bot-handler.json`)
  - [ ] Webhook trigger responds to test message: `curl -X POST http://localhost:5678/webhook-test/teams -d '{"text":"test"}'`
  - [ ] All command routes verified:
    - [ ] `/help` returns help template
    - [ ] `/ask` routes to query-analyzer
    - [ ] `/search` routes to bms-api-caller
    - [ ] `/admin` routes to admin-commands
    - [ ] `/status`, `/history`, `/upload` return expected responses
  - [ ] Whitelist check enforced (non-whitelisted channel rejected)
  - [ ] Integration test T010 passes with this workflow
  - [ ] Typing indicator sent before processing

- [ ] **T017** [P] Create query analyzer workflow ⚠️ MANUAL IN n8n UI
  - Path: `/workspace/002-n8n/workflows/query-analyzer.json`
  - **Status**: Implementation guide ready (Section 2 of workflow-implementation-guide.md)
  - Components:
    1. **Input Validation (FR-022)**: Detect unclear/invalid queries
       - Query quality checks:
         - Word count < 3 → unclear (except commands)
         - Only stopwords (the, a, is, what, etc.) → unclear
         - Only special characters/numbers → invalid
         - Empty or whitespace-only → invalid
       - If unclear/invalid → Return intent="UNCLEAR" with suggestion template from response-templates.json
       - If valid → Proceed to step 2
    2. HTTP Request to Ollama (Mistral Nemo)
    3. Prompt: Intent classification (ASK vs SEARCH vs COMMAND)
    4. Parse LLM response
    5. Return intent + confidence
  - Use prompts from research.md section 4
  - Stopword list: ["the", "a", "an", "is", "are", "was", "were", "what", "when", "where", "how", "why"]
  - Export as JSON

  **Acceptance Criteria** (Mark task complete when ALL checked):
  - [ ] Workflow created in n8n UI with all components documented above
  - [ ] Exported as JSON to `/workspace/002-n8n/workflows/query-analyzer.json`
  - [ ] Query quality validation working (test unclear queries return intent="UNCLEAR")
  - [ ] LLM intent classification working (test: "What are brakes?" returns intent="ASK")
  - [ ] Integration test T011 passes with this workflow

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

  **Acceptance Criteria** (Mark task complete when ALL checked):
  - [ ] Workflow created in n8n UI with all components documented above
  - [ ] Exported as JSON to `/workspace/002-n8n/workflows/bms-api-caller.json`
  - [ ] ASK intent calls /api/v1/ask (test with mock request)
  - [ ] SEARCH intent calls /api/v1/search/semantic (test with mock request)
  - [ ] Error handling working (BMS API 503 returns correct error message)
  - [ ] Response includes citations array
  - [ ] Integration test T010 passes with this workflow

- [ ] **T019** [P] Create context manager workflow ⚠️ MANUAL IN n8n UI
  - Path: `/workspace/002-n8n/workflows/context-manager.json`
  - **Status**: Implementation guide ready (Section 4), Redis client module available
  - **Dependencies**: Uses `/workspace/002-n8n/lib/redis-client.js` ✓
  - Components:
    1. GET /context/{conversation_id} from Redis
    2. If not found → create new Conversation
    3. POST message to conversation
    4. Update context_summary (condensed summary with key entities extracted via LLM - topics, document references, user intent)
    5. Set 7-day TTL (604800s)
    6. **Restoration Detection (NFR-003)**: Track Redis availability state
       - If previous request failed (503) and current request succeeds → set flag `storage_restored=true`
       - Return `storage_restored` flag to main-bot-handler
       - **CRITICAL**: Main handler MUST send notification using response-templates.json "storage_restored" template when flag is true
       - Notification text: "Conversation history has been restored. Your previous context is now available."
  - Schema from data-model.md
  - Export as JSON

  **Acceptance Criteria** (Mark task complete when ALL checked):
  - [ ] Workflow created in n8n UI with all components documented above
  - [ ] Exported as JSON to `/workspace/002-n8n/workflows/context-manager.json`
  - [ ] GET /context retrieves conversation from Redis
  - [ ] POST /context stores message with 7-day TTL
  - [ ] Context summary updated (condensed summary with extracted entities, not full message history)
  - [ ] Restoration detection working (storage_restored flag returned)
  - [ ] Integration test T014 passes with this workflow

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

- [ ] **T019b** [P] Implement dismiss handler for similar query suggestions (FR-032) ⚠️ NEW
  - Path: Extension to `/workspace/002-n8n/workflows/similar-query-detector.json`
  - Components:
    1. Add "Dismiss" button to similar query suggestion message (MS Teams adaptive card or inline action)
    2. Handle dismiss action: Store user preference in Redis (user:{user_id}:dismissed_suggestions)
    3. Add key: {suggestion_id: timestamp} with 7-day TTL (matches conversation TTL)
    4. Update T019a workflow: Check dismissed suggestions before showing
    5. If suggestion was dismissed → skip suggestion, continue with query processing
  - **POST-POC Enhancement**: Add global preference to disable all suggestions (user:{user_id}:disable_suggestions flag)
  - Integration: Called when user clicks "Dismiss" button in similar query notification
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

  **Acceptance Criteria** (Mark task complete when ALL checked):
  - [ ] Workflow created in n8n UI with all components documented above
  - [ ] Exported as JSON to `/workspace/002-n8n/workflows/admin-commands.json`
  - [ ] /admin allow adds channel to whitelist
  - [ ] /admin revoke removes channel from whitelist
  - [ ] /admin list displays current whitelist
  - [ ] Admin verification working (non-admin users rejected)
  - [ ] Integration test T013 passes with this workflow

- [ ] **T020-bootstrap** [P] Implement first-user-admin bootstrap logic (FR-024a) ⚠️ NEW
  - Path: Extension to `/workspace/002-n8n/workflows/admin-commands.json`
  - **Prerequisite**: T020 admin-commands workflow
  - Components:
    1. Check if whitelist.json admins array is empty
    2. If empty AND user sends any message (natural language or /admin command):
       - Add user to admins array automatically
       - Log bootstrap event to Redis: `audit:admin_bootstrap`
       - Send welcome message: "You are now the bot admin. Use /admin grant @user to add more admins."
    3. If admins array not empty:
       - Enforce normal admin verification
       - Reject non-admin /admin commands
    4. Store bootstrap state in Redis: `system:admin_bootstrapped` with value=true (no TTL)
  - **Security**: Bootstrap only works when admins array is empty (prevent re-bootstrap attacks)
  - Integration: Called from main-bot-handler before routing to admin-commands
  - Export as JSON

- [ ] **T020a** [P] Implement audit logging for admin reset command (FR-024b) ⚠️ NEW
  - Path: Extension to `/workspace/002-n8n/workflows/admin-commands.json`
  - **Security Requirement**: All `/admin reset [secret_key]` attempts MUST be logged for audit trail
  - Components:
    1. Add handler for `/admin reset [secret_key]` command in admin-commands workflow
    2. Validate secret_key against environment variable ADMIN_RESET_SECRET
    3. **Audit Logging (MANDATORY)**:
       - Log to Redis list: `audit:admin_resets`
       - Entry format: {timestamp: ISO8601, user_id: string, display_name: string, success: boolean, ip_address: string (if available)}
       - TTL: 90 days (7776000s) for compliance retention
       - Use LPUSH to append, LTRIM to maintain max 1000 entries
    4. If secret_key matches:
       - Grant admin privileges (add user_id to whitelist.json admins array)
       - Update User entity: is_admin=true
       - Return success message: "Admin privileges granted. This action has been logged."
    5. If secret_key invalid:
       - Log failed attempt (success: false)
       - Return error: "Invalid reset key" (do NOT reveal admin status or key format)
       - Do NOT grant privileges
  - **Security Notes**:
    - Secret key generation: `openssl rand -hex 32` (64-character hex string)
    - Store in `/workspace/002-n8n/config/.env`: `ADMIN_RESET_SECRET=<generated_key>`
    - Never log the actual secret key value
  - Export as JSON

- [x] **T020b** Update bms-ai-agent workflow to accept MS Teams webhook triggers ⚠️ NEW - USER REQUEST ✅
  - Path: `/workspace/002-n8n/workflows/bms-ai-agent.json`
  - **Objective**: Replace existing trigger with MS Teams webhook to enable chat message integration
  - **Prerequisites**:
    - teams-webhook-bot-handler.json workflow exists ✓
    - BMS AI agent workflow (bms-ai-agent.json) exists
  - **Analysis Phase** (read current workflow):
    1. Read current bms-ai-agent.json structure
    2. Identify existing trigger type (manual, webhook, schedule, etc.)
    3. Document current input schema expected by agent
    4. Identify dependencies on trigger data format
  - **Modification Phase**:
    1. **Option A - Direct Integration**: Replace trigger with MS Teams webhook
       - Change trigger node to Webhook node
       - Path: `/webhook/bms-agent-teams`
       - Configure to receive MS Teams Bot Framework activity schema
       - Extract required fields: text (query), from.id (user), conversation.id
       - Map MS Teams message format to agent input format
    2. **Option B - Sub-workflow Integration**: Keep agent as called workflow
       - Keep existing trigger (or make it a sub-workflow callable by Execute Workflow node)
       - Update teams-webhook-bot-handler.json to call bms-ai-agent.json
       - Pass: {query: text, user_id: from.id, conversation_id: conversation.id}
       - **Recommended**: This preserves separation of concerns
  - **Testing Phase**:
    1. Send test message via MS Teams: "What are railway safety procedures?"
    2. Verify webhook triggers bms-ai-agent workflow
    3. Verify agent receives correct input format
    4. Verify agent response flows back to MS Teams
  - **Decision Required**: Choose Option A (direct) or Option B (sub-workflow)
    - **Recommendation**: Option B for modularity
  - **DECISION (2025-10-07)**: **Option B - Sub-workflow Integration** selected
    - Reasoning: Preserves separation of concerns, allows independent testing of AI agent
    - Implementation: teams-webhook-bot-handler calls bms-ai-agent via Execute Workflow node
    - Data mapping: {query: text, user_id: from.id, conversation_id: conversation.id, context: previous_messages}
    - Status: ✅ Implemented (see T020b completion status)
  - Export as JSON

- [x] **T020c** Create integration tests for MS Teams → BMS AI Agent flow ⚠️ NEW - USER REQUEST ✅
  - Path: `/workspace/002-n8n/tests/integration/test-teams-ai-agent-integration.js`
  - **Prerequisites**: T020b complete
  - Test scenarios:
    1. **Test: Natural language question triggers AI agent**
       - Send MS Teams message: "What is the emergency brake procedure?"
       - Assert: bms-ai-agent workflow executes
       - Assert: Agent calls BMS API with query
       - Assert: Response includes LangChain tool execution logs
       - Assert: Final answer posted to MS Teams
    2. **Test: AI agent uses correct tools**
       - Send MS Teams message: "Search for VLAN configuration documents"
       - Assert: Agent selects semantic search tool (not ask tool)
       - Assert: Results formatted with document citations
    3. **Test: Conversation context passed to agent**
       - Message 1: "What are the safety procedures?"
       - Message 2: "Can you explain step 3?"
       - Assert: Agent receives context from message 1
       - Assert: Agent understands "step 3" refers to previous response
    4. **Test: Whitelist enforcement before agent execution**
       - Send message from non-whitelisted channel
       - Assert: Agent workflow NOT triggered
       - Assert: Whitelist rejection message sent
    5. **Test: Agent error handling**
       - Mock BMS API failure (503)
       - Send MS Teams message
       - Assert: Agent gracefully handles error
       - Assert: User-friendly error message posted to Teams
  - Run: `npm test tests/integration/test-teams-ai-agent-integration.js`
  - Expected: All 5 scenarios passing

- [x] **T020d** Document MS Teams + BMS AI Agent integration architecture ⚠️ NEW - USER REQUEST ✅
  - Path: `/workspace/002-n8n/docs/teams-ai-agent-integration.md`
  - Content:
    1. **Architecture Overview**
       - Diagram: MS Teams → Webhook → teams-webhook-bot-handler → bms-ai-agent → BMS API → Response
       - Component responsibilities
       - Data flow between workflows
    2. **Configuration Guide**
       - Environment variables required
       - Webhook URL configuration in Azure Bot Service
       - n8n workflow activation steps
    3. **Message Flow**
       - Incoming message processing (teams-webhook-bot-handler)
       - Agent invocation (Execute Workflow node or direct trigger)
       - Tool selection logic (LangChain agent decision-making)
       - Response formatting and delivery
    4. **Agent Tools Available**
       - List all LangChain tools configured in bms-ai-agent.json
       - Tool selection criteria
       - Example queries that trigger each tool
    5. **Troubleshooting**
       - Webhook not triggering agent
       - Agent receives malformed input
       - Tool execution failures
       - Response not appearing in Teams
    6. **Testing Procedures**
       - Manual testing via MS Teams
       - Automated testing via integration tests
       - Monitoring agent execution logs in n8n

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

- [x] **T026** Implement file upload handler ✅
  - Path: Extension to main-bot-handler workflow
  - File: `/workspace/002-n8n/lib/file-upload-handler.js` (235 lines)
  - Components:
    1. Detect attachments array in message
    2. Download file from attachment.contentUrl
    3. Validate file type (FR-011)
    4. POST multipart/form-data to /api/v1/documents/upload/async
    5. Store job_id in Redis (DocumentUploadJob entity)
    6. Return confirmation with document_id
  - File type validation from data-model.md
  - **Status:** Module complete, supports PDF, CSV, XLSX, DOCX, PPTX, TXT, MD
  - **Features:** File type validation, size limits (100MB), batch upload, error handling

- [x] **T027** Implement typing indicator support ✅
  - Path: Extension to main-bot-handler workflow
  - File: `/workspace/002-n8n/lib/typing-indicator.js` (138 lines)
  - Components:
    1. Extract serviceUrl from incoming message
    2. POST typing activity to MS Teams Bot Framework API
    3. Set type: "typing", duration: ~3s
    4. Send before query processing starts
  - Implementation from research.md section 7
  - **Status:** Module complete, supports continuous and one-time indicators
  - **Features:** Auto-refresh every 3s, graceful cleanup, error handling

- [x] **T026a** Implement proactive document completion notification (FR-014) ✅
  - Path: Extension to main-bot-handler workflow + new polling workflow
  - File: `/workspace/002-n8n/workflows/document-status-poller.json`
  - **Approach**: Polling-based (BMS API does not provide webhook callback)
  - Components:
    1. Create polling workflow: `/workspace/002-n8n/workflows/document-status-poller.json` ✅
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
  - **Status:** Polling workflow complete with 9-node pipeline
  - **Features:**
    - Schedule trigger (30s intervals)
    - Redis sorted set for job queue
    - Exponential backoff retry (100ms → 2s, 3 attempts)
    - Proactive MS Teams notifications (success/failure)
    - Automatic job cleanup with 7-day audit trail
    - Comprehensive logging and error handling

- [x] **T027a** Implement BMS API embeddings endpoint (FR-017 dependency)
  - Path: `/workspace/001-bms-agent/api/main.py`
  - **Prerequisite**: Required for similar query detection (T019a)
  - Components:
    1. Create endpoint: POST /api/v1/embeddings
    2. Request schema: `{"query": "string"}`
    3. Response schema: `{"embedding": [768 floats], "model": "sentence-transformers/all-mpnet-base-v2"}`
    4. Use existing processor._generate_embeddings() method
    5. Add error handling and validation (query length, encoding)
  - **Rationale**: Clarification from Session 2025-10-07 - implement endpoint as part of this project

- [x] **T027b** Create enhanced search workflows for new BMS API endpoints
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

- [x] **T027c** [P] Add command handlers for enhanced search features
  - Path: Created 4 tool workflows for integration with bms-ai-agent.json
  - **Tool Workflows Created**:
    1. `bms-tool-batch-search.json` - Multi-query batch search
    2. `bms-tool-faceted-search.json` - Faceted search with metadata grouping
    3. `bms-tool-explained-search.json` - Search with score explanations
    4. `bms-tool-latest-search.json` - Latest document versions only
  - **Setup Guide**: See `/workspace/002-n8n/workflows/ENHANCED_SEARCH_SETUP.md`
  - **Manual Step Required**: Import workflows and add tools to bms-ai-agent.json in n8n UI
  - **Note**: These integrate as LangChain tools, not slash commands (agent decides when to use them)

- [x] **T027d** [P] Update integration tests for new search capabilities
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

- [x] **T028** [P] Unit tests for whitelist validation ✅
  - Path: `/workspace/002-n8n/tests/unit/test-whitelist.js`
  - **Prerequisite**: T025 (whitelist.js module) must be complete
  - Test: isChannelAllowed returns true for active channels
  - Test: isAdmin returns true for whitelisted admins
  - Test: Cache refresh works after 60s
  - Test: invalidateCache() immediately clears cache
  - Test: Cache invalidation triggers reload on next access
  - **Completed**: 27 test cases covering isChannelAllowed, isAdmin, cache behavior, cache invalidation, list functions, and error handling

- [x] **T029** [P] Unit tests for Redis TTL enforcement ✅
  - Path: `/workspace/002-n8n/tests/unit/test-redis-ttl.js`
  - Test: New conversation has 7-day TTL
  - Test: Expired conversations auto-deleted
  - Test: TTL refreshed on message update
  - Test: Exponential backoff retry logic (NFR-011)
    - Mock Redis connection failure
    - Assert retry attempts: 1st (0ms), 2nd (100ms), 3rd (200ms)
    - Assert max 3 attempts before fallback
    - Assert fallback to stateless mode with NFR-002 warning
  - **Completed**: 22 test cases covering retry logic, connection handling, execute with fallback, TTL enforcement (60s cache), error handling, and integration with context manager

### Documentation & Validation

- [x] **T030** [P] Create MS Teams bot setup guide ✅
  - Path: `/workspace/002-n8n/docs/setup-ms-teams.md`
  - Content: Bot Framework registration steps from quickstart.md section 2
  - Include: Screenshots, webhook URL configuration

- [x] **T031** [P] Create troubleshooting guide ✅
  - Path: `/workspace/002-n8n/docs/troubleshooting.md`
  - Content: Common issues from quickstart.md section 7
  - Include: Redis errors, webhook failures, timeout issues

- [ ] **T031b** [P] Validate all exported workflow JSON schemas
  - Path: Script validation in `/workspace/002-n8n/scripts/validate-workflows.sh`
  - **Constitution Requirement**: §13 n8n Integration - Workflow JSON schema validation
  - Components:
    1. For each workflow JSON in workflows/:
       - Validate JSON syntax: `jq . <workflow>.json`
       - Check required fields: nodes[], connections{}
       - Verify node structure: id, name, type, typeVersion, position, parameters
       - Validate connection references (source/target nodes exist)
    2. n8n import dry-run test:
       ```bash
       n8n import:workflow --input <workflow>.json --separate
       ```
    3. Report validation results:
       - ✓ Valid workflows
       - ✗ Invalid workflows with error details
  - Exit code: 0 if all valid, 1 if any invalid
  - Run before T032 (quickstart validation)
  - Make executable: `chmod +x`

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

- [x] **T033a** [P] Create script-based health monitoring (NFR-006) ✅
  - Path: `/workspace/002-n8n/scripts/health-check.sh` (primary health endpoint)
  - **Rationale**: Avoid circular dependency (n8n workflow cannot check its own health)
  - Components:
    1. HTTP script that checks all 4 components:
       - Redis connectivity: `redis-cli ping` → PONG
       - BMS API availability: `curl http://localhost:8000/health` → 200
       - Ollama availability: `curl http://localhost:11434/api/tags` → 200
       - n8n availability: `curl http://localhost:5678` → 200 (meta-check: HTTP server responsive)
    2. Return JSON health status:
       ```json
       {
         "status": "healthy|degraded|unhealthy",
         "components": {
           "redis": {"status": "up|down", "latency_ms": 5},
           "bms_api": {"status": "up|down", "latency_ms": 120},
           "ollama": {"status": "up|down", "latency_ms": 45},
           "n8n": {"status": "up|down", "latency_ms": 12}
         },
         "timestamp": "2025-10-07T17:30:00Z"
       }
       ```
    3. Exit codes: 0 (healthy), 1 (degraded), 2 (unhealthy)
    4. Response time target: <500ms (NFR-006)
  - Optional: Create n8n workflow wrapper that calls this script via HTTP Request node
  - Make executable: `chmod +x`
  - Constitution: Addresses §8 Monitoring & Observability (POC-appropriate level)

- [x] **T034** Validate test coverage meets 60% POC threshold (NFR-012) ⚠️ **BELOW THRESHOLD - BLOCKS DEPLOYMENT**
  - Path: Run from `/workspace/002-n8n/`
  - Command: `npm test -- --coverage`
  - Assert: Overall coverage ≥60% (lines, branches, functions, statements)
  - Generate: `coverage/lcov-report/index.html` for detailed report
  - Document: Final coverage percentage in `/workspace/specs/002-create-a-microsoft/quickstart.md`
  - Constitution: Enforces §4 Code Quality & Testing (POC minimum 60%, production 80%)
  - Validation Gate: Must pass before POC deployment (critical blocking issue)
  - **Status:** Coverage validation executed
  - **Current Coverage:** 22.61% statements (⚠️ 37.39% below 60% POC threshold)
  - **Analysis:** Comprehensive test coverage summary at `/workspace/002-n8n/docs/test-coverage-summary.md`
  - **Findings:**
    - 3 modules with 0% coverage (file-upload-handler, typing-indicator, workflow-helpers)
    - 2 modules with partial coverage (redis-client 50.84%, whitelist 55.73%)
    - 56 total tests: 21 passed, 35 failed (due to Redis unavailability in test env)
    - Root cause: Tests require real service dependencies (Redis, file system)
  - **Remediation Plan:** `/workspace/002-n8n/docs/TEST_COVERAGE_REMEDIATION_PLAN.md` ✅ CREATED
    - **Priority 1** (4-5 hours): Add mocked tests → 52% coverage (POC ready)
      - Task 1.1: Mock redis-client tests (2h) → +10% coverage
      - Task 1.2: Mock file-upload-handler tests (1.5h) → +15% coverage
      - Task 1.3: Mock typing-indicator tests (1h) → +5% coverage
    - **Priority 2** (4-5 hours): Add module-specific tests → 87% coverage (production ready)
      - Task 2.1: Whitelist edge cases (1.5h) → +5% coverage
      - Task 2.2: Redis integration tests (1h) → +3% coverage
      - Task 2.3: Workflow helpers tests (2h) → +12% coverage
  - **Next Steps (CRITICAL):**
    1. Install mocking libraries: `npm install --save-dev redis-mock axios-mock-adapter memfs`
    2. Execute Priority 1 tasks (Task 1.1, 1.2, 1.3)
    3. Re-validate: `npm test -- --coverage` → Assert ≥60%
    4. Proceed with POC deployment only if coverage gate passes

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
T020b (MS Teams AI Agent integration) ← depends on T016 (teams-webhook-bot-handler)
  ↓
T020c (integration tests) ← depends on T020b
  ↓
T026, T027, T026a (advanced integrations)
  ↓
T027a (BMS embeddings endpoint) → T027b, T027c, T027d (enhanced search features)
  ↓
T020d (AI Agent integration docs) [P] can run in parallel with T028-T034
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
- T020d (MS Teams AI Agent integration docs) ⚠️ NEW - can run in parallel with polish tasks
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

## Total Task Count: 48

- Setup: 6 tasks (T001-T006)
- n8n Installation: 1 task (T015a)
- Tests: 11 tasks (T007-T015, T015b POST-POC, T020c ⚠️ NEW)
- Core Workflows: 8 tasks (T016-T020, T019a, T019b ⚠️ NEW, T020a ⚠️ NEW)
- MS Teams AI Agent Integration: 3 tasks (T020b-T020d ⚠️ NEW - USER REQUEST)
- Scripts: 3 tasks (T021-T023)
- Integration: 5 tasks (T024-T027, T026a)
- Enhanced Search: 4 tasks (T027a-T027d) ⭐ NEW
- Polish: 8 tasks (T028-T034)

**Estimated Effort**: 68-82 hours (POC phase) + 3-4 hours (T015b POST-POC)
**Critical Path**: ~20-24 hours (sequential dependencies)
**Parallelizable**: ~44-58 hours (if 5-6 parallel workers)

**New Tasks Added (2025-10-07 Analysis Remediation)**:
- T019b: Dismiss handler for similar query suggestions (FR-032) - 2 hours
- T020a: Audit logging for admin reset command (FR-024b) - 2 hours

**New Tasks Added (2025-10-07 MS Teams AI Agent Integration - USER REQUEST)**:
- T020b: Update bms-ai-agent workflow for MS Teams webhook triggers - 4 hours
- T020c: Integration tests for MS Teams → AI Agent flow - 2 hours
- T020d: Document MS Teams + AI Agent integration architecture - 2 hours

---

*Tasks generated from design artifacts: research.md, data-model.md, contracts/, quickstart.md*
*Ready for execution - Start with T001 or use parallel groups above*
