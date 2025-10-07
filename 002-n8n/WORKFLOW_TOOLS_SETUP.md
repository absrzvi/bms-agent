# BMS AI Agent - Workflow Tools Setup Guide

## Problem Solved

The original `bms-ai-agent.json` workflow used HTTP Request tools with `$fromAI()` expressions, which causes "No execution data available" errors in n8n 1.113.3. This is a [known limitation](https://github.com/n8n-io/n8n/issues/14274) with the platform.

## Solution: Call n8n Workflow Tools

Instead of HTTP Request tools, we now use **Call n8n Workflow Tools** that invoke separate sub-workflows. Each sub-workflow handles one BMS API endpoint.

## Files Created

### Sub-Workflows (Import These First)
1. **bms-tool-ask.json** - Calls `/api/v1/ask` endpoint
2. **bms-tool-semantic-search.json** - Calls `/api/v1/search/semantic` endpoint
3. **bms-tool-hybrid-search.json** - Calls `/api/v1/search/hybrid` endpoint
4. **bms-tool-contextual-search.json** - Calls `/api/v1/search/contextual` endpoint

### Main Workflow
5. **bms-ai-agent.json** - Main AI Agent workflow with workflow tools

## Import Instructions

### Step 1: Import Sub-Workflows

In n8n, import each sub-workflow file in this order:

```bash
# In n8n UI: Workflows > Import from File
1. Import bms-tool-ask.json
2. Import bms-tool-semantic-search.json
3. Import bms-tool-hybrid-search.json
4. Import bms-tool-contextual-search.json
```

**Note:** These workflows don't need to be activated. They run on-demand when called.

### Step 2: Import Main Workflow

```bash
# In n8n UI: Workflows > Import from File
5. Import bms-ai-agent.json
```

### Step 3: Connect Tools to Sub-Workflows

After importing, you'll need to connect each tool node to its corresponding sub-workflow:

1. Open the **BMS AI Agent** workflow in n8n
2. Click on each tool node and select the corresponding sub-workflow:

| Tool Node | Connect to Sub-Workflow |
|-----------|-------------------------|
| Ask BMS | BMS Tool - Ask |
| Semantic Search BMS | BMS Tool - Semantic Search |
| Hybrid Search BMS | BMS Tool - Hybrid Search |
| Contextual Search BMS | BMS Tool - Contextual Search |

### Step 4: Configure Ollama Model

Make sure the Ollama Chat Model node is configured:
- Model: `mistral-nemo:12b-instruct`
- Base URL: `http://localhost:11434`

### Step 5: Activate and Test

1. Activate the main workflow
2. Visit the chat interface: `http://localhost:5678/webhook-test/bms-ai-agent-chat`
3. Ask a question like: "What are the railway safety procedures?"

## How It Works

### Architecture Flow

```
User Question
    ↓
Chat Trigger
    ↓
Parse Input
    ↓
AI Agent (decides which tool to use)
    ↓
Call n8n Workflow Tool
    ↓
Sub-Workflow (HTTP Request to BMS API)
    ↓
API Response
    ↓
AI Agent (generates final answer)
    ↓
Respond to Webhook
```

### Why This Works

1. **No $fromAI() in HTTP Requests**: The sub-workflows use regular n8n expressions (`$json.query`), avoiding the limitation
2. **Clean Parameter Passing**: The AI Agent passes parameters to sub-workflows through the workflow execution context
3. **Modular Design**: Each tool is isolated, making debugging and updates easier
4. **Reliable Execution**: Uses stable n8n workflow calling mechanism instead of experimental AI functions

## Advantages Over HTTP Request Tools

| Feature | HTTP Request Tools | Workflow Tools |
|---------|-------------------|----------------|
| $fromAI() support | ❌ Broken | ✅ Not needed |
| Debugging | Difficult | Easy (view sub-workflow) |
| Reusability | No | Yes (can call from other workflows) |
| Error handling | Limited | Full n8n error handling |
| Testing | Must run full agent | Can test sub-workflows independently |

## Troubleshooting

### Tool Not Found Error

**Problem:** "Workflow not found" error when AI Agent tries to call a tool

**Solution:**
1. Make sure all 4 sub-workflows are imported
2. Check that each tool node in the main workflow has the correct workflow selected
3. The workflow name must match exactly (e.g., "BMS Tool - Ask")

### API Connection Error

**Problem:** HTTP Request fails with connection refused

**Solution:**
1. Verify BMS API is running: `curl http://localhost:8000/health`
2. Check the URL in each sub-workflow HTTP Request node
3. Make sure you're using the correct port (8000 by default)

### Agent Not Using Tools

**Problem:** AI Agent responds without calling any tools

**Solution:**
1. Check the system prompt in the AI Agent node
2. Verify tools are connected to the agent (ai_tool connections)
3. Try a more explicit question: "Use Ask BMS to find information about..."

## Testing Individual Tools

You can test each sub-workflow independently:

```bash
# In n8n, open a sub-workflow and click "Execute Workflow"
# Provide test input in the "Execute Workflow Trigger" node

# Example test input for bms-tool-ask.json:
{
  "question": "What are railway safety procedures?"
}

# Example test input for search tools:
{
  "search_query": "emergency brake"
}
```

## Next Steps

1. **MS Teams Integration**: Connect this workflow to the MS Teams Bot Main Handler
2. **Additional Tools**: Add more sub-workflows for document upload, status checks, etc.
3. **Monitoring**: Use n8n's execution log to monitor tool usage and performance
4. **Customization**: Adjust the AI Agent system prompt to change behavior

## Related Files

- `bms-ai-simple-direct.json` - Simple direct API calling workflow (no AI Agent)
- `BMS_AI_AGENT_GUIDE.md` - General guide for BMS AI Agent
- `WORKFLOW_FIX_EXPLANATION.md` - Redis and other workflow fixes

## Support

If you encounter issues:
1. Check n8n execution logs for each node
2. Test sub-workflows individually
3. Verify BMS API is responding correctly
4. Review n8n GitHub issues for similar problems
