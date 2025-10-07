# Enhanced Search Tools - Setup Guide

## Overview

This guide explains how to integrate the 4 new enhanced search tools into the BMS AI Agent workflow.

## New Tool Workflows Created

1. **bms-tool-batch-search.json** - Multi-query batch search
2. **bms-tool-faceted-search.json** - Search with metadata grouping
3. **bms-tool-explained-search.json** - Search with score explanations
4. **bms-tool-latest-search.json** - Latest document versions only

## Integration Steps

### Step 1: Import Tool Workflows

Import all 4 new tool workflows into n8n:

```bash
# Via n8n UI:
# 1. Go to Workflows > Import
# 2. Import each file:
#    - workflows/bms-tool-batch-search.json
#    - workflows/bms-tool-faceted-search.json
#    - workflows/bms-tool-explained-search.json
#    - workflows/bms-tool-latest-search.json
```

### Step 2: Edit Main Agent Workflow

Open `BMS AI Agent - Railway Documentation RAG` workflow in n8n UI.

### Step 3: Add New Tool Nodes

Add 4 new `Call n8n Workflow` tool nodes to the main agent. Position them below the existing tools.

**For each tool, configure:**

#### Tool 1: Batch Search BMS

- **Node Type:** `@n8n/n8n-nodes-langchain.toolWorkflow`
- **Name:** `Batch Search BMS`
- **Description:**
  ```
  Search multiple queries simultaneously and combine results. Use when you need to search for several related topics at once. Returns combined results from all queries with union or intersection modes.
  ```
- **Workflow:** Select `BMS Tool - Batch Search`
- **Fields:**
  - `queries` (array) - "Array of search queries to run simultaneously"
  - `mode` (string) - "Aggregation mode: 'union' or 'intersection' (default: union)"
  - `limit` (number) - "Max results per query (default: 5)"

#### Tool 2: Faceted Search BMS

- **Node Type:** `@n8n/n8n-nodes-langchain.toolWorkflow`
- **Name:** `Faceted Search BMS`
- **Description:**
  ```
  Search with metadata facet grouping. Shows breakdown by document type, department, etc. Use when you want to understand the distribution of results across categories.
  ```
- **Workflow:** Select `BMS Tool - Faceted Search`
- **Fields:**
  - `search_query` (string) - "The search query"
  - `facet_fields` (array) - "Metadata fields to group by (default: ['document_type', 'department'])"
  - `limit` (number) - "Max results (default: 10)"

#### Tool 3: Explained Search BMS

- **Node Type:** `@n8n/n8n-nodes-langchain.toolWorkflow`
- **Name:** `Explained Search BMS`
- **Description:**
  ```
  Search with detailed score explanations showing semantic similarity, quality boost, and relevance factors. Use for debugging or when transparency is needed about why results were ranked.
  ```
- **Workflow:** Select `BMS Tool - Explained Search`
- **Fields:**
  - `search_query` (string) - "The search query"
  - `limit` (number) - "Max results (default: 5)"

#### Tool 4: Latest Versions Search BMS

- **Node Type:** `@n8n/n8n-nodes-langchain.toolWorkflow`
- **Name:** `Latest Versions Search BMS`
- **Description:**
  ```
  Search only the latest versions of documents, filtering out older revisions. Use for production queries where only current information is relevant. Shows version and date metadata.
  ```
- **Workflow:** Select `BMS Tool - Latest Versions Search`
- **Fields:**
  - `search_query` (string) - "The search query"
  - `limit` (number) - "Max results (default: 10)"

### Step 4: Connect Tools to Agent

1. Connect each new tool node to the **BMS AI Agent** node
2. Ensure all 8 tools are now connected (4 existing + 4 new)

### Step 5: Update System Prompt (Optional)

You may want to update the agent's system message to mention the new tools:

```
**Your Tools:**

1. **Ask BMS** (PRIMARY): Use first for all questions. Returns answers from database with citations.

2. **Semantic Search BMS**: Use when Ask BMS returns no results or you need more document chunks.

3. **Hybrid Search BMS**: Use for specific technical terms, codes, IDs.

4. **Contextual Search BMS**: Use when you need full document sections with surrounding context.

5. **Batch Search BMS**: Search multiple related queries simultaneously. Useful for comparing topics.

6. **Faceted Search BMS**: Group results by metadata (document type, department). Useful for understanding data distribution.

7. **Explained Search BMS**: Get score explanations for debugging and transparency.

8. **Latest Versions Search BMS**: Search only current document versions, excluding historical revisions.
```

### Step 6: Test the Integration

Test each new tool:

1. **Batch Search Test:**
   ```
   Search for both "safety procedures" and "emergency protocols"
   ```

2. **Faceted Search Test:**
   ```
   Show me documents about track maintenance, grouped by document type
   ```

3. **Explained Search Test:**
   ```
   Search for "VLAN configuration" and explain the scores
   ```

4. **Latest Versions Test:**
   ```
   Find the latest version of documents about fleet management
   ```

## Architecture

```
BMS AI Agent (main)
├── Ask BMS Tool → bms-tool-ask.json
├── Semantic Search Tool → bms-tool-semantic-search.json
├── Hybrid Search Tool → bms-tool-hybrid-search.json
├── Contextual Search Tool → bms-tool-contextual-search.json
├── Batch Search Tool → bms-tool-batch-search.json (NEW)
├── Faceted Search Tool → bms-tool-faceted-search.json (NEW)
├── Explained Search Tool → bms-tool-explained-search.json (NEW)
└── Latest Versions Tool → bms-tool-latest-search.json (NEW)
```

Each tool calls the corresponding BMS API endpoint:
- `/api/v1/search/batch`
- `/api/v1/search/facets`
- `/api/v1/search/explain`
- `/api/v1/search/latest`

## Verification

After setup, verify:
1. All 8 tool nodes are visible in the workflow
2. Each tool is connected to its sub-workflow
3. The agent can select and use all tools based on queries
4. API endpoints are responding (check BMS API is running on port 8000)

## Troubleshooting

**Tool not appearing in agent:**
- Ensure tool workflow is imported and saved
- Check that tool node is connected to agent node
- Verify workflow ID is correctly set in tool configuration

**API errors:**
- Ensure BMS API is running: `curl http://localhost:8000/health`
- Check API logs: `/workspace/logs/api.log`
- Verify endpoints exist: `/api/v1/search/batch`, etc.

**Agent not using new tools:**
- Update system prompt to mention new tools
- Test with explicit queries that should trigger each tool
- Check n8n execution logs for tool selection reasoning

## Related Tasks

- ✅ T027a: BMS API embeddings endpoint implemented
- ✅ T027b: Enhanced search workflows created
- 🔄 T027c: Command handlers integration (this guide)
- ⏳ T027d: Integration tests
- ⏳ T028-T029: Unit tests
- ⏳ T032-T034: Validation

## Next Steps

After completing this setup:
1. Run integration tests (T027d)
2. Implement unit tests for new endpoints (T028-T029)
3. Run full validation suite (T032-T034)
