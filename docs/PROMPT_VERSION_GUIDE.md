# BMS Agent System Prompt Version Guide

**Last Updated**: 2025-10-04  
**Purpose**: Map OpenWebUI tool versions to their corresponding system prompts

---

## Quick Reference

| Tool Version | Tool File | System Prompt | Functions | Status |
|--------------|-----------|---------------|-----------|--------|
| **v3.0** | `bms_search_v3.py` | `SYSTEM_PROMPT_BMS_AGENT_V3.md` | 20 | ✅ **Recommended** |
| v2.0 | `bms_search.py` | `SYSTEM_PROMPT_BMS_AGENT.md` | 11 | ⚠️ Legacy |

---

## v3.0 - Enhanced RAG (Recommended)

### Tool Configuration
- **File**: `tools/bms_search_v3.py`
- **System Prompt**: `docs/SYSTEM_PROMPT_BMS_AGENT_V3.md`
- **Functions**: 20 (11 core + 9 advanced)
- **Release Date**: 2025-10-04
- **Status**: ✅ Production-ready

### Capabilities
Advanced RAG with state-of-the-art retrieval enhancements:

#### Core Features (11 functions)
1. `search_documents()` - General search with full configurability
2. `search_semantic()` - Dense vector similarity
3. `search_hybrid()` - Semantic + keyword matching
4. `compare_search_types()` - Compare semantic vs hybrid
5. `search_by_document_type()` - Filter by file type
6. `search_by_fleet_type()` - Filter by train type
7. `search_by_standard()` - Filter by compliance standard
8. `search_by_department()` - Filter by department
9. `search_with_context()` - Prioritize contextual chunks
10. `search_high_quality()` - Filter by quality score
11. `get_api_status()` - Check API health

#### Advanced Features (9 NEW functions)
12. `search_with_session()` 🆕 - Conversational context tracking
13. `search_expanded()` 🆕 - Query expansion with LLM
14. `search_with_explanation()` 🆕 - Detailed score breakdowns
15. `search_synthesized()` 🆕 - Multi-document synthesis
16. `search_by_train_id()` 🆕 - Railway train/fleet search
17. `search_by_component()` 🆕 - Railway component search
18. `search_by_date_range()` 🆕 - Temporal filtering
19. `search_latest_versions()` 🆕 - Version-aware search
20. `search_multiple_queries()` 🆕 - Batch multi-query
21. `search_with_facets()` 🆕 - Faceted result grouping

### When to Use v3.0
✅ **Use v3.0 for:**
- Multi-turn conversations requiring context tracking
- Complex queries needing query expansion
- Comprehensive answers requiring multi-document synthesis
- Railway-specific queries (trains, components, standards)
- Temporal queries (recent documents, latest versions)
- Explainability and transparency requirements
- Production deployments requiring advanced RAG

### System Prompt Features
The v3.0 system prompt (`SYSTEM_PROMPT_BMS_AGENT_V3.md`) includes:
- Decision-making guidelines for when to use each function
- Conversational context examples
- Multi-document synthesis strategies
- Explainability response templates
- Railway ontology usage patterns
- Temporal search guidelines
- Batch query strategies
- Faceted exploration patterns

### Deployment Instructions

1. **Copy tool to OpenWebUI:**
   ```bash
   cp /workspace/001-bms-agent/tools/bms_search_v3.py \
      /workspace/openwebui/data/tools/
   ```

2. **Configure system prompt in OpenWebUI:**
   - Navigate to OpenWebUI settings → Models → [Your Model]
   - Copy contents of `docs/SYSTEM_PROMPT_BMS_AGENT_V3.md`
   - Paste into system prompt field
   - Save configuration

3. **Verify installation:**
   - Start a new chat
   - Ask: "What search functions do you have?"
   - LLM should list all 20 functions

---

## v2.0 - Metadata-Aware (Legacy)

### Tool Configuration
- **File**: `tools/bms_search.py`
- **System Prompt**: `docs/SYSTEM_PROMPT_BMS_AGENT.md`
- **Functions**: 11 (basic search + filters)
- **Release Date**: 2025-09-29
- **Status**: ⚠️ Legacy (use v3.0 for new deployments)

### Capabilities
Basic search with metadata-aware ranking:

1. `search_documents()` - General search
2. `search_semantic()` - Semantic search
3. `search_hybrid()` - Hybrid search
4. `search_by_document_type()` - Document type filter
5. `search_by_fleet_type()` - Fleet type filter
6. `search_by_standard()` - Standard filter
7. `search_by_department()` - Department filter
8. `search_with_context()` - Context prioritization
9. `search_high_quality()` - Quality filter
10. `compare_search_types()` - Search comparison
11. `get_api_status()` - API health

### When to Use v2.0
⚠️ **Use v2.0 only for:**
- Legacy deployments requiring backward compatibility
- Simple single-turn queries without context tracking
- Resource-constrained environments
- Testing and comparison purposes

### Migration Path
To upgrade from v2.0 to v3.0:

1. **Backup current configuration:**
   ```bash
   cp /workspace/openwebui/data/tools/bms_search.py \
      /workspace/openwebui/data/tools/bms_search_v2_backup.py
   ```

2. **Install v3.0 tool** (see v3.0 deployment instructions above)

3. **Update system prompt** to v3.0 version

4. **Test functionality:**
   - Verify all 11 core functions work (backward compatible)
   - Test new advanced functions
   - Validate conversational context tracking

5. **Remove v2.0 tool** (optional):
   ```bash
   rm /workspace/openwebui/data/tools/bms_search.py
   ```

---

## Comparison Matrix

| Feature | v2.0 | v3.0 |
|---------|------|------|
| **Core Search** | ✅ 11 functions | ✅ 11 functions |
| **Conversational Context** | ❌ | ✅ Session tracking |
| **Query Expansion** | ❌ | ✅ LLM-based |
| **Multi-Document Synthesis** | ❌ | ✅ 3 strategies |
| **Explainability** | ❌ | ✅ Score breakdowns |
| **Railway Ontology** | ⚠️ Basic filters | ✅ Train/component search |
| **Temporal Search** | ❌ | ✅ Date range + versions |
| **Batch Queries** | ❌ | ✅ Multi-query aggregation |
| **Faceted Search** | ❌ | ✅ Result grouping |
| **Retrieval Accuracy** | 96% | 96% (baseline) + enhancements |
| **Response Time** | <100ms p95 | <100ms p95 (optimized) |
| **Backward Compatible** | N/A | ✅ All v2 functions work |

---

## Performance Considerations

### v3.0 Performance
- **Latency**: <100ms p95 for core functions
- **Advanced Functions**: May add 50-200ms for LLM-based features (query expansion, synthesis)
- **Session Management**: Minimal overhead (<10ms)
- **Recommended**: Enable caching for frequently used queries

### Configuration Tuning
For optimal v3.0 performance:

```python
# In OpenWebUI tool Valves configuration
BMS_API_URL = "http://localhost:8000"
DEFAULT_LIMIT = 5  # Reduce for faster responses
ENABLE_QUERY_EXPANSION = True  # Disable if latency critical
ENABLE_EXPLAINABILITY = False  # Enable only when needed
SESSION_TTL_MINUTES = 30  # Adjust based on usage patterns
```

---

## Troubleshooting

### Issue: LLM not using advanced functions
**Cause**: Wrong system prompt version  
**Solution**: Verify you're using `SYSTEM_PROMPT_BMS_AGENT_V3.md` with `bms_search_v3.py`

### Issue: "Function not found" errors
**Cause**: Tool version mismatch  
**Solution**: Check tool file matches prompt version (see Quick Reference table)

### Issue: Conversational context not working
**Cause**: Session management not enabled  
**Solution**: Ensure `search_with_session()` is being called (check system prompt guidelines)

### Issue: Performance degradation
**Cause**: Advanced features adding latency  
**Solution**: Disable query expansion or reduce session TTL in Valves configuration

---

## Version History

| Version | Release Date | Changes |
|---------|--------------|---------|
| **v3.0** | 2025-10-04 | Added 9 advanced functions: conversational context, query expansion, synthesis, explainability, railway ontology, temporal search, batch queries, faceted search |
| v2.0 | 2025-09-29 | Metadata-aware ranking, 11 core functions, quality filtering |
| v1.0 | 2025-09-28 | Initial release, basic semantic/hybrid search |

---

## Support & Documentation

- **Tool Documentation**: `tools/README.md`
- **System Prompts**: `docs/SYSTEM_PROMPT_BMS_AGENT*.md`
- **API Documentation**: http://localhost:8000/docs
- **Analysis Report**: `.specify/analysis-report.md`

---

## Recommendations

### For New Deployments
✅ **Use v3.0** - Full feature set, production-ready, backward compatible

### For Existing v2.0 Deployments
⚠️ **Migrate to v3.0** - Follow migration path above for enhanced capabilities

### For Development/Testing
✅ **Use v3.0** - Test advanced features, validate conversational context

---

**Last Updated**: 2025-10-04 13:18 UTC  
**Maintained By**: BMS Agent Team  
**Next Review**: 2025-11-04
