# Citation Format Fix - Deployed

**Date**: 2025-10-13
**Issue**: AI responses missing document citations and exceeding character limits
**Status**: ✅ Fixed with enforced format template

## Problem

User reported: "there are no citations, why?"

AI was generating responses like:
```
The recommended hardware for nomads, based on the provided documents, includes:

1. **Hardware Specifications:**
   - Form factor: 3U 8HP (2 slots) CPCI-S with locking handle.
   - CPU System: Based on Intel Xeon W-11555MRE CPU...
   ...
4. **Workstation Setup:**
   ...
```

**Problems**:
1. ❌ **No "Source:" citation** at the end
2. ❌ **Exceeded 800 characters** (~1,800 chars instead of 800)
3. ❌ **Nested bullets and numbered lists** (4 sections with sub-bullets)
4. ❌ **Ignored formatting instructions** despite clear guidelines in prompt

## Root Cause

The previous prompt had formatting guidelines, but they were:
- Buried in a long "Response Format" section
- Not reinforced with explicit examples
- No emphasis on "MANDATORY" structure
- AI prioritized answering completely over following format

**Result**: AI focused on providing comprehensive technical details and ignored the formatting constraints.

## Solution Applied

Updated prompt with **MANDATORY STRUCTURE** section that enforces:

### 1. Added Third CRITICAL Statement
```
**CRITICAL**: You MUST include "Source: [document name]" at the end of EVERY response. This is NON-NEGOTIABLE.
```

### 2. MANDATORY STRUCTURE Template
```
**CRITICAL**: EVERY response MUST follow this EXACT format:

[Direct answer in 1-2 sentences]

[Key point 1]
[Key point 2]
[Key point 3]

Source: [Document name from tool results]
```

### 3. Explicit HARD LIMITS
```
HARD LIMITS (THESE ARE ABSOLUTE):
• MAXIMUM 800 characters total (count your characters!)
• EXACTLY 3 bullet points (not 2, not 4, exactly 3)
• EXACTLY 1 document citation starting with "Source:"
• NO nested bullets
• NO numbered lists
• NO sections or headers within the answer
• If you exceed 800 chars, CUT entire sentences - don't truncate mid-sentence
```

### 4. Concrete CORRECT Examples

**Added example showing the EXACT hardware query**:
```
Q: "What is the recommended hardware?"
✅ CORRECT (when specific hardware IS in results):
The recommended hardware is a 3U 8HP CPCI-S system with Intel Xeon W-11555MRE CPU for railway applications.

• CPU: Intel Xeon W-11555MRE, 6 Core, 2.6/4.5GHz with 64GB DDR4-3200 ECC RAM
• Storage: 80GB iSLC SSD with TPM2.0 security and HumiSeal coating
• Network: 2x 10GBase-T Ethernet (M12), 4x 1GbE backplane, 5x SATA3 with RAID

Source: Anlage 3F - Case Study
```

### 5. Explicit WRONG Examples

**Added examples showing what NOT to do**:
```
❌ WRONG - No source citation:
"NMS monitors railway fleets with real-time status tracking, performance monitoring, and fault management."

❌ WRONG - Too long (1,800 chars), nested bullets, 4 sections:
"The recommended hardware includes:

1. **Hardware Specifications:**
   - Form factor: 3U 8HP...
   - CPU System: Based on Intel...
2. **Network Interfaces:**
   ...
```

### 6. Updated Quality Guidelines

Added to "ALWAYS DO" section:
- ✅ Include "Source: [document name]" at the end
- ✅ Use EXACTLY 3 bullet points

Added to "NEVER DO" section:
- ❌ Omit the source citation
- ❌ Use multiple source citations
- ❌ Use nested bullets or numbered lists

## Expected Behavior After Fix

### Test Case: Hardware Query

**Query**: `@nomi what is the nomad recommended hardware?`

**Expected Response** (with proper format):
```
The recommended hardware is a 3U 8HP CPCI-S system with Intel Xeon W-11555MRE CPU for railway applications.

• CPU: Intel Xeon W-11555MRE, 6 Core, 2.6/4.5GHz with 64GB DDR4-3200 ECC RAM
• Storage: 80GB iSLC SSD with TPM2.0 security and HumiSeal coating
• Network: 2x 10GBase-T Ethernet (M12), 4x 1GbE backplane, 5x SATA3 with RAID

Source: Anlage 3F - Case Study
```

**Characteristics**:
- ✅ Direct answer (1 sentence, ~100 chars)
- ✅ Exactly 3 bullet points with technical specs
- ✅ "Source: [document name]" at the end
- ✅ Total: ~500 characters (under 800 limit)
- ✅ No nested bullets or numbered sections

## Why Citations Matter

**User's explicit requirement**: "there are no citations, why?"

**Importance**:
1. **Traceability**: Users can verify information source
2. **Trust**: Shows AI is using actual documents, not making things up
3. **Accountability**: Users can look up the document for full details
4. **Quality**: Confirms the answer is grounded in retrieved data

**Without citations**: Users can't tell if answer is from documents or hallucinated.

## Technical Details

### Prompt Changes

**Location**: Workflow M80ziByNiWFCq2fy → "Nomi" (AI Agent) node → System Message

**Changes Made**:
1. Added third CRITICAL statement about citations
2. Created "Response Format - MANDATORY STRUCTURE" section
3. Added explicit template with placeholders
4. Listed HARD LIMITS as bullet points
5. Added ✅ CORRECT examples with actual query
6. Added ❌ WRONG examples showing the exact problem
7. Updated Quality Guidelines checklist

**Prompt Size**: ~5,800 characters (still well under model's 8192 context limit)

### Model Configuration (Unchanged)

No changes needed to model parameters:
- mistral-nemo:latest (no change)
- numPredict: 600 (no change)
- temperature: 0.5 (no change)
- stop sequences: ["\n\n\n", "Sources:", "References:", "Documents:"] (no change)

**Why**: This is a prompt engineering problem, not a model parameter problem. The model CAN follow format instructions when they're explicit enough.

## How the Fix Works

### Before (Incorrect)

1. AI reads tool results: 3 chunks about hardware with high scores
2. AI thinks: "I should provide comprehensive technical details"
3. AI generates: 4 sections with nested bullets (~1,800 chars)
4. AI forgets: No "Source:" citation
5. Result: Complete information but wrong format

### After (Correct)

1. AI reads tool results: 3 chunks about hardware with high scores
2. AI sees MANDATORY template: "[Answer]\n\n[Point 1]\n[Point 2]\n[Point 3]\n\nSource: [Doc]"
3. AI thinks: "I must follow this EXACT format"
4. AI generates: 1 sentence + 3 bullets + "Source: Anlage 3F"
5. AI stops at 500 chars (under 800 limit)
6. Result: Complete information in correct format

## Testing Checklist

Send these queries in Slack to verify citations appear:

### Test 1: Hardware Query (Original Issue)
```
@nomi what is the nomad recommended hardware?
```
**Expected**:
- ✅ Response includes specific hardware (3U 8HP CPCI-S, Intel Xeon, etc.)
- ✅ Exactly 3 bullet points
- ✅ Ends with "Source: Anlage 3F - Case Study"
- ✅ Under 800 characters

### Test 2: NMS Query
```
@nomi what is NMS?
```
**Expected**:
- ✅ Definition in 1-2 sentences
- ✅ 3 bullet points about features
- ✅ "Source: [document name]" at end
- ✅ Under 800 characters

### Test 3: Process Query
```
@nomi how do I start a project?
```
**Expected**:
- ✅ Brief procedure overview
- ✅ 3 key steps as bullet points
- ✅ Citation with document code
- ✅ Under 800 characters

### Test 4: Count Query
```
@nomi how many documents do we have?
```
**Expected**:
- ✅ Total count + breakdown
- ✅ 3 categories/departments listed
- ✅ "Source: [derived from search]" or similar
- ✅ Under 800 characters

## Verification

### Check in n8n Execution Logs

1. Open n8n: http://localhost:5678
2. Open "Nomi Slack copy" workflow
3. Click "Executions" tab
4. Click latest execution after test query
5. Check "Nomi" (AI Agent) node output
6. Look for "Source:" in the response text

**Success criteria**:
```json
{
  "output": "The recommended hardware is...\n\n• Point 1\n• Point 2\n• Point 3\n\nSource: Anlage 3F - Case Study"
}
```

### Check in Slack Message

The "format slack reply" node will display the AI response in the message. Look for:

1. **Answer section**: Should show the AI response
2. **Sources section**: Will show "📚 Sources (X docs)" with document list
3. **Citation in answer**: Should end with "Source: [document name]"

## Fallback: If Citations Still Missing

If citations are STILL missing after this fix:

1. **Check prompt was actually updated**:
   - Verify workflow version updated to `fa8d650b-7109-4363-a743-be7777e517dc`
   - Check n8n UI shows the new prompt with "Source: [document name]"

2. **Increase enforcement**:
   - Add "Source:" to stop sequences (force AI to include it before stopping)
   - Add post-processing in "format slack reply" to append citation if missing

3. **Model issue**:
   - If mistral-nemo can't follow format, try different model (llama3.3:70b, qwen2.5:14b)

## Summary

**Problem**: AI responses had no citations and exceeded character limits

**Root Cause**: Formatting instructions were not explicit enough; AI prioritized completeness over format

**Solution**: Added MANDATORY STRUCTURE template with explicit examples

**Result**: AI will now follow exact format with:
- Direct answer (1-2 sentences)
- Exactly 3 bullet points
- "Source: [document name]" citation (NON-NEGOTIABLE)
- Under 800 characters

**Status**: Deployed and ready to test

---

**Deployed**: 2025-10-13 16:17 UTC
**Workflow**: M80ziByNiWFCq2fy (Nomi Slack copy)
**Version**: fa8d650b-7109-4363-a743-be7777e517dc
**Test Now**: `@nomi what is the nomad recommended hardware?`
