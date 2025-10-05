# Tasks: Pipeline Server Integration for Document Generation

## Task List
1. **T001 — Environment setup**  
   - Checkout branch `002-pipeline-server-integration` and pull latest changes.  
   - Verify Python 3.11 virtual environment (.venv) is active and install base dependencies from `requirements.txt`.  
   - Paths: repository root

2. **T002 — Author research summary** [P]  
   - Create `/workspace/001-bms-agent/specs/002-pipeline-server-integration/research.md` consolidating dependency isolation rationale, pipeline branch policy, and retention plan.  
   - Reference `docs/openwebui-doc-gen.md` and existing scripts.

3. **T003 — Draft data model** [P]  
   - Produce `/workspace/001-bms-agent/specs/002-pipeline-server-integration/data-model.md` listing pipeline server components: deployment scripts, valves, output artifacts, retention command.  
   - Describe relationships (scripts ↔ pipeline runtime ↔ OpenWebUI).

4. **T004 — Define pipeline contracts**  
   - Write `/workspace/001-bms-agent/specs/002-pipeline-server-integration/contracts/pipeline-server.md` capturing:  
     - REST endpoints (`GET /health`, `GET /pipelines`).  
     - Function schemas (`create_word_document`, `create_excel_spreadsheet`, `create_presentation`).  
     - Admin/user valve shapes and responses.

5. **T005 — Enumerate contract tests** [P]  
   - Document `/workspace/001-bms-agent/specs/002-pipeline-server-integration/contracts/tests.md` outlining failing test cases for each contract (health, pipelines listing, three tools).  
   - Include expected status codes and file outputs per test.

6. **T006 — Create quickstart validation** [P]  
   - Build `/workspace/001-bms-agent/specs/002-pipeline-server-integration/quickstart.md` with step-by-step prompts for demo engineer, procurement analyst, and operations specialist validating DOCX/XLSX/PPTX generation and retention purge.

7. **T007 — Align deployment scripts with dedicated branch**  
   - Update `pipelines/deploy-pipelines-server.sh` and `pipelines/deploy-pipelines-server-simple.sh` to clone/pull from the BMS fork `002-pipeline-server` branch.  
   - Ensure branch selection is configurable via environment variable.

8. **T008 — Implement retention helper** [P]  
   - Add `pipelines/purge-output.sh` running `find /workspace/001-bms-agent/pipelines/output -type f -mtime +30 -delete`.  
   - Make script idempotent and chmod +x in README instructions.

9. **T009 — Harden start/install scripts**  
   - Update `pipelines/start-server.sh` and `pipelines/install-document-pipeline.sh` to respect new branch path, verify dependencies, and log versions.  
   - Ensure scripts exit non-zero on failure.

10. **T010 — Extend automated tests**  
    - Enhance `pipelines/test-document-generation.sh` to:  
      - Assert branch info via log snippet.  
      - Verify purge script existence and dry-run message.  
      - Continue validating DOCX/XLSX/PPTX outputs.

11. **T011 — Refresh documentation** [P]  
    - Update `pipelines/README.md` to cover dedicated branch usage, retention script invocation, and new verification steps.  
    - Cross-link to research/quickstart artifacts.

12. **T012 — Run validation pass**  
    - Execute deployment, install, purge, and test scripts end-to-end.  
    - Capture logs in `pipelines/server.log` and note outcomes in a short summary appended to `research.md`.

13. **T013 — Final polish & PR readiness** [P]  
    - Run linting/formatting on shell scripts (`shfmt` or `bashate`), ensure executable bits set, and prepare PR checklist noting constitution compliance.  
    - Paths: updated scripts + root docs.

## Parallel Execution Guide
- **Group A (documentation artifacts)**: `T002`, `T003`, `T005`, `T006`, `T011`, `T013` can run in parallel once `T001` completes.  
  - Example command: `cascade run-task --id T003` (after finishing T001).
- **Group B (script updates)**: `T007`, `T008`, `T009`, `T010` should follow `T001`; execute sequentially within the group to avoid conflicts.  
  - Example command: `cascade run-task --id T007`.
- **Group C (verification)**: `T012` runs after Groups A & B finish.
