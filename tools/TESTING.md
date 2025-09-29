# Testing the BMS Search OpenWebUI Tool

## Quick Test (Without OpenWebUI)

### 1. Run the Test Suite

```bash
cd /root/CascadeProjects/windsurf-project/001-bms-agent
python3 tools/test_bms_search.py
```

This will test:
- ✅ API health check
- ✅ Semantic search
- ✅ Hybrid search
- ✅ Document type filtering
- ✅ Custom filters
- ✅ Configuration valves
- ✅ Error handling

**Expected Output**: 7/7 tests passed

---

## Manual Testing (Without OpenWebUI)

### Test 1: Import and Initialize

```python
cd /root/CascadeProjects/windsurf-project/001-bms-agent
python3

>>> from tools.bms_search import Tools
>>> tool = Tools()
>>> print("✅ Tool initialized")
```

### Test 2: Check API Status

```python
>>> result = tool.get_api_status()
>>> print(result)
```

**Expected**: Shows BMS API status with Qdrant and Ollama connection status

### Test 3: Semantic Search

```python
>>> result = tool.search_semantic("business continuity", limit=3)
>>> print(result)
```

**Expected**: Returns 3 search results with document names and excerpts

### Test 4: Hybrid Search

```python
>>> result = tool.search_hybrid("railway safety", limit=3)
>>> print(result)
```

**Expected**: Returns results using both semantic and keyword matching

### Test 5: Filtered Search

```python
>>> result = tool.search_by_document_type("maintenance", "pdf", limit=2)
>>> print(result)
```

**Expected**: Returns only PDF documents

### Test 6: Custom Filters

```python
>>> filters = {"quality_score_min": 0.7}
>>> result = tool.search_documents("safety", limit=5, filters=filters)
>>> print(result)
```

**Expected**: Returns only high-quality documents (score ≥ 0.7)

---

## Testing with OpenWebUI (Full Integration)

### Prerequisites

1. **OpenWebUI must be installed**:
   ```bash
   cd /workspace/openwebui && source venv/bin/activate
   which open-webui  # Should show path
   ```

2. **BMS API must be running**:
   ```bash
   curl http://localhost:8000/health  # Should return healthy
   ```

### Step 1: Install the Tool

```bash
# Create tools directory
mkdir -p /workspace/openwebui/data/tools

# Copy tool
cp /root/CascadeProjects/windsurf-project/001-bms-agent/tools/bms_search.py \
   /workspace/openwebui/data/tools/

# Verify
ls -la /workspace/openwebui/data/tools/bms_search.py
```

### Step 2: Start OpenWebUI

```bash
bash /workspace/openwebui/start_openwebui.sh
```

**Or manually**:
```bash
cd /workspace/openwebui
source venv/bin/activate
export OPEN_WEBUI_DATA_DIR=/workspace/openwebui/data
open-webui serve --host 0.0.0.0 --port 3000
```

### Step 3: Access OpenWebUI

Open browser: **http://localhost:3000**

### Step 4: Enable the Tool

1. Go to **Settings** → **Tools**
2. Find **BMS Agent Search** in the list
3. Click **Enable**
4. (Optional) Configure Valves:
   - Click **Settings** icon
   - Adjust parameters
   - Click **Save**

### Step 5: Test in Chat

Try these queries in the chat interface:

#### Test 1: Simple Search
```
Find documents about business continuity
```

**Expected**: Tool activates and returns search results

#### Test 2: Specific Search
```
Search for railway safety procedures
```

**Expected**: Returns relevant railway safety documents

#### Test 3: Document Type
```
Show me PDF files about maintenance
```

**Expected**: Returns only PDF documents

#### Test 4: Hybrid Search
```
Use hybrid search to find "emergency response"
```

**Expected**: Uses hybrid search mode

#### Test 5: Health Check
```
What's the status of the BMS API?
```

**Expected**: Returns API health status

---

## Verification Checklist

### Tool Installation
- [ ] Tool file exists in `/workspace/openwebui/data/tools/`
- [ ] File is readable (check permissions)
- [ ] No syntax errors (run `python3 -m py_compile bms_search.py`)

### OpenWebUI Integration
- [ ] Tool appears in Tools list
- [ ] Tool can be enabled
- [ ] Valves configuration is accessible
- [ ] Tool shows in chat interface

### Functionality
- [ ] Semantic search returns results
- [ ] Hybrid search works
- [ ] Document filtering works
- [ ] Quality filtering works
- [ ] Health check works
- [ ] Error messages are clear
- [ ] Results are formatted correctly

### Performance
- [ ] Search completes in <5 seconds
- [ ] No timeout errors
- [ ] Multiple queries work consecutively
- [ ] Results are relevant to query

---

## Troubleshooting

### Tool Not Appearing in OpenWebUI

**Check 1**: Verify file location
```bash
ls -la /workspace/openwebui/data/tools/bms_search.py
```

**Check 2**: Verify syntax
```bash
python3 -m py_compile /workspace/openwebui/data/tools/bms_search.py
```

**Check 3**: Check OpenWebUI logs
```bash
# Find OpenWebUI process
ps aux | grep open-webui

# Check logs (if running in background)
tail -f /workspace/logs/openwebui.log
```

**Check 4**: Restart OpenWebUI
```bash
pkill -f open-webui
bash /workspace/openwebui/start_openwebui.sh
```

### Search Returns No Results

**Check 1**: Verify BMS API is running
```bash
curl http://localhost:8000/health
```

**Check 2**: Verify Qdrant has data
```bash
curl http://localhost:6333/collections/nomad_bms_documents | python3 -m json.tool
```

**Check 3**: Test search directly
```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 1}'
```

### Connection Errors

**Check 1**: Verify API URL in Valves
- Default: `http://localhost:8000`
- Change if API is on different host/port

**Check 2**: Test connectivity
```bash
curl http://localhost:8000/health
```

**Check 3**: Check firewall
```bash
# Ensure port 8000 is accessible
netstat -tlnp | grep 8000
```

---

## Quick Test Commands

### Test Everything (Automated)
```bash
python3 /root/CascadeProjects/windsurf-project/001-bms-agent/tools/test_bms_search.py
```

### Test API Connection
```bash
curl http://localhost:8000/health
```

### Test Search Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "business continuity", "limit": 3}' | python3 -m json.tool
```

### Test Qdrant
```bash
curl http://localhost:6333/collections/nomad_bms_documents | python3 -m json.tool
```

### Test Tool Import
```bash
python3 -c "from tools.bms_search import Tools; t = Tools(); print(t.get_api_status())"
```

---

## Expected Results

### Successful Test Output

```
======================================================================
  BMS SEARCH TOOL - COMPREHENSIVE TEST SUITE
======================================================================

======================================================================
  TEST 1: API Health Check
======================================================================

✅ BMS API Status: HEALTHY

Services:
  ✅ qdrant: connected
  ✅ ollama: connected

✅ PASS: API is healthy

[... more tests ...]

======================================================================
  TEST SUMMARY
======================================================================

✅ PASS: API Health Check
✅ PASS: Semantic Search
✅ PASS: Hybrid Search
✅ PASS: Document Type Filter
✅ PASS: Custom Filters
✅ PASS: Configuration
✅ PASS: Error Handling

======================================================================
  Results: 7/7 tests passed (100%)
======================================================================

🎉 All tests passed! Tool is ready for OpenWebUI integration.
```

---

## Next Steps After Testing

1. **If all tests pass**: Tool is ready for production use
2. **If some tests fail**: Check troubleshooting section
3. **If OpenWebUI not installed**: Wait for installation to complete
4. **If ready to deploy**: Follow installation guide in README.md

---

**Testing Status**: Ready  
**Last Updated**: 2025-09-29  
**Tool Version**: 1.0.0
