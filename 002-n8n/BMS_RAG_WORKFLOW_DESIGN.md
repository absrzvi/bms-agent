# BMS AI Agent Workflow Design
**Based on sample-rag.json pattern**

---

## Workflow Analysis: Sample RAG vs BMS Environment

### Sample RAG Workflow Pattern

**Core Components:**
1. **AI Agent** (`@n8n/n8n-nodes-langchain.agent`)
   - OpenAI GPT-4 as language model
   - Postgres Chat Memory for conversation history
   - Multiple tools connected via `ai_tool` connections

2. **Tools Available to Agent:**
   - **Postgres PGVector Store** (retrieve-as-tool mode) - RAG vector search
   - **List Documents** - SQL query to list available documents
   - **Get File Contents** - SQL query to fetch full document text
   - **Query Document Rows** - SQL for tabular data analysis
   - Cohere Reranker for improved results

3. **System Prompt Strategy:**
   ```
   "Always start by performing RAG unless the question requires SQL query for tabular data.
   If RAG doesn't help, then look at the documents available, find relevant ones,
   and analyze those."
   ```

4. **Tool Selection Logic:**
   - Agent analyzes the query
   - Decides which tool(s) to use
   - Can chain multiple tools (RAG → Get File Contents → Answer)

---

## BMS Environment Mapping

### Key Differences

| Sample RAG | BMS Equivalent | Notes |
|------------|----------------|-------|
| Postgres PGVector | Qdrant (via BMS API) | Vector search via `/api/v1/search/semantic` |
| Postgres Chat Memory | Redis (via Context Manager) | Already implemented |
| SQL Tools | HTTP Request Tools | Call BMS API endpoints |
| OpenAI GPT-4 | Ollama Mistral Nemo | Running locally at localhost:11434 |
| List Documents SQL | BMS API metadata | Could add `/api/v1/documents/list` endpoint |
| Get File Contents SQL | BMS RAG Search | Use high-context search |
| Query Tabular Data | Not needed | BMS doesn't have tabular data |

### BMS API Tools to Create

Based on your existing workflows and BMS API:

1. **RAG Semantic Search Tool**
   - Endpoint: `/api/v1/search/semantic`
   - Use: General knowledge retrieval
   - Description: "Use this to search the railway documentation knowledge base by meaning/semantics"

2. **Ask BMS Tool** (Primary)
   - Endpoint: `/api/v1/ask`
   - Use: Direct question answering with citations
   - Description: "Use this to get direct answers to questions about railway procedures, safety, or technical topics with source citations"

3. **Hybrid Search Tool**
   - Endpoint: `/api/v1/search/hybrid`
   - Use: Keyword + semantic search
   - Description: "Use this when the query has specific technical terms, codes, or identifiers (like VLAN IDs, equipment names)"

4. **Contextual Search Tool**
   - Endpoint: `/api/v1/search/contextual`
   - Use: Search with document hierarchy
   - Description: "Use this when you need full context around a topic, including parent sections and related content"

5. **Search by Metadata Tool** (Optional)
   - Endpoint: `/api/v1/search/semantic` with filters
   - Use: Filter by document type, profile, etc.
   - Description: "Use this to search specific types of documents or filter by category"

---

## BMS AI Agent Workflow Architecture

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    MS Teams Bot Trigger                          │
│                  (Webhook or Chat Trigger)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Parse Input                                 │
│          Extract: query, sessionId, conversationId               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BMS AI Agent                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Language Model: Ollama Mistral Nemo (localhost:11434)     │ │
│  │ Memory: Redis Chat Memory (via Context Manager)            │ │
│  │ System Prompt: BMS-specific guidance                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Tools (connected via ai_tool):                                  │
│  ├─ [1] Ask BMS Tool (PRIMARY)                                   │
│  ├─ [2] Semantic Search Tool                                     │
│  ├─ [3] Hybrid Search Tool                                       │
│  ├─ [4] Contextual Search Tool                                   │
│  └─ [5] Metadata Search Tool (optional)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Format Response                                 │
│        Extract: answer, citations, confidence                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               Store Context (Context Manager)                    │
│        Save conversation history in Redis (7-day TTL)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Respond to MS Teams                              │
│          Send formatted answer with citations                    │
└─────────────────────────────────────────────────────────────────┘
```

### Tool Implementation Options

**Option A: HTTP Request Tools (Simple)**
- Create HTTP Request nodes for each BMS API endpoint
- Configure as LangChain tools with descriptions
- Direct API calls

**Option B: Workflow Tools (Recommended)**
- Use existing tool workflows:
  - `tool-ask-bms-enhanced.json`
  - `tool-search-semantic.json`
  - `tool-search-hybrid.json`
  - `tool-contextual-search.json`
  - `tool-search-by-metadata.json`
- Use "Execute Workflow" LangChain node
- Benefit: Reuse existing logic, validation, error handling

**Option C: Hybrid**
- Primary tool: Call Ask BMS workflow directly
- Fallback tools: HTTP requests for other searches

---

## System Prompt for BMS Agent

```
You are a knowledgeable assistant for railway operations and maintenance documentation.

You help users find information about:
- Railway safety procedures
- Emergency brake systems (EBS)
- Network configurations (VLAN, switching, routing)
- Equipment manuals and technical specifications
- Maintenance procedures
- Regulatory compliance

**Your Tools:**

1. **Ask BMS** (PRIMARY TOOL): Use this first for most questions. It searches the knowledge base and generates a comprehensive answer with source citations. Best for:
   - "What are the..." questions
   - "How do I..." questions
   - "Explain..." requests
   - Safety procedures
   - Technical explanations

2. **Semantic Search**: Use when Ask BMS doesn't provide enough detail, or when you need to see multiple document chunks. Searches by meaning/concept.

3. **Hybrid Search**: Use when the query has specific technical terms, codes, identifiers, or product names (like "VLAN 100", "switch model XYZ").

4. **Contextual Search**: Use when you need the full surrounding context of a topic, including parent sections and related content.

**Guidelines:**
- Always start with Ask BMS for questions
- Use Semantic Search if you need more context or multiple perspectives
- Use Hybrid Search for technical/specific identifiers
- Always provide source citations from the tools
- If information is not found, say so clearly - don't make up information
- For safety-critical topics, always cite sources

**Response Format:**
- Direct answer first
- Key points as bullets if applicable
- Source citations at the end

Remember: Railway safety information must be accurate. Always cite your sources.
```

---

## Implementation Steps

### Phase 1: Core Agent Setup
1. Create new workflow: `bms-ai-agent.json`
2. Add Chat Trigger or Webhook
3. Add Ollama Chat Model node (Mistral Nemo)
4. Add AI Agent node
5. Configure system prompt

### Phase 2: Connect Tools
1. Add HTTP Request Tool for Ask BMS API
2. Add HTTP Request Tool for Semantic Search
3. Add HTTP Request Tool for Hybrid Search
4. Connect all as `ai_tool` to agent
5. Add tool descriptions

### Phase 3: Memory Integration
1. Add Redis memory or Context Manager integration
2. Store sessionId in Redis
3. Retrieve conversation history

### Phase 4: Response Formatting
1. Parse agent response
2. Extract answer and citations
3. Format for MS Teams (Adaptive Cards or text)

### Phase 5: Integration
1. Connect to MS Teams Bot Main Handler
2. Test with sample queries
3. Monitor performance and accuracy

---

## Tool Configuration Examples

### Ask BMS Tool (HTTP Request)

```json
{
  "name": "Ask BMS",
  "type": "@n8n/n8n-nodes-langchain.toolHttp Request",
  "parameters": {
    "toolDescription": "Use this to get direct answers to questions about railway procedures, safety, or technical topics. Returns a comprehensive answer with source citations.",
    "method": "POST",
    "url": "http://localhost:8000/api/v1/ask",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": {
      "query": "={{ $fromAI('question') }}",
      "max_chunks": 5,
      "include_citations": true
    }
  }
}
```

### Semantic Search Tool

```json
{
  "name": "Semantic Search",
  "type": "@n8n/n8n-nodes-langchain.toolHttpRequest",
  "parameters": {
    "toolDescription": "Search the railway documentation by meaning/concept. Use when Ask BMS needs more context or you want to see multiple relevant chunks.",
    "method": "POST",
    "url": "http://localhost:8000/api/v1/search/semantic",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": {
      "query": "={{ $fromAI('search_query') }}",
      "limit": 5,
      "min_score": 0.7
    }
  }
}
```

---

## Expected Performance

### Latency Targets
- Agent reasoning: ~500-1000ms
- Ask BMS API: ~500-2000ms (includes LLM generation)
- Search APIs: ~45-100ms
- **Total end-to-end**: 1-3 seconds

### Quality Metrics
- Answer accuracy: >90% (with citations)
- Relevance score: >0.7 threshold
- Source citation rate: 100%
- Context retention: 7 days (Redis TTL)

---

## Testing Strategy

### Test Queries

**1. Direct Questions (Should use Ask BMS)**
- "What are the emergency brake procedures?"
- "How do I configure VLAN 100 for safety-critical systems?"
- "Explain the inspection process for brake calipers"

**2. Technical Searches (Should use Hybrid)**
- "VLAN 100 configuration"
- "Model XYZ-1000 specifications"
- "Emergency brake system EBS-2000"

**3. Contextual Queries (Should use Contextual Search)**
- "Tell me everything about the maintenance schedule section"
- "What's the full procedure including prerequisites and safety checks?"

**4. Failure Cases**
- "What is the weather today?" (Should say "not in knowledge base")
- "Tell me a joke" (Should decline politely)

---

## Next Steps

1. ✅ Review this design document
2. Create BMS AI Agent workflow JSON
3. Test with sample queries
4. Integrate with MS Teams Bot
5. Monitor and refine tool selection
6. Add more tools as needed

---

**This design leverages your existing BMS API and workflows while following the proven agentic RAG pattern from the sample!**
