# n8n MCP Server Setup

This guide explains how to configure the n8n Model Context Protocol (MCP) server for Claude Code.

## What is n8n-mcp?

The n8n-mcp server provides Claude Code with tools to interact with n8n workflows directly, enabling:
- Reading workflow configurations
- Updating workflow nodes
- Managing workflow connections
- Searching n8n documentation

## Installation

The n8n-mcp server is already installed at `/workspace/n8n-mcp`.

## Configuration

### 1. Generate n8n API Key

1. Open n8n at `http://localhost:5678`
2. Go to Settings → API
3. Create a new API key
4. Copy the generated JWT token

### 2. Configure Claude Code

Create or update `~/.config/Claude/mcp_settings.json`:

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "node",
      "args": ["dist/mcp/index.js"],
      "cwd": "/workspace/n8n-mcp",
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "YOUR_API_KEY_HERE",
        "N8N_DB_PATH": "/workspace/n8n/.n8n/database.sqlite"
      }
    }
  }
}
```

Replace `YOUR_API_KEY_HERE` with your actual n8n API key.

### 3. Restart Claude Code

Exit and restart your Claude Code session. The MCP server will automatically connect.

## Verification

After restart, ask Claude Code:

```
List available MCP servers
```

You should see `n8n-mcp` in the list with 23 available tools.

## Available Tools

The n8n-mcp server provides:

### Workflow Management
- `mcp__n8n-mcp__list_workflows` - List all workflows
- `mcp__n8n-mcp__get_workflow` - Get workflow details by ID
- `mcp__n8n-mcp__update_workflow` - Update workflow configuration
- `mcp__n8n-mcp__create_workflow` - Create new workflow
- `mcp__n8n-mcp__delete_workflow` - Delete workflow

### Node Operations
- `mcp__n8n-mcp__update_node` - Update specific node parameters
- `mcp__n8n-mcp__add_node` - Add new node to workflow
- `mcp__n8n-mcp__delete_node` - Remove node from workflow

### Documentation
- `mcp__n8n-mcp__search_nodes` - Search n8n node documentation
- `mcp__n8n-mcp__get_node_details` - Get detailed node documentation

### Execution
- `mcp__n8n-mcp__execute_workflow` - Trigger workflow execution
- `mcp__n8n-mcp__get_execution` - Get execution results

## Example Usage

### List All Workflows
```
Show me all my n8n workflows
```

### Update a Workflow Node
```
Update the "Format Response" node in workflow T6dXPYYfceYgNrd4
to return formatted text instead of JSON
```

### Search Documentation
```
Show me documentation for the HTTP Request node
```

## Troubleshooting

### MCP Server Not Connecting

1. **Check n8n is running:**
   ```bash
   curl http://localhost:5678/healthz
   ```

2. **Verify API key:**
   - Try the API key with curl:
     ```bash
     curl -H "X-N8N-API-KEY: YOUR_KEY" http://localhost:5678/api/v1/workflows
     ```

3. **Check MCP logs:**
   - Look for MCP initialization messages when Claude Code starts

### Permission Denied

Ensure the database file is readable:
```bash
ls -la /workspace/n8n/.n8n/database.sqlite
```

### Tools Not Appearing

Restart Claude Code completely (exit the terminal session and start new one).

## Configuration Files

- **Example config**: `config/mcp_settings.example.json`
- **Active config**: `~/.config/Claude/mcp_settings.json`
- **n8n database**: `/workspace/n8n/.n8n/database.sqlite`

## Security Notes

- The n8n API key grants full access to all workflows
- Keep the API key secure and never commit it to git
- The example config file uses a placeholder - replace with actual key
- Consider rotating API keys periodically

## References

- n8n MCP GitHub: https://github.com/yourusername/n8n-mcp
- MCP Protocol Docs: https://modelcontextprotocol.io
- n8n API Docs: https://docs.n8n.io/api/
