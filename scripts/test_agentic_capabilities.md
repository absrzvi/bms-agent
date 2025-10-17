# Agentic Capabilities Test Script

**Purpose**: Verify OpenWebUI + BMS Agent can perform agentic tasks before demo  
**Run**: 30 minutes before recording agentic demo  
**Model Required**: mistral-nemo or similar (capable of structured output)

---

## Quick Pre-Test (5 scenarios, ~10 minutes)

### Test 1: Form Filling ⭐ CRITICAL
**Prompt**:
```
I need to evaluate Siemens Railway Systems as a potential vendor for 
signaling equipment. They're based in Munich, Germany, have 30 years 
of railway experience, ISO9001 and EN50155 certified, and quoted 
€75,000 for the complete system. Can you fill out a vendor evaluation 
form for me?
```

**Expected Output**:
- ✅ Structured form with filled fields
- ✅ Vendor details populated
- ✅ Evaluation criteria with scores
- ✅ Recommendation section
- ✅ 2-4 document citations

**If FAILS**:
- LLM may not generate structured output
- Try simpler prompt: "Fill out vendor evaluation for Siemens"
- Consider showing search + manual explanation instead

**Status**: ☐ Pass ☐ Fail  
**Notes**: _______________________

---

### Test 2: Workflow Creation ⭐ CRITICAL
**Prompt**:
```
Walk me through the complete onboarding process for a new safety 
officer joining the QHSE department. What forms do they need, what 
training is required, and in what order?
```

**Expected Output**:
- ✅ Step-by-step timeline (Week 1, Week 2, etc.)
- ✅ Forms listed with document IDs
- ✅ Training requirements
- ✅ Responsibility assignments
- ✅ 5-10 document citations

**If FAILS**:
- LLM may just list documents without structuring
- Rephrase: "Create an onboarding checklist for QHSE safety officer"
- Focus on "what documents exist" rather than "create a plan"

**Status**: ☐ Pass ☐ Fail  
**Notes**: _______________________

---

### Test 3: Multi-Document Comparison
**Prompt**:
```
Compare the procurement processes between ENGI and QHSE departments. 
What are the differences in approval thresholds, timelines, and 
required documentation?
```

**Expected Output**:
- ✅ Comparison table or structured list
- ✅ Specific differences identified
- ✅ Explanations for why differences exist
- ✅ 3-5 document citations (both departments)

**If FAILS**:
- LLM may describe each separately without comparison
- Try: "What's different between ENGI and QHSE procurement?"
- Show side-by-side outputs even if not formatted as table

**Status**: ☐ Pass ☐ Fail  
**Notes**: _______________________

---

### Test 4: "Why" Explanation
**Prompt**:
```
Why do we need three quotes for procurement over €10,000? It seems 
like extra work. What's the actual benefit?
```

**Expected Output**:
- ✅ Explains rationale (not just states rule)
- ✅ Lists 3-5 specific benefits
- ✅ Provides context or examples
- ✅ Acknowledges the effort but justifies
- ✅ 2-3 document citations

**If FAILS**:
- LLM may just quote policy without explaining
- This is actually a STRENGTH—shows grounding
- Can still demo as "policy explanation"

**Status**: ☐ Pass ☐ Fail  
**Notes**: _______________________

---

### Test 5: Safety Checklist Generation
**Prompt**:
```
I'm installing new brake systems in Railjet trains. Generate a safety 
checklist for the installation team covering pre-installation, during 
installation, and post-installation safety requirements.
```

**Expected Output**:
- ✅ Structured checklist (pre/during/post)
- ✅ 10-20 checklist items with ✅ checkboxes
- ✅ Organized by phase
- ✅ Safety-specific items (PPE, lockout, testing)
- ✅ 3-5 safety document citations

**If FAILS**:
- LLM may provide narrative instead of checklist
- Can still show as "safety procedure explanation"
- Reframe: "What safety steps are required for brake installation?"

**Status**: ☐ Pass ☐ Fail  
**Notes**: _______________________

---

## Test Results Summary

**Tests Passed**: ____ / 5

### If 5/5 Pass: ✅ FULL AGENTIC DEMO
You can record the complete 15-20 minute agentic demo showing:
- Document generation
- Workflow creation
- Multi-doc analysis
- Intelligent Q&A
- Quality validation

### If 3-4/5 Pass: ⚠️ MODIFIED AGENTIC DEMO
Focus on scenarios that worked:
- If form filling works → emphasize document automation
- If workflow works → emphasize process guidance
- If comparison works → emphasize analysis capabilities
- Skip scenarios that don't generate good structured output

### If 0-2/5 Pass: 🔄 FALL BACK TO SEARCH DEMO
The LLM may not be generating structured outputs effectively.
Options:
1. Use original comprehensive search demo (13 functions)
2. Show "search + explanation" style (still valuable)
3. Demo simple Q&A rather than document generation
4. Consider upgrading LLM model (GPT-4, Claude, etc.)

---

## Detailed Evaluation Criteria

### For Test 1 (Form Filling):
- [ ] Agent searches for vendor evaluation form
- [ ] Agent extracts form structure
- [ ] Agent fills vendor details (Siemens, Munich, Germany)
- [ ] Agent adds technical criteria (ISO9001, EN50155)
- [ ] Agent calculates/adds financial data (€75k)
- [ ] Agent provides evaluation scores (1-5 scale)
- [ ] Agent gives recommendation (Approved/Review/Reject)
- [ ] Agent cites 2-4 policy documents
- [ ] Output is structured (not just narrative)
- [ ] Output is actionable (could be used as-is)

**Scoring**: 8-10 = Excellent, 5-7 = Good, 0-4 = Weak

### For Test 2 (Workflow):
- [ ] Agent searches multiple documents (5-10)
- [ ] Agent organizes by timeline (Week 1, 2, 3, etc.)
- [ ] Agent lists specific forms with IDs
- [ ] Agent includes training requirements
- [ ] Agent assigns responsibilities (HR, manager, employee)
- [ ] Agent shows dependencies (do X before Y)
- [ ] Output is chronological and logical
- [ ] Output includes 8-15 concrete action items
- [ ] Agent cites 5+ supporting documents
- [ ] Output could be used as actual onboarding plan

**Scoring**: 8-10 = Excellent, 5-7 = Good, 0-4 = Weak

### For Test 3 (Comparison):
- [ ] Agent retrieves docs from both departments
- [ ] Agent identifies 3+ specific differences
- [ ] Agent explains WHY differences exist
- [ ] Agent uses structured format (table or side-by-side)
- [ ] Agent compares equivalent aspects (apples to apples)
- [ ] Agent cites docs from both departments
- [ ] Output is easy to scan/compare
- [ ] Output reveals insights (not just describing each)

**Scoring**: 7-8 = Excellent, 4-6 = Good, 0-3 = Weak

### For Test 4 ("Why" Explanation):
- [ ] Agent searches for policy rationale
- [ ] Agent lists 3-5 specific benefits
- [ ] Agent explains in practical terms
- [ ] Agent provides examples or context
- [ ] Agent acknowledges the user's concern
- [ ] Agent justifies the requirement
- [ ] Tone is helpful (not just "because policy says so")
- [ ] Cites authoritative sources

**Scoring**: 7-8 = Excellent, 4-6 = Good, 0-3 = Weak

### For Test 5 (Checklist):
- [ ] Agent searches for safety procedures
- [ ] Agent creates structured checklist (not paragraph)
- [ ] Agent uses ✅ checkboxes or numbering
- [ ] Agent organizes by phase (pre/during/post)
- [ ] Agent includes 12-20 specific items
- [ ] Items are actionable ("Check X", "Verify Y")
- [ ] Safety-specific items included (PPE, lockout)
- [ ] Agent cites safety standards and procedures

**Scoring**: 7-8 = Excellent, 4-6 = Good, 0-3 = Weak

---

## Known Limitations & Workarounds

### Limitation 1: LLM Not Generating Structured Output
**Symptom**: Responses are narrative paragraphs, not forms/tables/checklists

**Workaround**:
- Emphasize "search + explanation" rather than "generation"
- Show agent finding relevant documents and explaining them
- Focus on intelligence of retrieval rather than output format
- This is still valuable—just different framing

**Demo Pivot**: "BMS Agent - Intelligent Search with Context"

---

### Limitation 2: Citations Not Appearing
**Symptom**: LLM generates content but doesn't cite sources

**Workaround**:
- Check system prompt is loaded correctly
- Verify SYSTEM_PROMPT_v3.1.md is in tool configuration
- May need to explicitly request citations in prompt
- Add "and cite your sources" to each prompt

**Demo Note**: Emphasize that agent CAN'T hallucinate—only uses retrieved docs

---

### Limitation 3: Responses Too Slow (>30 seconds)
**Symptom**: Agent takes too long to respond for demo

**Workaround**:
- Use simpler prompts (shorter, more direct)
- Reduce limit parameter (search fewer docs)
- Pre-run queries before recording to "warm up"
- Consider showing "thinking..." message as feature

**Demo Note**: "Agent is analyzing 5-7 documents" (shows thoroughness)

---

### Limitation 4: Inconsistent Quality
**Symptom**: Some prompts work great, others fail

**Workaround**:
- Test each scenario 2-3 times before recording
- Keep only scenarios that consistently work
- Have backup prompts ready
- Record multiple takes if needed

**Demo Strategy**: Only show your best 3-4 scenarios, not all 10

---

## Pre-Demo Decision Tree

```
START: Run 5 quick tests
   ↓
5/5 Pass? → YES → Record FULL AGENTIC DEMO (15-20 min)
   ↓ NO
3-4 Pass? → YES → Record MODIFIED DEMO (10-12 min, successful scenarios only)
   ↓ NO
0-2 Pass? → YES → Record SEARCH DEMO (use comprehensive search guide)
   ↓
Choose demo type based on test results
   ↓
Record with confidence (tested and verified)
```

---

## Backup Demo Options

### Backup Option 1: Hybrid Demo (12 minutes)
- Part 1: Core search functions (3 functions, 3 min)
- Part 2: Successful agentic scenarios (2-3 scenarios, 6 min)
- Part 3: Summary (what works today, what's coming)

### Backup Option 2: Search + Explanation (10 minutes)
- Show all 13 search functions (as planned)
- Add 2-3 "explain this document" scenarios
- Focus on retrieval intelligence rather than generation

### Backup Option 3: Use Case Demo (12 minutes)
- Scenario 1: New employee needs forms (search + list)
- Scenario 2: Manager needs compliance info (search + explain)
- Scenario 3: Auditor needs document comparison (search + analysis)
- Focus on practical workflows rather than features

---

## ✅ Final Pre-Recording Checklist

### System Check
- [ ] OpenWebUI accessible (http://localhost:3000)
- [ ] BMS API healthy (curl http://localhost:8000/health)
- [ ] LLM model loaded (mistral-nemo or better)
- [ ] BMS search tool active in OpenWebUI

### Agentic Tests
- [ ] Test 1: Form filling (☐ Pass ☐ Fail)
- [ ] Test 2: Workflow creation (☐ Pass ☐ Fail)
- [ ] Test 3: Document comparison (☐ Pass ☐ Fail)
- [ ] Test 4: "Why" explanation (☐ Pass ☐ Fail)
- [ ] Test 5: Checklist generation (☐ Pass ☐ Fail)

### Demo Decision
- [ ] Passed tests: ____ / 5
- [ ] Demo type chosen: ☐ Full Agentic ☐ Modified ☐ Search-Focus
- [ ] Recording script selected
- [ ] Backup scenarios identified
- [ ] Response times acceptable (<20s per query)

### Recording Prep
- [ ] Browser zoom 110%
- [ ] Chat history cleared
- [ ] Screen recorder ready
- [ ] Demo script open
- [ ] Backup prompts ready

---

**Status**: ☐ Ready to Record ☐ Need Adjustments

**Notes**: 
```
[Your observations from testing]
```

---

**Remember**: Even if agentic features don't work perfectly, the comprehensive search demo (13 functions, 65% coverage) is still excellent POC evidence! The agentic capabilities are "bonus wow factor" if they work.
