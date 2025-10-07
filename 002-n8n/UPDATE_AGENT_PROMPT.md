# How to Update BMS AI Agent System Prompt

## Quick Update (Via n8n UI)

**1. Open the workflow:**
```
http://localhost:5678/workflow/FyOwgZgsPFfsP2TE
```

**2. Click on "BMS AI Agent" node** (center node)

**3. Scroll down to "Options" section** and expand it

**4. Find "System Message" field**

**5. Copy the new prompt:**
```bash
cat /workspace/002-n8n/system-prompt-for-agent.txt
```

**6. Paste into "System Message" field** (replacing the old prompt)

**7. Click "Save"** (top right)

---

## Automated Update (Via API)

```bash
# Read the new prompt
NEW_PROMPT=$(cat /workspace/002-n8n/system-prompt-for-agent.txt)

# Update the workflow via n8n API
curl -X PATCH http://localhost:5678/api/v1/workflows/FyOwgZgsPFfsP2TE \
  -H "X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4ODczMzU4MC1lYzVkLTQyNDQtODNiNC02Y2UzZjcyMGMwYzIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU5NzU4NjUxfQ.Jw6PkPgleHX6YsvA7gsZPI0rrYiTmVY_nDlYpZAIA2o" \
  -H "Content-Type: application/json" \
  -d @<(jq -n \
    --arg prompt "$NEW_PROMPT" \
    '{
      "nodes": [
        {
          "id": "ai-agent",
          "parameters": {
            "options": {
              "systemMessage": $prompt
            }
          }
        }
      ]
    }')
```

---

## What Changed

| Aspect | Before | After |
|--------|--------|-------|
| **Model info** | Generic assistant | Mistral-Nemo with knowledge cutoff |
| **Tool guidance** | Simple descriptions | Decision table with examples |
| **Response format** | Basic answers | Workflow steps + comprehensive answer + citations |
| **Citations** | Simple inline | Structured with metadata in <sub> |
| **Safety emphasis** | Mentioned | Strongly emphasized with CRITICAL tag |
| **Privacy** | Basic | Explicit redaction rules |
| **Explanations** | Moderate | Comprehensive WHY/WHAT/HOW required |
| **Examples** | None | Full response example included |

---

## Test After Update

**Test Query:**
```
What are the emergency brake procedures?
```

**Expected Output Format:**
```
<sub>Step 1: Direct question → Ask BMS</sub>
<sub>Step 2: Action: Ask BMS(...)</sub>
<sub>Step 3: Synthesize comprehensive answer</sub>

[Comprehensive flowing paragraphs explaining WHY emergency brake
procedures exist, WHAT they accomplish, and HOW to execute them,
with inline citations [1], [2], [3]]

<sub>
[1] Emergency Brake System Operating Procedures
   Source: [metadata]
   Relevance: 95%
[2] Railway Safety Protocols
   Source: [metadata]
   Relevance: 92%
</sub>
```

**NOT Expected:**
- ❌ Brief bullet-point answer
- ❌ No citations
- ❌ No workflow steps
- ❌ Generic response without context

---

## Key Improvements

### 1. Better Tool Selection
Agent now has a clear decision table:
- Direct questions → Ask BMS
- Technical terms (VLAN, model numbers) → Hybrid Search
- Comprehensive procedures → Contextual Search
- Concept search → Semantic Search

### 2. Richer Responses
- Workflow steps shown in small text
- Comprehensive explanations (not just lists)
- Inline citations [1], [2], [3]
- Source references with metadata

### 3. Safety Emphasis
- Explicit rules for safety-critical information
- Multiple source citation requirement
- Warning preservation and emphasis

### 4. Privacy Protection
- Personal information redaction required
- Use of role-based references ("your supervisor")
- No names, contacts, or credentials

### 5. Conversation Awareness
- Explicit guidance on using memory
- Follow-up question handling
- Context reference handling

---

## Files

- **System Prompt**: `/workspace/002-n8n/system-prompt-for-agent.txt` (copy-paste ready)
- **Documentation**: `/workspace/002-n8n/BMS_AI_AGENT_SYSTEM_PROMPT.md` (full guide)
- **This File**: `/workspace/002-n8n/UPDATE_AGENT_PROMPT.md`

---

## Verification

After updating, test with these queries:

1. **Direct question**: "What are emergency brake procedures?"
   - Should use Ask BMS
   - Should show workflow steps
   - Should have comprehensive answer with citations

2. **Technical query**: "VLAN 100 configuration"
   - Should use Hybrid Search BMS
   - Should preserve technical codes/specs

3. **Follow-up**: "What are the safety requirements for that?"
   - Should reference previous context
   - Should use conversation memory

4. **Out of scope**: "What's the weather?"
   - Should clearly state it's not in railway documentation
   - Should suggest consulting appropriate resources

---

**Ready to update! The new prompt will make responses more comprehensive, better structured, and safety-conscious. 🚂🤖**
