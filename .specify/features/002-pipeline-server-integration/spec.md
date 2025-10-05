# Pipeline Server Integration Specification

## 1. Overview
- **Feature Name**: Pipeline Server Integration for Document Generation
- **Problem Statement**: The BMS Agent cannot reliably generate Office documents because OpenWebUI marketplace tools are limited and installing heavy document libraries in the primary UI introduces dependency conflicts. This blocks the document-creation roadmap described in `docs/openwebui-doc-gen.md`.
- **Goal**: Provide a dedicated OpenWebUI Pipelines server running within the existing pod to host the `bms_document_generator` pipeline, enabling DOCX, XLSX, and PPTX generation without impacting search workflows.
- **Success Metrics (POC)**: Pipelines server starts in <2 minutes, `/health` responds with HTTP 200, automated test script generates all three document types in <10 seconds each.

## 2. Scope
- **In Scope**
  - Deploying the Pipelines server as a managed background Python process using scripts in `pipelines/`.
  - Installing and maintaining required Python packages (`python-docx`, `openpyxl`, `python-pptx`) in the pod environment (no Docker).
  - Implementing the `bms_document_generator` pipeline with tools for Word, Excel, and PowerPoint creation.
  - Documenting deployment, troubleshooting, and demo usage in `pipelines/README.md`.
  - Enabling OpenWebUI function-calling integration via connection configuration (Admin → Settings → Connections).
- **Out of Scope / Deferred**
  - PDF export, advanced document templating, or SharePoint upload automation (planned for MVP).
  - High availability, scaling across multiple nodes, or automated restarts beyond provided scripts.
  - Production-grade authentication beyond default Pipelines API key.

## 3. User Stories
- **Demo Engineer**: “I need to showcase document generation during the POC demo without destabilizing the search experience.”
- **Procurement Analyst**: “I need formatted vendor evaluation reports generated directly from retrieved data.”
- **Operations Specialist**: “I need safety checklists and presentations produced from chat queries to reduce manual formatting.”

## 4. Functional Requirements
1. **Server Deployment**
   - Provide scripts (`pipelines/deploy-pipelines-server.sh`, `pipelines/deploy-pipelines-server-simple.sh`, `pipelines/start-server.sh`) to install dependencies, start, stop, and restart the Pipelines server.
   - Server listens on `0.0.0.0:9099`, logs to `pipelines/server.log`, and writes PID to `pipelines/server.pid`.
2. **Pipeline Registration**
   - Server startup must discover `pipelines/bms_document_generator.py` and list it via `GET /pipelines`.
   - Admin valves enable/disable each document format and set output directory + max file size.
   - User valves toggle timestamped filenames and default author metadata.
3. **Document Generation Tools**
   - `create_word_document`: Generates DOCX containing title, metadata paragraph, and section bodies.
   - `create_excel_spreadsheet`: Generates XLSX with styled headers, auto-sized columns, and supplied data rows.
   - `create_presentation`: Generates PPTX with title slide and content slides per provided payload.
   - Output files saved under `/workspace/001-bms-agent/pipelines/output/` with timestamp suffix when enabled.
   - `pipelines/test-document-generation.sh` validates dependency imports, generates sample DOCX/XLSX/PPTX, and confirms file existence and non-zero size.
   - Script detects missing dependencies or stale PID files and exits with helpful messaging.
5. **OpenWebUI Integration**
   - README documents connection setup (Admin → Settings → Connections → API URL `http://localhost:9099`, API key `0p3n-w3bu!`).
   - Provide sample prompts demonstrating successful tool invocation via chat.
6. **Dependency Isolation & Versions**
   - Pipelines server must install `python-docx>=0.8.11`, `openpyxl>=3.1.0`, and `python-pptx>=0.6.21` inside the pipeline process, never through OpenWebUI's main tool installer (prevents UI blocking and dependency conflicts noted in `docs/openwebui-doc-gen.md`).
   - Document optional PDF libraries (reportlab/fpdf2) as deferred enhancements while ensuring current requirements list matches installed versions.
7. **Status & Error Feedback**
   - Pipeline should emit progress updates via `event_emitter` when available so users see "creating document" statuses, aligning with best practices from `openwebui-doc-gen.md`.
## 7. Data & Storage Considerations
- Generated documents reside under `pipelines/output/` with timestamped filenames to avoid collisions.
- **Storage**: Ensure output directory exists with 755 permissions; automatically purge generated files older than 30 days via a weekly operator-run command (`find /workspace/001-bms-agent/pipelines/output -type f -mtime +30 -delete`).
- No database persistence; OpenWebUI responses include local file paths for manual download.
- Recommend manual archival or cleanup prior to MVP.

## 8. Operational Considerations
- **Deployment**: Scripts handle cloning (if needed), dependency installation, server startup.
- **Backups**: Encourage optional copy to `/workspace/001-bms-agent/generated-documents/`; automated retention beyond the weekly 30-day purge command is out of scope.
- **Failure Handling**: Document troubleshooting steps for dependency issues, port conflicts, and missing pipelines in README.

## 9. Risks & Mitigations
- **Upstream Repo Changes**: Pin commit in documentation; consider vendoring pipeline entry point if instability occurs.
- **Large Requests**: Enforce max file size via admin valve and document recommended limits.
- **Security Exposure**: Binding to localhost minimizes risk; revisit authentication before MVP release.
- **Process Drift**: PID tracking and restart script ensure orphan processes are cleaned up.

## 10. Milestones
| Milestone | Description | Owner | Target |
|-----------|-------------|-------|--------|
| M1 | Scripts & README committed | Cascade | ✅ Complete |
| M2 | Pipelines server deployed & verified in pod | Cascade | 2025-10-06 |
| M3 | Automated DOCX/XLSX/PPTX tests pass | Cascade | 2025-10-06 |
| M4 | Optional demo segment recorded | Absar | 2025-10-08 |

## 11. Acceptance Criteria
- Deployment script starts Pipelines server and `/health` responds successfully.
- `pipelines/test-document-generation.sh` confirms all three formats are generated with valid files.
- OpenWebUI function calling triggers document creation for each format.
- `pipelines/README.md` covers deployment, testing, troubleshooting, and demo usage.
- Backlog captures deferred enhancements (PDF, templates, SharePoint uploads).

## 12. Open Questions
- Should we pin a specific Pipelines repository commit to avoid upstream breaks?
- Do we need an automated cleanup or retention policy for generated documents post-MVP?
- Should PDF export be implemented within this pipeline or a dedicated future pipeline?

## Clarifications
### Session 2025-10-05
- **Source control**: Maintain deployments from the dedicated `002-pipeline-server` branch of the BMS Agent Pipelines fork; do not pull upstream `main` during testing.
- **Retention workflow**: Operators run `find /workspace/001-bms-agent/pipelines/output -type f -mtime +30 -delete` at least weekly to enforce the 30-day purge policy.
