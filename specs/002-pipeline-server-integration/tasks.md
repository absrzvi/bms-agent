# Tasks: Pipeline Server Integration for Document Generation

**Feature**: 002-pipeline-server-integration
**Branch**: `002-pipeline-server-integration`
**Status**: M1 Complete, M2/M3 In Progress
**Target**: 2025-10-06 (M2/M3), 2025-10-08 (M4)

## Task Summary

| Phase | Total | Complete | In Progress | Blocked |
|-------|-------|----------|-------------|---------|
| M1: Setup | 4 | 4 | 0 | 0 |
| M2: Deployment | 5 | 0 | 0 | 0 |
| M3: Testing | 6 | 0 | 0 | 0 |
| M4: Integration | 4 | 0 | 0 | 0 |
| M5: Documentation | 3 | 0 | 0 | 0 |
| **TOTAL** | **22** | **4** | **0** | **0** |

**Legend**: [P]=Critical Path, [H]=High Priority, [M]=Medium Priority, [L]=Low Priority

---

## M1: Setup & Foundation ✅ COMPLETE

### T001: Create pipeline implementation [P] ✅
**Status**: Complete
**Owner**: Cascade
**Estimate**: 2 hours
**Dependencies**: None

**Description**: Implement `bms_document_generator.py` with three document generation tools (Word, Excel, PowerPoint).

**Acceptance Criteria**:
- [x] Pipeline class with Valves and UserValves
- [x] `create_word_document()` function with sections support
- [x] `create_excel_spreadsheet()` function with styled headers
- [x] `create_presentation()` function with slides
- [x] Error handling and progress updates via event_emitter
- [x] Dependency imports (python-docx, openpyxl, python-pptx)

**Validation**: File exists at `/workspace/001-bms-agent/pipelines/bms_document_generator.py`

---

### T002: Create deployment scripts [P] ✅
**Status**: Complete
**Owner**: Cascade
**Estimate**: 1 hour
**Dependencies**: None

**Description**: Implement deployment automation scripts.

**Acceptance Criteria**:
- [x] `deploy-pipelines-server.sh` - Full deployment with repository clone
- [x] `deploy-pipelines-server-simple.sh` - Simplified deployment
- [x] `install-document-pipeline.sh` - Pipeline installation and dependencies
- [x] Scripts are executable (chmod +x)
- [x] Proper error handling and status messages

**Validation**: Scripts exist and are executable in `/workspace/001-bms-agent/pipelines/`

---

### T003: Create test automation script [P] ✅
**Status**: Complete
**Owner**: Cascade
**Estimate**: 1 hour
**Dependencies**: T001

**Description**: Implement automated testing script for all three document formats.

**Acceptance Criteria**:
- [x] `test-document-generation.sh` created
- [x] Dependency import validation (python-docx, openpyxl, python-pptx)
- [x] Sample DOCX generation test
- [x] Sample XLSX generation test
- [x] Sample PPTX generation test
- [x] File existence and size validation
- [x] Clear success/failure reporting

**Validation**: Script exists at `/workspace/001-bms-agent/pipelines/test-document-generation.sh`

---

### T004: Create deployment documentation [H] ✅
**Status**: Complete
**Owner**: Cascade
**Estimate**: 1 hour
**Dependencies**: T001, T002, T003

**Description**: Create comprehensive README with deployment, testing, and troubleshooting guidance.

**Acceptance Criteria**:
- [x] Deployment instructions (Phase 1)
- [x] Pipeline installation instructions (Phase 2)
- [x] OpenWebUI connection configuration (Phase 3)
- [x] Testing procedures (Phase 4)
- [x] Sample prompts for function calling
- [x] Troubleshooting section

**Validation**: README.md exists at `/workspace/001-bms-agent/pipelines/README.md`

---

## M2: Server Deployment 🔄 PENDING

### T005: Verify pipelines directory structure [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 10 minutes
**Dependencies**: T001, T002, T003, T004

**Description**: Verify all required files and directories exist before deployment.

**Acceptance Criteria**:
- [ ] Verify `bms_document_generator.py` exists
- [ ] Verify deployment scripts exist and are executable
- [ ] Verify test script exists and is executable
- [ ] Verify README.md exists
- [ ] Create `output/` directory if missing
- [ ] Verify write permissions on pipelines directory

**Validation**:
```bash
ls -la /workspace/001-bms-agent/pipelines/
test -w /workspace/001-bms-agent/pipelines/output
```

---

### T006: Execute deployment script [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 15 minutes
**Dependencies**: T005

**Description**: Run the deployment script to install Pipelines server and dependencies.

**Commands**:
```bash
cd /workspace/001-bms-agent/pipelines
bash deploy-pipelines-server-simple.sh
```

**Acceptance Criteria**:
- [ ] Script completes without errors
- [ ] Pipelines repository cloned to `/tmp/pipelines-repo`
- [ ] Dependencies installed (python-docx, openpyxl, python-pptx)
- [ ] Server process started
- [ ] PID file created at `pipelines/server.pid`
- [ ] Log file created at `pipelines/server.log`

**Validation**:
```bash
cat pipelines/server.pid
ps aux | grep $(cat pipelines/server.pid)
tail -20 pipelines/server.log
```

---

### T007: Validate server health endpoint [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 5 minutes
**Dependencies**: T006

**Description**: Verify the Pipelines server is responding to health checks.

**Commands**:
```bash
curl http://localhost:9099/health
```

**Acceptance Criteria**:
- [ ] Health endpoint returns HTTP 200
- [ ] Response includes status information
- [ ] Server responds within 2 seconds
- [ ] No error messages in logs

**Validation**:
```bash
curl -w "\nHTTP Code: %{http_code}\n" http://localhost:9099/health
```

---

### T008: Verify pipeline registration [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 5 minutes
**Dependencies**: T007

**Description**: Confirm the `bms_document_generator` pipeline is registered and discoverable.

**Commands**:
```bash
curl http://localhost:9099/pipelines
```

**Acceptance Criteria**:
- [ ] Pipeline list endpoint returns HTTP 200
- [ ] `bms_document_generator` appears in pipeline list
- [ ] Pipeline metadata includes correct name and version
- [ ] Three tools registered (create_word_document, create_excel_spreadsheet, create_presentation)

**Validation**:
```bash
curl http://localhost:9099/pipelines | jq '.pipelines[] | select(.id == "bms_document_generator")'
```

---

### T009: Verify process management [H]
**Status**: Pending
**Owner**: TBD
**Estimate**: 10 minutes
**Dependencies**: T006

**Description**: Test server restart workflow and PID file management.

**Commands**:
```bash
# Test restart
bash deploy-pipelines-server-simple.sh  # Should stop existing and start new

# Verify PID updated
cat pipelines/server.pid
ps aux | grep $(cat pipelines/server.pid)
```

**Acceptance Criteria**:
- [ ] Old process stopped gracefully
- [ ] New process started successfully
- [ ] PID file updated with new process ID
- [ ] Log file contains restart event
- [ ] No orphan processes remain

**Validation**:
```bash
# Verify only one pipelines process running
ps aux | grep -c "pipelines.*serve" | grep 1
```

---

## M3: Testing & Validation 🔄 PENDING

### T010: Run automated test script [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 10 minutes
**Dependencies**: T008

**Description**: Execute the automated test script to validate all document generation functions.

**Commands**:
```bash
cd /workspace/001-bms-agent/pipelines
bash test-document-generation.sh
```

**Acceptance Criteria**:
- [ ] Script completes without errors
- [ ] All dependency imports successful
- [ ] All three document types generated
- [ ] Test outputs clear success messages
- [ ] Script returns exit code 0

**Validation**:
```bash
bash test-document-generation.sh && echo "Tests passed"
```

---

### T011: Verify DOCX generation [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 10 minutes
**Dependencies**: T010

**Description**: Validate Word document generation with sample content.

**Acceptance Criteria**:
- [ ] DOCX file created in output directory
- [ ] File size > 0 bytes
- [ ] File is valid DOCX format (can be opened)
- [ ] Contains expected title and sections
- [ ] Metadata includes author information
- [ ] Timestamp in filename (if enabled)

**Validation**:
```bash
ls -lh /workspace/001-bms-agent/pipelines/output/*.docx
file /workspace/001-bms-agent/pipelines/output/*.docx  # Should show "Microsoft Word"
```

---

### T012: Verify XLSX generation [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 10 minutes
**Dependencies**: T010

**Description**: Validate Excel spreadsheet generation with sample data.

**Acceptance Criteria**:
- [ ] XLSX file created in output directory
- [ ] File size > 0 bytes
- [ ] File is valid XLSX format (can be opened)
- [ ] Contains expected headers and data rows
- [ ] Headers are styled (bold, colored)
- [ ] Columns are auto-sized

**Validation**:
```bash
ls -lh /workspace/001-bms-agent/pipelines/output/*.xlsx
file /workspace/001-bms-agent/pipelines/output/*.xlsx  # Should show "Microsoft Excel"
```

---

### T013: Verify PPTX generation [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 10 minutes
**Dependencies**: T010

**Description**: Validate PowerPoint presentation generation with sample slides.

**Acceptance Criteria**:
- [ ] PPTX file created in output directory
- [ ] File size > 0 bytes
- [ ] File is valid PPTX format (can be opened)
- [ ] Contains title slide and content slides
- [ ] Slides include expected text content
- [ ] Layout is properly formatted

**Validation**:
```bash
ls -lh /workspace/001-bms-agent/pipelines/output/*.pptx
file /workspace/001-bms-agent/pipelines/output/*.pptx  # Should show "Microsoft PowerPoint"
```

---

### T014: Performance validation [M]
**Status**: Pending
**Owner**: TBD
**Estimate**: 15 minutes
**Dependencies**: T011, T012, T013

**Description**: Verify document generation meets performance targets (<10 seconds per document).

**Commands**:
```bash
# Time DOCX generation
time python -c "from bms_document_generator import Pipeline; import asyncio; p = Pipeline(); asyncio.run(p.create_word_document(...))"

# Repeat for XLSX and PPTX
```

**Acceptance Criteria**:
- [ ] DOCX generation < 10 seconds
- [ ] XLSX generation < 10 seconds
- [ ] PPTX generation < 10 seconds
- [ ] Server remains responsive during generation
- [ ] No memory leaks or process bloat

**Validation**: All three formats generate within time limits

---

### T015: Error handling validation [H]
**Status**: Pending
**Owner**: TBD
**Estimate**: 15 minutes
**Dependencies**: T010

**Description**: Test error scenarios and validate proper error reporting.

**Test Cases**:
1. Missing dependencies (temporarily rename library)
2. Invalid input data (empty sections, malformed data)
3. File size exceeding max limit
4. Disabled format (via admin valves)
5. Disk space issues (simulate full disk)

**Acceptance Criteria**:
- [ ] Errors return descriptive messages
- [ ] No server crashes or hangs
- [ ] Proper HTTP status codes returned
- [ ] Error details logged to server.log
- [ ] Graceful degradation when possible

**Validation**:
```bash
# Test with invalid data
curl -X POST http://localhost:9099/pipelines/bms_document_generator \
  -d '{"invalid": "data"}' | jq '.error'
```

---

## M4: OpenWebUI Integration 🔄 PENDING

### T016: Configure OpenWebUI connection [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 10 minutes
**Dependencies**: T008

**Description**: Configure OpenWebUI to connect to the Pipelines server.

**Manual Steps**:
1. Navigate to OpenWebUI Admin Panel
2. Go to Settings → Connections
3. Add new connection:
   - API URL: `http://localhost:9099`
   - API Key: `0p3n-w3bu!`
4. Save configuration

**Acceptance Criteria**:
- [ ] Connection saved in OpenWebUI settings
- [ ] Connection test passes (green indicator)
- [ ] Pipeline appears in available tools list
- [ ] No connection errors in OpenWebUI logs

**Validation**: Tools menu shows `bms_document_generator` functions

---

### T017: Test function calling via chat [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 15 minutes
**Dependencies**: T016

**Description**: Verify document generation can be triggered via OpenWebUI chat interface.

**Test Prompts**:
1. "Create a Word document about railway safety with 3 sections"
2. "Generate an Excel spreadsheet comparing vendor prices"
3. "Make a PowerPoint presentation about network maintenance"

**Acceptance Criteria**:
- [ ] LLM recognizes document generation intent
- [ ] Function calls made to correct tools
- [ ] Documents generated successfully
- [ ] File paths returned in chat response
- [ ] No timeout or connection errors

**Validation**: Each prompt successfully generates expected document type

---

### T018: Verify progress updates [M]
**Status**: Pending
**Owner**: TBD
**Estimate**: 10 minutes
**Dependencies**: T017

**Description**: Confirm event_emitter progress updates display in OpenWebUI during generation.

**Acceptance Criteria**:
- [ ] "Creating document..." status appears during generation
- [ ] Progress indicator updates (if implemented)
- [ ] Completion message shows file path
- [ ] Status updates clear after completion
- [ ] No hanging status indicators

**Validation**: Visual confirmation in OpenWebUI interface during document generation

---

### T019: Document sample prompts [H]
**Status**: Pending
**Owner**: TBD
**Estimate**: 20 minutes
**Dependencies**: T017

**Description**: Create comprehensive list of sample prompts for documentation and demos.

**Acceptance Criteria**:
- [ ] 5+ DOCX prompts (reports, forms, procedures)
- [ ] 5+ XLSX prompts (tables, comparisons, analysis)
- [ ] 5+ PPTX prompts (briefings, summaries, training)
- [ ] Prompts demonstrate various features (sections, styling, metadata)
- [ ] All prompts tested and verified working
- [ ] Added to README.md

**Validation**: README contains "Sample Prompts" section with tested examples

---

## M5: Documentation & Finalization 🔄 PENDING

### T020: Review README completeness [H]
**Status**: Pending
**Owner**: TBD
**Estimate**: 20 minutes
**Dependencies**: T019

**Description**: Ensure README.md covers all deployment, testing, and troubleshooting scenarios.

**Acceptance Criteria**:
- [ ] Deployment section complete and tested
- [ ] Testing section includes all validation steps
- [ ] Troubleshooting covers common issues
- [ ] Sample prompts section comprehensive
- [ ] OpenWebUI connection setup documented
- [ ] Retention/cleanup workflow documented
- [ ] No broken links or outdated information

**Validation**: Technical reviewer can deploy from README alone

---

### T021: Create quickstart guide [M]
**Status**: Pending
**Owner**: TBD
**Estimate**: 30 minutes
**Dependencies**: T020

**Description**: Create `quickstart.md` with streamlined deployment for new users.

**Acceptance Criteria**:
- [ ] Quick deployment (3-5 commands)
- [ ] Essential configuration only
- [ ] One test command to verify
- [ ] Link to full README for details
- [ ] Clear success indicators
- [ ] < 5 minutes to complete

**Validation**:
```bash
# Quickstart should be this simple:
cd /workspace/001-bms-agent/pipelines
bash deploy-pipelines-server-simple.sh
bash test-document-generation.sh
```

---

### T022: Acceptance criteria validation [P]
**Status**: Pending
**Owner**: TBD
**Estimate**: 30 minutes
**Dependencies**: All previous tasks

**Description**: Final validation against all acceptance criteria from spec.md.

**Acceptance Criteria from Spec**:
- [ ] Deployment script starts Pipelines server successfully
- [ ] `/health` endpoint responds with HTTP 200
- [ ] `test-document-generation.sh` confirms all three formats generated
- [ ] OpenWebUI function calling triggers document creation for each format
- [ ] `README.md` covers deployment, testing, troubleshooting, and demo usage
- [ ] Backlog captures deferred enhancements (PDF, templates, SharePoint)

**Additional Validation**:
- [ ] Server startup < 2 minutes
- [ ] Document generation < 10 seconds each
- [ ] No dependency conflicts with main OpenWebUI
- [ ] Output directory persists across restarts
- [ ] Manual cleanup workflow documented

**Validation**: All spec acceptance criteria checked and passing

---

## Task Dependencies Graph

```
M1 Foundation (Complete):
T001 → T002 → T003 → T004

M2 Deployment:
T004 → T005 → T006 → T007 → T008
                            ↓
                          T009

M3 Testing:
T008 → T010 → T011 → T014
            ↓ T012 → T014
            ↓ T013 → T014
            → T015

M4 Integration:
T008 → T016 → T017 → T018
                  ↓
                T019

M5 Documentation:
T019 → T020 → T021
All → T022
```

## Next Actions

**Immediate (Today - 2025-10-05)**:
1. Start T005: Verify pipelines directory structure
2. Execute T006: Run deployment script
3. Complete T007-T009: Server validation
4. Begin T010-T013: Document generation testing

**Tomorrow (2025-10-06)**:
5. Complete M3: All testing and validation tasks
6. Start M4: OpenWebUI integration configuration
7. Begin M5: Documentation review

**By 2025-10-08**:
8. Complete T022: Final acceptance validation
9. Optional: Record demo segment (M4 from spec)
10. Close milestone and update main CLAUDE.md

---

**Status Legend**:
- ✅ Complete
- 🔄 In Progress
- ⏳ Blocked
- 📋 Pending

**Last Updated**: 2025-10-05
