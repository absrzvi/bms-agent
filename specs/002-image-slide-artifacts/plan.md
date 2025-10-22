# Implementation Plan: Image and Slide Visual Artifacts for RAG Search

**Branch**: `002-image-slide-artifacts` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-image-slide-artifacts/spec.md`

## Summary

Extend the BMS Agent RAG system to extract images from PDF/DOCX documents and render PowerPoint slides as static images, storing them as visual artifacts that display alongside text search results in OpenWebUI. The feature enhances user comprehension of technical railway documentation by providing visual context (diagrams, schematics, photos, slide layouts) with semantic search results.

**Core Technical Approach**:
- **Image Extraction**: PyMuPDF (fitz) for PDF, python-docx for DOCX embedded image extraction
- **Slide Rendering**: LibreOffice headless + pdf2image for high-fidelity PPTX-to-PNG conversion
- **OCR Integration**: Tesseract OCR for text extraction from images and diagrams
- **Storage Strategy**: File system storage in `/workspace/visual-artifacts/` with metadata references in Qdrant
- **Association Algorithm**: Proximity-based image-chunk linking using page coordinates and caption matching
- **OpenWebUI Integration**: Base64-encoded artifacts with metadata wrapper for inline display

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- **Existing**: PyMuPDF (`fitz`), python-docx, Pillow (PIL) - already installed
- **New**: pytesseract (≥0.3.10), pdf2image (≥1.16.3)
- **System**: Tesseract OCR, Poppler utilities, LibreOffice headless
- **Framework**: FastAPI (existing), Qdrant client (existing)

**Storage**:
- **File System**: `/workspace/visual-artifacts/` for image/slide files (persistent on RunPod)
- **Vector Database**: Qdrant payload extension for artifact metadata references
- **Estimated Size**: ~10MB per document with 20 images, 3.6GB for 300-document corpus

**Testing**: pytest for unit/integration tests, manual OpenWebUI verification

**Target Platform**: Linux server (Ubuntu/Debian), RunPod POD environment with persistent `/workspace` storage

**Project Type**: Web (backend API extension + OpenWebUI integration)

**Performance Goals**:
- Image extraction: ~50-100ms per page
- PPTX rendering: < 5 minutes for 20-50 slides (SC-002)
- Image load time: < 1 second for 90% of artifacts (SC-004)
- OCR processing: ~200-500ms per image

**Constraints**:
- Storage: < 2x overhead vs. text-only (SC-007)
- Memory: Image processing without OOM for documents with 50+ images (SC-008)
- Accuracy: 95%+ image extraction success rate (SC-003)
- Display: 99%+ artifact rendering in OpenWebUI without issues (SC-006)

**Scale/Scope**:
- 300+ railway documents (existing corpus)
- Average 20 images per document → ~6,000 total artifacts
- Max 50 images per document edge case
- Support PDF, DOCX, PPTX formats

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: N/A - No project constitution exists

**Recommendation**: Consider establishing (for future governance):
1. **Storage Quotas**: Define max artifacts per document, total storage limits
2. **Performance Baselines**: Enforce latency/throughput targets for image processing
3. **Quality Standards**: Minimum OCR confidence, image resolution requirements
4. **Backward Compatibility**: Ensure new features don't break existing text-only workflows

## Project Structure

### Documentation (this feature)

```text
specs/002-image-slide-artifacts/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (current)
├── research.md          # Phase 0 output (technology decisions and best practices)
├── data-model.md        # Phase 1 output (visual artifact entities and schemas)
├── quickstart.md        # Phase 1 output (developer setup guide)
├── contracts/           # Phase 1 output (API extensions)
│   └── visual-artifacts-api.yaml
├── checklists/          # Quality validation
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

**Existing Structure Extended**:

```text
bms-agent/
├── bms-agent/                      # Main package
│   ├── api/
│   │   ├── main.py                 # FastAPI app (extend upload endpoint)
│   │   └── processor_wrapper.py   # Add artifact processing orchestration
│   ├── scr/                        # Core processing modules
│   │   ├── enhanced_document_processor.py    # EXTEND: Add image extraction workflow
│   │   ├── image_extractor.py                # NEW: Image/slide extraction module
│   │   ├── artifact_storage.py               # NEW: File system storage manager
│   │   ├── ocr_processor.py                  # NEW: Tesseract OCR wrapper
│   │   ├── proximity_associator.py           # NEW: Image-chunk association logic
│   │   ├── qdrant_schema_v4.py               # EXTEND: Add artifact metadata fields
│   │   └── chapter_extractor.py              # Existing (unchanged)
│   └── tests/
│       ├── test_image_extraction.py          # NEW: Image extraction unit tests
│       ├── test_slide_rendering.py           # NEW: PPTX rendering tests
│       ├── test_ocr.py                       # NEW: OCR accuracy tests
│       ├── integration/
│       │   └── test_artifacts_end_to_end.py  # NEW: Full pipeline test
│       └── performance/
│           └── test_artifact_performance.py  # NEW: Processing time tests
├── upload-files/                   # Existing document storage (21 departments)
├── bms_search.py                   # EXTEND: Add artifact display in OpenWebUI tool
├── ingest_documents_to_qdrant.py   # EXTEND: Support artifact extraction
├── batch_ingest_by_department.py   # EXTEND: Batch processing with artifacts
└── requirements.txt                # ADD: pytesseract, pdf2image

# NEW: Visual artifacts storage (persistent)
/workspace/visual-artifacts/
├── images/                         # Extracted PDF/DOCX images
│   └── doc_{document_id}/
│       └── page_{num}_img_{idx}.{format}
├── slides/                         # Rendered PPTX slides
│   └── pres_{presentation_id}/
│       └── slide_{num}.png
└── thumbnails/                     # Compressed previews
    └── thumb_{artifact_id}.jpg
```

**Structure Decision**: Extend existing web application structure with new modules for image/slide processing while preserving backward compatibility with text-only workflows.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations to track (no active constitution). This section reserved for future governance compliance.

## Phase 0: Research & Technical Decisions

**Objective**: Resolve technology choices and document best practices for image extraction, slide rendering, and OCR.

### Research Topics Resolved (See research.md)

1. **PDF Image Extraction**: PyMuPDF (fitz) primary, pdf2image fallback
2. **DOCX Image Extraction**: python-docx with _rels inspection
3. **PPTX Slide Rendering**: LibreOffice headless + pdf2image (production), python-pptx fallback
4. **OCR Engine**: Tesseract OCR via pytesseract
5. **Image Storage**: File system (`/workspace/visual-artifacts/`) with Qdrant metadata refs
6. **Image-Chunk Association**: Proximity algorithm + caption matching
7. **OpenWebUI Integration**: Base64 encoding with structured metadata
8. **Image Optimization**: Pillow for resize (max 1920x1080), format conversion

**Output**: See `research.md` for detailed findings and implementation patterns

## Phase 1: Design Artifacts

### Data Model

**Objective**: Define entity schemas for visual artifacts and extended chunk metadata.

**Entities Defined** (See data-model.md):
1. **Visual Artifact**: Core entity for extracted images and rendered slides
2. **Enhanced Chunk**: Extension of existing Chunk with artifact references
3. **Image Metadata**: OCR text, captions, detected labels
4. **Slide Render Job**: Processing status tracking for PPTX rendering

**Qdrant Payload Extension**:
- `has_visual_artifacts` (boolean, indexed)
- `visual_artifact_ids` (array[string])
- `visual_artifact_count` (integer, indexed)
- `image_ocr_text` (string, searchable)
- `image_captions` (array[string], searchable)

**Output**: See `data-model.md` for complete schemas and validation rules

### API Contracts

**Objective**: Extend existing API endpoints and define new artifact-specific endpoints.

**Endpoints Extended/Added** (See contracts/visual-artifacts-api.yaml):
1. **POST /api/v1/documents/upload** - Extended with `extract_images`, `render_slides`, `enable_ocr` parameters
2. **GET /api/v1/artifacts/{artifact_id}** - NEW: Retrieve specific artifact
3. **POST /api/v1/artifacts/search** - NEW: Search artifacts by caption/OCR/labels
4. **POST /api/v1/search/semantic** - Extended with `include_artifacts`, `artifact_format` parameters

**OpenWebUI Tool Updates**:
- Modify search result formatting to include base64 artifacts
- Add artifact carousel/gallery display for multi-image chunks

**Output**: See `contracts/visual-artifacts-api.yaml` for OpenAPI specification

### Quickstart Guide

**Objective**: Provide step-by-step developer onboarding for local testing.

**Contents** (See quickstart.md):
1. **Prerequisites**: System packages (Tesseract, Poppler, LibreOffice)
2. **Installation**: Python dependencies, storage directory setup
3. **First Run**: Test image extraction, slide rendering, OCR
4. **Integration Test**: End-to-end document processing with Qdrant verification
5. **OpenWebUI Test**: Verify artifact display in search results
6. **Troubleshooting**: Common issues (OCR not found, LibreOffice missing, images not displaying)

**Output**: See `quickstart.md`

## Phase 2: Implementation Roadmap (Task Generation)

**Note**: Detailed task breakdown generated by `/speckit.tasks` command after planning completes.

**High-Level Implementation Phases**:

### Phase 2.1: Core Image Extraction (P1 - MVP Foundation)
- Implement `ImageExtractor` class for PDF, DOCX, PPTX
- PyMuPDF integration for PDF embedded image extraction
- python-docx integration for DOCX inline/floating images
- LibreOffice + pdf2image pipeline for PPTX slide rendering
- File system storage manager for `/workspace/visual-artifacts/`
- Unit tests for each extraction method

### Phase 2.2: OCR Integration (P1 - Search Enhancement)
- Tesseract OCR wrapper (`OCRProcessor` class)
- Image preprocessing for better OCR accuracy (binarization, contrast)
- Caption and ALT text extraction from source documents
- OCR text indexing in chunk metadata
- OCR accuracy tests with sample diagrams

### Phase 2.3: Image-Chunk Association (P1 - Core Linking Logic)
- Proximity-based association algorithm
- Bounding box distance calculation for PDF images
- Caption matching (e.g., "Figure 3" reference detection)
- Multi-image grouping for P2 scenarios
- Association accuracy validation tests

### Phase 2.4: Enhanced Document Processor Integration (P1 - Pipeline Extension)
- Extend `EnhancedDocumentProcessor` with artifact extraction workflow
- Add artifact metadata to Qdrant chunk payloads
- Update `processor_wrapper.py` orchestration
- Backward compatibility for documents without images
- End-to-end integration tests

### Phase 2.5: OpenWebUI Tool Updates (P1 - User Interface)
- Update `bms_search.py` to load and format artifacts
- Base64 encoding for inline display
- Thumbnail optimization for fast loading
- Artifact carousel/gallery for multi-image chunks
- Manual OpenWebUI testing with real documents

### Phase 2.6: Multi-Image Handling (P2 - Enhanced UX)
- Extend association algorithm for sequential image grouping
- Gallery artifact format for OpenWebUI
- Caption-based ordering (Figure 1, Figure 2, Figure 3)
- Configurable `MAX_IMAGES_PER_CHUNK` limit
- Test with maintenance manuals (step-by-step procedures)

### Phase 2.7: Image Metadata Search (P3 - Advanced Discovery)
- Implement `/api/v1/artifacts/search` endpoint
- Caption-based search (match caption text directly)
- Detected label classification (diagram, photo, chart)
- OCR-only search (find images by text within them)
- Search result ranking by relevance

### Phase 2.8: Performance Optimization (All Phases)
- Async image processing (parallel extraction)
- Image caching (LRU cache for base64-encoded artifacts)
- Lazy artifact loading (thumbnails first, full-res on demand)
- Batch processing for large documents (50+ images)
- Storage compression (PNG optimization, JPEG quality tuning)

### Phase 2.9: Testing & Validation (All Phases)
- Unit tests: image extraction, OCR, slide rendering
- Integration tests: end-to-end document processing with artifacts
- Performance tests: processing time (SC-002), load time (SC-004)
- Edge case tests: corrupted images, unsupported formats, blank slides
- OpenWebUI manual testing: artifact display, full-res view

## Implementation Notes

### Technology Choices Rationale

**PyMuPDF vs pdf2image**:
- **Chosen**: PyMuPDF (primary)
- **Rationale**: 10x faster, extracts images directly from PDF structure, already installed in BMS Agent

**LibreOffice Headless vs python-pptx Manual Rendering**:
- **Chosen**: LibreOffice headless
- **Rationale**: High-fidelity slide rendering, preserves all PowerPoint formatting, stable production solution

**File System Storage vs Base64 in Qdrant**:
- **Chosen**: File system
- **Rationale**: Avoids bloating vector database, scalable to 1000s of images, supports lazy loading

**Tesseract OCR vs Cloud OCR APIs**:
- **Chosen**: Tesseract (local)
- **Rationale**: No API costs, no latency, no internet dependency, sufficient accuracy (70-95%)

### Integration with Existing System

**Minimal Changes Required**:
- **EnhancedDocumentProcessor**: Add `_extract_visual_artifacts()` method, extend chunking workflow
- **Qdrant Payload**: Add 5 new optional fields (backward compatible)
- **OpenWebUI Tool**: Extend search result formatter with artifact display

**Backward Compatibility**:
- Existing text-only workflows continue unchanged
- New `extract_images=false` parameter to disable artifacts
- Chunks without images simply have `has_visual_artifacts=false`

### Deployment Strategy

**Phase 1: Development/Testing** (Feature Branch):
- Develop and test on local/dev RunPod instance
- Verify with small document subset (5-10 docs)

**Phase 2: Staging Validation**:
- Deploy to staging environment
- Batch ingest full 300-document corpus
- Validate storage overhead < 2x (SC-007)
- Performance testing at scale

**Phase 3: Production Rollout**:
- Deploy to production RunPod
- Re-ingest existing documents to extract artifacts
- Monitor OpenWebUI for artifact display issues
- Collect user feedback on visual context value

### Risk Mitigation

**High-Risk Areas**:

1. **LibreOffice Unavailable** (Slide Rendering Failure)
   - **Mitigation**: Fallback to text-only PPTX processing, clear error logging
   - **Detection**: Health check endpoint verifies LibreOffice installation

2. **Storage Overflow** (Too Many Images)
   - **Mitigation**: Configurable max images per doc, compression, monitoring
   - **Detection**: Pre-flight disk space check before saving artifacts

3. **OCR Low Accuracy** (Poor Image Quality)
   - **Mitigation**: Image preprocessing (contrast, binarization), log low-confidence results
   - **Acceptance**: 70%+ accuracy acceptable (per assumptions)

4. **Performance Degradation** (Large PPTX Files)
   - **Mitigation**: Async processing, timeout handling, slide count limits
   - **Testing**: Performance tests with 100-slide presentations

**Medium-Risk Areas**:

1. **OpenWebUI Artifact Display Issues**
   - **Mitigation**: Contract tests, manual testing, multiple browser verification

2. **Image-Chunk Association Errors**
   - **Mitigation**: Caption fallback, proximity threshold tuning, manual review logs

3. **Corrupted Image Extraction**
   - **Mitigation**: Try-catch error handling, skip corrupted images, continue processing

## Dependencies & Prerequisites

### System Dependencies (RunPod Installation)

```bash
# Tesseract OCR
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Poppler utilities (for pdf2image)
apt-get install -y poppler-utils

# LibreOffice (for PPTX rendering)
apt-get install -y libreoffice-core libreoffice-impress

# Optional: Image optimization tools
apt-get install -y optipng pngquant
```

### Python Dependencies (requirements.txt)

**New Packages**:
```
pytesseract>=0.3.10
pdf2image>=1.16.3
# Pillow already installed (≥10.0.0)
```

**Existing Packages** (no changes):
- PyMuPDF, python-docx, python-pptx (already installed)
- FastAPI, Qdrant client, sentence-transformers (existing)

### Environment Variables

**New Configuration**:
```bash
VISUAL_ARTIFACTS_DIR=/workspace/visual-artifacts
MAX_IMAGE_WIDTH=1920
MAX_IMAGE_HEIGHT=1080
MAX_IMAGES_PER_CHUNK=5
ENABLE_OCR=true
OCR_LANGUAGE=eng
PPTX_RENDER_DPI=150
PPTX_RENDER_ENGINE=libreoffice  # or 'manual'
IMAGE_PROCESSING_WORKERS=4
ARTIFACT_CACHE_SIZE_MB=100
```

### Storage Requirements

- **Minimum**: 10GB for `/workspace/visual-artifacts/`
- **Recommended**: 20GB for 300-document corpus with headroom
- **Monitoring**: Alert if free space < 10GB

## Success Criteria Verification

**How to validate each success criterion**:

- **SC-001** (80%+ queries with visuals get artifacts): Integration test with query log analysis
- **SC-002** (< 5min for 20-50 slide PPTX): Performance test with timer wrapper
- **SC-003** (95%+ extraction success): Unit test pass rate on sample documents
- **SC-004** (< 1s image load time): Performance test with base64 encoding timer
- **SC-005** (15-25% OCR recall improvement): A/B test search with/without OCR text
- **SC-006** (99%+ OpenWebUI display): Manual testing across browsers + automated screenshot tests
- **SC-007** (< 2x storage overhead): Monitor `/workspace/visual-artifacts/` size vs text data
- **SC-008** (Handle 50+ images/doc): Stress test with photo-heavy manual
- **SC-009** (Filter results by images): Query Qdrant with `has_visual_artifacts=true` filter
- **SC-010** (85%+ caption findability): Test search using caption keywords from ground truth

## Next Steps

**After `/speckit.plan` completes**:

1. **Review Phase 0 Research** (`research.md`)
   - Validate technology choices (PyMuPDF, LibreOffice, Tesseract)
   - Confirm implementation patterns

2. **Review Phase 1 Design** (`data-model.md`, `contracts/`, `quickstart.md`)
   - Validate Visual Artifact entity schema
   - Review API contract extensions
   - Test quickstart guide for accuracy

3. **Run `/speckit.tasks`** to generate detailed implementation tasks
   - Break down roadmap into atomic tasks with priorities
   - Assign dependencies and effort estimates
   - Create actionable task list in `tasks.md`

4. **Begin Implementation** with `/speckit.implement`
   - Execute tasks in dependency order
   - Track progress and completion
   - Validate against success criteria

**Estimated Timeline** (new development only):
- Phase 0 (Research): COMPLETE (documented)
- Phase 1 (Design): COMPLETE (artifacts generated)
- Phase 2.1-2.3 (P1 Core): 1-2 weeks
- Phase 2.4-2.5 (P1 Integration): 1 week
- Phase 2.6 (P2 Multi-Image): 3-4 days
- Phase 2.7 (P3 Metadata Search): 3-4 days
- Phase 2.8-2.9 (Optimization & Testing): 1 week
- **Total**: 3-4 weeks for complete implementation

**Dependencies on Feature 001**:
- Requires operational BMS Agent RAG system (already deployed)
- Extends `EnhancedDocumentProcessor` (existing and stable)
- Uses existing Qdrant collection schema (minimal extension)

---

**Planning Complete** - Ready for task generation and implementation. The design preserves backward compatibility while adding powerful visual context to search results.
