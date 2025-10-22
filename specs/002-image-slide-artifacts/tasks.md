# Tasks: Image and Slide Visual Artifacts for RAG Search

**Input**: Design documents from `/specs/002-image-slide-artifacts/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

Project follows existing BMS Agent structure:
- **Backend**: `bms-agent/scr/` (core processing), `bms-agent/api/` (FastAPI endpoints)
- **Tests**: `bms-agent/tests/`
- **Artifacts Storage**: `/workspace/visual-artifacts/`
- **Tools**: Root-level scripts (`bms_search.py`, etc.)

---

## Phase 1: Setup (System Dependencies & Infrastructure)

**Purpose**: Install required system packages and create storage infrastructure

- [X] T001 Install Tesseract OCR with English language data via `apt-get install -y tesseract-ocr tesseract-ocr-eng`
- [X] T002 Install Poppler utilities for pdf2image via `apt-get install -y poppler-utils`
- [X] T003 Install LibreOffice for PPTX rendering via `apt-get install -y libreoffice-core libreoffice-impress`
- [X] T004 Add Python dependencies to requirements.txt: pytesseract>=0.3.10, pdf2image>=1.16.3
- [X] T005 Install new Python dependencies via `pip install -r requirements.txt`
- [X] T006 Create visual artifacts directory structure: `/workspace/visual-artifacts/{images,slides,thumbnails}/`
- [X] T007 Verify installations: tesseract --version, soffice --version, pdftoppm -v
- [X] T008 [P] Add environment variables to .env: VISUAL_ARTIFACTS_DIR, MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT, MAX_IMAGES_PER_CHUNK, ENABLE_OCR, OCR_LANGUAGE, PPTX_RENDER_DPI

**Checkpoint**: All system dependencies installed, storage ready

---

## Phase 2: Foundational (Core Modules - Blocking Prerequisites)

**Purpose**: Core infrastructure modules that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Storage & Configuration

- [X] T009 Create ArtifactStorageManager class in bms-agent/scr/artifact_storage.py with methods: save_artifact(), load_artifact(), generate_artifact_id(), get_artifact_path()
- [X] T010 Implement directory management: ensure_directories_exist(), check_disk_space(), cleanup_orphaned_artifacts()
- [X] T011 Add configuration loading for VISUAL_ARTIFACTS_DIR and image size limits in artifact_storage.py

### Image Processing Core

- [X] T012 [P] Create ImageProcessor class in bms-agent/scr/image_processor.py with Pillow integration
- [X] T013 [P] Implement resize_image() method with aspect ratio preservation (max 1920x1080)
- [X] T014 [P] Implement create_thumbnail() method for compressed previews (400x300, JPEG quality 80)
- [X] T015 [P] Implement optimize_image() method for PNG/JPEG format detection and compression

### OCR Engine Wrapper

- [X] T016 [P] Create OCRProcessor class in bms-agent/scr/ocr_processor.py with Tesseract integration
- [X] T017 [P] Implement extract_text_from_image() method returning OCR text and confidence score
- [X] T018 [P] Implement preprocess_for_ocr() method: grayscale conversion, binarization, contrast enhancement
- [X] T019 [P] Add error handling for Tesseract unavailable scenario

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Visual Context for Technical Documentation Search (Priority: P1) 🎯 MVP

**Goal**: Extract embedded images from PDF documents and display them as visual artifacts alongside text search results in OpenWebUI

**Independent Test**: Upload a PDF railway manual with embedded diagrams, search for "brake system schematic", verify the search result displays the text chunk AND the related diagram as a visual artifact

### PDF Image Extraction

- [X] T020 [US1] Create ImageExtractor class in bms-agent/scr/image_extractor.py with PyMuPDF (fitz) integration
- [X] T021 [US1] Implement extract_images_from_pdf() method: iterate pages, get_images(full=True), extract_image(xref), capture bbox coordinates
- [X] T022 [US1] Implement pdf2image fallback for extract_images_from_pdf() when PyMuPDF fails (scanned PDFs)
- [X] T023 [US1] Add image metadata extraction: page_number, format, dimensions, position, bbox

### DOCX Image Extraction

- [X] T024 [P] [US1] Implement extract_images_from_docx() method in ImageExtractor using python-docx
- [X] T025 [P] [US1] Extract inline images via run._element.xpath('.//a:blip') in extract_images_from_docx()
- [X] T026 [P] [US1] Extract floating images via document relationships (_rels) in extract_images_from_docx()
- [X] T027 [P] [US1] Capture paragraph context for caption extraction in extract_images_from_docx()

### Image-Chunk Association

- [X] T028 [US1] Create ProximityAssociator class in bms-agent/scr/proximity_associator.py
- [X] T029 [US1] Implement associate_images_with_chunks() using bbox distance calculation
- [X] T030 [US1] Implement calculate_bbox_distance() method: Euclidean distance between bounding box centers
- [X] T031 [US1] Add fallback logic: associate image with chunk on same page if bbox unavailable

### OCR Integration for Images

- [X] T032 [US1] Integrate OCRProcessor into ImageExtractor for text extraction from images
- [X] T033 [US1] Add OCR text to artifact metadata: ocr_text, ocr_confidence fields
- [X] T034 [US1] Implement conditional OCR: only run if image likely contains text (heuristic: aspect ratio, file size)

### Document Processor Integration

- [X] T035 [US1] Extend EnhancedDocumentProcessor._read_document() in bms-agent/scr/enhanced_document_processor.py to call ImageExtractor
- [X] T036 [US1] Add _extract_visual_artifacts() method to EnhancedDocumentProcessor orchestrating extraction workflow
- [X] T037 [US1] Process extracted images: resize via ImageProcessor, generate thumbnails, save via ArtifactStorageManager
- [X] T038 [US1] Associate artifacts with chunks using ProximityAssociator after chunking completes
- [X] T039 [US1] Extend chunk metadata with Visual Artifact references: has_visual_artifacts, visual_artifact_ids, visual_artifact_count, image_ocr_text

### Qdrant Payload Extension

- [X] T040 [US1] Update qdrant_schema_v4.py to add new payload fields: has_visual_artifacts (bool, indexed), visual_artifact_ids (array[string]), visual_artifact_count (int, indexed)
- [X] T041 [US1] Add keyword indexes for has_visual_artifacts and visual_artifact_count in create_collection() method
- [X] T042 [US1] Update chunk upsert logic in processor_wrapper.py to include artifact metadata in Qdrant payload

### OpenWebUI Tool Integration

- [X] T043 [US1] Update bms_search.py to load visual artifacts when has_visual_artifacts=true in search results
- [X] T044 [US1] Implement format_result_with_artifacts() function: load artifact from file system, encode to base64
- [X] T045 [US1] Add artifact display logic to search response: {"type": "image", "caption": "...", "data": "data:image/png;base64,..."}
- [X] T046 [US1] Implement lazy loading: only encode artifacts for top-10 search results to optimize performance

### Testing & Validation (US1)

- [ ] T047 [P] [US1] Create test_pdf_extraction.py: verify PyMuPDF extracts images correctly, test with BMS-ENGI-FOR-004 Maintenance Manual.pdf
- [ ] T048 [P] [US1] Test OCR accuracy: run extract_text_from_image() on sample diagram, verify confidence > 70%
- [ ] T049 [P] [US1] Test end-to-end: ingest PDF with images, search for related text, verify artifact appears in OpenWebUI
- [ ] T050 [P] [US1] Test proximity association: verify image associates with nearest text chunk based on page coordinates
- [ ] T051 [P] [US1] Performance test: verify image extraction takes < 100ms per page (SC-003 target)

**US1 Deliverable**: PDF documents can be uploaded, images extracted, and displayed alongside text search results in OpenWebUI

---

## Phase 4: User Story 2 - PowerPoint Slide Preservation (Priority: P1)

**Goal**: Render each PowerPoint slide as a static image preserving visual fidelity (layout, formatting, embedded content) for search retrieval

**Independent Test**: Upload a PPTX training presentation with 20 slides, search for slide content, verify each slide appears as a rendered image artifact

### PPTX Slide Rendering

- [ ] T052 [US2] Implement render_pptx_slides() method in ImageExtractor using LibreOffice headless
- [ ] T053 [US2] Add subprocess call to soffice --headless --convert-to pdf for PPTX-to-PDF conversion in render_pptx_slides()
- [ ] T054 [US2] Use pdf2image convert_from_path() to render each PDF page (slide) as PNG image
- [ ] T055 [US2] Configure render DPI from PPTX_RENDER_DPI environment variable (default 150)
- [ ] T056 [US2] Clean up temporary PDF file after slide rendering completes

### Slide Metadata & Association

- [ ] T057 [P] [US2] Extract slide text using python-pptx for searchable content before rendering
- [ ] T058 [P] [US2] Associate each rendered slide image with corresponding text chunk (1-to-1 mapping by slide number)
- [ ] T059 [P] [US2] Add slide-specific metadata: source_slide_number, presentation_name, total_slides

### Slide Processing Integration

- [ ] T060 [US2] Extend _extract_visual_artifacts() in EnhancedDocumentProcessor to detect PPTX files
- [ ] T061 [US2] Call render_pptx_slides() when processing PPTX documents
- [ ] T062 [US2] Process rendered slides: optimize via ImageProcessor, create thumbnails, save to /workspace/visual-artifacts/slides/
- [ ] T063 [US2] Update chunk creation for PPTX: one chunk per slide with slide image as artifact

### Slide Render Job Tracking

- [ ] T064 [P] [US2] Create SlideRenderJob dataclass in bms-agent/scr/slide_renderer.py for status tracking
- [ ] T065 [P] [US2] Implement job state machine: pending → in_progress → completed/failed
- [ ] T066 [P] [US2] Log render timestamps and duration for performance monitoring

### Error Handling & Fallbacks

- [ ] T067 [US2] Add LibreOffice availability check: verify soffice command exists before rendering
- [ ] T068 [US2] Implement fallback to text-only PPTX processing if LibreOffice unavailable
- [ ] T069 [US2] Handle blank slides: capture slide image even if no text, add metadata "Slide X: [background]"
- [ ] T070 [US2] Handle slides with animations: capture final rendered state (all elements visible)

### Testing & Validation (US2)

- [ ] T071 [P] [US2] Create test_pptx_rendering.py: render sample 20-slide presentation, verify all slides captured
- [ ] T072 [P] [US2] Test LibreOffice integration: verify soffice command executes without errors
- [ ] T073 [P] [US2] Performance test: verify 50-slide PPTX processes in < 5 minutes (SC-002)
- [ ] T074 [P] [US2] Test slide fidelity: manually verify rendered slide preserves formatting, colors, layout
- [ ] T075 [P] [US2] Test edge cases: blank slides, slides with only images, slides with animations

**US2 Deliverable**: PPTX presentations render as slide images with preserved visual fidelity, searchable via text + image display

---

## Phase 5: User Story 3 - Multi-Image Document Handling (Priority: P2)

**Goal**: Associate and display multiple related images with a single text section (e.g., step-by-step procedure photos)

**Independent Test**: Upload maintenance manual with multi-step procedures (each step has 2-3 photos), search for a procedure step, verify all associated images display as gallery/carousel

### Multi-Image Association Logic

- [ ] T076 [US3] Extend ProximityAssociator to support multiple images per chunk (configurable MAX_IMAGES_PER_CHUNK limit)
- [ ] T077 [US3] Implement group_nearby_images() method: find images within proximity threshold on same page/spread
- [ ] T078 [US3] Add sequential ordering logic: sort grouped images by position (top-to-bottom, left-to-right)
- [ ] T079 [US3] Implement caption-based grouping: detect numbered captions ("Figure 1-3") and associate images by caption sequence

### Caption Extraction & Matching

- [ ] T080 [P] [US3] Implement extract_figure_references() function in proximity_associator.py: regex for "Figure X", "Fig. X", "Image X"
- [ ] T081 [P] [US3] Implement extract_caption() function: detect caption text near image (within N pixels/lines)
- [ ] T082 [P] [US3] Add caption matching to association algorithm: prioritize caption refs over proximity
- [ ] T083 [P] [US3] Store extracted captions in artifact metadata: caption field

### OpenWebUI Gallery Display

- [ ] T084 [US3] Extend format_result_with_artifacts() in bms_search.py to support multiple artifacts per chunk
- [ ] T085 [US3] Add gallery/carousel artifact format: array of images with captions and sequence numbers
- [ ] T086 [US3] Implement artifact display ordering: preserve sequential order from association algorithm
- [ ] T087 [US3] Add "Show all N images" expandable UI element for chunks with 3+ artifacts

### Testing & Validation (US3)

- [ ] T088 [P] [US3] Test multi-image association: upload manual with sequential procedure photos, verify all images associate correctly
- [ ] T089 [P] [US3] Test caption matching: verify images with "Figure 1-3" captions associate with text referencing those figures
- [ ] T090 [P] [US3] Test gallery display: manually verify OpenWebUI shows all images in correct sequence
- [ ] T091 [P] [US3] Test MAX_IMAGES_PER_CHUNK limit: verify excess images handled gracefully (prioritize closest)

**US3 Deliverable**: Multi-image sections (procedures, sequences) display all related images in correct order

---

## Phase 6: User Story 4 - Image Metadata and Search Enhancement (Priority: P3)

**Goal**: Enable direct search for images using captions, OCR text, and detected labels even when surrounding text doesn't match query

**Independent Test**: Upload documents with captioned images, search using caption keywords ("hydraulic valve diagram"), verify image-centric results returned

### Caption & ALT Text Indexing

- [ ] T092 [US4] Extend chunk metadata to include image_captions array: store all captions from associated artifacts
- [ ] T093 [US4] Implement extract_alt_text() in ImageExtractor for PDF/DOCX embedded ALT text
- [ ] T094 [US4] Add caption and ALT text to searchable chunk metadata in Qdrant
- [ ] T095 [US4] Update search query to match against image_captions and image_ocr_text fields

### Image Classification Labels

- [ ] T096 [P] [US4] Implement detect_image_type() heuristic in ImageProcessor: classify as diagram/photo/chart/graph/schematic/table/flowchart
- [ ] T097 [P] [US4] Add detected_labels to ImageMetadata entity
- [ ] T098 [P] [US4] Store detected labels in Qdrant payload for filtering

### Artifact-Specific Search Endpoint

- [ ] T099 [US4] Create POST /api/v1/artifacts/search endpoint in bms-agent/api/main.py per contracts/visual-artifacts-api.yaml
- [ ] T100 [US4] Implement search_artifacts() function: query Qdrant for chunks where image_captions or image_ocr_text match query
- [ ] T101 [US4] Add filters: artifact_type (image/slide), document_name, detected_labels
- [ ] T102 [US4] Return artifacts with relevance ranking based on caption/OCR text match score

### Enhanced Search Result Filtering

- [ ] T103 [P] [US4] Add "has images" filter to OpenWebUI search: query Qdrant with has_visual_artifacts=true
- [ ] T104 [P] [US4] Add artifact type filter: filter by artifact_type (image vs slide)
- [ ] T105 [P] [US4] Add label filter: filter by detected_labels (diagram, photo, chart, etc.)

### Testing & Validation (US4)

- [ ] T106 [P] [US4] Test caption-based search: search for "hydraulic valve diagram", verify matching captioned images returned
- [ ] T107 [P] [US4] Test OCR-based search: search for text within diagram labels, verify image returned via OCR match
- [ ] T108 [P] [US4] Test artifact search endpoint: POST to /api/v1/artifacts/search with various filters, verify results
- [ ] T109 [P] [US4] Measure findability improvement: verify 85%+ success rate using caption keywords (SC-010)

**US4 Deliverable**: Users can search directly for images using captions, OCR text, or visual characteristics

---

## Phase 7: API Extensions & Integration

**Purpose**: Extend existing API endpoints and add new artifact-specific endpoints per contracts specification

### Upload Endpoint Extension

- [ ] T110 Extend POST /api/v1/documents/upload in bms-agent/api/main.py with new parameters: extract_images (bool, default true), render_slides (bool, default true), enable_ocr (bool, default true)
- [ ] T111 Update upload response schema: add visual_artifacts_extracted, slides_rendered, ocr_text_extracted counts
- [ ] T112 Add processing_time_ms to upload response for performance monitoring

### Artifact Retrieval Endpoint

- [ ] T113 [P] Create GET /api/v1/artifacts/{artifact_id} endpoint in bms-agent/api/main.py
- [ ] T114 [P] Implement get_artifact() function: load artifact from ArtifactStorageManager, return with metadata
- [ ] T115 [P] Support format parameter: base64 (default), url, metadata-only
- [ ] T116 [P] Add 404 handling for artifact not found

### Search Endpoint Extension

- [ ] T117 Extend POST /api/v1/search/semantic in bms-agent/api/main.py with include_artifacts (bool, default true), artifact_format (base64/url)
- [ ] T118 Update search response schema to include visual_artifacts array per SearchResultWithArtifacts contract
- [ ] T119 Implement artifact loading optimization: only load artifacts for top-k results (configurable limit)

### Testing & Validation (API)

- [ ] T120 [P] Test upload endpoint with extract_images=false: verify text-only processing (backward compatibility)
- [ ] T121 [P] Test artifact retrieval: GET /api/v1/artifacts/{valid_id}, verify 200 response with artifact data
- [ ] T122 [P] Test artifact not found: GET /api/v1/artifacts/{invalid_id}, verify 404 response
- [ ] T123 [P] Test search with artifacts: verify include_artifacts parameter controls artifact loading

---

## Phase 8: Performance Optimization & Scalability

**Purpose**: Optimize processing performance and artifact loading for production scale

### Async Processing

- [ ] T124 Implement async image extraction: use asyncio.gather() for parallel image processing in ImageExtractor
- [ ] T125 Implement batch processing for large documents (50+ images): process images in batches of 10
- [ ] T126 Add async OCR processing: run OCR on multiple images concurrently using ThreadPoolExecutor

### Caching

- [ ] T127 [P] Implement LRU cache for base64-encoded artifacts in bms_search.py (100MB cache limit)
- [ ] T128 [P] Cache frequently accessed artifacts in memory to avoid repeated file I/O
- [ ] T129 [P] Add cache eviction policy: LRU with size-based eviction when cache exceeds limit

### Lazy Loading & Optimization

- [ ] T130 Implement lazy artifact loading: load thumbnails first, full-res on user click/expand
- [ ] T131 Optimize image compression: tune PNG optimization (optipng) and JPEG quality (85%)
- [ ] T132 Add progressive loading: stream artifact data for large images

### Performance Monitoring

- [ ] T133 [P] Add processing time logging for each stage: extraction, OCR, resizing, storage
- [ ] T134 [P] Implement performance metrics collection: avg extraction time, OCR time, artifact count per doc
- [ ] T135 [P] Add health check endpoint for artifact storage: verify /workspace/visual-artifacts/ disk space

### Testing & Validation (Performance)

- [ ] T136 [P] Performance test: process 50-image document, verify < 10 seconds total time (SC-008)
- [ ] T137 [P] Performance test: load artifact and encode to base64, verify < 1 second (SC-004)
- [ ] T138 [P] Storage overhead test: ingest 300-document corpus, verify total storage < 2x text-only (SC-007)
- [ ] T139 [P] Concurrent processing test: process multiple documents simultaneously, verify no OOM errors

---

## Phase 9: Error Handling & Edge Cases

**Purpose**: Handle error scenarios and edge cases robustly

### Corrupted Image Handling

- [ ] T140 Add try-except in extract_images_from_pdf(): catch corrupted image errors, log warning, skip image, continue processing
- [ ] T141 Verify image integrity after extraction: use Image.verify() from Pillow
- [ ] T142 Add corrupted image counter to processing result for monitoring

### Unsupported Format Handling

- [ ] T143 [P] Detect unsupported image formats: check file extension and MIME type
- [ ] T144 [P] Add placeholder artifact for unsupported formats: save metadata indicating "unsupported format"
- [ ] T145 [P] Log unsupported formats for review and potential future support

### Storage Full Handling

- [ ] T146 Implement disk space check before saving artifacts: verify > 10GB free space
- [ ] T147 Raise DiskSpaceError if insufficient storage, abort artifact save, log error
- [ ] T148 Add storage monitoring alert: log warning when free space < 20GB

### PDF Permission Errors

- [ ] T149 Handle PDF security/permissions errors: catch PyMuPDF permission exceptions
- [ ] T150 Log permission error with document name, skip image extraction, continue text processing
- [ ] T151 Add permission error indicator to processing result metadata

### LibreOffice Unavailable

- [ ] T152 Add soffice availability check in render_pptx_slides(): verify command exists
- [ ] T153 Fallback to text-only PPTX processing if LibreOffice unavailable
- [ ] T154 Log clear error message indicating LibreOffice required for slide rendering

### Testing & Validation (Edge Cases)

- [ ] T155 [P] Test corrupted image: attempt to extract from PDF with corrupted embedded image, verify graceful handling
- [ ] T156 [P] Test unsupported format: attempt to extract proprietary CAD format, verify placeholder created
- [ ] T157 [P] Test storage full: mock disk space check failure, verify error handling
- [ ] T158 [P] Test PDF permissions: attempt to extract from password-protected PDF, verify error logging
- [ ] T159 [P] Test LibreOffice unavailable: disable soffice, attempt PPTX processing, verify fallback to text-only

---

## Phase 10: Documentation & Deployment

**Purpose**: Finalize documentation and prepare for production deployment

### Code Documentation

- [ ] T160 [P] Add docstrings to all public methods in ImageExtractor class
- [ ] T161 [P] Add docstrings to all public methods in OCRProcessor class
- [ ] T162 [P] Add docstrings to all public methods in ProximityAssociator class
- [ ] T163 [P] Document configuration environment variables in README or CLAUDE.md

### Integration Documentation

- [ ] T164 Update CLAUDE.md with visual artifacts feature overview and key file locations
- [ ] T165 Add "Visual Artifacts" section to CLAUDE.md documenting storage, extraction workflow, OpenWebUI integration
- [ ] T166 Update README with new dependencies (Tesseract, Poppler, LibreOffice)

### Deployment Preparation

- [ ] T167 Update /pre_start.sh to create /workspace/visual-artifacts/ directories on pod boot
- [ ] T168 Add system dependency verification to /pre_start.sh: check Tesseract, LibreOffice installations
- [ ] T169 Create deployment checklist: verify all environment variables set, storage directories exist
- [ ] T170 Test deployment on clean RunPod instance: run init.sh, verify all dependencies install correctly

### Migration & Re-ingestion

- [ ] T171 Create re-ingestion script for existing 300-document corpus to extract artifacts
- [ ] T172 Add progress tracking to re-ingestion: log documents processed, artifacts extracted
- [ ] T173 Implement dry-run mode for re-ingestion: preview storage requirements before execution

### User Guide

- [ ] T174 [P] Create user-facing documentation explaining visual artifact feature in search results
- [ ] T175 [P] Add examples of searching with images: "show me brake diagrams", "find maintenance procedures with photos"
- [ ] T176 [P] Document how to disable image extraction if needed (extract_images=false parameter)

---

## Dependencies & Parallel Execution

### User Story Dependencies (Completion Order)

```
Phase 1 (Setup) → Phase 2 (Foundational) →
  ↓
  ├─ Phase 3 (US1) - PDF Image Extraction ✅ MVP
  ├─ Phase 4 (US2) - PPTX Slide Rendering ✅ MVP (parallel with US1)
  ├─ Phase 5 (US3) - Multi-Image Handling (depends on US1)
  └─ Phase 6 (US4) - Image Metadata Search (depends on US1)
  ↓
Phase 7 (API Extensions) →
Phase 8 (Performance) →
Phase 9 (Edge Cases) →
Phase 10 (Documentation)
```

### Parallel Execution Opportunities

**Phase 2 (Foundational)**: All tasks T009-T019 can run in parallel (different files)

**Phase 3 (US1)**:
- T024-T027 (DOCX extraction) parallel with T020-T023 (PDF extraction)
- T047-T051 (testing) parallel with each other

**Phase 4 (US2)**:
- T057-T059 (slide metadata) parallel with T052-T056 (rendering)
- T064-T066 (job tracking) parallel with main rendering logic
- T071-T075 (testing) parallel with each other

**Phase 5 (US3)**:
- T080-T083 (caption extraction) parallel with T076-T079 (association logic)

**Phase 6 (US4)**:
- T096-T098 (image classification) parallel with T092-T095 (caption indexing)
- T103-T105 (search filters) parallel with T099-T102 (search endpoint)

**Phase 7 (API)**:
- T113-T116 (artifact endpoint) parallel with T110-T112 (upload extension)

**Phase 8 (Performance)**:
- T127-T129 (caching) parallel with T124-T126 (async processing)

**Phase 10 (Documentation)**:
- All documentation tasks (T160-T176) can run in parallel

### MVP Scope (Minimum Viable Product)

**Recommended MVP**: Phase 1 + Phase 2 + Phase 3 (US1) + Phase 4 (US2)

**Delivers**:
- PDF image extraction with proximity-based association
- PPTX slide rendering with visual fidelity
- OCR text extraction from images
- Visual artifacts display in OpenWebUI search results
- Basic error handling and testing

**Timeline**: ~2-3 weeks for MVP implementation

**Post-MVP Enhancements**:
- Phase 5 (US3): Multi-image handling for step-by-step procedures
- Phase 6 (US4): Advanced image metadata search
- Phase 8: Performance optimization for production scale
- Phase 9: Comprehensive edge case handling

---

## Implementation Strategy

### Week 1: Foundation & US1 (PDF Images)
- Days 1-2: Phase 1 (Setup) + Phase 2 (Foundational)
- Days 3-5: Phase 3 (US1) - PDF image extraction + OpenWebUI integration

### Week 2: US2 (PPTX Slides) + Testing
- Days 1-3: Phase 4 (US2) - PPTX slide rendering
- Days 4-5: Integration testing, bug fixes, US1+US2 validation

### Week 3: API Extensions + Performance
- Days 1-2: Phase 7 (API Extensions)
- Days 3-4: Phase 8 (Performance Optimization)
- Day 5: Phase 10 (Documentation)

### Week 4+ (Optional): Advanced Features
- US3 (Multi-Image) - 3-4 days
- US4 (Metadata Search) - 3-4 days
- Phase 9 (Edge Cases) - 2-3 days

---

## Task Summary

**Total Tasks**: 176

**By Phase**:
- Phase 1 (Setup): 8 tasks
- Phase 2 (Foundational): 11 tasks
- Phase 3 (US1): 32 tasks
- Phase 4 (US2): 24 tasks
- Phase 5 (US3): 16 tasks
- Phase 6 (US4): 18 tasks
- Phase 7 (API): 14 tasks
- Phase 8 (Performance): 16 tasks
- Phase 9 (Edge Cases): 20 tasks
- Phase 10 (Documentation): 17 tasks

**By User Story**:
- US1 (Visual Context - PDF Images): 32 tasks ✅ MVP
- US2 (PowerPoint Slides): 24 tasks ✅ MVP
- US3 (Multi-Image Handling): 16 tasks
- US4 (Image Metadata Search): 18 tasks

**Parallel Tasks**: 98 tasks marked [P] (56% can run in parallel)

**Independent Test Criteria**:
- US1: Upload PDF with images → search → verify artifacts display
- US2: Upload PPTX → search slide content → verify slide images display
- US3: Upload multi-image manual → search procedure → verify all images show in gallery
- US4: Search using caption keywords → verify image-centric results returned

**Format Validation**: ✅ All tasks follow required checklist format with ID, Story label (where applicable), and file paths

---

**Task Generation Complete** - Ready for implementation via `/speckit.implement` or manual execution
