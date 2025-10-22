# Feature Specification: Image and Slide Visual Artifacts for RAG Search

**Feature Branch**: `002-image-slide-artifacts`
**Created**: 2025-10-22
**Status**: Draft
**Input**: User description: "in my RAG ingestion pipeline (enhanced-document-processor) i want to add the ingestion of any pictures and all pptx slides to be captured as pictures that are shown as the openwebui artifact when the relevant chunk is queried"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visual Context for Technical Documentation Search (Priority: P1)

Railway engineers searching for technical information need to see relevant diagrams, schematics, and visual content alongside text results to fully understand technical procedures and specifications.

**Why this priority**: Core value proposition - technical documentation relies heavily on visual aids (circuit diagrams, safety schematics, procedural flowcharts). Text-only search results are often incomplete without the associated images.

**Independent Test**: Can be fully tested by uploading a PDF containing images, searching for related text, and verifying that relevant images appear as visual artifacts in OpenWebUI search results.

**Acceptance Scenarios**:

1. **Given** a PDF railway manual contains embedded diagrams, **When** a user searches for "brake system schematic", **Then** the search result displays the text chunk AND shows the related brake system diagram as a visual artifact in OpenWebUI
2. **Given** a document has multiple images on different pages, **When** search matches a text chunk near an image, **Then** the system associates and displays the closest/most relevant image with that chunk
3. **Given** an image has no nearby text context, **When** OCR text from the image matches the query, **Then** the system returns the image as a visual artifact with OCR-extracted text as the chunk content
4. **Given** a user views search results with visual artifacts, **When** they click on an image artifact, **Then** they can view the full-resolution image in a modal/expanded view

---

### User Story 2 - PowerPoint Slide Preservation (Priority: P1)

Users need to retrieve PowerPoint presentation content with visual fidelity preserved, seeing each slide as it was originally formatted rather than as extracted text.

**Why this priority**: PowerPoint slides are designed as visual communication tools - extracting only text loses layout, emphasis, bullet structure, and embedded images. This is equally critical as PDF image extraction for presentation-based documentation.

**Independent Test**: Can be tested by uploading a PPTX file with formatted slides, searching for slide content, and verifying each slide appears as a rendered image artifact.

**Acceptance Scenarios**:

1. **Given** a PPTX training presentation with 20 slides, **When** the document is ingested, **Then** each slide is captured as a separate image (PNG or JPEG format) and associated with its text chunk
2. **Given** a user searches for content that matches slide 5 of a presentation, **When** results are returned, **Then** the visual artifact shows the rendered slide 5 image preserving all formatting, colors, and layout
3. **Given** a PowerPoint slide contains both text and embedded images, **When** that slide's chunk is returned in search results, **Then** the slide image artifact shows the complete slide as it would appear in PowerPoint
4. **Given** a presentation has slides with minimal text (mostly images/charts), **When** those slides are ingested, **Then** the system uses OCR or image description to create searchable text while preserving the slide image as artifact

---

### User Story 3 - Multi-Image Document Handling (Priority: P2)

Users working with documents containing multiple related images (e.g., step-by-step procedures with photos) need to see all relevant images for a given text section.

**Why this priority**: Enhances user experience for procedural documentation but system can function with single-image association (P1). This handles complex multi-image scenarios common in maintenance manuals.

**Independent Test**: Upload a maintenance manual with multi-step procedures (each step has 2-3 photos), search for a procedure step, verify all associated images are displayed.

**Acceptance Scenarios**:

1. **Given** a maintenance manual section has 3 sequential images showing assembly steps, **When** search matches that section's text, **Then** all 3 images are returned as a gallery/carousel artifact in the correct sequence
2. **Given** images are numbered or captioned (e.g., "Figure 1-3: Assembly Process"), **When** text references these figures, **Then** the system associates the correctly numbered images with the text chunk
3. **Given** a document has images on facing pages or within the same 2-page spread, **When** text from that spread matches a query, **Then** the system groups those images together in the visual artifact

---

### User Story 4 - Image Metadata and Search Enhancement (Priority: P3)

Users need to search for visual content directly using image descriptions, captions, or visual characteristics to find diagrams and photos even when surrounding text doesn't match their query.

**Why this priority**: Advanced feature that improves discoverability but basic image display (P1-P2) provides core value. This enables "search for circuit diagram" without knowing exact text terms.

**Independent Test**: Upload documents with captioned images, search using caption text or image descriptions, verify image-centric results are returned.

**Acceptance Scenarios**:

1. **Given** document images have captions (e.g., "Figure 3: Hydraulic Pressure Valve"), **When** user searches for "hydraulic valve diagram", **Then** the system matches the caption text and returns the image as primary result
2. **Given** images contain text/labels (e.g., technical diagrams with annotations), **When** OCR extracts this text, **Then** the image is searchable by the OCR text content
3. **Given** an image has ALT text or metadata embedded in the document, **When** ingestion occurs, **Then** this metadata is indexed and searchable

---

### Edge Cases

- What happens when an image is corrupted or unreadable during extraction?
  - System should log warning, skip the corrupted image, continue processing other images, and index the text chunk without visual artifact
- What happens when a PowerPoint slide is blank or contains only a background image?
  - System should still capture the slide as image artifact, use empty or minimal text chunk with metadata indicating "Slide X: [background description]"
- What happens when a document contains hundreds of images (e.g., photo-heavy manual)?
  - System should handle large image counts without memory issues, potentially resizing images for storage efficiency, providing thumbnail artifacts with full-res on-demand
- What happens when image file formats are unsupported (e.g., proprietary CAD formats)?
  - System should attempt standard image extraction, fall back to placeholder artifact indicating "unsupported format", log format for review
- What happens when a single chunk should be associated with multiple images but storage limits exist?
  - System should prioritize closest/most relevant images (configurable max, e.g., 5 images per chunk), store references to additional images in metadata
- What happens when PowerPoint slides have animations or transitions?
  - System should capture the final rendered state of the slide (all elements visible), ignoring animation sequences
- What happens when an image is referenced multiple times across different text chunks?
  - System should store the image once and create references from multiple chunks to avoid duplication, display same image in all relevant search results
- What happens when user searches and multiple results contain the same visual artifact?
  - System should display each result with its artifact independently (duplicates acceptable in search results), optionally group similar images
- What happens when images are embedded as base64 in HTML or CSS within documents?
  - System should decode and extract base64 images during processing, treat them as standard image artifacts
- What happens when image extraction fails due to PDF security/permissions?
  - System should log permission error, attempt OCR if possible, indicate to user that visual artifacts unavailable due to document restrictions

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract all embedded images from PDF documents during ingestion and store them as visual artifacts linked to relevant text chunks
- **FR-002**: System MUST render each PowerPoint slide as a static image (PNG or JPEG format) during PPTX ingestion, preserving layout, formatting, and embedded content
- **FR-003**: System MUST associate each extracted image or rendered slide with the nearest relevant text chunk based on document position proximity
- **FR-004**: System MUST support image formats commonly found in technical documentation (PNG, JPEG, GIF, BMP, TIFF, SVG)
- **FR-005**: System MUST store image artifacts in a persistent location accessible for retrieval when displaying search results
- **FR-006**: System MUST include visual artifact references in chunk metadata stored in the vector database
- **FR-007**: System MUST perform OCR on images containing text to create searchable content, indexing OCR output as additional chunk metadata
- **FR-008**: System MUST extract image captions, ALT text, and figure labels from source documents and index them as searchable metadata
- **FR-009**: System MUST support multiple images per text chunk when document structure indicates multiple related visuals
- **FR-010**: System MUST provide image artifacts to OpenWebUI search tool in a format compatible with artifact display (base64, URL reference, or file path)
- **FR-011**: System MUST handle large images by resizing/compressing for efficient storage while maintaining readability (configurable max dimensions, e.g., 1920x1080)
- **FR-012**: System MUST preserve original image aspect ratios during any resizing operations
- **FR-013**: System MUST log image extraction failures with sufficient detail for troubleshooting (document name, page number, error type)
- **FR-014**: System MUST track which chunks have associated visual artifacts via metadata flag for filtering search results by "has images"
- **FR-015**: System MUST extract images from DOCX documents embedded as inline graphics or floating images
- **FR-016**: System MUST handle documents with no images gracefully (continue normal text-only processing)
- **FR-017**: System MUST support configurable image storage location (file system path or cloud storage bucket)
- **FR-018**: System MUST generate unique identifiers for each extracted image to prevent naming conflicts
- **FR-019**: System MUST link extracted images back to source document and page/slide number in metadata
- **FR-020**: System MUST provide fallback behavior when image extraction libraries are unavailable (skip images, continue text processing)

### Key Entities

- **Visual Artifact**: Represents an extracted image or rendered slide with attributes: artifact_id (unique identifier), artifact_type (image/slide), source_document, source_page_or_slide_number, file_format (PNG/JPEG/etc), file_path or storage_url, file_size, dimensions (width x height), extraction_timestamp, associated_chunk_ids (list of chunks linked to this artifact)

- **Enhanced Chunk** (extends existing Chunk entity): Adds attributes: has_visual_artifacts (boolean flag), visual_artifact_ids (list of artifact_id references), image_ocr_text (OCR extracted text if applicable), image_captions (list of extracted captions/labels), visual_artifact_count (number of associated images)

- **Image Metadata**: Represents extracted metadata from images with attributes: metadata_id, artifact_id (foreign key), caption_text, alt_text, ocr_extracted_text, detected_labels (e.g., "diagram", "photo", "chart"), image_description (optional AI-generated description for search enhancement)

- **Slide Render Job**: Represents PowerPoint slide rendering task with attributes: job_id, source_pptx_path, slide_number, render_status (pending/completed/failed), output_artifact_id (resulting image artifact), render_timestamp, render_error (if failed)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users searching for technical content receive visual artifacts (images/slides) alongside text results for 80%+ of queries matching documents with embedded visuals
- **SC-002**: PowerPoint presentations are fully processed with all slides rendered as images within the same time limit as current document processing (< 5 minutes for typical 20-50 slide presentation)
- **SC-003**: Image extraction accuracy achieves 95%+ success rate for common formats (PDF, DOCX, PPTX) under normal conditions (non-corrupted files)
- **SC-004**: Users can view full-resolution visual artifacts without perceptible loading delay (< 1 second image load time for 90% of artifacts)
- **SC-005**: OCR text extraction from images improves search recall by 15-25% for queries matching text within diagrams or scanned documents
- **SC-006**: Visual artifacts display correctly in OpenWebUI without layout issues, image distortion, or broken links for 99%+ of results
- **SC-007**: Storage overhead for image artifacts remains within acceptable limits (< 2x increase in total storage compared to text-only chunks for average document corpus)
- **SC-008**: System handles documents with high image counts (50+ images per document) without processing failures or significant performance degradation
- **SC-009**: Users can filter or search specifically for results containing visual content ("show me results with diagrams")
- **SC-010**: Image caption and ALT text extraction improves findability - users successfully locate images using caption keywords in 85%+ of test scenarios

## Assumptions

- Railway documentation images are primarily technical diagrams, schematics, photos, and charts (not decorative graphics)
- Image quality in source documents is sufficient for OCR (minimum 150 DPI for text recognition)
- OpenWebUI artifact system can display images via base64 encoding, URLs, or file paths (no format limitations)
- PowerPoint slides can be rendered using standard libraries (python-pptx + Pillow or LibreOffice headless)
- Storage capacity is sufficient for image artifacts (estimated 5-50MB per document depending on image count/quality)
- Users have network bandwidth to load image artifacts in web UI (no extreme low-bandwidth constraints)
- Image extraction does not violate document security/DRM restrictions (most railway docs are unencrypted)
- Image file formats found in railway documents are standard industry formats supported by Python imaging libraries
- OCR accuracy for technical diagrams with annotations is 70%+ (sufficient for keyword search, not perfect transcription)
- Users prefer visual artifacts displayed inline with search results rather than requiring separate click to view
- Image aspect ratios in railway documentation are typically landscape or square (standard document layouts)
- System has sufficient compute resources for image processing (resizing, OCR) without impacting search performance
- Images embedded in documents are contextually relevant to nearby text (not random unrelated graphics)

## Dependencies

- **Image Extraction Libraries**: Python libraries for image extraction from PDFs (PyMuPDF/fitz, pdf2image), DOCX (python-docx), PPTX (python-pptx)
- **Image Processing**: Pillow (PIL) for image manipulation, resizing, format conversion
- **OCR Engine**: Tesseract OCR (via pytesseract) for text extraction from images
- **Slide Rendering**: LibreOffice headless mode OR python-pptx + Pillow for PowerPoint slide-to-image conversion
- **Storage**: File system or cloud storage (AWS S3, Azure Blob, etc.) for persisting image artifacts
- **OpenWebUI Compatibility**: OpenWebUI must support artifact display formats (base64, image URLs, or file references)
- **Existing System**: Enhanced Document Processor (already implemented) must be extended to handle image extraction workflow

## Scope Boundaries

**In Scope:**
- Image extraction from PDF, DOCX, PPTX documents
- PowerPoint slide rendering to static images
- Image-chunk association based on document proximity
- OCR text extraction from images
- Image caption/ALT text/label extraction
- Visual artifact storage and retrieval
- OpenWebUI artifact integration for image display
- Image metadata indexing for enhanced search
- Multi-image handling per chunk
- Image format support (PNG, JPEG, GIF, BMP, TIFF, SVG)

**Out of Scope:**
- Video extraction or video frame capture (only static images)
- 3D model or CAD file rendering (specialized formats beyond standard images)
- Image similarity search or visual AI search (semantic search on image content, not metadata)
- Real-time image generation or manipulation (no on-the-fly editing)
- Image annotation or markup features (display only, no user editing)
- Accessibility features beyond ALT text extraction (no automatic image description generation)
- Image version control (single version per extraction)
- Advanced OCR language support beyond English (Tesseract default)
- Image compression optimization beyond basic resizing (no advanced codecs)
- Custom image viewer in OpenWebUI (uses default artifact display)
- Image-based authentication or watermarking
- Extraction from password-protected or DRM-restricted documents
