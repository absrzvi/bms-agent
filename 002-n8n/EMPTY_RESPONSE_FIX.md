# Empty AI Response Fix - Tool Results Not Being Used

**Issue**: AI Agent successfully calls tools and gets results, but returns empty response to user.

## Problem Analysis

### What's Happening

1. ✅ **Tool Call Works**: AI Agent successfully calls `search_semantic` tool
2. ✅ **Tool Returns Data**: Gets 10 results with scores 0.42-0.50
3. ✅ **LLM Generates Tokens**: 800 completion tokens generated
4. ❌ **Response is Empty**: `"text": ""` in output

### Root Cause

The `granite4:small-h` model is from the **GraniteHybrid** family - a tool-calling model that uses special output formatting. When n8n's LangChain integration processes the response:

1. Model wraps response in function-calling syntax
2. LangChain's parser extracts tool calls
3. Parser strips the wrapper
4. **No final answer remains** → empty text

This is a **known issue with tool-calling models in n8n's AI Agent node**.

## Solution Options

### Option 1: Switch to Non-Tool-Calling Model (RECOMMENDED)

Use a standard chat model instead of a hybrid tool-calling model.

**Best Models for n8n AI Agent**:
- `mistral-nemo:12b-instruct` - Good balance of quality and speed
- `llama3.3:70b-instruct` - Highest quality (if you have GPU)
- `qwen2.5:14b-instruct` - Good for technical content

**How to Fix**:
1. Open n8n UI: http://localhost:5678
2. Open "Nomi Slack copy" workflow
3. Click "Ollama Chat Model" node
4. Change model from `granite4:small-h` to `mistral-nemo:12b-instruct`
5. Update parameters:
   ```json
   {
     "temperature": 0.7,
     "topK": 40,
     "topP": 0.9,
     "numCtx": 8192,        // Increased context window
     "numPredict": 1500,    // Increased output limit
     "repeatPenalty": 1.1
   }
   ```
6. Save workflow

**Why This Works**:
- mistral-nemo is a pure chat model, not a tool-calling model
- n8n's AI Agent handles tool orchestration
- LLM only needs to generate final response text

### Option 2: Add Response Formatter Node (WORKAROUND)

Keep granite4 but add a node to extract response from tool results.

**Implementation**:
1. Add a new Code node after "Nomi" (AI Agent)
2. Name it "Extract AI Response from Tool Results"
3. Add this code:

```javascript
const agentOutput = $input.item.json;

// Check if we have tool results but empty text
const hasToolOutput = agentOutput.tool && agentOutput.tool.results;
const hasEmptyText = !agentOutput.output || agentOutput.output.trim() === '';

if (hasToolOutput && hasEmptyText) {
  // Extract tool results
  const toolResults = agentOutput.tool.results || [];

  // Format a response from the tool results
  let response = '';

  if (toolResults.length > 0) {
    // Get top 3 results
    const topResults = toolResults.slice(0, 3);

    // Build response
    response = `Based on the documentation:\n\n`;

    topResults.forEach((result, i) => {
      const score = (parseFloat(result.score) * 100).toFixed(0);
      response += `${i + 1}. [${result.document_name}] (${score}% match)\n`;
      response += `${result.content.substring(0, 300)}...\n\n`;
    });

    response += `\nSee ${result.document_name} for more details.`;
  } else {
    response = "I couldn't find relevant documentation for that query.";
  }

  // Return with formatted response
  return {
    json: {
      ...agentOutput,
      output: response,
      text: response,
      hasEmptyResponseFix: true
    }
  };
}

// If response is not empty, pass through
return { json: agentOutput };
```

4. Update workflow connections:
   - Nomi → Extract AI Response → Fetch Document Details

**Why This Works**:
- Bypasses the LangChain parsing issue
- Manually formats response from tool results
- Still uses granite4's tool-calling capability

### Option 3: Use OpenAI-Compatible Model (ADVANCED)

Use a model that fully implements OpenAI's function-calling API.

**Not Recommended** because:
- Requires additional setup
- Ollama's function calling is still experimental
- Option 1 is simpler and works better

## Testing the Fix

After implementing Option 1 (recommended), test with:

```
@nomi what is NMS?
```

**Expected Output** (with mistral-nemo):
```
NMS stands for Network Management System. It's a mobile operator-grade monitoring
tool for railway fleets with 4 key components:

1. Real-time fleet status and location tracking
2. Performance monitoring with customizable metrics
3. Fault management with automated alerts
4. User activity reporting via web interface

The system integrates with Remedy Force ticketing and supports data export in
JSON/CSV formats. It runs on Kubernetes for high availability.

[Anlage 3F - Case Study_v1.0 en.docx] - Multiple sections covering NMS functionality
```

**Success Criteria**:
- ✅ Response contains actual information (not empty)
- ✅ Mentions NMS components
- ✅ Cites document source
- ✅ Under 1,200 characters
- ✅ Appears in Slack without truncation

## Why granite4:small-h Failed

**granite4:small-h characteristics**:
- Family: `granitehybrid`
- Size: 32.2B parameters (quantized to Q4_K_M)
- **Designed for**: Native function calling
- **Problem**: n8n's AI Agent already handles function calling

**What happened**:
1. n8n AI Agent: "Call this tool" → granite4
2. granite4: Generates response with `<tool_call>` wrapper
3. LangChain parser: Extracts tool call, executes it
4. LangChain parser: Looks for final answer... finds none
5. n8n: Returns empty text

**Model mismatch**: granite4's built-in tool calling conflicts with n8n's agent framework.

## Recommended Configuration

### Updated Ollama Chat Model Node

```json
{
  "parameters": {
    "model": "mistral-nemo:12b-instruct",
    "options": {
      "temperature": 0.7,
      "topK": 40,
      "topP": 0.9,
      "numCtx": 8192,
      "numPredict": 1500,
      "repeatPenalty": 1.1
    }
  },
  "name": "Ollama Chat Model",
  "type": "@n8n/n8n-nodes-langchain.lmChatOllama"
}
```

### Model Comparison

| Model | Family | Best For | Context | Output | n8n AI Agent |
|-------|--------|----------|---------|--------|--------------|
| granite4:small-h | granitehybrid | Native tool calling | 4096 | 800 | ❌ Conflicts |
| mistral-nemo:12b | mistral | General chat | 8192 | 1500 | ✅ Perfect |
| llama3.3:70b | llama3 | High quality | 8192 | 2048 | ✅ Great |
| qwen2.5:14b | qwen2 | Technical docs | 32768 | 2048 | ✅ Great |

## Implementation Steps

1. **Pull mistral-nemo model** (if not already installed):
   ```bash
   ollama pull mistral-nemo:12b-instruct
   ```

2. **Update workflow**:
   - Open n8n UI
   - Edit "Ollama Chat Model" node
   - Change model to `mistral-nemo:12b-instruct`
   - Update numCtx to 8192
   - Update numPredict to 1500
   - Save workflow

3. **Test in Slack**:
   ```
   @nomi what is NMS?
   ```

4. **Verify in n8n logs**:
   - Check execution output
   - Verify `output` field has content
   - Confirm response appears in Slack

## Alternative: Keep granite4 + Formatter Node

If you want to keep granite4:small-h (not recommended), implement Option 2:

1. Add "Extract AI Response from Tool Results" code node
2. Place between "Nomi" and "Fetch Document Details"
3. Copy code from Option 2 above
4. Test thoroughly

**Drawbacks**:
- More complex workflow
- Manual response formatting
- Harder to maintain
- Bypasses LLM's natural language generation

## Summary

**Problem**: Tool-calling model (granite4) conflicts with n8n's AI Agent framework

**Best Solution**: Switch to mistral-nemo:12b-instruct (pure chat model)

**Expected Result**: AI Agent generates complete responses using tool results

**Status**: Ready to implement (5 minutes)

---

**Created**: 2025-10-13
**Priority**: Critical (bot non-functional)
**Estimated Fix Time**: 5 minutes
