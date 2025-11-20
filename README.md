# n8n-support Skill

> Production-ready n8n workflow patterns and MCP integration for Claude Code

This skill provides comprehensive support for building, deploying, and executing n8n workflows through the Model Context Protocol (MCP).

## Features

✅ **Battle-tested workflow patterns** that work around n8n platform limitations
✅ **MCP integration** for seamless n8n API access (Claude Desktop)
✅ **Direct API access** works on web version (see [WEB_VERSION_NOTES.md](WEB_VERSION_NOTES.md))
✅ **Python utilities** for workflow generation and validation
✅ **Anti-pattern detection** to avoid common pitfalls
✅ **Hierarchical workflow support** for complex multi-tier automation
✅ **Data Table architecture** for reliable state management

## Platform Notes

**Claude Code Web Version**: MCP tools are not available, but the skill is **100% functional** using direct n8n API calls. See [WEB_VERSION_NOTES.md](WEB_VERSION_NOTES.md) for details.

**Claude Desktop**: Full MCP support with `mcp__n8n__*` tools. Follow setup guide below.

## Quick Start

### 1. Set Up MCP Integration

```bash
# Install n8n MCP server
npm install -g @leonardsellem/n8n-mcp-server

# Configure credentials
cp .mcp.json.example .mcp.json
# Edit .mcp.json with your n8n API key

# Restart Claude Code
```

See [MCP_SETUP.md](MCP_SETUP.md) for detailed instructions.

### 2. Use the Skill

In Claude Code:

```
User: List my n8n workflows

User: Create a book series workflow with 3 books and 10 chapters each

User: Execute workflow "Data Sync" with parameters {...}
```

## Documentation

### Core Documentation
- **[SKILL.md](SKILL.md)** - Main skill reference with patterns and best practices
- **[MCP_SETUP.md](MCP_SETUP.md)** - MCP server installation and configuration

### Reference Guides
- **[anti-patterns.md](references/anti-patterns.md)** - What NOT to do in n8n
- **[hierarchical-workflows.md](references/hierarchical-workflows.md)** - Multi-tier workflow patterns
- **[table-manager.md](references/table-manager.md)** - Data Table management
- **[known-issues.md](references/known-issues.md)** - Known n8n bugs and workarounds

### Examples
- **[01-execute-workflow.md](examples/01-execute-workflow.md)** - Run existing workflows
- **[02-deploy-workflow.md](examples/02-deploy-workflow.md)** - Deploy generated workflows
- **[03-monitor-executions.md](examples/03-monitor-executions.md)** - Monitor and debug

## Python Scripts

### generate-workflow.py
Generate production-ready n8n workflows programmatically.

```bash
python scripts/generate-workflow.py
```

Creates workflow JSON following best practices for:
- Loop patterns with state management
- Hierarchical workflows (series → books → chapters)
- Sub-workflow patterns
- Data Table initialization

### table-manager.py
Manage Data Table schemas and operations.

```bash
python scripts/table-manager.py
```

Generates:
- Table schemas for different use cases
- Code snippets for table operations
- Migration scripts

### validate-workflow.py
Validate workflows for anti-patterns and issues.

```bash
python scripts/validate-workflow.py workflow.json
```

Detects:
- Nested Loop Over Items (critical error)
- Missing merge nodes for parallel branches
- Excel usage in loops
- Static data usage in Code nodes
- Missing error handling

## Key Concepts

### What Works in n8n ✅
- **Sub-workflows** for nested operations
- **Data Tables** for state management
- **Conditional loop-back** patterns
- **Webhook callbacks** (inline only)
- **Google Sheets Append** in loops

### What's Broken in n8n ❌
- Direct nested Loop Over Items
- `$workflow.staticData` in Code nodes
- Microsoft Excel in loops
- Parallel operations without Merge nodes
- Memory-based state persistence

## MCP Tools Available

Once configured, you'll have access to:

### Workflow Management
- `mcp__n8n__workflow_list` - List all workflows
- `mcp__n8n__workflow_create` - Create new workflow
- `mcp__n8n__workflow_activate` - Activate workflow
- `mcp__n8n__workflow_get` - Get workflow details

### Execution Control
- `mcp__n8n__execution_run` - Execute workflow
- `mcp__n8n__execution_get` - Get execution status
- `mcp__n8n__execution_list` - List executions
- `mcp__n8n__execution_stop` - Stop execution

See [SKILL.md](SKILL.md) for complete API reference.

## Common Use Cases

### 1. Execute Existing Workflow
```
User: Execute "Book Generator" with 5 books and 10 chapters each
```

### 2. Create Custom Workflow
```
User: Create a workflow that generates a book series with:
- 3 books
- 15 chapters per book
- Parallel book generation
- Sequential chapters for context
```

### 3. Debug Failures
```
User: Why did execution exec_123 fail?
```

### 4. Monitor Progress
```
User: What's the status of the Book Generator execution?
```

## Project Structure

```
n8n-support/
├── SKILL.md                    # Main skill documentation
├── MCP_SETUP.md               # MCP configuration guide
├── README.md                  # This file
├── .mcp.json.example          # Example MCP configuration
├── .mcp.json                  # Your MCP config (gitignored)
├── examples/                  # Usage examples
│   ├── 01-execute-workflow.md
│   ├── 02-deploy-workflow.md
│   └── 03-monitor-executions.md
├── references/                # Reference documentation
│   ├── anti-patterns.md
│   ├── hierarchical-workflows.md
│   ├── table-manager.md
│   └── known-issues.md
└── scripts/                   # Python utilities
    ├── generate-workflow.py
    ├── table-manager.py
    └── validate-workflow.py
```

## Security Notes

⚠️ **Important:**
- Never commit `.mcp.json` with real credentials
- The file is in `.gitignore` for your protection
- Use `.mcp.json.example` as a template
- Rotate API keys periodically

## Contributing

This skill is based on real-world n8n production experience. Issues and improvements welcome!

### Adding New Patterns
1. Test pattern thoroughly in production
2. Document in appropriate reference file
3. Add validation to `validate-workflow.py`
4. Create example in `examples/`

## Troubleshooting

### MCP Tools Not Available
1. Check `.mcp.json` configuration
2. Verify n8n MCP server is installed
3. Restart Claude Code
4. Check n8n instance is accessible

### Workflow Validation Fails
1. Run `python scripts/validate-workflow.py workflow.json`
2. Check for anti-patterns in output
3. See [references/anti-patterns.md](references/anti-patterns.md)

### Execution Failures
1. Check execution logs: `mcp__n8n__execution_get`
2. Review [references/known-issues.md](references/known-issues.md)
3. Verify workflow follows best practices

## License

MIT

## Credits

Built from production experience working around n8n's limitations and bugs. Special thanks to the n8n community for documenting issues and workarounds.

## Related Links

- [n8n Documentation](https://docs.n8n.io/)
- [n8n Community](https://community.n8n.io/)
- [n8n GitHub Issues](https://github.com/n8n-io/n8n/issues)
- [Model Context Protocol](https://modelcontextprotocol.io/)
