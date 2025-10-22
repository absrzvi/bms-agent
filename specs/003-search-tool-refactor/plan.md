# Implementation Plan: Search Tool Enhanced Retrieval

**Branch**: `003-search-tool-refactor` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-search-tool-refactor/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enhance the existing BMS search tool (`bms_search.py`) to display visual artifacts (images, diagrams, slides), chapter hierarchy, quality scores, and hierarchical chunk relationships from enhanced metadata already stored in Qdrant. This is a single-file modification targeting OpenWebUI integration with no backend or schema changes required. The implementation uses progressive enhancement principles to maintain backward compatibility with existing documents while unlocking rich context for documents ingested with Feature 002 (enhanced document processor).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: aiohttp>=3.9.0, pydantic>=2.0.0, base64 (stdlib), Pillow (for image handling)
**Storage**: `/workspace/visual-artifacts/` (filesystem), Qdrant `nomad_bms_documents` collection (vector DB)
**Testing**: Manual integration testing via OpenWebUI, pytest for unit tests (test framework exists at `/workspace/bms-agent/tests/`)
**Target Platform**: OpenWebUI v0.4.0+ running on RunPod (Linux server, persistent `/workspace` directory)
**Project Type**: Single-file enhancement (single project structure)
**Performance Goals**: ≤2s dashboard rendering for 5 results with artifacts (client-side only), ≤500ms enrichment overhead
**Constraints**: No FastAPI backend modifications, no Qdrant schema changes, backward compatibility required, base64 encoding for inline images
**Scale/Scope**: 300+ documents, 21 departments, ~50,000 chunks in production, single 1,200-line Python file modification

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ⚠️ No project constitution found at `/workspace/bms-agent/.specify/memory/constitution.md`

**Gate Evaluation**: PASS (no constitution to validate against)

**Recommendation**: Consider running `/speckit.constitution` to establish project principles for future features. For this feature, proceeding without constitution validation based on:
- Single-file modification (low complexity)
- No new dependencies (uses existing infrastructure)
- Backward compatibility maintained
- Clear success criteria defined in spec.md

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
bms-agent/
├── bms_search.py              # PRIMARY FILE - All modifications here (1,200 lines)
├── bms-agent/
│   ├── api/
│   │   ├── main.py            # FastAPI backend (NO CHANGES)
│   │   └── processor_wrapper.py  # Document ingestion (NO CHANGES)
│   └── scr/
│       ├── enhanced_document_processor.py  # Ingestion pipeline (NO CHANGES)
│       ├── qdrant_schema_v4.py            # Vector DB schema (NO CHANGES)
│       └── artifact_storage.py            # Storage manager (reads only)
├── tests/
│   ├── test_basic.py          # Existing tests (NO CHANGES)
│   ├── integration/           # May add new test files here
│   └── performance/           # May add performance tests here
└── upload-files/              # Department folders (NO CHANGES)

/workspace/
├── visual-artifacts/          # Artifact storage (READ-ONLY for search tool)
│   └── {document_id}/
│       ├── images/
│       │   └── img_{artifact_id}.png
│       └── slides/
│           └── slide_{artifact_id}.png
└── qdrant-data/               # Qdrant persistent storage (NO CHANGES)
```

**Structure Decision**: Single-file enhancement strategy. All code changes are confined to `/workspace/bms-agent/bms_search.py`. This OpenWebUI tool reads from Qdrant (via HTTP API) and filesystem (`/workspace/visual-artifacts/`) but does not modify any backend services or data. The feature adds new methods and enhances existing methods within the `Tools` class.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations detected. This feature maintains simplicity:
- Single-file modification (minimal complexity)
- No new external dependencies
- No architectural changes
- Uses existing infrastructure (Qdrant, filesystem, OpenWebUI)

---

## Architecture & Design

### Result Enrichment Pipeline

The implementation adds a centralized enrichment layer between Qdrant query and dashboard generation:

```
Qdrant Search Results (existing)
    ↓
_update_result_cache(results) [NEW]
    └─ Caches results for hierarchy navigation (LRU, limit 100)
    ↓
_enrich_search_results(results) [NEW] - Orchestrator
    ├─ Check metadata availability
    ├─ if ENABLE_VISUAL_ARTIFACTS: _load_visual_artifacts_optimized()
    ├─ if ENABLE_CHAPTER_CONTEXT: _format_chapter_context()
    ├─ if ENABLE_QUALITY_BADGES: _format_quality_breakdown()
    └─ Set hierarchy flags (has_parent, has_children, parent_in_cache)
    ↓
_deduplicate_parent_child_results(enriched) [NEW]
    └─ Remove child chunks when parent exists
    ↓
_generate_search_dashboard(enriched) [MODIFY]
    └─ Render enriched HTML with artifacts, breadcrumbs, badges
```

### Key Design Patterns

1. **Progressive Enhancement**
   - Each enrichment type (artifacts, chapters, quality) is independent
   - Missing metadata doesn't break existing functionality
   - Feature flags (Valves) allow per-feature toggle

2. **Graceful Degradation**
   - Check metadata presence before enrichment
   - Default to empty lists/None for missing fields
   - Log warnings (INFO level) rather than errors

3. **Performance Optimization**
   - Direct path construction: O(m) vs O(n) directory scanning
   - Parallel artifact loading with `asyncio.gather()`
   - Limit artifacts per card (max 3, configurable)
   - Base64 encoding with 5MB size limit per artifact

4. **Backward Compatibility**
   - Documents without enhanced metadata display exactly as before
   - All new methods check for metadata availability first
   - Existing search functions (25 total) unchanged in behavior

### Data Flow

**Visual Artifacts Loading**:
```
Qdrant payload: visual_artifact_ids = ["img_001", "slide_002"]
    ↓
For each artifact_id:
    path = /workspace/visual-artifacts/{document_id}/images/img_001.png
    if exists and size < 5MB:
        base64_data = encode_image(path)
        artifact = {id, data, caption}
    ↓
Return artifacts[:3]  # Limit to 3
```

**Chapter Context Formatting**:
```
Qdrant payload: chapter_number="2", chapter_title="Safety Protocols", sub_chapter="2.3"
    ↓
Format: "📂 Chapter 2 > Safety Protocols > 2.3"
    ↓
Render as breadcrumb above result card
```

**Quality Score Badge**:
```
Qdrant payload: quality_score=87.5, quality_components={...}
    ↓
Color mapping: score ≥ 80% → green
    ↓
Badge: "High 87.5%" (green background)
Tooltip: "Faithfulness: 90%, Relevancy: 85%, ..."
```

**Parent-Child Deduplication**:
```
Results: [parent_chunk_A, child_chunk_B (parent_id=A), child_chunk_C (parent_id=A)]
    ↓
Build map: parent_id → chunk_id
    ↓
Filter: Remove child_B and child_C (parent_A exists in results)
    ↓
Final: [parent_chunk_A only]
```

### Implementation Strategy

**MVP-First Approach** (from tasks.md):
1. **Phase 1-2**: Setup + Foundation (result caching, enrichment skeleton)
2. **Phase 3**: User Story 1 (Visual Artifacts) - **MVP DELIVERY**
3. **Phase 4-6**: User Stories 2-4 (independent, can be parallel)
4. **Phase 7**: Polish (error handling, valves, documentation)

**Critical Success Factors**:
- Backward compatibility: Validate with T093-T096
- Performance: Dashboard ≤2s for 5 results (SC-001)
- Single-file: All changes in bms_search.py
- MVP first: Deploy US1 before US2-US4

### Testing Strategy

**Manual Integration Tests** (via OpenWebUI):
- Search for "safety card" → verify visual artifacts display
- Search for "test completion" → verify chapter breadcrumbs
- Search for any document → verify quality badges (if enabled)
- Click "Expand Context" → verify parent chunk displays

**Performance Benchmarks**:
- Dashboard rendering: ≤2s for 5 results with artifacts
- Enrichment overhead: ≤500ms per result
- Artifact loading: ~10ms per artifact (direct path construction)

**Backward Compatibility**:
- Documents ingested before Feature 002 (no enhanced metadata)
- Documents with partial metadata (some fields missing)
- Existing search functions (all 25) still work unchanged

---

## Phase 0 & 1 Artifacts

✅ **research.md** - All technical decisions documented (8 research questions resolved)
✅ **data-model.md** - Data structures for enriched results, visual artifacts, chapter context, quality breakdown
✅ **quickstart.md** - Developer guide for implementation, testing, deployment
✅ **contracts/** - No external APIs (internal tool only)

**Next Step**: Run `/speckit.tasks` to generate implementation tasks from this plan.

---

## Summary

This feature enhances the BMS search tool with rich metadata display while maintaining:
- **Zero backend changes** (Qdrant schema unchanged)
- **Single-file modification** (bms_search.py only)
- **Backward compatibility** (graceful degradation)
- **Performance targets** (≤2s dashboard rendering)
- **MVP-first delivery** (US1 visual artifacts first)

All design artifacts complete. Ready for task generation.
