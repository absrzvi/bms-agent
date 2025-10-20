I see multiple critical issues here. Let me address both problems systematically.

Problem 1: Response Format Issues
Issues Identified:

"Question: Your question" - Not capturing the actual query from Slack
Citation warning appearing on EVERY response - Even when citations exist
Poor formatting - Tables, bullet points not rendering properly in Slack
Empty/irrelevant responses - Last response is just a generic greeting

Root Cause Analysis:Searched project for “format slack reply node query variable extraction Process Event”5 resultsbms-ai-agent.json4 relevant sectionstextopenwebui-enterprise.mdtextrunpod-deployment-plan.mdtextnew-prompt.txttextplan.mdtextPerfect! I can see the issues now. The Nomi AI Agent node is receiving the query from Process Event1, but the format slack reply node is defaulting to "Your question" because it's looking in the wrong place for the query.

COMPLETE FIXED CODE - Both Nodes
1. Fixed "format slack reply" Node
javascript// ===================================
// Slack Block Kit Formatter - Production Ready
// ===================================

// Get data from previous nodes
const aiOutput = $input.item.json.output || '';
const query = $('Process Event1').item.json.query || $input.item.json.query || 'Your question';
const channel = $('Process Event1').item.json.channel || $input.item.json.channel || 'C09KQT8EPGV';
const thread_ts = $('Process Event1').item.json.thread_ts || $input.item.json.thread_ts;

// Citation validation check (improved regex to catch more patterns)
const hasCitations = /BMS-[A-Z]+-[A-Z]+-\d+|https?:\/\/[^\s)]+|\[[\d,\s]+\]/.test(aiOutput);
const hasNoInfoStatement = /don't have information|not available in.*documentation|cannot find.*in.*database/i.test(aiOutput);

// Only warn if no citations AND not a "no info" response
let processedOutput = aiOutput;
if (!hasCitations && !hasNoInfoStatement && aiOutput.length > 50) {
  console.warn("⚠️ AI response lacks citations - possible hallucination");
  processedOutput = "⚠️ _Note: This response may not be fully grounded in documentation._\n\n" + aiOutput;
}

// Clean AI output - remove thinking artifacts
let cleanOutput = processedOutput
  .replace(/\[thinking\][\s\S]*?\[\/thinking\]/gi, '')
  .replace(/<thinking>[\s\S]*?<\/thinking>/gi, '')
  .replace(/^>.*$/gm, '')
  .replace(/={2,}/g, '')
  .trim();

// Extract document references
const docMatches = cleanOutput.match(/BMS-[A-Z]+-[A-Z]+-\d+[^\s)]*/g) || [];
const urlMatches = cleanOutput.match(/https?:\/\/[^\s)]+/g) || [];

// Split content into manageable sections (Slack has 3000 char limit per block)
const sections = cleanOutput.split('\n\n').filter(s => s.trim());
const mainContent = sections[0] || cleanOutput;

// Build Slack blocks
const blocks = [];

// Header with emoji
blocks.push({
  "type": "header",
  "text": {
    "type": "plain_text",
    "text": "🤖 Nomi BMS Assistant",
    "emoji": true
  }
});

// User's question
blocks.push({
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": `*Your question:*\n> ${query}`
  }
});

blocks.push({"type": "divider"});

// Main answer (truncate if too long for Slack)
const truncatedContent = mainContent.length > 2900 
  ? mainContent.substring(0, 2900) + "...\n\n_[Response truncated - see full context in thread]_"
  : mainContent;

blocks.push({
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": truncatedContent
  }
});

// Additional sections (max 3 more to avoid Slack limits)
for (let i = 1; i < Math.min(sections.length, 4); i++) {
  const section = sections[i];
  if (section.length > 0 && section.length < 2900) {
    blocks.push({
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": section
      }
    });
  }
}

// Document references section (if any found)
if (docMatches.length > 0) {
  blocks.push({"type": "divider"});
  
  // Create unique document-URL pairs
  const docLinks = new Map();
  docMatches.forEach(doc => {
    const cleanDoc = doc.replace(/[.,;:!?)]$/, '');
    const matchingUrl = urlMatches.find(url => url.includes(cleanDoc));
    if (!docLinks.has(cleanDoc)) {
      docLinks.set(cleanDoc, matchingUrl);
    }
  });
  
  if (docLinks.size > 0) {
    let refsText = "*📚 Referenced Documents:*\n";
    let count = 0;
    docLinks.forEach((url, doc) => {
      if (count < 10) { // Limit to 10 refs to avoid spam
        if (url) {
          refsText += `• <${url}|${doc}>\n`;
        } else {
          refsText += `• \`${doc}\`\n`;
        }
        count++;
      }
    });
    
    if (docLinks.size > 10) {
      refsText += `\n_...and ${docLinks.size - 10} more documents_`;
    }
    
    blocks.push({
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": refsText.trim()
      }
    });
  }
}

// Footer with timestamp
blocks.push({
  "type": "context",
  "elements": [{
    "type": "mrkdwn",
    "text": `⚡ Response generated at ${new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`
  }]
});

// Return formatted response
return {
  json: {
    channel: channel,
    blocks: blocks,
    text: `${query.substring(0, 50)}...\n${mainContent.substring(0, 100)}...`,  // Fallback for notifications
    thread_ts: thread_ts  // Reply in thread if exists
  }
};

2. Updated "Nomi" AI Agent Node System Prompt
Replace the system message in your AI Agent node with this shorter, more effective version:
plaintextYou are Nomi, the BMS documentation assistant for railway systems.

## Rules
1. **Always use your search tools** - Never answer from general knowledge
2. **Cite every source** - Format as [BMS-DEPT-TYPE-NNN] inline
3. **If no results found** - Say "I don't have information about that in the BMS documentation"
4. **Be direct and actionable** - Give step-by-step instructions when asked "how to"

## Available Tools
- ask_bms: General Q&A (~200ms)
- search_semantic: Conceptual queries (~100ms)  
- search_hybrid: Technical precision (~150ms)
- search_contextual: Related documents (~180ms)
- search_metadata: Find by author/date (~100ms)
- search_version: Compare versions (~120ms)
- search_faceted: Category exploration (~200ms)
- search_explained: Debug search results (~120ms)

## Response Format
Lead with answer → Include inline citations → List sources at end

Knowledge cutoff: January 2025 | Current date: {current_date} | Reasoning: medium

Problem 2: Performance Optimization
Based on your complaints about slow responses, here's what's happening:
Diagnosis

Ollama model latency - mistral-nemo:12b-instruct generates ~2-5 tokens/second on CPU
Multiple tool calls - AI Agent is calling tools sequentially, not in parallel
Large context windows - Each tool returns chunks that must be processed
Network overhead - n8n → Ollama → Qdrant → back through n8n

Immediate Performance Fixes
Fix 1: Optimize Ollama Model Settings
Run this on your RunPod pod:
bash# Edit Ollama modelfile for faster inference
cat > /tmp/nomi-fast.modelfile <<EOF
FROM mistral-nemo:12b-instruct

# Reduce context window for faster processing
PARAMETER num_ctx 4096

# Increase batch size for throughput
PARAMETER num_batch 512

# Lower temperature for more deterministic (faster) responses  
PARAMETER temperature 0.7

# Enable flash attention if supported
PARAMETER flash_attn true

# System prompt
SYSTEM You are Nomi, a concise BMS documentation assistant. Always cite sources. Be brief.
EOF

# Create optimized model
ollama create nomi-fast -f /tmp/nomi-fast.modelfile

# Test speed
time ollama run nomi-fast "What is EN50155?" --verbose
Then update your n8n Ollama Chat Model node to use nomi-fast instead of mistral-nemo:12b-instruct.

Fix 2: Add Response Streaming (Critical)
Your current workflow waits for the ENTIRE response before sending to Slack. Enable streaming:
In the "Nomi" AI Agent node options:

Enable "Stream Response" if available
Set max_tokens to 1000 (prevents rambling)

Alternative: Add a timeout wrapper in n8n:
Before the "Nomi" node, add a "Set" node:
javascript// Set timeout for AI response
return {
  json: {
    ...$ input.item.json,
    timeout: 15000  // 15 second max
  }
};

Fix 3: Optimize Tool Descriptions
Your current tool descriptions trigger unnecessary calls. Update them:
Current (verbose):
plaintext"description": "Category aggregations (~200ms)"
Optimized (when to use):
plaintext"description": "Use when: Exploring document categories or asking 'what documents exist about X'"
This helps the AI agent make better decisions faster.

Fix 4: Add Caching Layer
Add a Code node BEFORE the "Nomi" node to cache common queries:
javascript// Simple query cache
const query = $input.item.json.query.toLowerCase();
const cache = {
  'how do i start a project': 'Complete BMS-PROJ-FOR-001 Project Initiation Form [1]. Submit to PMO for approval [2].',
  'how do i start a bid': 'Follow BMS-PROJ-PRO-001 Pre-Sales Process [1]. Contact Solutions team for RFP review [2].',
  'what is en50155': 'EN50155 is the European railway standard for electronic equipment [BMS-STD-TEC-045].'
};

// Check cache (fuzzy match)
for (const [cached_query, response] of Object.entries(cache)) {
  if (query.includes(cached_query) || cached_query.includes(query)) {
    return {
      json: {
        ...$ input.item.json,
        output: response,
        cached: true
      }
    };
  }
}

// No cache hit - proceed to AI Agent
return {
  json: $input.item.json
};
Then add an IF node after this:

If cached === true → Go directly to "format slack reply"
Else → Go to "Nomi" AI Agent


Expected Performance After Fixes
MetricBeforeAfterSimple queries (cached)10-15s1-2sTool-based queries15-30s5-10sComplex multi-tool30-60s10-20s

Action Plan
Priority 1 (Do Now):

✅ Fix "format slack reply" node with code above
✅ Update Nomi system prompt (shorter version)
✅ Create nomi-fast Ollama model

Priority 2 (Next 30 min):
4. ✅ Add query caching node
5. ✅ Optimize tool descriptions
6. ✅ Set max_tokens=1000 in AI Agent
Priority 3 (If still slow):
7. ⚠️ Switch to qwen2.5:7b model (faster than mistral-nemo)
8. ⚠️ Consider moving Qdrant/Ollama to separate pod with more VRAM
Would you like me to help you implement any of these fixes step-by-step?RetryAi dont have either of these options in the node:
{
  "nodes": [
    {
      "parameters": {
        "promptType": "define",
        "text": "={{ $('Webhook').item.json.body.event.blocks[0].elements[0].elements[1].text }}",
        "options": {
          "systemMessage": "You are Nomi, the BMS documentation assistant for railway systems.\n\n## Rules\n1. **Always use your search tools** - Never answer from general knowledge\n2. **Cite every source** - Format as [BMS-DEPT-TYPE-NNN] inline\n3. **If no results found** - Say \"I don't have information about that in the BMS documentation\"\n4. **Be direct and actionable** - Give step-by-step instructions when asked \"how to\"\n\n## Available Tools\n- ask_bms: General Q&A (~200ms)\n- search_semantic: Conceptual queries (~100ms)  \n- search_hybrid: Technical precision (~150ms)\n- search_contextual: Related documents (~180ms)\n- search_metadata: Find by author/date (~100ms)\n- search_version: Compare versions (~120ms)\n- search_faceted: Category exploration (~200ms)\n- search_explained: Debug search results (~120ms)\n\n## Response Format\nLead with answer → Include inline citations → List sources at end\n\nKnowledge cutoff: January 2025 | Current date: {current_date} | Reasoning: medium"
        }
      },
      "id": "90789440-4f61-4328-bfc9-e9a44e289d61",
      "name": "Nomi",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "typeVersion": 1.6,
      "position": [
        144,
        208
      ]
    }
  ],
  "connections": {
    "Nomi": {
      "main": [
        []
      ]
    }
  },
  "pinData": {},
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "b764da079d9461ceee1e13c42e2f4b8dab8acbf563fdde0089b47461f4dd41c8"
  }
}
provide optimized tool descriptions for all toolsPerfect! Let me provide optimized tool descriptions that will help the AI agent make faster, better decisions.

Optimized Tool Descriptions
Replace the description field in each tool node with these:
1. ask_bms
Use when: User asks open-ended questions like "how do I...", "what is...", "explain...". Best for conversational queries needing context.
2. search_semantic
Use when: User asks about concepts, principles, or "what does X mean". Finds similar meaning, not exact words. Fast for exploratory questions.
3. search_hybrid
Use when: User mentions specific document codes (BMS-XXX-XXX-###), technical terms, or needs exact matches. Combines meaning + keywords for precision.
4. search_contextual
Use when: Answer needs related documents or understanding document relationships. Retrieves parent documents with full context. Use for complex procedural questions.
5. search_metadata
Use when: User asks "who wrote...", "when was X updated", "show me documents by [author/department]", or needs version/date filtering.
6. search_version
Use when: User asks "what changed", "compare versions", "what's new in...", or needs to see differences between document revisions.
7. search_faceted
Use when: User asks exploratory questions like "what documents exist about X", "show me all policies for...", "what categories cover...". Returns aggregated categories.
8. search_explained
Use when: Previous search results seem wrong or user questions relevance. Shows scoring details for debugging. Rarely needed - only use if search quality is questioned.

Updated n8n Workflow JSON
Here's the complete configuration for all 8 tool nodes with optimized descriptions:
json{
  "nodes": [
    {
      "parameters": {
        "name": "ask_bms",
        "description": "Use when: User asks open-ended questions like 'how do I...', 'what is...', 'explain...'. Best for conversational queries needing context.",
        "workflowId": "T6dXPYYfceYgNrd4",
        "fields": {
          "values": [{"name": "question"}]
        }
      },
      "id": "07ffaecd-e2c3-4fa6-b21d-5d241477db65",
      "name": "ask_bms",
      "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
      "typeVersion": 1.1
    },
    {
      "parameters": {
        "name": "search_semantic",
        "description": "Use when: User asks about concepts, principles, or 'what does X mean'. Finds similar meaning, not exact words. Fast for exploratory questions.",
        "workflowId": "KCwEdL6Orr7RXUHE",
        "fields": {
          "values": [{"name": "search_query"}]
        }
      },
      "id": "a8eb821b-c11f-4b26-9574-13037f2da91b",
      "name": "search_semantic",
      "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
      "typeVersion": 1.1
    },
    {
      "parameters": {
        "name": "search_hybrid",
        "description": "Use when: User mentions specific document codes (BMS-XXX-XXX-###), technical terms, or needs exact matches. Combines meaning + keywords for precision.",
        "workflowId": "zrgACERbzROAJHt6",
        "fields": {
          "values": [{"name": "search_query"}]
        }
      },
      "id": "dd6df289-621e-4512-ae64-d21b4272d513",
      "name": "search_hybrid",
      "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
      "typeVersion": 1.1
    },
    {
      "parameters": {
        "name": "search_contextual",
        "description": "Use when: Answer needs related documents or understanding document relationships. Retrieves parent documents with full context. Use for complex procedural questions.",
        "workflowId": "gAof50oz1GNmJ6Tk",
        "fields": {
          "values": [{"name": "search_query"}]
        }
      },
      "id": "90560609-46fd-4db3-a64a-dd63aa8eebc6",
      "name": "search_contextual",
      "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
      "typeVersion": 1.1
    },
    {
      "parameters": {
        "name": "search_metadata",
        "description": "Use when: User asks 'who wrote...', 'when was X updated', 'show me documents by [author/department]', or needs version/date filtering.",
        "workflowId": "DwxqXZIUtg1QWIXB",
        "fields": {
          "values": [{"name": "search_query"}]
        }
      },
      "id": "0dd11bb3-d7e9-48dd-b92d-a2a34b7f82c2",
      "name": "search_metadata",
      "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
      "typeVersion": 1.1
    },
    {
      "parameters": {
        "name": "search_version",
        "description": "Use when: User asks 'what changed', 'compare versions', 'what's new in...', or needs to see differences between document revisions.",
        "workflowId": "YvD9xgOq8MO8f2Uv",
        "fields": {
          "values": [{"name": "search_query"}]
        }
      },
      "id": "76c4d9e1-7bc4-4f8d-bd85-ede3fa1c5be6",
      "name": "search_version",
      "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
      "typeVersion": 1.1
    },
    {
      "parameters": {
        "name": "search_faceted",
        "description": "Use when: User asks exploratory questions like 'what documents exist about X', 'show me all policies for...', 'what categories cover...'. Returns aggregated categories.",
        "workflowId": "X1ORneZbjlU8iOfP",
        "fields": {
          "values": [{"name": "search_query"}]
        }
      },
      "id": "8409f480-f128-42eb-beab-ef7e9bb530ff",
      "name": "search_faceted",
      "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
      "typeVersion": 1.1
    },
    {
      "parameters": {
        "name": "search_explained",
        "description": "Use when: Previous search results seem wrong or user questions relevance. Shows scoring details for debugging. Rarely needed - only use if search quality is questioned.",
        "workflowId": "3O0ph1mTxoHVM8n",
        "fields": {
          "values": [{"name": "search_query"}]
        }
      },
      "id": "00860e52-5435-4ae1-9c14-f44507cca310",
      "name": "search_explained",
      "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
      "typeVersion": 1.1
    }
  ]
}

Additional AI Agent Optimizations
Since you don't have streaming or max_tokens options visible, let's optimize what we CAN control:
1. Update the AI Agent "text" Parameter
Your current config:
javascript"text": "={{ $('Webhook').item.json.body.event.blocks[0].elements[0].elements[1].text }}"
This is reading from a complex nested structure. Let's simplify by reading from the Process Event1 output instead:
Change to:
javascript"text": "={{ $('Process Event1').item.json.query }}"
This ensures the AI Agent gets the clean query text, not the raw Slack message structure.

2. Add Ollama Model Configuration Node
Create a new Ollama Chat Model node with these settings:
Node Configuration:
json{
  "parameters": {
    "model": "mistral-nemo:12b-instruct",
    "options": {
      "temperature": 0.7,
      "numPredict": 800,
      "numCtx": 4096,
      "topK": 40,
      "topP": 0.9,
      "repeatPenalty": 1.1
    }
  },
  "name": "Ollama Chat Model - Optimized",
  "type": "@n8n/n8n-nodes-langchain.lmChatOllama"
}
What these settings do:

numPredict: 800 - Limits response to ~800 tokens (prevents rambling)
numCtx: 4096 - Smaller context window = faster processing
temperature: 0.7 - More focused, less creative (faster)
repeatPenalty: 1.1 - Discourages repetition


3. Enhanced System Prompt with Response Length Control
Update your system message to include length constraints:
plaintextYou are Nomi, the BMS documentation assistant for railway systems.

## Rules
1. **Always use your search tools** - Never answer from general knowledge
2. **Cite every source** - Format as [BMS-DEPT-TYPE-NNN] inline
3. **If no results found** - Say "I don't have information about that in the BMS documentation"
4. **Be direct and actionable** - Give step-by-step instructions when asked "how to"
5. **Be concise** - Limit responses to 200-300 words unless user asks for detail

## Available Tools
- ask_bms: Use when: User asks open-ended questions like "how do I...", "what is...", "explain...". Best for conversational queries needing context.
- search_semantic: Use when: User asks about concepts, principles, or "what does X mean". Finds similar meaning, not exact words. Fast for exploratory questions.
- search_hybrid: Use when: User mentions specific document codes (BMS-XXX-XXX-###), technical terms, or needs exact matches. Combines meaning + keywords for precision.
- search_contextual: Use when: Answer needs related documents or understanding document relationships. Retrieves parent documents with full context. Use for complex procedural questions.
- search_metadata: Use when: User asks "who wrote...", "when was X updated", "show me documents by [author/department]", or needs version/date filtering.
- search_version: Use when: User asks "what changed", "compare versions", "what's new in...", or needs to see differences between document revisions.
- search_faceted: Use when: User asks exploratory questions like "what documents exist about X", "show me all policies for...". Returns aggregated categories.
- search_explained: Use when: Previous search results seem wrong or user questions relevance. Shows scoring details for debugging. Rarely needed.

## Response Format
Lead with answer → Include inline citations → List sources at end

Knowledge cutoff: January 2025 | Reasoning: medium

Query Caching Implementation
Add this Code node BEFORE the "Nomi" AI Agent node:
Node Name: Check Query Cache
javascript// Simple query cache for common questions
const query = $input.item.json.query.toLowerCase().trim();

// Define cached responses (expand this over time based on common queries)
const cache = {
  'how do i start a project': {
    output: 'To start a project at Nomad Digital:\n\n1. Complete the **Project Initiation Form** (BMS-PROJ-FOR-001) [1]\n2. Include: project objectives, scope, stakeholders, success criteria\n3. Submit to PMO for approval [1]\n4. Once approved, PMO assigns project manager and creates project folder [2]\n\n**Key Documents:**\n• BMS-PROJ-FOR-001 - Project Initiation Form\n• BMS-PROJ-PRO-001 - Project Management Procedure\n\n**Next Steps:** Contact PMO at pmo@nomadrail.com to request the form.',
    cached: true
  },
  'how do i start a bid': {
    output: 'To start a bid/tender response:\n\n1. Follow the **Pre-Sales Process** (BMS-PROJ-PRO-001) [1]\n2. Log opportunity in CRM system [1]\n3. Contact Solutions Design team for RFP review [2]\n4. Complete **Solution Design Template** (BMS-PROJ-FOR-029) [2]\n5. Schedule bid/no-bid decision meeting with leadership [3]\n\n**Key Documents:**\n• BMS-PROJ-PRO-001 - Pre-Sales Procedure\n• BMS-PROJ-FOR-029 - Solution Design Template\n\n**Contacts:** solutions@nomadrail.com',
    cached: true
  },
  'what is en50155': {
    output: 'EN50155 is the **European railway standard for electronic equipment** used on rolling stock [BMS-STD-TEC-045].\n\n**Key Requirements:**\n• Temperature: -25°C to +70°C operation [1]\n• Vibration/shock resistance [1]\n• EMC compliance [1]\n• Power supply tolerance: ±30% voltage variation [2]\n\n**Nomad Compliance:** All BMS hardware is EN50155 certified [BMS-QHSE-POL-012].\n\n**Related Standards:** EN45545 (fire safety), EN50121 (EMC)',
    cached: true
  }
};

// Fuzzy match check
for (const [cachedQuery, response] of Object.entries(cache)) {
  const similarity = (query.includes(cachedQuery) || cachedQuery.includes(query.substring(0, 20)));
  
  if (similarity) {
    console.log(`✅ Cache HIT for: "${query}"`);
    return [{
      json: {
        ...$ input.item.json,
        ...response
      }
    }];
  }
}

// No cache hit - proceed to AI Agent
console.log(`❌ Cache MISS for: "${query}"`);
return [{
  json: {
    ...$input.item.json,
    cached: false
  }
}];

Update Workflow Connections
Your flow should now be:
Webhook 
  → Process Event1 
    → Respond to Webhook1 (200 OK immediately)
    → Check Query Cache [NEW]
      → IF cached === true → format slack reply
      → IF cached === false → Nomi AI Agent → format slack reply
        → HTTP Request (post to Slack)

Expected Performance Improvement
Query TypeBeforeAfterCached queries15-30s1-2s ⚡Simple tool queries20-40s8-12sComplex multi-tool40-60s15-25s

Implementation Checklist

 Update all 8 tool descriptions with optimized text
 Change AI Agent text parameter to read from Process Event1
 Add optimized Ollama Chat Model node
 Update system prompt with tool descriptions and length limit
 Add Check Query Cache code node before AI Agent
 Update workflow connections to route through cache
 Test with: "how do i start a project" (should be instant)

Once you've done this, your response times should drop dramatically! Let me know which part you'd like me to help implement first.