# BMS Document Generator Pipeline

**Implementation Plan for OpenWebUI Document Generation**

Based on research in `docs/openwebui-doc-gen.md`, this implements the **Pipelines approach** (recommended) for generating Word, Excel, and PowerPoint documents via BMS Agent.

---

## 🎯 What This Does

Enables BMS Agent to create:
- ✅ **Word documents** (DOCX) - Reports, forms, procedures
- ✅ **Excel spreadsheets** (XLSX) - Data tables, comparisons, analysis
- ✅ **PowerPoint presentations** (PPTX) - Briefings, summaries, training materials

**Approach**: Separate Pipelines server (avoids dependency conflicts with main OpenWebUI)  
**Time**: ~1 hour total implementation  
**Risk**: Low (isolated from main instance)

---

## 📋 Implementation Steps

### Phase 1: Deploy Pipelines Server (15 minutes)

**Pod Environment** (No Docker):

```bash
# Make scripts executable
chmod +x pipelines/*.sh

# Deploy Pipelines server
bash pipelines/deploy-pipelines-server.sh
```

**What this does**:
- Clones OpenWebUI Pipelines repository
- Installs pipelines package with pip
- Installs document generation dependencies
- Creates startup script
- Starts server on port 9099 in background
- Configures with default API key `0p3n-w3bu!`

**Verify**:
```bash
# Check server is running
ps aux | grep pipelines
cat pipelines/server.pid

# Test health endpoint
curl http://localhost:9099/health

# View logs
tail -f pipelines/server.log
```

---

### Phase 2: Install Document Generator Pipeline (30 minutes)

```bash
# Install pipeline and dependencies
bash pipelines/install-document-pipeline.sh
```

**What this does**:
- Verifies `bms_document_generator.py` exists
- Installs Python libraries:
  - `python-docx >= 0.8.11` (Word documents)
  - `openpyxl >= 3.1.0` (Excel spreadsheets)
  - `python-pptx >= 0.6.21` (PowerPoint presentations)
- Creates output directory at `/workspace/001-bms-agent/pipelines/output`
- Restarts Pipelines server to load pipeline

**Verify**:
```bash
# Check pipeline file exists
ls -l pipelines/bms_document_generator.py

# Check dependencies installed
pip list | grep -E "python-docx|openpyxl|python-pptx"

# Check server running
ps aux | grep pipelines
```

---

### Phase 3: Connect to OpenWebUI (5 minutes)

**Manual steps in OpenWebUI interface**:

1. **Open Admin Panel**:
   - Navigate to: `http://localhost:3000/admin`

2. **Add Connection**:
   - Go to: **Settings → Connections**
   - Click: **+ Add Connection**
   - Enter:
     - **API URL**: `http://localhost:9099`
     - **API Key**: `0p3n-w3bu!`
   - Click: **Save**

3. **Enable Pipeline for Model**:
   - Go to: **Workspace → Models**
   - Select your model (e.g., `mistral-nemo`)
   - Click: **✏️ Edit**
   - Scroll to: **Pipelines** section
   - Check: **BMS Document Generator**
   - Click: **Save**

---

### Phase 4: Test & Verify (10 minutes)

```bash
# Run automated tests
bash pipelines/test-document-generation.sh
```

**Expected output**:
```
✅ Word document created: ~15000 bytes
✅ Excel spreadsheet created: ~6000 bytes
✅ PowerPoint presentation created: ~28000 bytes
```

**Manual test in OpenWebUI chat**:

```
Test 1: Word Document
Prompt: "Create a Word document with a vendor evaluation form for Siemens Railway Systems"

Test 2: Excel Spreadsheet
Prompt: "Generate an Excel spreadsheet comparing ENGI and QHSE procurement processes"

Test 3: PowerPoint Presentation
Prompt: "Create a PowerPoint presentation about railway safety procedures"
```

**Download generated files**:
```bash
# Files are already on your pod filesystem
ls -lh /workspace/001-bms-agent/pipelines/output/

# Copy to a different location if needed
cp -r /workspace/001-bms-agent/pipelines/output ./generated-documents/

# View files
ls -lh ./generated-documents/
```

---

## 🔧 Pipeline Architecture

### File Structure

```
pipelines/
├── README.md                          # This file
├── deploy-pipelines-server.sh         # Step 1: Deploy server
├── install-document-pipeline.sh       # Step 2: Install pipeline
├── test-document-generation.sh        # Step 3: Test
├── bms_document_generator.py          # Pipeline implementation
└── output/                            # Generated documents (in container)
```

### Pipeline Implementation

**`bms_document_generator.py`** provides three tools:

1. **`create_word_document`**
   - **Input**: title, sections (heading + content), filename
   - **Output**: Formatted DOCX with title, metadata, sections
   - **Library**: python-docx

2. **`create_excel_spreadsheet`**
   - **Input**: title, headers, data rows, filename
   - **Output**: Formatted XLSX with styled headers, auto-width columns
   - **Library**: openpyxl

3. **`create_presentation`**
   - **Input**: title, slides (title + content), filename
   - **Output**: PPTX with title slide + content slides
   - **Library**: python-pptx

### Configuration Options

**Admin Settings** (Valves):
- `OUTPUT_DIR`: Where documents are saved (default: `/app/pipelines/output`)
- `MAX_FILE_SIZE_MB`: Maximum file size limit (default: 10 MB)
- `ENABLE_DOCX`: Enable Word generation (default: true)
- `ENABLE_XLSX`: Enable Excel generation (default: true)
- `ENABLE_PPTX`: Enable PowerPoint generation (default: true)

**User Settings** (UserValves):
- `include_timestamp`: Add timestamp to filenames (default: true)
- `default_author`: Document author name (default: "BMS Agent")

---

## 🎬 Demo Integration

### For POC Demo Recording

**Option A: Show Document Generation** (bonus feature):

```
Scene 1: Introduction (30s)
"BMS Agent can now create downloadable documents"

Scene 2: Word Document (1 min)
Prompt: "Create a vendor evaluation form for Bombardier"
Show: Generated DOCX, download, open in Word

Scene 3: Excel Spreadsheet (1 min)
Prompt: "Compare ENGI vs QHSE procurement in a table"
Show: Generated XLSX, download, open in Excel

Scene 4: PowerPoint Presentation (1 min)
Prompt: "Create presentation about safety procedures"
Show: Generated PPTX, download, open in PowerPoint

Total: ~4 minutes added to search demo
```

**Option B: Keep Search-Focused Demo** (safer for POC):
- Record main demo with v3.1 search functions (10-12 min)
- Mention document generation as "coming soon"
- Defer full demo to MVP phase

---

## 🚀 Usage Examples

### Example 1: Vendor Evaluation Form

**Prompt**:
```
Create a Word document with a vendor evaluation form for:
- Vendor: Siemens Railway Systems
- Location: Munich, Germany
- Certifications: ISO9001, EN50155
- Quote: €75,000
Include evaluation criteria and recommendation section.
```

**Generated**: `vendor_evaluation_siemens_20251005_143022.docx`

---

### Example 2: Procurement Comparison

**Prompt**:
```
Generate an Excel spreadsheet comparing procurement processes 
between ENGI and QHSE departments. Include approval thresholds, 
timelines, and required documentation.
```

**Generated**: `procurement_comparison_20251005_143145.xlsx`

---

### Example 3: Safety Training Presentation

**Prompt**:
```
Create a PowerPoint presentation about railway safety procedures 
including:
- Slide 1: Introduction to safety protocols
- Slide 2: Personal protective equipment (PPE)
- Slide 3: Lockout/tagout procedures
- Slide 4: Emergency response
```

**Generated**: `safety_training_20251005_143312.pptx`

---

## 🔍 Troubleshooting

### Issue 1: Pipelines Server Not Starting

**Symptoms**: Server process exits immediately or won't start

**Solutions**:
```bash
# Check logs
tail -f pipelines/server.log

# Check port availability
lsof -i :9099
# Or: netstat -tulpn | grep 9099

# Stop existing process and restart
if [ -f pipelines/server.pid ]; then
    kill $(cat pipelines/server.pid)
fi
bash pipelines/deploy-pipelines-server.sh
```

---

### Issue 2: Dependencies Not Installing

**Symptoms**: Import errors in pipeline logs

**Solutions**:
```bash
# Reinstall dependencies manually
pip install --upgrade python-docx openpyxl python-pptx

# Check installation
pip list | grep -E "docx|openpyxl|pptx"

# Verify imports work
python3 -c "import docx, openpyxl, pptx; print('All imports OK')"

# Restart server
if [ -f pipelines/server.pid ]; then
    kill $(cat pipelines/server.pid)
fi
bash pipelines/start-server.sh
```

---

### Issue 3: Pipeline Not Appearing in OpenWebUI

**Symptoms**: Can't find "BMS Document Generator" in model settings

**Solutions**:
```bash
# Verify pipeline file exists
ls -l pipelines/bms_document_generator.py

# Check server logs for loading errors
tail -50 pipelines/server.log | grep -i error

# Verify connection in OpenWebUI
# Admin → Settings → Connections → Check API URL and key

# Check server is running
ps aux | grep pipelines

# Restart Pipelines server
if [ -f pipelines/server.pid ]; then
    kill $(cat pipelines/server.pid)
fi
bash pipelines/deploy-pipelines-server.sh
```

---

### Issue 4: Tools Not Being Called

**Symptoms**: Model doesn't generate documents, just describes them

**Solutions**:
1. **Check function calling mode**:
   - Chat Controls → Advanced Params → Function Calling
   - Try switching between "Default" and "Native"

2. **Use better model**:
   - GPT-4o, GPT-3.5-turbo, Gemini 1.5 work best
   - Local models (Llama, Mistral) struggle with tool calling

3. **Be explicit in prompt**:
   - ❌ "Tell me about vendor forms"
   - ✅ "Create a Word document with vendor evaluation form"

---

### Issue 5: Can't Find Generated Files

**Symptoms**: Documents created but can't locate them

**Solutions**:
```bash
# List generated documents
ls -lh /workspace/001-bms-agent/pipelines/output/

# Check if output directory exists
ls -ld /workspace/001-bms-agent/pipelines/output

# Create if missing
mkdir -p /workspace/001-bms-agent/pipelines/output

# Search for recently created files
find /workspace/001-bms-agent/pipelines -name "*.docx" -o -name "*.xlsx" -o -name "*.pptx"

# Copy to another location
cp /workspace/001-bms-agent/pipelines/output/*.docx ~/documents/
```

---

## 📊 Comparison to v4.0 HTML Artifacts

| Aspect | v4.0 HTML Artifacts | Pipelines Document Gen |
|--------|---------------------|------------------------|
| **Status** | Deprecated (not working) | ✅ Working |
| **Approach** | LLM generates HTML | Python libraries generate docs |
| **Formats** | HTML only | DOCX, XLSX, PPTX |
| **Dependency Risk** | High (breaks OpenWebUI) | Low (isolated) |
| **File Quality** | Basic HTML | Professional Office formats |
| **Downloadable** | Copy HTML source | Native Office files |
| **Shareable** | Email HTML | Email DOCX/XLSX/PPTX |
| **Print-ready** | Browser print | Native Office print |
| **Editable** | Manual in editor | Native in Office apps |

**Verdict**: Pipelines approach is superior and working

---

## 🎯 Next Steps

### Immediate (POC Phase):
- [x] Deploy Pipelines server
- [x] Install document generator
- [x] Test basic functionality
- [ ] Record demo (optional, can defer to MVP)
- [ ] Complete T032.3 (search demo is sufficient)

### Short-term (MVP Phase):
- [ ] Add templates for common documents
- [ ] Implement form auto-fill from BMS data
- [ ] Add PDF export capability
- [ ] Create document library/storage

### Long-term (Production):
- [ ] Document versioning
- [ ] Approval workflows
- [ ] Digital signatures
- [ ] SharePoint integration (upload to BMS repository)

---

## 📚 Related Documentation

- **Research**: `docs/openwebui-doc-gen.md` (comprehensive analysis)
- **System Prompt**: `docs/SYSTEM_PROMPT_v3.1.md` (active version)
- **Search Demo**: `docs/COMPREHENSIVE_DEMO_GUIDE.md` (primary POC demo)
- **Agentic Capabilities**: `docs/AGENTIC_CAPABILITIES_DEMO.md` (without HTML)

---

## ✅ Success Criteria

**For POC Completion**:
- [ ] Pipelines server running and connected
- [ ] All 3 document types tested (DOCX, XLSX, PPTX)
- [ ] Documents downloadable and openable in Office apps
- [ ] Optional: 4-minute demo recorded showing document generation

**For MVP Transition**:
- [ ] Templates for 5+ common document types
- [ ] Integration with BMS search (auto-fill from retrieved data)
- [ ] User feedback collected and incorporated
- [ ] Production deployment strategy defined

---

**Implementation Time**: ~1 hour  
**Difficulty**: Medium (requires Docker, basic Python understanding)  
**Risk**: Low (separate from main OpenWebUI instance)  
**Value**: High (professional document generation from AI)

**Status**: ✅ Ready to implement  
**Next Command**: `bash pipelines/deploy-pipelines-server.sh`
