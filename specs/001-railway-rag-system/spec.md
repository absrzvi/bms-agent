# Feature Specification: BMS Agent - Railway Documentation RAG System

**Feature Branch**: `001-railway-rag-system`
**Created**: 2025-10-22
**Status**: Draft
**Input**: User description: "BMS Agent - Railway Documentation RAG System with semantic search, multi-vector embeddings, and OpenWebUI integration"

## Clarifications

### Session 2025-10-22

- Q: What level of data security and protection is required for the indexed railway documentation and search queries? → A: Minimal Security - No encryption at rest, HTTP acceptable, basic input validation only
- Q: What observability capabilities are required beyond basic logging? → A: Logging + Basic Metrics - Logs plus key metrics (request count, latency percentiles, error rates, queue depths) exposed via health endpoints
- Q: Should the system enforce rate limiting per user/IP to prevent abuse, and if so, what are the limits? → A: No Rate Limiting - Trust all users, rely only on 1,000 concurrent user capacity, no per-user or per-IP throttling

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Technical Documentation Search (Priority: P1)

Railway engineers and technical staff need to quickly find accurate information from railway technical manuals, standards, and operational documentation across 21 different departments (HR, Safety, Operations, Maintenance, etc.).

**Why this priority**: This is the core value proposition - enabling fast, accurate retrieval of technical information from a large corpus of railway documentation (300+ documents). Without this, the system has no purpose.

**Independent Test**: Can be fully tested by uploading sample railway documents, submitting natural language queries (e.g., "What are the safety procedures for train braking systems?"), and verifying that relevant document chunks are returned with proper metadata (source document, chapter, quality score).

**Acceptance Scenarios**:

1. **Given** a collection of 300+ railway documents across 21 departments, **When** a user searches for "brake system maintenance procedures", **Then** the system returns relevant document chunks ranked by semantic similarity with source citations and chapter information
2. **Given** the user needs information from a specific department, **When** they filter search results by department (e.g., "Safety"), **Then** only documents from that department are searched and returned
3. **Given** the user submits a query, **When** the search completes, **Then** results are returned within 2 seconds with quality scores above 85%
4. **Given** a multi-part document with chapters, **When** search returns a result, **Then** the response includes chapter number, chapter title, and hierarchical chapter path for context

---

### User Story 2 - Document Ingestion & Processing (Priority: P1)

System administrators need to upload and process new railway documentation (PDF, DOCX, PPTX, XLSX, CSV, TXT, MD formats) so that the content becomes searchable through the RAG system.

**Why this priority**: Without document ingestion, there's no content to search. This is equally critical as search itself and represents the other half of the core MVP.

**Independent Test**: Can be tested by uploading various document formats, verifying text extraction quality, confirming hierarchical chunking occurs, and checking that documents appear in the vector database with all required metadata fields populated.

**Acceptance Scenarios**:

1. **Given** a user has a PDF railway manual, **When** they upload it via the API, **Then** the system extracts text, detects chapter structure, creates parent/child chunks with overlap, generates embeddings, and indexes to the vector database
2. **Given** a document has low OCR quality or corrupted text, **When** quality validation runs, **Then** chunks below the quality threshold (85%) are filtered out and logged without being indexed
3. **Given** a document contains numbered sections (e.g., "1.2.3 Safety Protocols"), **When** chapter extraction runs, **Then** the hierarchical structure is captured (chapter_number: "1.2.3", chapter_title: "Safety Protocols", chapter_path: "1 > 1.2 > 1.2.3")
4. **Given** a user uploads documents from the "Operations" department, **When** batch ingestion completes, **Then** all documents are tagged with department="Operations" for later filtering
5. **Given** an administrator uploads a 100MB document, **When** the upload is attempted, **Then** the system accepts the file (within max size limit) and processes it successfully

---

### User Story 3 - Hybrid Search with Keyword Matching (Priority: P2)

Users need to find documents using both semantic similarity and exact keyword matching to handle technical terminology and acronyms that may not embed well semantically.

**Why this priority**: Railway documentation contains many technical terms, model numbers, and acronyms (e.g., "EMU-750", "SPAD", "AWS") that benefit from exact keyword matching in addition to semantic understanding. This improves search accuracy for technical queries.

**Independent Test**: Can be tested by submitting queries with specific technical terms or model numbers, comparing pure semantic search results vs. hybrid search results, and measuring the improvement in precision for technical queries.

**Acceptance Scenarios**:

1. **Given** a user searches for a specific train model number like "EMU-750", **When** hybrid search is used, **Then** results combine vector similarity with keyword matching (BM25-style sparse vectors) using Reciprocal Rank Fusion
2. **Given** the user adjusts the keyword vs. semantic weighting, **When** they set alpha=0.7 (more semantic weight), **Then** search results favor semantically similar content over exact keyword matches
3. **Given** a query contains both concepts and specific terms, **When** hybrid search runs, **Then** results rank higher when they match both semantic meaning AND contain the exact keywords

---

### User Story 4 - Conversational Interface via OpenWebUI (Priority: P2)

Railway staff need a conversational interface where they can ask questions in natural language and receive comprehensive answers synthesized from multiple document sources.

**Why this priority**: While direct search API access is useful for developers, most end-users prefer a chat interface. This significantly improves usability and adoption, making the system accessible to non-technical staff.

**Independent Test**: Can be tested by installing the OpenWebUI custom tool, submitting natural language questions through the chat interface, and verifying that the tool retrieves relevant chunks, synthesizes an answer with citations, and supports follow-up questions.

**Acceptance Scenarios**:

1. **Given** a user asks "What are the emergency procedures for signal failure?" via OpenWebUI, **When** the BMS search tool processes the query, **Then** it returns relevant chunks with source citations that the LLM uses to generate a comprehensive answer
2. **Given** the user needs information from a specific chapter, **When** they ask "What does Chapter 5 say about maintenance schedules?", **Then** the search filters by chapter_number="5" and returns only relevant sections
3. **Given** search results contain numerical data, **When** the user requests a chart, **Then** the OpenWebUI tool generates SVG visualizations or Mermaid diagrams to present the information visually
4. **Given** the user asks a follow-up question, **When** context from the previous query is needed, **Then** the system maintains conversation context for coherent multi-turn interactions

---

### User Story 5 - Multi-Vector Hierarchical Retrieval (Priority: P3)

Users searching for detailed technical information need the system to return broader contextual chunks when they match on very specific sub-chunks, ensuring they don't miss surrounding context.

**Why this priority**: This enhances search quality by providing better context, but the system can function adequately with standard semantic search. It's a quality improvement rather than a core requirement.

**Independent Test**: Can be tested by submitting a very specific query that matches a small child chunk, then verifying that the system can optionally return the larger parent chunk that contains additional context around the matched section.

**Acceptance Scenarios**:

1. **Given** a user searches for a very specific procedure detail, **When** the query matches a child chunk (500 chars), **Then** the system can optionally retrieve the parent chunk (1500 chars) that provides broader context
2. **Given** a document has been chunked hierarchically with parent/child relationships, **When** indexing completes, **Then** each chunk stores 4 dense vectors (chunk, parent, child, full_doc embeddings) plus 1 sparse vector for hybrid search
3. **Given** the user enables hierarchical search mode, **When** child chunks match the query, **Then** results return parent chunks to provide more comprehensive context

---

### User Story 6 - Railway-Specific Metadata Filtering (Priority: P3)

Railway operations teams need to filter search results by railway-specific attributes like fleet type, train ID, standard compliance, or network component to narrow results to their specific operational context.

**Why this priority**: This is domain-specific enhancement that improves precision for railway use cases, but general semantic search works without it. It's valuable for power users but not essential for MVP.

**Independent Test**: Can be tested by tagging documents with railway-specific metadata (fleet_type, train_id, standard_compliance, network_component), then submitting filtered queries and verifying only matching documents are searched.

**Acceptance Scenarios**:

1. **Given** documents are tagged with fleet_type (e.g., "DMU", "EMU", "Locomotive"), **When** a user filters search by fleet_type="EMU", **Then** only documents related to Electric Multiple Units are searched
2. **Given** documents reference specific standards (e.g., "EN 50126", "ISO 9001"), **When** a user searches with standard_compliance filter, **Then** only compliant documents appear in results
3. **Given** the user needs information about a specific network component (e.g., "signaling", "track", "overhead_line"), **When** they apply the network_component filter, **Then** search scope is limited to relevant technical documentation

---

### Edge Cases

- What happens when a document contains no detectable chapter structure (e.g., unstructured text files)?
  - System should still chunk the document using hierarchical parent/child strategy without chapter metadata
- What happens when uploaded document is corrupted or has very poor OCR quality?
  - Quality validation should filter out chunks with quality scores below threshold (default 85%) and log them for review
- What happens when a user submits an empty query or query with only stop words?
  - System should return validation error prompting for a meaningful search query
- What happens when vector database is empty (no documents indexed)?
  - Search should return empty results with helpful message indicating no documents are available
- What happens when embedding service (Ollama or sentence-transformers) is unavailable?
  - System should return graceful error message indicating service unavailability and retry logic for transient failures
- What happens when user uploads a document exceeding the max file size (100MB default)?
  - System should reject upload with clear error message indicating size limit
- What happens when two departments have documents with identical names?
  - System should disambiguate using department metadata and full file path in search results
- What happens when a search query contains special characters or non-Latin scripts?
  - System should handle Unicode properly and sanitize input to prevent injection attacks
- What happens when concurrent users upload documents simultaneously?
  - System should handle concurrent uploads with proper async processing and avoid race conditions in vector DB
- What happens when user searches across all departments but many documents match?
  - System should return top-k results (configurable limit, e.g., 10-50) ranked by relevance score

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept document uploads in multiple formats (PDF, DOCX, PPTX, XLSX, CSV, TXT, MD) via API endpoint
- **FR-002**: System MUST extract text content from uploaded documents with fallback to OCR for scanned PDFs
- **FR-003**: System MUST detect and extract hierarchical chapter structure from documents including chapter numbers, titles, and nested sub-chapters
- **FR-004**: System MUST chunk documents hierarchically with configurable parent chunk size (default 1500 chars) and child chunk size (default 500 chars) with overlap (default 200 chars)
- **FR-005**: System MUST validate chunk quality using faithfulness, relevancy, precision, and recall metrics with configurable threshold (default 85%)
- **FR-006**: System MUST generate semantic embeddings for each chunk using configurable embedding model
- **FR-007**: System MUST store multiple vector representations per chunk: chunk embedding, parent embedding, child embedding, full document embedding (4 dense vectors) plus keyword sparse vector
- **FR-008**: System MUST index processed chunks to vector database with comprehensive metadata including document name, department, category, document type, chapter info, quality scores, and timestamps
- **FR-009**: System MUST provide semantic search API endpoint that accepts natural language queries and returns ranked results by cosine similarity
- **FR-010**: System MUST support hybrid search combining vector similarity and keyword matching using Reciprocal Rank Fusion with configurable alpha weighting
- **FR-011**: System MUST support filtering search results by metadata fields: department, category, document_name, document_type, chapter_number
- **FR-012**: System MUST support filtering by railway-specific metadata: fleet_type, train_id, standard_compliance, network_component
- **FR-013**: System MUST return search results with source citations including document name, page/chunk number, chapter information, and quality scores
- **FR-014**: System MUST support batch document ingestion by department with progress tracking
- **FR-015**: System MUST provide health check endpoints for API, vector database connectivity, and embedding service availability, including basic metrics (request count, latency percentiles, error rates, queue depths)
- **FR-016**: System MUST persist all indexed data to survive service restarts in designated persistent storage location
- **FR-017**: System MUST enforce maximum upload file size limit (configurable, default 100MB)
- **FR-018**: System MUST log all document processing operations including successes, failures, and quality validation results to file-based logs
- **FR-018a**: System MUST collect and expose operational metrics including request count, latency percentiles (p50, p95, p99), error rates, and processing queue depths
- **FR-019**: System MUST provide OpenWebUI integration through custom tool interface with 25+ search functions
- **FR-020**: System MUST support configurable processing profiles (RAILWAY, TECHNICAL, GENERAL) that adjust chunking and validation parameters
- **FR-021**: System MUST handle concurrent search requests from multiple users without degradation up to 1,000 concurrent users (no per-user or per-IP rate limiting enforced)
- **FR-022**: System MUST optionally enforce API key authentication when configured, allowing anonymous access when disabled
- **FR-022a**: System MUST validate and sanitize all user input (queries, file uploads, metadata) to prevent injection attacks
- **FR-022b**: System MAY support HTTP or HTTPS transport (encryption in transit is optional)
- **FR-022c**: System does NOT require encryption at rest for vector database or indexed documents (minimal security posture)
- **FR-023**: System MUST provide hierarchical search mode that can return parent chunks when child chunks match query
- **FR-024**: System MUST support n8n workflow integration for conversational search via messaging platforms

### Key Entities

- **Document**: Represents an uploaded railway technical document with attributes: document_name, document_type (PDF/DOCX/etc), department (one of 21 departments), category, upload_timestamp, file_size, total_pages, processing_status, indexed_chunks_count
- **Chunk**: Represents a processed segment of a document with attributes: chunk_id, chunk_text, chunk_size, parent_chunk_id (for hierarchical relationship), chapter_number, chapter_title, chapter_level, chapter_path, sub_chapter, quality_score (overall 0-100), quality_metrics (faithfulness, relevancy, precision, recall), embeddings (4 dense + 1 sparse vector), metadata (source document reference, position in document)
- **Chapter**: Represents a hierarchical section of a document with attributes: chapter_number (e.g., "1.2.3"), chapter_title, chapter_level (1, 2, 3 for nesting depth), chapter_path (full hierarchy path), parent_chapter, child_chapters
- **Search Query**: Represents a user search request with attributes: query_text, query_embedding, filter_criteria (department, category, chapter, etc.), search_mode (semantic/hybrid/hierarchical), result_limit, alpha_weight (for hybrid search)
- **Search Result**: Represents a retrieved chunk matching a query with attributes: chunk_reference, relevance_score (cosine similarity or RRF score), source_document, chapter_context, quality_score, metadata, ranking_position
- **Department**: Represents an organizational unit owning documents with attributes: department_name (one of 21: HR, Safety, Operations, Maintenance, etc.), document_count, total_indexed_chunks
- **Embedding Model Config**: Represents embedding service configuration with attributes: model_name (e.g., "all-mpnet-base-v2", "snowflake-arctic-embed2"), embedding_dimension (768 or 1024), service_type (sentence-transformers/Ollama), service_url, model_status (loaded/unloaded)
- **Processing Profile**: Represents document processing configuration with attributes: profile_name (RAILWAY/TECHNICAL/GENERAL), parent_chunk_size, child_chunk_size, chunk_overlap, quality_threshold, enable_hybrid_search, enable_quality_validation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can find relevant railway documentation within 2 seconds for 95% of queries (p95 latency)
- **SC-002**: System successfully processes and indexes documents with 95%+ accuracy in chapter structure detection for documents with clear formatting
- **SC-003**: Search results achieve 85%+ average quality scores indicating high faithfulness and relevance
- **SC-004**: System handles 1,000 concurrent search requests without response time degradation beyond 10%
- **SC-005**: Document upload and processing completes for typical railway manuals (50-200 pages) within 5 minutes
- **SC-006**: Hybrid search improves precision by 15-20% compared to pure semantic search for technical terminology queries
- **SC-007**: System maintains 99.9% uptime with automatic service recovery after transient failures
- **SC-008**: Users can successfully filter search results by department, reducing irrelevant results by 70%+ when filtering is applied
- **SC-009**: Quality validation filters out 5-10% of low-quality chunks, improving overall search result relevance
- **SC-010**: System successfully persists all indexed data across service restarts with zero data loss
- **SC-011**: OpenWebUI integration enables 90%+ of users to complete information retrieval tasks through conversational interface without directly using API
- **SC-012**: Batch document ingestion processes 100+ documents from a department with progress visibility and error handling
- **SC-013**: System scales to support 300+ documents across 21 departments without search performance degradation
- **SC-014**: Railway-specific metadata filtering reduces search scope by 60-80% when applied, improving response time and relevance

## Assumptions

- Railway documentation is primarily in English (system can be extended for other languages with model changes)
- Documents follow standard formatting conventions (headings, numbered sections) for optimal chapter extraction
- Embedding service (Ollama or sentence-transformers) is available and pre-configured in the deployment environment
- Vector database (Qdrant) is available and properly configured with multi-vector support
- System runs in persistent storage environment (e.g., RunPod /workspace) where designated directories survive restarts
- Users have basic familiarity with search interfaces (web UI or chat) and don't require extensive training
- Document upload size limit of 100MB is sufficient for 95%+ of railway technical documentation
- Quality threshold of 85% provides good balance between comprehensiveness and precision (configurable per deployment)
- Standard web application performance expectations apply (2-second p95 latency for search)
- API key authentication is optional, allowing both secure production deployments and open MVP/development environments
- OpenWebUI is available as the conversational interface platform (system can integrate with other chat platforms)
- Railway domain knowledge is embedded in document content, not in the RAG system itself (system is domain-agnostic)
- System operates in trusted network environment with minimal security requirements (no encryption at rest, HTTP acceptable)
- Railway documentation is not classified or highly sensitive (appropriate for minimal security posture)
- Users are trusted and well-intentioned (no rate limiting required, system relies on natural usage patterns staying within 1,000 concurrent user capacity)

## Dependencies

- External services: Vector database (Qdrant v1.15.5+), Embedding service (Ollama or sentence-transformers), OpenWebUI (for chat interface)
- Runtime environment: Python 3.11+, sufficient compute resources for embedding generation (recommended 8-16 vCPU, 32-64GB RAM)
- Storage: Persistent storage location for vector database, uploaded documents, logs, and metrics (minimum 100GB recommended)
- Network: HTTP or HTTPS access for API endpoints (HTTPS optional), connectivity between services (FastAPI, Qdrant, Ollama)

## Scope Boundaries

**In Scope:**
- Document upload, processing, and indexing for supported file formats
- Semantic and hybrid search with metadata filtering
- Chapter-aware chunking and hierarchical retrieval
- Quality validation and scoring
- OpenWebUI custom tool integration
- API key authentication (optional)
- Batch ingestion by department
- Railway-specific metadata support

**Out of Scope:**
- Real-time document synchronization from external sources
- User management, roles, and permissions (beyond optional API key)
- Document editing or modification capabilities
- Version control for documents
- Collaborative annotation or commenting on documents
- Automatic document classification or tagging (beyond manual department assignment)
- Multi-language support (English only in initial version)
- Custom embedding model training
- Advanced analytics dashboard for usage patterns
- Integration with external railway management systems (ERP, CMMS, etc.)
- Mobile native applications (web API can be consumed by mobile apps)
- Offline search capabilities
