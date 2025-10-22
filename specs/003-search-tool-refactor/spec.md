# Feature Specification: Search Tool Enhanced Retrieval

**Feature Branch**: `003-search-tool-refactor`
**Created**: 2025-10-22
**Status**: Draft
**Input**: User description: "i want to refactor the bms_search.py tool so that it uses all the features the enhanced doc processor script has used to ingest the qdrant collection"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visual Artifacts Display in Search Results (Priority: P1)

When users search for documents through the OpenWebUI search tool, they should see visual artifacts (images, diagrams, slides) embedded directly in the search results alongside the text content, providing richer context and improving comprehension.

**Why this priority**: This is the most valuable enhancement because visual artifacts provide critical context that text alone cannot convey. Users currently see only text chunks, missing important diagrams, charts, and images that were extracted during ingestion.

**Independent Test**: Can be fully tested by performing a search for documents known to contain visual artifacts (e.g., technical proposals, presentations) and verifying that images appear inline with search results.

**Acceptance Scenarios**:

1. **Given** a document with embedded images has been ingested with visual artifacts, **When** user searches for content related to that document, **Then** the search result card displays associated visual artifacts with captions
2. **Given** a PPTX presentation has been rendered as slide images during ingestion, **When** user searches for slide content, **Then** the dashboard shows rendered slide images inline with text chunks
3. **Given** a search result has 5 visual artifacts associated with it, **When** the dashboard renders, **Then** up to 3 artifacts are displayed per result card with thumbnails and click-to-enlarge functionality

---

### User Story 2 - Chapter-Aware Result Grouping (Priority: P2)

When users search for information across large documents, results should be grouped and labeled by their chapter/section hierarchy, making it easier to understand document structure and navigate to related content.

**Why this priority**: Chapter awareness was added during ingestion but isn't exposed in search results. This provides critical navigation context for complex technical documents.

**Independent Test**: Can be tested by searching for a term that appears in multiple chapters of the same document and verifying that results display chapter hierarchy (e.g., "Chapter 3 > Section 3.2 > Safety Protocols").

**Acceptance Scenarios**:

1. **Given** a document has been ingested with chapter structure, **When** user searches and gets multiple results from the same document, **Then** each result card shows its chapter path (e.g., "Chapter 2 > 2.3 Risk Assessment")
2. **Given** search returns results from different chapters, **When** the dashboard renders, **Then** results can be grouped by chapter for easier navigation
3. **Given** a document has hierarchical sub-chapters, **When** displaying results, **Then** the full chapter hierarchy is shown with proper nesting indicators

---

### User Story 3 - Quality Score Transparency (Priority: P3)

When users view search results, they should see the quality validation scores that were computed during ingestion, helping them assess document reliability and completeness.

**Why this priority**: Quality scores help users prioritize which results to trust, especially when dealing with large result sets from multiple sources.

**Independent Test**: Can be tested by performing a search and verifying that result cards display quality score badges with color-coded indicators (green for high quality, yellow for medium, red for low).

**Acceptance Scenarios**:

1. **Given** search results with varying quality scores, **When** the dashboard renders, **Then** each result card shows a quality score percentage with appropriate color coding
2. **Given** a high-quality document (score ≥ 85%), **When** displayed in results, **Then** it shows a green quality badge and is ranked higher
3. **Given** the quality score breakdown is available, **When** user hovers over the score, **Then** a tooltip shows the component scores (faithfulness, relevancy, precision, recall)

---

### User Story 4 - Hierarchical Context Retrieval (Priority: P4)

When users find a relevant child chunk, they should have easy access to its parent chunk for broader context, and when viewing a parent chunk, they should see links to detailed child chunks.

**Why this priority**: Hierarchical chunking was implemented during ingestion to provide context at different granularities, but the search tool doesn't expose this hierarchy to users.

**Independent Test**: Can be tested by searching for a specific detail and verifying that the result card offers an "expand to show parent context" button, and conversely that parent chunks offer "show detailed sections" links.

**Acceptance Scenarios**:

1. **Given** a search returns a child chunk, **When** the result card renders, **Then** an "Expand Context" button shows the parent chunk content
2. **Given** a search returns a parent chunk with child chunks, **When** displayed, **Then** a "Show Details" button expands to show all child chunks
3. **Given** hierarchical navigation is triggered, **When** expanding context, **Then** the UI clearly indicates parent/child relationships with visual indentation or hierarchy icons

---

### Edge Cases

- What happens when a document has visual artifacts but they failed to load or are corrupted?
- How does the system handle search results that return parent and child chunks for the same content (deduplication)?
- What happens when chapter structure is incomplete or malformed (e.g., missing chapter numbers)?
- How does the system display very large visual artifacts (e.g., high-resolution diagrams) without breaking the UI?
- What happens when a document has 20+ visual artifacts but the UI should only show 3 per result?
- How does the system handle mixed artifact types (images from PDFs, rendered slides from PPTX) in the same result?
- What happens when quality score metadata is missing from older documents?
- How does the dashboard perform when displaying 20 results, each with 3 visual artifacts (60 images total)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Search tool MUST retrieve visual artifact metadata (artifact IDs, captions, types) from Qdrant point payloads for each search result
- **FR-002**: Search tool MUST load visual artifacts from persistent storage (`/workspace/visual-artifacts/`) using artifact IDs
- **FR-003**: Search tool MUST display up to 3 visual artifacts per result card with base64-encoded image data for inline rendering
- **FR-004**: Search tool MUST show visual artifact captions beneath each image in result cards
- **FR-005**: System MUST retrieve chapter hierarchy metadata (chapter_number, chapter_title, chapter_path, chapter_level, sub_chapter) from Qdrant payloads
- **FR-006**: Search results MUST display chapter path for each chunk in a human-readable format (e.g., "Chapter 2 > Section 2.3 > Risk Assessment")
- **FR-007**: Search tool MUST retrieve quality score metadata (overall quality_score and component scores) from Qdrant payloads
- **FR-008**: Result cards MUST display quality scores as percentage badges with color coding (green ≥ 80%, yellow ≥ 60%, red < 60%)
- **FR-009**: Search tool MUST retrieve parent-child chunk relationships from Qdrant metadata (parent_id, child_ids)
- **FR-010**: Result cards MUST provide UI controls to expand parent context or show child details based on chunk hierarchy
- **FR-011**: System MUST handle cases where visual artifacts are referenced in metadata but files are missing from storage (graceful degradation)
- **FR-012**: System MUST deduplicate results when both parent and child chunks match the same query
- **FR-013**: Search tool MUST apply existing result boosting and ranking algorithms after enriching results with enhanced metadata
- **FR-014**: Dashboard MUST maintain backward compatibility with existing artifact rendering, SVG charts, and Mermaid diagrams
- **FR-015**: System MUST log warnings when enhanced metadata is missing or incomplete for a search result

### Key Entities

- **EnrichedSearchResult**: Search result enriched with visual artifacts, chapter context, quality scores, and hierarchical links
  - Attributes: `text`, `score`, `metadata` (base), `visual_artifacts` (list), `chapter_context` (dict), `quality_breakdown` (dict), `parent_chunk` (reference), `child_chunks` (list)

- **VisualArtifact**: Representation of an image, diagram, or slide associated with a chunk
  - Attributes: `artifact_id`, `type` (image/slide), `caption`, `file_path`, `base64_data`, `thumbnail_path`, `ocr_text`

- **ChapterContext**: Hierarchical document structure information for a chunk
  - Attributes: `chapter_number`, `chapter_title`, `chapter_level`, `chapter_path`, `sub_chapter`, `full_hierarchy_string`

- **QualityBreakdown**: Detailed quality validation scores for a chunk
  - Attributes: `overall_score`, `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`, `passed_threshold`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users searching for documents with visual artifacts see images displayed inline within search results within 2 seconds of result rendering
- **SC-002**: 90% of search results that have chapter metadata display chapter hierarchy in a readable format (e.g., "Chapter 2 > Section 2.3")
- **SC-003**: Dashboard loading time increases by no more than 500ms when displaying visual artifacts compared to text-only results (baseline: 1-2 seconds)
- **SC-004**: Users can expand parent/child context for hierarchical chunks with no more than one click, and expansion completes within 300ms
- **SC-005**: Quality score badges are displayed for 100% of search results that have quality metadata in Qdrant
- **SC-006**: System gracefully handles missing visual artifacts without breaking the UI, showing a placeholder or skipping the artifact
- **SC-007**: Search tool maintains backward compatibility - existing searches without enhanced metadata work exactly as before
- **SC-008**: Visual artifact display works correctly for at least 95% of documents ingested with the enhanced processor (validated through spot checks)

## Assumptions

- Visual artifacts are already stored in `/workspace/visual-artifacts/` as a result of ingestion with the enhanced document processor
- Qdrant collection `nomad_bms_documents` already contains enhanced metadata (visual_artifact_ids, chapter_number, quality_score, etc.) for documents ingested after Feature 002 deployment
- The bms_search.py tool runs in the OpenWebUI environment with access to the same file system as the ingestion pipeline
- Base64 encoding of images for inline display is acceptable for OpenWebUI artifact rendering (no performance constraints exceeded)
- Existing search tool configuration (Valves, UserValves) can be extended without breaking backward compatibility
- The FastAPI backend does not need modification - all enhancements are client-side in the search tool

## Dependencies

- **Visual Artifacts Storage**: Requires `/workspace/visual-artifacts/` directory to be populated by enhanced_document_processor.py during ingestion
- **Qdrant Schema**: Requires Qdrant collection to have indexed payload fields: `has_visual_artifacts`, `visual_artifact_ids`, `image_captions`, `chapter_number`, `chapter_title`, `quality_score`, `quality_components`, `parent_id`, `child_ids`
- **Enhanced Document Processor**: Assumes all documents have been reingested using enhanced_document_processor.py with visual artifacts and chapter extraction enabled
- **OpenWebUI Artifact System**: Requires OpenWebUI v0.4.0+ with artifact rendering support (already confirmed in bms_search.py header)

## Out of Scope

- Modifying the FastAPI backend or Qdrant schema (search tool only)
- Reingesting documents - assumes enhanced metadata is already in Qdrant
- Real-time OCR or image processing in the search tool (artifacts are pre-processed during ingestion)
- Advanced image viewer features (zoom, pan, fullscreen) - users can click images to open in new tab
- Filtering or searching by visual artifact content (OCR text is available but not indexed)
- Version control for visual artifacts or document replacements
- Exporting search results with embedded images to external formats (PDF, Word, etc.)
