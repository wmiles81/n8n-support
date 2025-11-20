# Using n8n-support Skill on Claude Code Web Version

## MCP Limitations on Web

The web version of Claude Code (browser-based) **does not currently support project-level MCP servers** in the same way as Claude Desktop.

### What Doesn't Work
- ❌ Project-level `.mcp.json` configuration
- ❌ MCP tools like `mcp__n8n__workflow_list`
- ❌ MCP server subprocesses

### What Does Work ✅
- ✅ **Direct n8n API access via curl/bash**
- ✅ All the workflow patterns and best practices
- ✅ Python scripts for generation and validation
- ✅ Complete skill functionality

## Using n8n API Directly

The skill works perfectly using direct API calls. Here's how:

### List Workflows

```bash
curl -s -H "X-N8N-API-KEY: YOUR_API_KEY" \
  "https://your-n8n-instance.com/api/v1/workflows" | jq
```

### Execute Workflow

```bash
curl -s -X POST \
  -H "X-N8N-API-KEY: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"data": {"key": "value"}}' \
  "https://your-n8n-instance.com/api/v1/workflows/WORKFLOW_ID/execute"
```

### Get Execution Status

```bash
curl -s -H "X-N8N-API-KEY: YOUR_API_KEY" \
  "https://your-n8n-instance.com/api/v1/executions/EXECUTION_ID"
```

## Using the Skill on Web

Simply ask Claude to interact with n8n:

```
User: List my n8n workflows

Claude: [Uses curl to fetch and format workflows]

User: Execute the "Book Generator" workflow with 3 books

Claude: [Uses curl to execute and monitor]
```

Claude will automatically use the n8n API directly via bash commands.

## For Full MCP Support

If you need the MCP tools with `mcp__n8n__*` prefix, use:

### Claude Desktop (Mac/Windows/Linux)
Download from https://claude.ai/download

Configuration file locations:
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add to config:
```json
{
  "mcpServers": {
    "n8n": {
      "command": "n8n-mcp-server",
      "env": {
        "N8N_API_URL": "https://your-instance.com/api/v1",
        "N8N_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Advantages of Direct API Approach

1. **Works everywhere** - Web, desktop, CLI
2. **No installation required** - Just curl and jq
3. **Full control** - See exactly what's happening
4. **Debugging** - Easier to troubleshoot API issues
5. **Portable** - Works in any environment with curl

## Skill Functionality Matrix

| Feature | Web Version | Desktop with MCP |
|---------|-------------|------------------|
| List workflows | ✅ curl | ✅ MCP tool |
| Execute workflows | ✅ curl | ✅ MCP tool |
| Get execution status | ✅ curl | ✅ MCP tool |
| Deploy workflows | ✅ curl | ✅ MCP tool |
| Generate workflows | ✅ Python | ✅ Python |
| Validate workflows | ✅ Python | ✅ Python |
| Best practices | ✅ Full | ✅ Full |
| Anti-pattern detection | ✅ Full | ✅ Full |

**Bottom line**: The skill is **100% functional** on the web version, just uses direct API calls instead of MCP tools.

## Example Session (Web Version)

```
User: Show me my n8n workflows

Claude: You have 21 workflows:

Active:
- Romance-Suspense Chapter Writer
- Romance-Suspense 30-Chapter Generator

Inactive:
- New MOP 20250827-1
- Series Dossier Builder
[... more workflows ...]

User: Execute "Romance-Suspense Chapter Writer" with chapter_number: 5

Claude: Executing workflow...
[Uses curl POST to /api/v1/workflows/{id}/execute]

Execution started: exec_abc123
Status: Running

User: What's the status?

Claude: [Uses curl GET to /api/v1/executions/exec_abc123]

Execution exec_abc123:
Status: Success
Duration: 45 seconds
Output: [workflow results]
```

## Conclusion

**Don't worry about MCP not loading on the web version.** The skill provides the same functionality using direct API calls, which work reliably and give you more visibility into what's happening.

For the smoothest MCP experience, use Claude Desktop. For browser-based work, the direct API approach is actually preferable!
