# AI Agent Prompt Fix - Successfully Deployed

**Date**: 2025-10-13
**Status**: ✅ Deployed to Production
**Workflow**: Nomi Slack copy (ID: M80ziByNiWFCq2fy)

## Problem Summary

After implementing strict character limits to fix Slack message truncation, the AI Agent stopped using tools entirely. Users reported: **"after the latest prompt update the ai node is not using any tools"**

## Root Cause

The previous prompt update focused heavily on:
1. Character limits (1,200 max)
2. "Answer ONLY from retrieved documents"

But didn't emphasize strongly enough that tools MUST be used first. The AI interpreted these constraints as meaning it couldn't effectively use tools, so it stopped calling them entirely.

## Solution Deployed

Updated the AI Agent's system prompt in the active workflow to emphasize tool usage as the PRIMARY requirement:

### Key Changes

**1. Added CRITICAL section at the very top:**
```
**CRITICAL**: You MUST use tools to retrieve information. You do not have any BMS knowledge without using tools first.
```

**2. Made "ALWAYS Use Tools First" the #1 Core Principle:**
```
1. ALWAYS Use Tools First
   • Every query REQUIRES a tool call
   • You have NO knowledge about BMS documents without tools
   • Select the most appropriate tool
   • Execute tool BEFORE responding
   • Answer ONLY from tool results
```

**3. Added Examples Section:**
Provided concrete examples of good tool usage for different query types:
- "how do I start a project?" → use ask_bms tool
- "how many documents?" → use search_doc_list tool
- "find BMS-QHSE-PRO-016" → use search_hybrid tool

**4. Clarified Response Format Timing:**
Made it clear that the 1,200 character limit applies AFTER tool usage:
```
Response Format

**CRITICAL**: Keep responses under 1,200 characters total to fit in Slack.

After using tool, structure response:
1. Direct answer (2-3 sentences, ~200 chars)
2. Key details (3-4 bullet points, ~600 chars)
3. Document citations (2-3 docs, ~250 chars)
```

**5. Added Quality Guidelines Checklist:**
Clear DO/DON'T list:
- ✅ ALWAYS DO: Use a tool for EVERY query
- ❌ NEVER DO: Answer without using tools first

## Changes Applied

**Workflow**: Nomi Slack copy (M80ziByNiWFCq2fy)
**Node Updated**: Nomi (AI Agent)
**Field Changed**: System Message
**Deployment Method**: n8n MCP API (n8n_update_partial_workflow)
**Timestamp**: 2025-10-13T15:47:18.598Z

## What to Test

### Test 1: General Question (Should use ask_bms)
```
@nomi how do I start a project?
```
**Expected**:
- ✅ AI calls ask_bms tool
- ✅ Response includes document citations ([BMS-PROJ-GUI-003], etc.)
- ✅ Response under 1,200 characters
- ✅ No Slack message truncation

### Test 2: Document Count (Should use search_doc_list)
```
@nomi how many documents do we have?
```
**Expected**:
- ✅ AI calls search_doc_list tool
- ✅ Response shows counts by category/department
- ✅ Response under 1,200 characters

### Test 3: Specific Document (Should use search_hybrid)
```
@nomi find BMS-QHSE-PRO-016
```
**Expected**:
- ✅ AI calls search_hybrid tool
- ✅ Response shows document details with score
- ✅ Response includes document URL if available

### Test 4: Concept Question (Should use search_semantic)
```
@nomi what does NMS mean?
```
**Expected**:
- ✅ AI calls search_semantic tool
- ✅ Response explains concept from retrieved documents
- ✅ Cites source documents

## Verification Checklist

Run these checks in Slack:

- [ ] AI agent calls a tool for every query
- [ ] AI agent selects the appropriate tool (ask_bms, search_hybrid, etc.)
- [ ] Responses include document citations with codes
- [ ] Responses stay under 1,200 characters
- [ ] Slack messages display completely (no truncation)
- [ ] Document details appear in "Sources" section when available

## n8n Execution Logs

To verify tool usage in n8n:

1. Open n8n: http://localhost:5678
2. Open workflow: "Nomi Slack copy"
3. Click "Executions" tab
4. Click on latest execution
5. Check "Nomi" (AI Agent) node output
6. Look for tool call in the execution data:
   ```json
   {
     "tool": "ask_bms",
     "input": {"question": "..."},
     "output": "..."
   }
   ```

If no tool call appears, the problem persists.

## Files Reference

| File | Purpose |
|------|---------|
| `/workspace/002-n8n/FIXED_AI_AGENT_PROMPT.txt` | Fixed prompt (source) |
| `/workspace/002-n8n/workflows/bms-ai-agent-optimized.json` | Workflow JSON (updated) |
| `/workspace/002-n8n/AI_AGENT_PROMPT_FIX_DEPLOYED.md` | This deployment report |

## Previous Issues Fixed

This deployment also includes fixes for:

1. ✅ **Slack Message Truncation** - Responses now limited to 1,200 chars
2. ✅ **Concise Formatter** - Document display compact (3 docs max)
3. ✅ **Channel Preservation** - Fixed channel_not_found errors
4. ✅ **Document Details** - Workflow fetches rich metadata

## Next Steps

1. **Test in Slack** - Send test queries to @nomi
2. **Monitor Executions** - Check n8n logs for tool calls
3. **Verify Character Limits** - Ensure responses fit in Slack
4. **Check Document Display** - Verify Sources section appears

## Rollback Plan (If Needed)

If the fix doesn't work or causes issues:

1. Open n8n UI: http://localhost:5678
2. Open "Nomi Slack copy" workflow
3. Click "Nomi" (AI Agent) node
4. Replace System Message with previous version from workflow history
5. Save workflow

Or use the n8n MCP API to restore the previous prompt.

## Success Criteria

The fix is successful when:

- ✅ AI agent calls tools for 100% of queries
- ✅ Tool selection is appropriate for query type
- ✅ Responses include document citations
- ✅ Responses stay under 1,200 characters
- ✅ No Slack message truncation
- ✅ Document metadata displays correctly

---

**Deployed by**: Claude Code
**Approved for**: Production use
**Monitoring**: Check Slack bot responses and n8n execution logs
