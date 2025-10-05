# BMS Agent System Prompt - Version Guide

**Last Updated**: 2025-10-05

---

## ✅ ACTIVE VERSION: v3.1

**File**: `docs/SYSTEM_PROMPT_v3.1.md`

**Status**: ✅ **Production Ready for POC**

**Use This For**:
- POC demo recording
- OpenWebUI deployment
- All current testing
- T032.3 demo completion

**Features**:
- 13 operational search functions (65% coverage)
- Semantic, hybrid, and smart search (+12% accuracy)
- Advanced search (contextual, rerank) from T036
- 8 filtered search functions
- Comprehensive citation system
- Privacy protection (redaction)
- Explainability valve support

**Deployment**:
```bash
# Copy this prompt to OpenWebUI
cat docs/SYSTEM_PROMPT_v3.1.md

# Paste into: OpenWebUI Admin → Models → System Prompt
```

---

## ⚠️ DEPRECATED: v4.0

**File**: `docs/SYSTEM_PROMPT_v4.0.md`

**Status**: ⚠️ **Experimental - Not Working Reliably**

**Why Deprecated**:
- HTML artifact generation not working as expected
- LLM not generating complete HTML documents
- Added complexity not needed for POC
- User rollback requested (2025-10-05)

**What It Tried to Add**:
- Static HTML document generation
- Filled forms as artifacts
- Checklists with checkboxes
- Comparison tables
- Workflow timelines

**Decision**: **Deferred to MVP phase**

HTML artifact generation is a good idea but adds complexity that's not needed for POC completion. Can be revisited after POC signoff with better LLM support or different implementation approach.

---

## 📋 Version History

### v3.1 (2025-10-04) - **CURRENT**
- ✅ Added explainability valve support
- ✅ Updated for T036 (contextual, rerank functions)
- ✅ 13 operational search functions documented
- ✅ Citation system with SharePoint URLs
- ✅ Privacy protection rules
- **Status**: Production ready, tested, working

### v4.0 (2025-10-05) - **DEPRECATED**
- ⚠️ Attempted HTML artifact generation
- ⚠️ Not working reliably
- ⚠️ Rollback requested by user
- **Status**: Experimental, do not use

### v3.0 (2025-10-03)
- Initial agent capabilities
- Basic search functions
- Citation system

---

## 🎯 For POC Demo

**Use v3.1 with these demo options**:

### Option 1: Comprehensive Search Demo (10-12 min)
**File**: `docs/COMPREHENSIVE_DEMO_GUIDE.md`
- Shows all 13 operational search functions
- Demonstrates T036 additions (contextual, rerank)
- Highlights metadata boosting (+12% accuracy)
- **Tested**: ✅ All functions verified working

### Option 2: Agentic Capabilities (Without HTML)
**File**: `docs/AGENTIC_CAPABILITIES_DEMO.md`
- Focus on intelligent Q&A
- "Why" explanations
- Multi-document synthesis
- Complex reasoning
- **Show capabilities through chat responses** (not HTML artifacts)

### Option 3: Simple POC (3-5 min)
**File**: `docs/DEMO_RECORDING_GUIDE.md`
- 3 core queries (GDPR, procurement, vendor)
- Quick proof of retrieval
- Safe, guaranteed success

---

## 🚀 Quick Start

### For OpenWebUI Deployment

1. **Copy v3.1 prompt**:
   ```bash
   cat /workspace/001-bms-agent/docs/SYSTEM_PROMPT_v3.1.md
   ```

2. **Open OpenWebUI Admin**:
   - Navigate to: http://localhost:3000/admin
   - Go to: Settings → Models → [Your Model] → System Prompt

3. **Paste and Save**:
   - Paste entire v3.1 content
   - Save changes
   - Start new chat

4. **Verify**:
   ```
   Query: "Show me GDPR compliance documents"
   Expected: Search results with citations and URLs
   ```

### Test Commands

```bash
# Pre-demo system test (v3.1 compatible)
bash scripts/pre_demo_test.sh

# All search functions test
bash scripts/test_all_search_functions.sh

# Expected: All tests pass with v3.1
```

---

## 💡 Future: HTML Artifacts (Post-POC)

**When to revisit v4.0**:
- After POC signoff (T026 complete)
- During MVP phase
- With better LLM model (GPT-4, Claude)
- Or alternative implementation (API endpoints generate HTML)

**Alternative Approaches**:
1. **API-Side Generation**: API returns HTML, not LLM
2. **Template Engine**: Use Jinja2 templates server-side
3. **Frontend Generation**: React/Vue components render forms
4. **Hybrid**: LLM provides data, frontend renders HTML

**Advantages of Deferring**:
- ✅ POC stays simple and focused
- ✅ Proven technology (search) for demo
- ✅ Faster path to T026 (POC signoff)
- ✅ Can iterate on HTML in MVP with better tools

---

## 📚 Related Documentation

### Active (v3.1)
- `docs/SYSTEM_PROMPT_v3.1.md` - **USE THIS**
- `docs/COMPREHENSIVE_DEMO_GUIDE.md` - Full search demo
- `docs/DEMO_RECORDING_SCRIPT.md` - Step-by-step
- `docs/DEMO_RECORDING_GUIDE.md` - Simple demo
- `scripts/test_all_search_functions.sh` - Verification

### Deprecated (v4.0)
- `docs/SYSTEM_PROMPT_v4.0.md` - Don't use
- `docs/HTML_ARTIFACT_DEPLOYMENT_GUIDE.md` - Reference only
- `docs/AGENTIC_CAPABILITIES_DEMO.md` - Good ideas, revisit in MVP

---

## ✅ Recommendation

**For POC Completion**:
1. Use **v3.1** system prompt
2. Record **comprehensive search demo** (10-12 min)
3. Show all **13 operational functions**
4. Highlight **T036 achievements** (contextual, rerank)
5. Focus on **proven, working features**

**POC Goal**: Demonstrate search functionality works reliably  
**MVP Goal**: Add document generation (HTML or alternative)

---

**Current Status**: v3.1 active, v4.0 deprecated, ready for POC demo recording

**Next Steps**:
1. Confirm v3.1 loaded in OpenWebUI
2. Test with: `scripts/test_all_search_functions.sh`
3. Record demo using: `docs/COMPREHENSIVE_DEMO_GUIDE.md`
4. Complete T032.3
5. Proceed to T026 (POC signoff)
