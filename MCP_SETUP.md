# n8n MCP Server Setup Guide

This guide shows you how to connect Claude Code to your n8n instance via MCP.

## Prerequisites

- n8n instance running (local or cloud)
- Node.js 20+ installed
- Access to n8n Settings

## Step 1: Install n8n MCP Server

Choose one based on your needs:

### Option A: Workflow Execution (Recommended)
For running and managing workflows:
```bash
npm install -g @leonardsellem/n8n-mcp-server
```

### Option B: Workflow Building
For documentation and building workflows:
```bash
npm install -g n8n-mcp
```

## Step 2: Create n8n API Key

1. Open your n8n instance (e.g., http://localhost:5678)
2. Navigate to: **Settings → API**
3. Click **Create API Key**
4. Give it a name (e.g., "Claude Code MCP")
5. Copy the key (starts with `n8n_api_...`)

## Step 3: Configure MCP Server

The `.mcp.json` file in this repository needs your credentials.

Edit `.mcp.json` and replace:
- `YOUR_N8N_API_KEY_HERE` with your actual API key
- `http://localhost:5678/api/v1` with your n8n URL (if different)

**Example configurations:**

### Local n8n
```json
{
  "mcpServers": {
    "n8n": {
      "command": "n8n-mcp-server",
      "env": {
        "N8N_API_URL": "http://localhost:5678/api/v1",
        "N8N_API_KEY": "n8n_api_1234567890abcdef"
      }
    }
  }
}
```

### Cloud n8n
```json
{
  "mcpServers": {
    "n8n": {
      "command": "n8n-mcp-server",
      "env": {
        "N8N_API_URL": "https://your-instance.app.n8n.cloud/api/v1",
        "N8N_API_KEY": "n8n_api_1234567890abcdef"
      }
    }
  }
}
```

### Self-hosted with Authentication
```json
{
  "mcpServers": {
    "n8n": {
      "command": "n8n-mcp-server",
      "env": {
        "N8N_API_URL": "https://n8n.yourdomain.com/api/v1",
        "N8N_API_KEY": "n8n_api_1234567890abcdef",
        "N8N_WEBHOOK_USERNAME": "your_webhook_user",
        "N8N_WEBHOOK_PASSWORD": "your_webhook_pass"
      }
    }
  }
}
```

## Step 4: Restart Claude Code

After editing `.mcp.json`, restart Claude Code for changes to take effect.

## Step 5: Verify Connection

In Claude Code, try:
```
List my n8n workflows
```

Claude should now have access to MCP tools like `mcp__n8n__workflow_list`.

## Available Tools

Once configured, you'll have access to:

### Workflow Management
- `mcp__n8n__workflow_list` - List all workflows
- `mcp__n8n__workflow_get` - Get workflow details
- `mcp__n8n__workflow_create` - Create new workflow
- `mcp__n8n__workflow_update` - Update workflow
- `mcp__n8n__workflow_activate` - Activate workflow
- `mcp__n8n__workflow_deactivate` - Deactivate workflow
- `mcp__n8n__workflow_delete` - Delete workflow

### Execution Control
- `mcp__n8n__execution_run` - Execute workflow via API
- `mcp__n8n__run_webhook` - Execute via webhook
- `mcp__n8n__execution_get` - Get execution details
- `mcp__n8n__execution_list` - List executions
- `mcp__n8n__execution_stop` - Stop execution

## Troubleshooting

### "Command not found: n8n-mcp-server"
Install the MCP server globally:
```bash
npm install -g @leonardsellem/n8n-mcp-server
```

### "Authentication failed"
1. Check your API key is correct
2. Verify the API URL includes `/api/v1`
3. Ensure your n8n instance allows API access

### "Connection refused"
1. Check if n8n is running
2. Verify the URL is accessible
3. For cloud instances, use HTTPS not HTTP

### MCP tools not showing up
1. Restart Claude Code completely
2. Check `.mcp.json` is valid JSON (use a validator)
3. Verify the file is in the project root

## Security Notes

⚠️ **Important:**
- Never commit `.mcp.json` with real credentials
- Add `.mcp.json` to `.gitignore`
- Use environment-specific configurations
- Rotate API keys periodically

## Next Steps

See [examples/](examples/) for practical usage patterns:
- Executing existing workflows
- Deploying generated workflows
- Monitoring execution status
- Working with data tables
