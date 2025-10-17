# Feature Specification: Slack Chat Bot for BMS Agent

**Feature Branch**: `002-create-a-microsoft` *(Note: Branch name retained for continuity; original intent was MS Teams but implementation pivoted to Slack)*
**Created**: 2025-10-06
**Status**: Active (Implementation Complete, Optimization In Progress)
**Platform**: Slack (changed from original MS Teams scope during implementation for better API support and simpler webhook configuration)
**Input**: User description: "Create a Slack chat bot integration for the BMS API using n8n workflows + Slack Events API."

## Glossary

- **POC DECISION**: Marker indicating a requirement relaxation or deferral specifically permitted for Proof-of-Concept phase per constitution's POC/MVP Exception Framework. All POC DECISION items must be upgraded to full compliance before production deployment.
- **NFR**: Non-Functional Requirement
- **FR**: Functional Requirement
- **Slack Events API**: Slack's real-time event API for receiving app mentions and messages via webhooks
- **Slack Web API**: Slack's HTTP API for posting messages, formatting with Block Kit

---

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature identified: Slack chat bot for railway documentation search
2. Extract key concepts from description
   → Actors: Railway staff, bot users (via Slack @mentions)
   → Actions: Ask questions, search documents, view conversation threads
   → Data: Conversations (Slack threads), messages, documents, search results
   → Constraints: 20 users (POC), <3s response time, event deduplication (Slack retries)
3. For each unclear aspect:
   → Marked with [NEEDS CLARIFICATION] tags
4. Fill User Scenarios & Testing section
   → Primary flow: User @mentions bot → receives answer with citations in thread
5. Generate Functional Requirements
   → 47 requirements identified (33 functional + 14 non-functional)
   → AI agent optimization: 8 tools → 4 tools (FR-033 to FR-038)
6. Identify Key Entities
   → Conversation, Message, SearchResult, Document (adapted for Slack threading model)
7. Run Review Checklist
   → WARN: Some technical implementation details need abstraction
8. Return: SUCCESS (spec ready for planning)
```

---

## � Quick Guidelines
-  Focus on WHAT users need and WHY
- L Avoid HOW to implement (no tech stack, APIs, code structure)
- =e Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-06
- Q: How should users upload documents to the bot? → A: Both methods supported (file attachment and `/upload` command)
- Q: How should users view their 7-day search history? → A: Both `/history` command and automatic prompts when relevant
- Q: Which specific Slack channels should have access during POC, and how should the whitelist be managed? → A: Multiple channels - admin manages via bot command (e.g., `/admin allow #channel`)
- Q: If conversation context storage fails, how should the system behave? → A: Hybrid - attempt to answer but warn user that context may be lost
- Q: What is the target user scale after POC? → A: 50-100 users (small team expansion)

### Session 2025-10-07
- Q: How should the system determine if a user is an admin? → A: First-user-admin - First user to interact with bot becomes admin, can designate others via command
- Q: What should the system do if the BMS API /api/v1/embeddings endpoint is unavailable? → A: Implement the endpoint - Add /api/v1/embeddings to BMS API as part of this project
- Q: What does the "3 seconds" response time measure from/to? → A: End-to-end user experience - From user sends @mention in Slack to user sees bot's threaded response appear
- Q: Where should the `/status` command retrieve document upload status from? → A: Hybrid approach - Check Redis first for recent uploads, fall back to BMS API for older/missing records
- Q: How should the system handle admin access if the initial admin becomes unavailable with no other admins designated? → A: Reset mechanism - Support special `/admin reset [secret_key]` command that grants admin using pre-configured secret
- Q: Where should the 3-second response time be measured and logged for POC validation? → A: Manual stopwatch testing during UAT - No automated instrumentation for POC phase
- Q: What is the maximum acceptable delay for notifying users after document processing completes? → A: Best effort, no SLA for POC phase
- Q: What conversation context should be stored for multi-turn conversations? → A: Message summaries - Condensed summary of conversation with key entities extracted

### Session 2025-10-09
- Q: How should citations be formatted in bot responses? → A: Footnote style - "...within 3 seconds.¹" with numbered references at bottom
- Q: What criteria should determine ASK vs SEARCH intent classification? → A: Hybrid approach - LLM classification with confidence ≥0.80 for ASK intent; fallback to SEARCH for lower confidence
- Q: Which validation rules should determine if a query is unclear or invalid? → A: LLM-based validation - Use Mistral Nemo to assess query clarity; unclear if clarity_score <0.60
- Q: What should be the maximum query length limit for the embeddings endpoint? → A: Same as bot queries (1000 characters) - Consistent with FR-031 max query length validation
- Q: What namespace convention should be used for all Redis keys? → A: Prefixed with `bms:` - All keys start with `bms:` followed by entity type (e.g., `bms:context:{id}`, `bms:user:{id}:history`)

### Session 2025-10-11
- Q: When the agent exceeds the 45-second timeout and n8n kills the workflow, what should happen to any partial results already retrieved from tool calls? → A: Cache partial results in Redis for 1 hour, allow user to retry with `/continue` command
- Q: When merging `search_contextual` into `search_hybrid` (per FR-036), how should context retrieval be controlled? → A: Always include context - search_hybrid automatically retrieves parent/child documents
- Q: NFR-016 requires validating agent performance with 50 diverse test queries (10 per tool type). What should happen if production query patterns differ significantly from the test set? → A: Hybrid validation - Keep static 50-query baseline + run monthly production sample (100 queries) through same metrics
- Q: FR-033 requires "Log response times with tool call breakdown for analysis" and NFR-015 requires reviewing tool call logs to identify ambiguous selections. What specific data fields must be logged for each tool invocation? → A: Standard fields - timestamp, tool_name, query, response_time_ms, result_count, confidence_score, success/failure, error_message
- Q: FR-036 requires removing 4 tools (search_contextual, search_version, search_faceted, search_explained) and merging 2 into existing tools. What is the deployment sequence to avoid breaking the running bms-ai-agent.json workflow? → A: Parallel deployment - Deploy new 4-tool agent as separate workflow, test with 20% of users, then cutover to new agent after 1 week validation

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
Railway staff members need quick access to technical documentation and safety procedures while working. Instead of manually searching through hundreds of documents, they can ask a chat bot questions in Slack (where they already work) by @mentioning the bot and receive instant answers with source citations.

**Example interaction:**
- User types: "@Nomi BMS Assistant What are the emergency brake procedures for Class 395 trains?"
- Bot responds within 3 seconds with the answer in a threaded reply, citing specific document sections with Slack Block Kit formatting
- User can ask follow-up questions in the same thread, and the bot uses conversation context

### Acceptance Scenarios

1. **Given** a user is in a Slack channel where the bot is present, **When** they @mention the bot with a natural language question about railway procedures, **Then** the bot responds with an answer and citations within 3 seconds in a threaded reply

2. **Given** a user is in a Slack channel, **When** they @mention the bot, **Then** the bot responds in a thread and all channel members can see the conversation

3. **Given** a user types `/help` command, **When** the bot receives it, **Then** it displays available commands and usage examples

4. **Given** a user asks "What is the VLAN configuration for emergency systems?", **When** the bot determines this is a specific document search query, **Then** it returns relevant document excerpts rather than a generated answer

5. **Given** a user uploads a PDF document via file attachment or `/upload` command, **When** the upload completes, **Then** the document is indexed and the user receives a confirmation with document ID

6. **Given** a user asks a follow-up question within the same conversation, **When** the bot processes it, **Then** it uses context from previous messages (up to 7 days old)

7. **Given** a user types `/search emergency brake`, **When** the bot receives it, **Then** it returns a list of relevant documents with relevance scores

8. **Given** the documentation search system is unavailable, **When** a user asks a question, **Then** the bot replies "BMS-search tool cannot be accessed at this time. Please try again later."

9. **Given** a user asks a vague or unclear question, **When** the bot cannot find relevant results, **Then** it suggests better ways to phrase the query with examples

10. **Given** a user asks a question that returns no results, **When** the search completes, **Then** the bot replies "No results found for your query. Try rephrasing or using different keywords."

11. **Given** a user types `/history` command, **When** the bot receives it, **Then** it displays the user's search queries from the last 7 days with timestamps

12. **Given** a user asks a question similar to a recent query, **When** the bot detects the similarity, **Then** it automatically suggests "You asked something similar on [date]: [previous query]"

13. **Given** an admin types `/admin allow #operations-team`, **When** the bot receives it, **Then** it adds that channel to the whitelist and confirms "Access granted to #operations-team"

14. **Given** a user in a non-whitelisted channel messages the bot, **When** the bot receives it, **Then** it responds "This bot is currently in POC phase. Contact your admin to request access."

15. **Given** conversation context storage is unavailable, **When** a user asks a question, **Then** the bot responds with the answer preceded by warning "Conversation history is temporarily unavailable. Your question will still be answered."

16. **Given** the initial admin is unavailable and no other admins exist, **When** an authorized user types `/admin reset [valid_secret_key]`, **Then** the bot grants admin privileges to that user and logs the reset event

### Edge Cases
- What happens when a user asks a question that spans multiple topics (e.g., both brakes and VLAN)? → System uses hybrid search to return results for all detected topics (topic detection via LLM keyword extraction in query-analyzer workflow)
- How does the system handle very long questions (>1000 characters)? → System enforces FR-031 max length validation
- What happens if a user tries to upload a non-document file (e.g., image, video)? → System validates file type per FR-012 and returns error from response-templates.json
- How does the bot handle messages in a group chat where multiple users are asking questions simultaneously? → **POC DECISION**: Deferred to post-POC. POC implementation processes messages sequentially per user; simultaneous multi-user queries in same channel may experience queuing delays. Production will implement async message queuing per channel.
- What happens to conversation context when the 7-day retention expires mid-conversation? → Context is purged by Redis TTL; next message starts new conversation
- How does the bot respond if the same question is asked multiple times in quick succession? → FR-017 similar query detection suggests previous answer; no rate limiting in POC
- What happens if a user tries `/admin reset` with an invalid secret key? → System logs the failed attempt (for security audit), responds "Invalid reset key" without revealing admin status, and does not grant privileges

**Agent Optimization Edge Cases** (Added 2025-10-11):
- What if the agent needs context from multiple documents? → Single call to `search_hybrid` with broader query. Agent should NOT call multiple tools - instead, use one tool with comprehensive query. Context retrieval (parent/child documents) is automatically included in all search_hybrid results after search_contextual merge (per FR-036).
- What if user asks compound question ("Who wrote document X and what changed in version Y?")? → Agent should decompose into 2 separate tool calls: `search_metadata` (author) → `search_metadata` (version changes). This counts as 2 calls, acceptable for complex queries per FR-034 max 2 tool calls.
- What if the selected tool returns no results? → Agent responds "I couldn't find information about that in the BMS documentation" instead of trying alternative tools automatically (per FR-037 fallback behavior). Do NOT retry with different tools.
- What if response time exceeds 45s hard limit (FR-033)? → n8n workflow timeout kills execution, caches any partial results retrieved from tool calls in Redis (`bms:partial:{conversation_id}`, 1-hour TTL), returns error "Response took too long. Partial results saved. Type `/continue` to see what was retrieved, or rephrase your question." User can invoke `/continue` within 1 hour to retrieve cached partial results. Log timeout event with query details and cache key for investigation.
- What if agent confidence on tool selection is <0.7? → Agent asks user to rephrase: "I'm not sure which search method is best for your question. Could you rephrase it? For example: 'Search for document BMS-XXX-YYY-###' or 'Explain what [concept] means'."
- What if user query matches multiple tool criteria? → Follow decision tree priority (FR-037): document code → `search_hybrid` (highest priority), "how to" → `ask_bms`, metadata questions → `search_metadata`, else → `search_semantic`.

## Requirements *(mandatory)*

### Functional Requirements

**Core Question & Answer**
- **FR-001**: System MUST accept natural language questions from users via Slack @mentions in channels (bot responds in threaded replies)
- **FR-003**: System MUST respond to all user interactions (natural language questions and commands) within 3 seconds end-to-end
  - **Measurement Definition**: Total elapsed time from Slack webhook received by n8n (T0) to Slack API confirms message delivery (T_final)
  - **Measurement Points** (for instrumentation and validation):
    - **T0**: n8n webhook receives Slack Events API POST request (log: `webhook_received`)
    - **T1**: Whitelist validation completes (log: `whitelist_checked`)
    - **T2**: Query analyzer returns intent (log: `intent_classified`)
    - **T3**: BMS API responds with results (log: `bms_api_completed`)
    - **T4**: Response formatted with Block Kit (log: `response_formatted`)
    - **T_final**: Slack Web API confirms message posted (log: `message_delivered`)
  - **Stage Time Budgets** (targets for optimization):
    - Webhook receipt & routing (T0 → T1): <500ms
    - Query analysis & intent classification (T1 → T2): <500ms
    - BMS API processing (T2 → T3): <2000ms
    - Response formatting & delivery (T3 → T_final): <500ms
  - **Total Budget**: T0 → T_final ≤ 3000ms (includes typing indicator overhead)
  - **Performance Target**: p95 latency <3000ms, p50 latency <1500ms (end-to-end T0 → T_final)
  - **Instrumentation**: All measurement points MUST log timestamps with correlation_id (per NFR-006 log schema) for stage-by-stage analysis
  - **POC DECISION**: Performance validation via manual stopwatch testing during UAT; automated instrumentation deferred to production. POC logging includes T0 and T_final timestamps minimum; full stage breakdown (T1-T4) optional for POC.
- **FR-004**: System MUST include source citations in all answers showing which documents were used
  - **Citation Format**: Footnote style with numbered references
  - **Slack Block Kit Rendering** (NFR-004): Use Slack Block Kit for rich formatting with collapsible sections, document links, and emoji indicators
  - **Example**:
    ```
    The emergency brake procedure requires activation within 3 seconds [1].
    This applies to all Class 395 trains [2].

    Sources:
    [1] Railway Safety Manual, Section 4.2
    [2] Fleet Operations Guide, Page 47
    ```
- **FR-005**: System MUST maintain conversation context for up to 7 days to support multi-turn conversations
  - **Context Storage**: Condensed summary of last 5 message exchanges with key entities extracted (topics, document references, user intent) generated via LLM (Mistral Nemo)
  - **Max Size**: 2000 characters per conversation (per data-model.md Conversation.context_summary)
  - **Rationale**: Optimizes storage, reduces retrieval latency, and provides focused context for LLM processing
- **FR-006**: System MUST intelligently determine whether to provide a generated answer or return document search results based on query type
  - **Intent Classification Criteria**: Use LLM (Mistral Nemo via query-analyzer workflow) to classify user intent
  - **ASK Intent**: If LLM confidence ≥0.80, provide generated answer with citations (route to /api/v1/ask)
  - **SEARCH Intent**: If LLM confidence <0.80, return document search results (route to /api/v1/search/semantic)
  - **Rationale**: High confidence threshold ensures accurate answers; safe fallback to search prevents hallucination on ambiguous queries

**Command Support**
- **FR-007**: System MUST support the following slash commands:
  1. `/search [query]` - Perform document searches
  2. `/ask [question]` - Get direct answers with citations
  3. `/upload` - Prompt user to attach file for upload
  4. `/status [document_id]` - View document upload status (queries Redis DocumentUploadJob, falls back to BMS API)
  5. `/history` - Display search queries from last 7 days
  6. `/help` - Display usage instructions with command examples
  7. `/admin [action] [target]` - Manage access control (admin-only): `/admin allow #channel`, `/admin revoke #channel`, `/admin grant @user`, `/admin reset [secret_key]`
  8. `/continue` - Retrieve partial results from timed-out agent query (1-hour cache, per FR-033)

**Document Management**
- **FR-011**: System MUST support document uploads via both `/upload` command and direct file attachment in chat
- **FR-012**: System MUST accept document uploads in the following formats: PDF, CSV, XLSX, XLS, TXT, MD, DOCX, PPTX
- **FR-013**: System MUST confirm successful document processing with a document ID
- **FR-014**: System MUST send proactive notification when document processing completes
  - **Notification Retry Policy**: 3 attempts with exponential backoff (base delay 1s, max delay 8s), 30s timeout per attempt
  - **Failure Handling**: If all retries fail, log error and update job status to "notification_failed" (user can still query via `/status`)
  - **POC DECISION**: Best-effort delivery with no guaranteed SLA; production deployment will establish notification SLA based on POC performance data
- **FR-015**: Users MUST be able to view document upload status via `/status [document_id]` command
  - **Retrieval Strategy**: Hybrid approach - Query Redis DocumentUploadJob entity first; if not found or expired, fall back to BMS API GET /api/v1/documents/status/{job_id} endpoint

**Search History**
- **FR-016**: Users MUST be able to view their search history from the last 7 days via `/history` command
- **FR-017**: System MUST automatically suggest recent similar queries when detecting related questions (similarity threshold ≥0.85 using cosine similarity on query embeddings generated via BMS API /api/v1/embeddings endpoint with sentence-transformers/all-mpnet-base-v2 model)
  - **Display Format**: Slack threaded reply with inline suggestion and dismiss buttons via Block Kit actions
  - **Example**: "💡 You asked something similar on 2025-10-08: 'What are emergency brake procedures?' [View Answer] [Dismiss]"
  - **Dependency**: Requires implementation of POST /api/v1/embeddings endpoint in BMS API with the following specification:
    - **Request**: `{"query": "string"}` (max 1000 characters, consistent with FR-031)
    - **Response**: `{"embedding": [768 floats], "model": "sentence-transformers/all-mpnet-base-v2"}`
    - **Error Handling**: 400 if query exceeds 1000 characters or is empty; 500 if model unavailable
    - **Rate Limit**: 60 requests/minute (shared with other BMS API endpoints)
    - **Timeout**: 2000ms maximum
- **FR-032**: Users MAY dismiss similar query suggestions on a per-occurrence basis by replying "dismiss" or clicking [Dismiss] button (POST-POC: Add persistent preference for disabling similar query detection entirely)

**AI Agent Performance Optimization** (Added 2025-10-11)
- **FR-033**: AI agent MUST respond within 30 seconds for 95% of queries (p95 ≤30s)
  - **Measurement**: Time from user message received (T0 = n8n webhook receives Slack Events API POST, per FR-003 measurement definition) to complete agent response sent
  - **Timeout Handling**: If >45s hard limit, cache partial results in Redis (key: `bms:partial:{conversation_id}`, TTL: 3600s) and return error "Response took too long. Partial results saved. Type `/continue` to see what was retrieved, or rephrase your question."
  - **Partial Result Recovery**: User can invoke `/continue` command within 1 hour to retrieve cached partial results
  - **Logging**: Log response times with tool call breakdown for analysis, including timeout events with partial result cache key
  - **Context**: Current bms-ai-agent.json has 8 tools with overlapping descriptions causing response times >30 seconds
- **FR-034**: AI agent MUST select the optimal tool on first attempt for ≥90% of queries
  - **Single-Call Optimization**: Agent should make 1 tool call per query in typical cases
  - **Max Tool Calls**: Hard limit of 2 tool calls per query (first attempt + optional refinement)
  - **Tool Call Logging**: Log every tool invocation with standard fields (JSON format):
    - `timestamp` (ISO 8601)
    - `tool_name` (ask_bms, search_hybrid, search_metadata, search_semantic)
    - `query` (user query text, sanitized if contains PII)
    - `response_time_ms` (integer, milliseconds)
    - `result_count` (integer, number of results returned)
    - `confidence_score` (float 0.0-1.0, agent's confidence in tool selection)
    - `success` (boolean, true if tool executed successfully)
    - `error_message` (string, null if success=true, error details if success=false)
  - **Duplicate Prevention**: Agent must NOT call multiple search tools (semantic + hybrid + contextual) for same query
- **FR-035**: AI agent MUST have mutually exclusive tool descriptions to prevent ambiguous selection
  - **Tool Description Format**: "Use ONLY when: [specific criteria]. Do NOT use if: [exclusion criteria]."
  - **Example Queries**: Each tool description includes 2-3 example queries that trigger it
  - **Validation**: Tool descriptions reviewed to ensure no overlap in use cases
  - **Anti-Pattern Rules**: System message includes "NEVER call search_semantic AND search_hybrid for same query"
- **FR-036**: System MUST reduce agent tool count to 4 core tools (down from current 8, reduced from initially planned 5 due to always-on context integration)
  - **Core Tools** (mandatory):
    1. `ask_bms` - Open-ended questions, explanations, "how to" queries
    2. `search_hybrid` - Specific document codes (BMS-XXX-YYY-###), technical terms, exact matches; **automatically retrieves parent/child document context** (merged from search_contextual)
       - **Context Retrieval Scope**: Retrieve parent document + immediate siblings (max 3 sibling chunks)
       - **Context Size Limit**: Total context limited to 2000 characters (per FR-005 conversation context limit)
       - **Rationale**: Provides surrounding document structure without overwhelming token budget
    3. `search_metadata` - Author, date, version, department filtering queries; includes version comparison capability (merged from search_version)
    4. `search_semantic` - Conceptual searches, exploratory "what is X" queries
  - **Tool Consolidation**:
    - `search_contextual` → **MERGE into `search_hybrid`** - Context retrieval (parent/child documents) enabled by default for all search_hybrid queries
    - `search_version` → **MERGE into `search_metadata`** - Version comparison functionality integrated into metadata filtering
    - `search_faceted` → **REMOVE** (redundant with `search_semantic` for exploratory queries)
    - `search_explained` → **REMOVE** (debugging only, not needed in agent - use separate admin workflow)
  - **Result**: 4 core tools with clear, mutually exclusive use cases (down from 5 planned due to always-on context)
- **FR-037**: AI agent system message MUST include strict tool selection decision tree
  - **Decision Tree**:
    - IF query contains document code (BMS-XXX-YYY-###) → ONLY use `search_hybrid`
    - IF query starts with "how do I" or "how to" → ONLY use `ask_bms`
    - IF query asks "who wrote/when updated/what version" → ONLY use `search_metadata`
    - IF query asks conceptual "what is/explain" → ONLY use `search_semantic`
    - ELSE → use `search_semantic` (safe default for exploratory queries)
  - **Confidence Threshold**: If agent confidence <0.7 on tool selection, ask user to rephrase instead of guessing
  - **Fallback Behavior**: If selected tool returns no results, respond "I couldn't find information about that" instead of trying alternative tools automatically
- **FR-038**: System MUST deploy optimized 4-tool agent using parallel deployment strategy to minimize risk
  - **Phase 1 - Parallel Deployment**: Deploy new 4-tool agent workflow (`bms-ai-agent-optimized.json`) alongside existing 8-tool agent (`bms-ai-agent.json`)
  - **Phase 2 - Canary Testing**: Route 20% of user queries to new agent (determined by user_id hash modulo 5 == 0), 80% to legacy agent
  - **Phase 3 - Validation Period**: Monitor for 1 week (7 days), compare metrics between new and legacy agents using FR-034 standard log fields
  - **Phase 4 - Cutover Decision**: If new agent meets success criteria (p95 ≤30s, accuracy ≥90%, duplicate rate <5%, timeout rate <2%, no critical bugs), route 100% traffic to new agent
  - **Phase 5 - Deprecation**: After 2 weeks of stable operation on new agent, decommission legacy 8-tool agent
  - **Rollback Plan**: If new agent fails validation, route 100% traffic back to legacy agent, analyze logs, fix issues, restart from Phase 1

**User Experience**
- **FR-018**: System MUST display typing indicator while processing requests
- **FR-019**: System MUST be visible to all participants in group chats (no private results in POC)

**Error Handling**
- **FR-020**: System MUST display "BMS-search tool cannot be accessed at this time. Please try again later." when any BMS API endpoint (/api/v1/ask, /api/v1/search/semantic, /api/v1/search/hybrid, /api/v1/search/contextual) is unavailable or returns a 5xx error
- **FR-021**: System MUST display "No results found for your query. Try rephrasing or using different keywords." when no relevant documents are found
- **FR-022**: System MUST suggest better query formats with examples when it detects an unclear or invalid query
  - **Validation Method**: Use LLM (Mistral Nemo via query-analyzer workflow) to assess query clarity
  - **Invalid Queries**: Empty queries or whitespace-only (immediate rejection, no LLM call)
  - **Unclear Queries**: LLM clarity_score <0.60 triggers suggestion response with examples
  - **Clear Queries**: clarity_score ≥0.60 proceed to intent classification (FR-006)
  - **Examples of unclear queries**: Single words ("brakes"), ambiguous pronouns ("how does it work?"), missing context ("the procedure")
  - **Testing Requirements**:
    - Test case 1: Query with clarity_score = 0.59 MUST trigger suggestion response
    - Test case 2: Query with clarity_score = 0.60 MUST proceed to intent classification (no suggestion)
    - Test case 3: Query with clarity_score = 0.61 MUST proceed to intent classification (no suggestion)
    - Test case 4: Empty query "" MUST return error immediately without LLM call
    - Test case 5: Whitespace-only query "   " MUST return error immediately without LLM call
    - Test implementation: `/workspace/002-n8n/tests/integration/test-commands.js` scenario for query clarity threshold validation

**Access Control (POC)**
- **FR-023**: System MUST restrict access to whitelisted Slack channels during POC phase (implemented via Slack app installation scopes)
- **FR-024**: System MUST support admin commands to manage whitelist (e.g., `/admin allow #channel`, `/admin revoke #channel`)
- **FR-024a**: System MUST grant admin privileges to the first user who interacts with the bot, who can then designate additional admins via `/admin grant @user` command
- **FR-024b**: System MUST support `/admin reset [secret_key]` command to grant admin privileges using a pre-configured secret key (recovery mechanism if initial admin becomes unavailable)
  - **Secret Generation**: Generate using `openssl rand -hex 32` during deployment, store in .env file as ADMIN_RESET_SECRET (64-character hex string)
  - **Security**: Secret key stored in environment variable ADMIN_RESET_SECRET (minimum 32 characters)
  - **Behavior**: Command grants admin to user who invokes it if secret_key matches; logs all reset attempts for audit trail
- **FR-025**: System MUST reject messages from non-whitelisted channels with a friendly notification
- **FR-026**: System MUST support up to 20 concurrent users without performance degradation during POC
  - **Performance Degradation Defined**: Either (a) ≥10% increase in p95 latency compared to single-user baseline OR (b) p95 latency exceeds 3000ms (as per FR-003)
  - **Measurement Method**: Load testing during UAT with 20 simulated concurrent users issuing queries over 5-minute period

**Data Retention**
- **FR-027**: System MUST retain conversation history for 7 days maximum
- **FR-028**: System MUST automatically purge conversation data older than 7 days

**Performance**
- **FR-029**: System MUST handle 50-100 queries per day during POC phase
- **FR-030**: System MUST maintain response time per FR-003 (p95 ≤3000ms, p50 ≤1500ms) under expected load (50-100 queries/day, 20 concurrent users per FR-026)

**Input Validation**
- **FR-031**: System MUST enforce maximum query length of 1000 Unicode characters (UTF-8 character count, where emoji and multi-byte characters count as 1 character each) at the bot handler layer (before BMS API call) and return error message "Query too long. Please limit to 1000 characters." if exceeded

### Non-Functional Requirements

**Reliability**
- **NFR-001**: System MUST gracefully handle backend service failures with user-friendly error messages
  - **User-Friendly Criteria**: (a) Maximum 100 characters, (b) Plain language (no technical jargon, error codes, or stack traces), (c) Actionable (tells user what to do next)
  - **Example**: "BMS-search tool cannot be accessed at this time. Please try again later." (see Acceptance Scenario 8)
- **NFR-002**: System MUST continue operating in stateless mode if conversation context storage fails, warning users "Conversation history is temporarily unavailable. Your question will still be answered."
- **NFR-003**: System MUST attempt to restore context storage on subsequent requests and notify users when restored

**Usability**
- **NFR-004**: Bot responses MUST be formatted using Slack Block Kit with rich formatting (headers, dividers, document reference sections, collapsible content for long responses)
- **NFR-005**: Help command output MUST include clear examples for all supported commands

**Monitoring & Observability**
- **NFR-006**: System MUST implement health monitoring and logging with the following measurable criteria:
  - **POC Phase (Current)**: Script-based health checks (scripts/health-check.sh) returning JSON with component statuses: Redis (connectivity), BMS API (availability), Ollama (availability), n8n (HTTP responsiveness)
    - **Implementation**: Script-based health check to avoid circular dependency (n8n workflow cannot check its own health)
    - **Structured Logging Requirements**: All application logs MUST use JSON format with the following mandatory fields:
      - `timestamp` (string, ISO 8601 format, e.g., "2025-10-12T14:30:00.000Z")
      - `level` (string, one of: "DEBUG", "INFO", "WARN", "ERROR", "FATAL")
      - `component` (string, source component, e.g., "main-bot-handler", "query-analyzer", "redis-client")
      - `message` (string, human-readable message describing the event)
      - `correlation_id` (string, UUID v4, links related log entries across components)
      - `user_id` (string, optional, Slack user ID when available, omit for system events)
      - `conversation_id` (string, optional, Slack channel:thread_ts when available)
      - `error_details` (object, optional, present when level="ERROR" or "FATAL", contains: `error_type`, `stack_trace`, `context`)
    - **Log Format Example**:
      ```json
      {
        "timestamp": "2025-10-12T14:30:00.123Z",
        "level": "INFO",
        "component": "main-bot-handler",
        "message": "Processing user query",
        "correlation_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "user_id": "U123ABC456",
        "conversation_id": "C456DEF789:1234567890.123456"
      }
      ```
    - Minimum log level: INFO for application logs, ERROR for exception logging
    - Log retention: 30 days minimum for troubleshooting
    - Health check response time: <500ms
  - **Production Phase (REQUIRED before production deployment per constitution §8)**:
    - Prometheus metrics integration (T026b implementation)
    - Grafana dashboards for visualization
    - Alerting rules for SLA violations (p95 >3000ms, error rate >5%)
    - **Transition Criteria**: T026b MUST be complete and validated before production deployment
- **POC DECISION**: Monitoring uses script-based health checks + n8n execution logs for POC phase (max 20 users, 50-100 queries/day). Advanced metrics (Prometheus) and dashboards (Grafana) **REQUIRED** before production deployment (50-100 users, 250-500 queries/day) per constitution §8 MUST requirement.

**Scalability**
- **NFR-007**: System architecture MUST support expansion to 50-100 users after POC phase (small team expansion)
- **NFR-008**: System MUST handle 5x increase in query volume (250-500 queries per day) post-POC

**Security**
- **NFR-009**: System MUST NOT store conversation data beyond 7-day retention period
- **NFR-010**: Uploaded documents MUST be validated for allowed file types before processing
- **NFR-011**: System SHOULD retry failed BMS API calls with exponential backoff (3 attempts max, base delay 100ms, max delay 2s)

**Future Enhancements (POST-POC)**
- **NFR-013**: System SHOULD display upload progress percentage during file transfer (deferred to post-POC)
- **NFR-014**: System MAY notify users when conversation context expires mid-conversation (UX improvement deferred to post-POC)

**AI Agent Performance** (Added 2025-10-11)
- **NFR-015**: Agent tool descriptions MUST be updated within 2 hours of response time violations
  - **Violation Definition**: ≥3 queries in 1 hour exceed 30s response time
  - **Remediation Process**: Review tool call logs (FR-034 standard fields: timestamp, tool_name, query, response_time_ms, result_count, confidence_score, success, error_message), identify ambiguous selections (low confidence_score <0.7, duplicate tool calls, wrong tool selections indicated by result_count=0), update tool descriptions
  - **Analysis Criteria**: Flag queries with confidence_score <0.7 or multiple tool calls as candidates for description clarification
  - **Escalation**: If violations persist after description updates, consider removing problematic tool
  - **Tracking**: Maintain log of description changes with timestamp, violation count, resolution in `/workspace/002-n8n/docs/tool-description-updates.md`
- **NFR-016**: Agent performance MUST be validated using hybrid validation approach
  - **Baseline Validation** (pre-deployment):
    - Static test set: 50 diverse queries (10 per tool type: ask_bms, search_hybrid, search_metadata, search_semantic)
    - Test categories: Document code queries (BMS-XXX-YYY-###), "How to" procedural questions, Conceptual "what is" questions, Metadata queries (author, date, version), Edge cases (compound questions, ambiguous queries, out-of-scope)
    - Passing criteria: p95 ≤30s, tool accuracy ≥90%, duplicate rate <5%, timeout rate <2%
    - Document baseline results in `/workspace/002-n8n/docs/agent-performance-validation.md`
  - **Production Validation** (monthly):
    - Sample 100 real production queries from previous month (stratified by tool type if possible)
    - Apply same metrics as baseline: p50, p95, p99 response times; tool selection accuracy; duplicate tool call rate; timeout rate
    - Compare against baseline: flag degradation if tool accuracy drops >5% or p95 increases >10s
    - Document monthly results in `/workspace/002-n8n/docs/agent-performance-validation-YYYY-MM.md`
  - **Baseline Updates**: If production patterns diverge significantly (accuracy <85% on production sample for 2 consecutive months), augment baseline test set with representative production queries and re-validate

**Testing & Quality**
- **NFR-012**: System MUST achieve ≥60% test coverage for POC phase (contract tests, integration tests, unit tests)
- **POC DECISION**: Test coverage relaxed from constitution section 4 requirement (80% MUST) to 60% for POC velocity per POC/MVP Exception Framework. This exception is explicitly documented here with clear path to 80% coverage for production deployment (constitution section 4 compliance).
- **Constitution Reference**: Section 4 - Code Quality & Testing
- **Current Status** (as of 2025-10-12):
  - **Overall Coverage**: 44.48% (below 60% POC target)
  - **POC Core Modules (T001-T034)**: 80%+ on critical paths (file-upload: 98.55%, redis: 83.05%, instrumentation: 91.93%, typing: 100%, workflow-helpers: 100%)
  - **Phase 3.6 Modules (T035-T042)**: 0% coverage (POST-POC enhancements, deferred)
- **Remediation Plan** (REQUIRED before POC deployment):
  - **Priority 1** (4-5 hours): Add mocked tests to reach 52-60% minimum coverage
    - Task 1.1: Mock redis-client tests (2h) → +10% coverage
    - Task 1.2: Mock file-upload-handler tests (1.5h) → +15% coverage
    - Task 1.3: Mock typing-indicator tests (1h) → +5% coverage
  - **Validation Gate**: Re-run `npm test -- --coverage` after Priority 1 tasks → Assert ≥60%
  - **Production Path** (POST-POC): Execute Priority 2 tasks (4-5 hours) → 87% coverage target
- **Phase 3.6 Exception**: AI optimization modules (T035-T042, 1,515 lines) have 0% test coverage and are explicitly deferred to POST-POC with TDD requirement before production deployment. This technical debt is documented and approved per constitution §POC exception framework.

### Key Entities *(mandatory)*

**Redis Key Namespace Convention**: All Redis keys MUST use the `bms:` prefix followed by entity type to prevent collisions and enable clear debugging. Standard format: `bms:{entity_type}:{identifier}` or `bms:{entity_type}:{id}:{attribute}`.

Examples:
- Conversation context: `bms:context:{conversation_id}`
- User query history: `bms:user:{user_id}:history`
- Upload job queue: `bms:upload:jobs:pending`
- Admin audit log: `bms:audit:admin:resets`
- Whitelist cache: `bms:whitelist:cache`

- **Conversation**: Represents an ongoing chat session between user(s) and bot
  - Attributes: conversation_id, participants (array supporting single user in POC; multi-user post-POC), created_at, last_message_at, expires_at (7 days), context_summary (condensed text with key entities)
  - Relationships: Contains multiple Messages
  - **POC Scope**: Participants array contains single user_id; group chat context is per-channel but history is per-user
  - **Context Storage**: context_summary field stores condensed summary generated from recent messages with extracted entities (topics, document references, user intent)
  - **Redis Storage**: Key = `bms:context:{conversation_id}`, TTL = 604800s (7 days)

- **Message**: Individual message in a conversation
  - Attributes: message_id, conversation_id, sender (user/bot), content, timestamp, message_type (question/answer/command)
  - Relationships: Belongs to one Conversation

- **SearchResult**: Outcome of a document search or question
  - Attributes: result_id, query, answer_text, citations[], confidence_score, response_time_ms, timestamp
  - Relationships: Referenced by Messages

- **Citation**: Reference to source document used in an answer
  - Attributes: document_name, document_section, relevance_score, excerpt_text
  - Relationships: Belongs to SearchResult

- **Document**: Uploaded document in the system
  - Attributes: document_id, file_name, file_type, upload_date, uploaded_by, processing_status, indexed_chunks_count
  - Relationships: Can be referenced by Citations

- **DocumentUploadJob**: Tracks async document upload processing (stored in Redis with 7-day TTL)
  - Attributes: job_id, document_id, file_name, uploaded_by, processing_status (queued/processing/completed/failed), created_at
  - Relationships: Created by Document uploads, queried by `/status` command
  - **Storage**: Redis primary, BMS API fallback for expired/missing records
  - **Redis Storage**: Sorted set key = `bms:upload:jobs:pending` (score = timestamp), individual job key = `bms:upload:job:{job_id}`, TTL = 604800s (7 days)

- **User**: Person interacting with the bot
  - Attributes: user_id (Slack user ID, format: U########), display_name, channel_membership[], last_active, is_admin (boolean - true for first user to interact with bot and users granted admin via `/admin grant @user`)
  - Relationships: Participates in Conversations

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain *(all 5 clarifications resolved in Session 2025-10-06, 5 additional clarifications in Session 2025-10-07)*
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (5 clarifications identified)
- [x] User scenarios defined
- [x] Requirements generated (33 functional + 14 non-functional, updated 2025-10-09)
- [x] Entities identified (7 core entities, updated 2025-10-07)
- [x] Review checklist passed
- [x] All clarifications resolved (Session 2025-10-06: 5 clarifications, Session 2025-10-07: 5 additional clarifications)

---

## Success Metrics (POC Phase)

**Bot Integration Metrics:**
- **Response Time**: 95% of queries answered within 3 seconds end-to-end (measured from user sends message to response appears in chat)
- **Query Volume**: 50-100 queries per day during POC phase
- **Accuracy**: Users find answers helpful (measured by follow-up question rate)
- **Availability**: System uptime >95% during business hours
- **User Adoption**: 15/20 users actively using bot within first month
- **Error Rate**: <5% of queries result in error messages

**AI Agent Optimization Metrics** (Added 2025-10-11):
- **Agent Response Time (p95)**: ≤30 seconds (FR-033) - Time from user message received to complete agent response sent
- **Agent Response Time (p50)**: ≤15 seconds (target) - Median response time for typical queries
- **Tool Selection Accuracy**: ≥90% first-call success rate (FR-034) - Agent selects optimal tool on first attempt
- **Duplicate Tool Call Rate**: <5% of queries (FR-034) - Agent calls multiple search tools for same query
- **Timeout Rate**: <2% of queries (FR-033) - Queries exceeding 45s hard limit
- **Tool Count**: 4 core tools (FR-036) - Down from 8 tools (search_contextual merged into search_hybrid with always-on context; search_version merged into search_metadata; search_faceted and search_explained removed)
- **Average Tool Calls per Query**: ≤1.2 (target) - Most queries resolved with single tool call
