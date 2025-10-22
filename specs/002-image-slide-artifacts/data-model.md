# Data Model: Image and Slide Visual Artifacts

**Feature Branch**: `002-image-slide-artifacts`
**Date**: 2025-10-22
**Status**: Complete

## Overview

This document defines the data entities, relationships, and validation rules for the visual artifacts feature extending the BMS Agent RAG system.

---

## Entity Definitions

### 1. Visual Artifact

Represents an extracted image or rendered PowerPoint slide.

**Attributes**:
- `artifact_id` (string, required): Unique identifier (UUID format: `img_abc123` or `slide_xyz789`)
- `artifact_type` (enum, required): Type of artifact
  - Values: `image` (extracted from PDF/DOCX), `slide` (rendered from PPTX)
- `source_document` (string, required): Original document filename
- `source_page_or_slide_number` (integer, required): Page number (PDF/DOCX) or slide number (PPTX)
- `file_format` (enum, required): Image file format
  - Values: `png`, `jpeg`, `gif`, `bmp`, `tiff`, `svg`
- `file_path` (string, required): Absolute path to artifact file
  - Pattern: `/workspace/visual-artifacts/{images|slides}/{doc_id}/{filename}`
- `thumbnail_path` (string, optional): Path to compressed thumbnail
- `file_size_bytes` (integer, required): File size in bytes
- `dimensions` (object, required):
  - `width` (integer): Image width in pixels
  - `height` (integer): Image height in pixels
- `extraction_timestamp` (datetime, required): When artifact was created (ISO 8601 format)
- `associated_chunk_ids` (array[string], required): List of chunk IDs linked to this artifact
- `ocr_text` (string, optional): OCR-extracted text from image (empty if OCR failed or not applicable)
- `ocr_confidence` (float, optional): OCR confidence score (0.0-1.0)
- `caption` (string, optional): Extracted image caption (e.g., "Figure 3: Hydraulic Valve")
- `alt_text` (string, optional): ALT text from source document
- `position_in_document` (object, optional): Bounding box coordinates
  - `x` (float): X coordinate
  - `y` (float): Y coordinate
  - `width` (float): Width
  - `height` (float): Height

**Validation Rules**:
- `artifact_id` must be unique across all artifacts
- `file_path` must exist on file system
- `dimensions.width` and `dimensions.height` must be > 0
- `file_format` must match actual file extension
- `associated_chunk_ids` must reference valid chunks in Qdrant
- `ocr_confidence` must be between 0.0 and 1.0 if present

**Relationships**:
- **One-to-Many** with Chunk: One artifact can be associated with multiple chunks (e.g., image referenced in multiple sections)
- **Many-to-One** with Document: Many artifacts belong to one source document

**Example**:
```json
{
  "artifact_id": "img_abc123def",
  "artifact_type": "image",
  "source_document": "BMS-ENGI-FOR-004 Maintenance Manual.pdf",
  "source_page_or_slide_number": 15,
  "file_format": "png",
  "file_path": "/workspace/visual-artifacts/images/doc_xyz/page_015_img_001.png",
  "thumbnail_path": "/workspace/visual-artifacts/thumbnails/thumb_img_abc123def.jpg",
  "file_size_bytes": 487234,
  "dimensions": {
    "width": 1920,
    "height": 1080
  },
  "extraction_timestamp": "2025-10-22T10:30:15Z",
  "associated_chunk_ids": ["chunk_001", "chunk_045"],
  "ocr_text": "Figure 3: Hydraulic Pressure Valve Assembly",
  "ocr_confidence": 0.92,
  "caption": "Hydraulic Pressure Valve",
  "alt_text": "Diagram showing hydraulic valve components",
  "position_in_document": {
    "x": 100.5,
    "y": 250.3,
    "width": 400.0,
    "height": 300.0
  }
}
```

---

### 2. Enhanced Chunk (Extension of Existing Entity)

Extends the existing Chunk entity with visual artifact references.

**New Attributes Added**:
- `has_visual_artifacts` (boolean, required): Flag indicating if chunk has associated images
  - Default: `false`
- `visual_artifact_ids` (array[string], optional): List of artifact IDs associated with this chunk
  - Empty array if `has_visual_artifacts` is false
- `visual_artifact_count` (integer, required): Number of associated visual artifacts
  - Default: 0
  - Max: configurable (default 5 per `MAX_IMAGES_PER_CHUNK`)
- `image_ocr_text` (string, optional): Concatenated OCR text from all associated images
  - Used for enhanced search matching
- `image_captions` (array[string], optional): List of captions from associated images
  - Used for caption-based search

**Existing Attributes Unchanged**:
- `chunk_id`, `chunk_text`, `chunk_size`, `parent_chunk_id`
- `chapter_number`, `chapter_title`, `chapter_level`, `chapter_path`
- `quality_score`, `quality_metrics`
- `embeddings` (4 dense + 1 sparse)
- `metadata` (document name, department, timestamps, etc.)

**Validation Rules**:
- If `has_visual_artifacts` is true, `visual_artifact_ids` must not be empty
- `visual_artifact_count` must equal `len(visual_artifact_ids)`
- `visual_artifact_count` must not exceed `MAX_IMAGES_PER_CHUNK`
- All IDs in `visual_artifact_ids` must reference existing Visual Artifacts

**Qdrant Payload Extension**:
```json
{
  "chunk_id": "chunk_001",
  "content": "The hydraulic brake system uses a pressure valve to regulate...",
  "document_name": "BMS-ENGI-FOR-004 Maintenance Manual.pdf",
  "department": "Engineering",
  "quality_score": 0.87,

  "has_visual_artifacts": true,
  "visual_artifact_ids": ["img_abc123def", "img_ghi456jkl"],
  "visual_artifact_count": 2,
  "image_ocr_text": "Figure 3: Hydraulic Pressure Valve Assembly",
  "image_captions": ["Hydraulic Pressure Valve", "Valve Cross-Section"]
}
```

---

### 3. Image Metadata

Represents extracted metadata and analysis for an image artifact.

**Attributes**:
- `metadata_id` (string, required): Unique identifier (UUID)
- `artifact_id` (string, required): Foreign key to Visual Artifact
- `caption_text` (string, optional): Extracted figure caption
- `alt_text` (string, optional): Accessibility ALT text
- `ocr_extracted_text` (string, optional): Full OCR output
- `ocr_word_count` (integer, optional): Number of words recognized by OCR
- `detected_labels` (array[string], optional): Image classification labels
  - Values: `diagram`, `photo`, `chart`, `graph`, `schematic`, `table`, `flowchart`
- `image_description` (string, optional): AI-generated description (future enhancement, P3)
- `extracted_timestamp` (datetime, required): When metadata was extracted

**Validation Rules**:
- `artifact_id` must reference a valid Visual Artifact
- `detected_labels` must use predefined label vocabulary
- `ocr_word_count` must match word count in `ocr_extracted_text`

**Relationships**:
- **One-to-One** with Visual Artifact: Each artifact has at most one metadata record

**Example**:
```json
{
  "metadata_id": "meta_xyz789",
  "artifact_id": "img_abc123def",
  "caption_text": "Figure 3: Hydraulic Pressure Valve Assembly",
  "alt_text": "Diagram showing internal components of hydraulic valve",
  "ocr_extracted_text": "Inlet Port\\nOutlet Port\\nPressure Chamber\\nSpring Mechanism",
  "ocr_word_count": 7,
  "detected_labels": ["diagram", "schematic"],
  "image_description": null,
  "extracted_timestamp": "2025-10-22T10:30:20Z"
}
```

---

### 4. Slide Render Job

Represents a PowerPoint slide rendering task for tracking processing status.

**Attributes**:
- `job_id` (string, required): Unique identifier (UUID)
- `source_pptx_path` (string, required): Path to source PowerPoint file
- `slide_number` (integer, required): Slide number to render (1-indexed)
- `render_status` (enum, required): Current job status
  - Values: `pending`, `in_progress`, `completed`, `failed`
- `output_artifact_id` (string, optional): Resulting Visual Artifact ID (null if not completed)
- `render_timestamp` (datetime, optional): When rendering completed
- `render_error` (string, optional): Error message if status is `failed`
- `render_duration_ms` (integer, optional): Rendering time in milliseconds

**Validation Rules**:
- `slide_number` must be > 0 and <= total slides in presentation
- If `render_status` is `completed`, `output_artifact_id` must not be null
- If `render_status` is `failed`, `render_error` must be provided
- `render_duration_ms` must be > 0 if status is `completed`

**State Transitions**:
```
pending → in_progress → completed
                     ↘ failed
```

**Relationships**:
- **Many-to-One** with Document: Many render jobs for one PPTX file
- **One-to-One** with Visual Artifact: Each job produces at most one artifact

**Example**:
```json
{
  "job_id": "job_pqr456stu",
  "source_pptx_path": "/workspace/bms-agent/upload-files/Training/safety_procedures.pptx",
  "slide_number": 5,
  "render_status": "completed",
  "output_artifact_id": "slide_mno789pqr",
  "render_timestamp": "2025-10-22T10:32:45Z",
  "render_error": null,
  "render_duration_ms": 1250
}
```

---

## Entity Relationships Diagram

```
┌─────────────────────┐
│     Document        │
│ (Existing Entity)   │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────▼──────────┐         ┌────────────────────┐
│  Visual Artifact    │◄────────│  Image Metadata    │
│                     │   1:1   │                    │
│ - artifact_id       │         │ - metadata_id      │
│ - artifact_type     │         │ - caption_text     │
│ - file_path         │         │ - ocr_text         │
│ - dimensions        │         │ - detected_labels  │
│ - ocr_text          │         └────────────────────┘
│ - caption           │
└──────────┬──────────┘
           │ N
           │
           │ N
┌──────────▼──────────┐
│  Enhanced Chunk     │
│ (Extended Entity)   │
│                     │
│ - chunk_id          │
│ - content           │
│ - embeddings        │
│ + has_visual_       │
│   artifacts         │
│ + visual_artifact_  │
│   ids               │
│ + image_ocr_text    │
└─────────────────────┘

┌─────────────────────┐
│ Slide Render Job    │
│                     │
│ - job_id            │
│ - source_pptx_path  │
│ - slide_number      │
│ - render_status     │
│ - output_artifact_  │
│   id                │
└──────────┬──────────┘
           │
           │ 1:1
           │
           ▼
     Visual Artifact
     (artifact_type=slide)
```

---

## Storage Locations

### File System Storage

**Visual Artifacts Directory Structure**:
```
/workspace/visual-artifacts/
├── images/                          # Extracted images
│   ├── doc_{document_id}/
│   │   ├── page_001_img_001.png
│   │   ├── page_001_img_002.jpg
│   │   ├── page_002_img_001.png
│   │   └── ...
│   └── ...
├── slides/                          # Rendered slides
│   ├── pres_{presentation_id}/
│   │   ├── slide_001.png
│   │   ├── slide_002.png
│   │   └── ...
│   └── ...
└── thumbnails/                      # Compressed previews
    ├── thumb_{artifact_id}.jpg
    └── ...
```

### Qdrant Payload Storage

**Chunk Metadata** (in existing `nomad_bms_documents` collection):
- `has_visual_artifacts` (boolean, indexed)
- `visual_artifact_ids` (array[string])
- `visual_artifact_count` (integer, indexed for filtering)
- `image_ocr_text` (string, searchable)
- `image_captions` (array[string], searchable)

**Separate Artifacts Collection** (optional enhancement):
- Collection name: `visual_artifacts_metadata`
- Stores Visual Artifact and Image Metadata entities
- Enables artifact-specific queries (e.g., "find all diagrams")

---

## Indexing Strategy

### Qdrant Indexes

**Existing Collection (`nomad_bms_documents`)**:
- Add keyword index on `has_visual_artifacts` for filtering
- Add keyword index on `visual_artifact_count` for range queries

**Search Query Examples**:
```python
# Find chunks with visual artifacts
from qdrant_client.models import Filter, FieldCondition, MatchValue

filter = Filter(
    must=[
        FieldCondition(
            key="has_visual_artifacts",
            match=MatchValue(value=True)
        )
    ]
)

# Find chunks with 2+ images
filter = Filter(
    must=[
        FieldCondition(
            key="visual_artifact_count",
            range={"gte": 2}
        )
    ]
)

# Combined: semantic search with visual artifact filter
results = qdrant_client.search(
    collection_name="nomad_bms_documents",
    query_vector=query_embedding,
    query_filter=filter,
    limit=10
)
```

---

## Data Flow

### Image Extraction Flow

```
Document Upload
    ↓
Read Document (PyMuPDF/python-docx/python-pptx)
    ↓
Extract Images/Render Slides
    ↓
For Each Image:
    ├─ OCR Text Extraction (Tesseract)
    ├─ Caption/ALT Text Extraction
    ├─ Image Processing (Resize, Optimize)
    ├─ Save to File System (/workspace/visual-artifacts/)
    └─ Create Visual Artifact Entity
    ↓
Associate Artifacts with Chunks (Proximity Algorithm)
    ↓
Update Chunk Metadata in Qdrant
    ├─ Set has_visual_artifacts = true
    ├─ Add visual_artifact_ids
    ├─ Add image_ocr_text
    └─ Add image_captions
```

### Search with Artifacts Flow

```
User Query
    ↓
Generate Query Embedding
    ↓
Qdrant Search (with has_visual_artifacts filter if requested)
    ↓
For Each Result Chunk:
    ├─ Check has_visual_artifacts flag
    └─ If True:
        ├─ Load Visual Artifact Metadata
        ├─ Read Image from File System
        ├─ Encode to Base64
        └─ Attach to Result
    ↓
Return Results with Visual Artifacts to OpenWebUI
```

---

## Validation and Constraints

### Business Rules

1. **Artifact Uniqueness**: Each `artifact_id` must be globally unique
2. **File System Integrity**: All `file_path` references must exist on disk
3. **Chunk Association**: At least one chunk must be associated with each artifact
4. **OCR Coherence**: If `ocr_text` is present, `ocr_confidence` must also be present
5. **Slide Sequencing**: Slide numbers must be sequential within a presentation
6. **Storage Limits**: Total artifacts per document should not exceed reasonable limits (configurable, default 100)

### Data Integrity Checks

**Periodic Validation** (cron job or manual trigger):
```python
def validate_artifact_integrity():
    # Check 1: File paths exist
    for artifact in get_all_artifacts():
        if not os.path.exists(artifact.file_path):
            logger.error(f"Missing file: {artifact.file_path}")

    # Check 2: Orphaned artifacts (no chunk associations)
    for artifact in get_all_artifacts():
        if not artifact.associated_chunk_ids:
            logger.warning(f"Orphaned artifact: {artifact.artifact_id}")

    # Check 3: Broken chunk references
    for chunk in get_all_chunks():
        if chunk.has_visual_artifacts:
            for artifact_id in chunk.visual_artifact_ids:
                if not artifact_exists(artifact_id):
                    logger.error(f"Broken reference: {artifact_id}")
```

---

## Migration Strategy

### Existing Data Compatibility

**No Migration Needed** for existing chunks:
- New attributes are optional extensions
- Existing chunks default to `has_visual_artifacts = false`
- Backward compatible with current search/retrieval logic

**New Document Processing**:
- Documents ingested after feature deployment automatically get visual artifacts
- Re-ingestion of existing documents will add visual artifacts

---

## Future Enhancements (Out of Scope for MVP)

### Potential Extensions

1. **Image Versioning**: Track multiple versions of same image when document is updated
2. **Artifact Deduplication**: Detect and deduplicate identical images across documents
3. **Visual Similarity Search**: Find images similar to a query image (vector embedding of image content)
4. **Automatic Image Descriptions**: Use vision AI (CLIP, BLIP) to generate image descriptions for better search
5. **Image Annotations**: Allow users to add notes/highlights to images

---

## Summary

This data model extends the existing BMS Agent RAG system with minimal changes:
- **1 new entity**: Visual Artifact (core)
- **3 supporting entities**: Image Metadata, Slide Render Job (processing tracking)
- **4 new chunk attributes**: Lightweight extension to existing Chunk entity
- **File system storage**: Scalable, no database bloat
- **Backward compatible**: Existing functionality unaffected

**Total Storage Overhead**: ~10MB per document with 20 images (within SC-007 < 2x target)
