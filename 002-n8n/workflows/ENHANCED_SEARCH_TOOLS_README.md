# Enhanced Search Tools - README

## Overview

4 new search tool workflows created to extend BMS Agent capabilities:

1. **tool-batch-search.json** - Multi-query batch search with union/intersection
2. **tool-faceted-search.json** - Search with metadata facet grouping
3. **tool-explained-search.json** - Search with detailed score explanations
4. **tool-latest-versions-search.json** - Search latest document versions only

## Architecture

These tools follow the same pattern as existing tools:
- Webhook trigger (HTTP POST)
- Parse input parameters
- Call BMS API endpoint
- Format response with rich metadata
- Respond with JSON

### Endpoints

| Tool | Webhook Path | BMS API Endpoint | Purpose |
|------|-------------|------------------|---------|
| Batch Search | `/webhook/tool-batch-search` | `/api/v1/search/batch` | Multi-query with union/intersection |
| Faceted Search | `/webhook/tool-faceted-search` | `/api/v1/search/facets` | Metadata grouping and facet breakdown |
| Explained Search | `/webhook/tool-explained-search` | `/api/v1/search/explain` | Score transparency and debugging |
| Latest Versions | `/webhook/tool-latest-search` | `/api/v1/search/latest` | Filter to current document versions |

## Usage

### Import into n8n

1. Open n8n UI
2. Go to **Workflows** > **Import**
3. Import each tool workflow:
   - `workflows/tool-batch-search.json`
   - `workflows/tool-faceted-search.json`
   - `workflows/tool-explained-search.json`
   - `workflows/tool-latest-versions-search.json`
4. Activate each workflow

### Testing via HTTP

**Batch Search:**
```bash
curl -X POST http://localhost:5678/webhook/tool-batch-search \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["safety procedures", "emergency protocols"],
    "mode": "union",
    "limit": 5
  }'
```

**Faceted Search:**
```bash
curl -X POST http://localhost:5678/webhook/tool-faceted-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "track maintenance",
    "facet_fields": ["document_type", "department"],
    "limit": 10
  }'
```

**Explained Search:**
```bash
curl -X POST http://localhost:5678/webhook/tool-explained-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "VLAN configuration",
    "limit": 5
  }'
```

**Latest Versions:**
```bash
curl -X POST http://localhost:5678/webhook/tool-latest-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fleet management procedures",
    "limit": 10
  }'
```

## Response Format

All tools return consistent JSON structure:

```json
{
  "success": true,
  "results": [
    {
      "document_id": "...",
      "document_name": "...",
      "document_type": "...",
      "department": "...",
      "content": "...",
      "content_preview": "...",
      "relevance_score": 0.85,
      "quality_score": 0.94,
      // Tool-specific fields...
    }
  ],
  "metadata": {
    "query": "...",
    "total_results": 5,
    "search_type": "batch|faceted|explained|latest_versions",
    // Tool-specific metadata...
  }
}
```

### Tool-Specific Response Fields

**Batch Search:**
- `results[].matched_queries`: Array of queries that matched this result
- `results[].match_count`: Number of queries matched
- `metadata.mode`: "union" or "intersection"
- `metadata.queries_count`: Number of queries in batch

**Faceted Search:**
- `facets`: Object with facet field breakdowns
  - Example: `{"document_type": {"PDF": 15, "DOCX": 8}, "department": {"QHSE": 12, "Engineering": 11}}`
- `metadata.facet_fields`: Array of fields used for faceting

**Explained Search:**
- `results[].explanation`: Detailed score breakdown
  - `semantic_score`: Base vector similarity
  - `quality_boost`: Quality multiplier
  - `recency_factor`: Document age factor
  - `tf_boost`: Term frequency boost
  - `matching_terms`: Keywords that matched
  - `formula`: Score calculation formula

**Latest Versions:**
- `results[].version`: Document version string
- `results[].is_latest_version`: Boolean flag (always true)
- `results[].document_date`: Date of document
- `results[].supersedes_version`: Previous version identifier
- `metadata.version_filter_applied`: Boolean (always true)

## Integration with Existing System

These tools complement the existing search tools:

**Existing Tools:**
1. `tool-ask-bms-enhanced.json` → `/api/v1/ask`
2. `tool-contextual-search.json` → `/api/v1/search/contextual`
3. `tool-search-by-metadata.json` → `/api/v1/search/semantic` (with filters)
4. `tool-search-hybrid.json` → `/api/v1/search/hybrid`
5. `tool-search-semantic.json` → `/api/v1/search/semantic`

**New Tools:**
6. `tool-batch-search.json` → `/api/v1/search/batch`
7. `tool-faceted-search.json` → `/api/v1/search/facets`
8. `tool-explained-search.json` → `/api/v1/search/explain`
9. `tool-latest-versions-search.json` → `/api/v1/search/latest`

## Error Handling

All tools include error handling:
- API errors return `{"success": false, "error": "...", "results": []}`
- Invalid parameters throw descriptive error messages
- Timeouts configured (15s-30s depending on operation complexity)

## Dependencies

**Required:**
- BMS API running on `http://localhost:8000`
- Qdrant vector database accessible to BMS API
- n8n instance running on `http://localhost:5678`

**Verify endpoints are available:**
```bash
curl http://localhost:8000/api/v1/search/batch \
  -H "Content-Type: application/json" \
  -d '{"queries": ["test"], "mode": "union", "limit": 1}'
```

## Development

All tools follow the same 5-node pattern:

1. **Webhook Trigger** - HTTP POST entry point
2. **Parse Input** - Extract and validate parameters
3. **Call BMS API** - HTTP request to BMS endpoint
4. **Format Response** - Extract rich metadata and format results
5. **Respond** - Return JSON to caller

To create a new tool, copy an existing tool workflow and modify:
- Webhook path and ID
- Input parameters in Parse Input
- API endpoint URL in Call BMS API
- Response formatting logic in Format Response

## Troubleshooting

**Webhook not responding:**
- Check workflow is activated in n8n UI
- Verify webhook path matches the URL you're calling
- Check n8n logs: Workflows > [workflow] > Executions

**API errors:**
- Verify BMS API is running: `curl http://localhost:8000/health`
- Check API logs: `/workspace/logs/api.log`
- Test endpoint directly without tool wrapper

**Empty results:**
- Check `min_score` threshold (default 0.7) isn't too high
- Verify Qdrant has data: `curl http://localhost:6333/collections/nomad_bms_documents`
- Test with broader query terms

## Related Documentation

- BMS API documentation: `/workspace/001-bms-agent/api/main.py`
- Qdrant schema: `/workspace/001-bms-agent/bms-agent/scr/qdrant_schema_v4.py`
- Existing tools: `tool-*-enhanced.json`, `tool-search-*.json`
- Setup guide (old - for LangChain integration): `ENHANCED_SEARCH_SETUP.md`

## Status

✅ **T027a:** BMS API embeddings endpoint - COMPLETE
✅ **T027b:** Enhanced search workflows - COMPLETE
✅ **T027c:** Tool workflows creation - COMPLETE
⏳ **T027d:** Integration tests - PENDING
⏳ **T028-T029:** Unit tests - PENDING
⏳ **T032-T034:** Validation - PENDING
