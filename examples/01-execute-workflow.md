# Example: Execute Existing n8n Workflow

This example shows how to execute an existing n8n workflow using MCP.

## Scenario

You have a pre-built workflow in n8n and want to execute it with custom parameters.

## Steps

### 1. List Available Workflows

First, see what workflows are available:

```
Claude, list my n8n workflows
```

Behind the scenes, Claude uses:
```javascript
mcp__n8n__workflow_list()
```

### 2. Get Workflow Details

To see what parameters a workflow expects:

```
Claude, show me the details of workflow ID "abc123"
```

Uses:
```javascript
mcp__n8n__workflow_get({
  workflowId: "abc123"
})
```

### 3. Execute the Workflow

Run the workflow with data:

```
Claude, execute workflow "abc123" with this data:
- num_books: 3
- chapters_per_book: 10
- genre: "sci-fi"
```

Uses:
```javascript
mcp__n8n__execution_run({
  workflowId: "abc123",
  data: {
    num_books: 3,
    chapters_per_book: 10,
    genre: "sci-fi"
  }
})
```

### 4. Check Execution Status

Monitor the execution:

```
Claude, check the status of execution "exec_456"
```

Uses:
```javascript
mcp__n8n__execution_get({
  executionId: "exec_456"
})
```

### 5. View Results

Once complete, get the results:

```
Claude, show me the results of execution "exec_456"
```

The execution details will include:
- Status (success/failed/running)
- Start/end time
- Output data
- Error messages (if any)

## Complete Conversation Example

```
User: List my n8n workflows

Claude: You have 3 workflows:
1. "Book Series Generator" (ID: abc123) - Active
2. "Content Pipeline" (ID: def456) - Inactive
3. "Data Sync" (ID: ghi789) - Active

User: Execute the Book Series Generator with 5 books, 15 chapters each

Claude: I'll execute the "Book Series Generator" workflow...
[Execution started: exec_001]
Status: Running
Started: 2025-01-20 10:30:00

User: What's the status now?

Claude: Execution exec_001:
Status: Success
Completed: 2025-01-20 10:32:45
Duration: 2m 45s
Results: Generated 5 books with 75 total chapters
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
