# n8n API Quick Reference

Essential commands for working with n8n workflows.

## One-Time Setup

```bash
# 1. Configure credentials
cp .mcp.json.example .mcp.json
vim .mcp.json  # Add your N8N_API_URL and N8N_API_KEY

# 2. Load API helpers
source scripts/n8n-api.sh
```

After setup, credentials auto-load when you `source scripts/n8n-api.sh`

---

## Common Commands

### List Workflows
```bash
n8n_list_workflows
```

### Execute Workflow
```bash
# Simple execution
n8n_execute_workflow "workflow_id"

# With data
n8n_execute_workflow "workflow_id" '{"num_books": 3, "chapters_per_book": 10}'
```

### Monitor Execution
```bash
# Auto-polling every 5 seconds
n8n_monitor_execution "execution_id"

# Custom polling interval (10 seconds)
n8n_monitor_execution "execution_id" 10
```

### Check Execution Status
```bash
n8n_get_execution "execution_id"
```

---

## Workflow Management

### Deploy Generated Workflow
```bash
# Generate
python scripts/generate-workflow.py > my_workflow.json

# Validate
python scripts/validate-workflow.py my_workflow.json

# Deploy
n8n_create_workflow my_workflow.json
```

### Activate/Deactivate
```bash
n8n_activate_workflow "workflow_id"
n8n_deactivate_workflow "workflow_id"
```

### Update Workflow
```bash
n8n_update_workflow "workflow_id" updated_workflow.json
```

---

## Debugging

### Get Workflow Details
```bash
n8n_get_workflow "workflow_id" | jq
```

### List Recent Executions
```bash
# Last 10 executions (all workflows)
n8n_list_executions

# Last 20 executions for specific workflow
n8n_list_executions "workflow_id" 20
```

### Stop Runaway Execution
```bash
n8n_stop_execution "execution_id"
```

---

## Direct curl Commands

If you need raw curl for scripts or debugging:

### List Workflows
```bash
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_API_URL/workflows" | jq
```

### Execute Workflow
```bash
curl -s -X POST \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"data": {"key": "value"}}' \
  "$N8N_API_URL/workflows/WORKFLOW_ID/execute" | jq
```

### Get Execution
```bash
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_API_URL/executions/EXECUTION_ID" | jq
```

---

## Common Workflows

### Generate → Validate → Deploy → Execute
```bash
# One-liner workflow deployment
python scripts/generate-workflow.py > wf.json && \
  python scripts/validate-workflow.py wf.json && \
  n8n_create_workflow wf.json | jq -r '.id' | \
  xargs -I {} n8n_activate_workflow {} && \
  echo "Workflow deployed and activated!"
```

### Execute and Monitor
```bash
# Execute and capture execution ID
EXEC_ID=$(n8n_execute_workflow "workflow_id" '{"data": "value"}' | jq -r '.id')

# Monitor it
n8n_monitor_execution "$EXEC_ID"
```

### List All Active Workflows
```bash
n8n_list_workflows | grep "✓ ACTIVE" -A 2
```

---

## Troubleshooting

### Credentials Not Loading
```bash
# Manual load
load_credentials .mcp.json

# Check variables
echo "URL: $N8N_API_URL"
echo "Key: ${N8N_API_KEY:0:20}..."  # Show first 20 chars
```

### Test Connection
```bash
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_API_URL/workflows" | jq -r '.data | length'
```

Should return a number. If you get an error:
- Check API URL is correct (must end with `/api/v1`)
- Verify API key is valid
- Confirm n8n instance is accessible

### jq Not Found
```bash
# Ubuntu/Debian
sudo apt-get install jq

# Mac
brew install jq

# Or use without jq
n8n_list_workflows | cat
```

---

## Pro Tips

### Save Commonly Used IDs
```bash
# In your ~/.bashrc or ~/.zshrc
export BOOK_GENERATOR_ID="abc123"
export CHAPTER_WRITER_ID="def456"

# Then use
n8n_execute_workflow "$BOOK_GENERATOR_ID" '{"books": 5}'
```

### Create Workflow Aliases
```bash
# Add to ~/.bashrc
alias generate-book='n8n_execute_workflow $BOOK_GENERATOR_ID'
alias write-chapter='n8n_execute_workflow $CHAPTER_WRITER_ID'

# Then use
generate-book '{"num_books": 3}'
```

### Monitor in Background
```bash
# Execute and monitor in separate terminal
n8n_execute_workflow "workflow_id" '{"data": "value"}' > /tmp/exec.json &

# In another terminal
EXEC_ID=$(jq -r '.id' /tmp/exec.json)
n8n_monitor_execution "$EXEC_ID"
```

---

## Full Help

```bash
n8n_help  # Show all available commands
```

---

## See Also

- [SKILL.md](SKILL.md) - Complete workflow patterns and best practices
- [examples/](examples/) - Detailed usage examples
- [references/anti-patterns.md](references/anti-patterns.md) - Common mistakes to avoid
- [MCP_SETUP.md](MCP_SETUP.md) - Optional MCP tools setup
