# Example: Execute Existing n8n Workflow

This example shows how to execute an existing n8n workflow using the n8n API.

## Scenario

You have a pre-built workflow in n8n and want to execute it with custom parameters.

## Setup

```bash
# One-time setup
source scripts/n8n-api.sh  # Auto-loads credentials from .mcp.json
```

## Steps

### 1. List Available Workflows

```bash
n8n_list_workflows
```

Or via Claude:
```
User: List my n8n workflows
```

Claude uses `n8n_list_workflows` behind the scenes.

### 2. Get Workflow Details

```bash
n8n_get_workflow "abc123"
```

Or via Claude:
```
User: Show me the details of workflow abc123
```

### 3. Execute the Workflow

```bash
# Direct execution
n8n_execute_workflow "abc123" '{
  "num_books": 3,
  "chapters_per_book": 10,
  "genre": "sci-fi"
}'
```

Or via Claude:
```
User: Execute workflow abc123 with:
- num_books: 3
- chapters_per_book: 10
- genre: "sci-fi"
```

Claude will construct and execute the API call.

### 4. Monitor Execution

```bash
# Auto-polls every 5 seconds until complete
n8n_monitor_execution "exec_456"
```

Or check status once:
```bash
n8n_get_execution "exec_456"
```

Via Claude:
```
User: Monitor execution exec_456
```

### 5. View Results

The execution details include:
- Status (success/failed/running/crashed)
- Start/end time
- Duration
- Output data
- Error messages (if any)

```bash
# Get full execution details
n8n_get_execution "exec_456" | jq
```

## Complete Examples

### Command Line

```bash
# Load helpers
source scripts/n8n-api.sh

# List workflows
n8n_list_workflows

# Execute
EXEC_ID=$(n8n_execute_workflow "abc123" '{"num_books": 5, "chapters_per_book": 15}' | jq -r '.id')

# Monitor
n8n_monitor_execution "$EXEC_ID"
```

### Via Claude

```
User: List my n8n workflows

Claude: [Runs n8n_list_workflows]
You have 21 workflows:

Active:
- Romance-Suspense Chapter Writer (ID: XLBQt6jk5g58FD1j)
- Romance-Suspense 30-Chapter Generator (ID: uQg5JVC1PXNvA6iS)

[... more workflows ...]

User: Execute "Romance-Suspense Chapter Writer" with chapter_number 5

Claude: [Runs n8n_execute_workflow with parameters]
Execution started: exec_001
Status: Running

User: Monitor it

Claude: [Runs n8n_monitor_execution]
Monitoring execution exec_001...
[10:30:15] Status: running
[10:30:20] Status: running
[10:30:25] Status: success
✓ Execution completed successfully!
```

## Error Handling

If execution fails:

```
User: Why did execution exec_002 fail?

Claude: Execution exec_002 failed with error:
"Missing required parameter: genre"

The workflow expects:
- num_books (required)
- chapters_per_book (required)
- genre (required)
- tone (optional)
```

## Best Practices

1. **Always check workflow requirements** before executing
2. **Monitor long-running executions** for status updates
3. **Use meaningful data** that matches the workflow's schema
4. **Handle errors gracefully** with retries if needed
5. **Clean up failed executions** periodically

## See Also

- [02-deploy-workflow.md](02-deploy-workflow.md) - Deploy generated workflows
- [03-monitor-executions.md](03-monitor-executions.md) - Advanced monitoring
