# Example: Deploy Generated Workflow

This example shows how to generate a workflow using Python scripts and deploy it to n8n via MCP.

## Scenario

You need to create a custom hierarchical workflow (series → books → chapters) and deploy it to n8n.

## Steps

### 1. Generate Workflow JSON

Use the Python script to generate the workflow:

```
Claude, generate a hierarchical workflow for a book series generator
```

Behind the scenes, Claude runs:
```bash
python scripts/generate-workflow.py
```

This creates a workflow JSON structure following n8n best practices.

### 2. Validate the Workflow

Before deploying, validate it:

```
Claude, validate the generated workflow for anti-patterns
```

Uses:
```bash
python scripts/validate-workflow.py hierarchical_example.json
```

Checks for:
- Nested loops (anti-pattern)
- Missing merge nodes
- Excel in loops
- Static data usage in code nodes

### 3. Deploy to n8n

Create the workflow in n8n:

```
Claude, deploy this workflow to n8n
```

Uses:
```javascript
mcp__n8n__workflow_create({
  workflow: {
    name: "Hierarchical Series Generator",
    nodes: [...],
    connections: {...},
    settings: {...}
  }
})
```

### 4. Activate the Workflow

Make it ready to execute:

```
Claude, activate workflow "new_workflow_id"
```

Uses:
```javascript
mcp__n8n__workflow_activate({
  workflowId: "new_workflow_id"
})
```

### 5. Test Execution

Run a test:

```
Claude, execute the new workflow with test data:
- num_books: 2
- chapters_per_book: 3
```

Uses:
```javascript
mcp__n8n__execution_run({
  workflowId: "new_workflow_id",
  data: {
    num_books: 2,
    chapters_per_book: 3
  }
})
```

## Complete Workflow

```
User: Create and deploy a book series workflow that generates 3 books with 10 chapters each

Claude: I'll create a hierarchical workflow for you...

Step 1: Generating workflow structure
✓ Created main orchestrator workflow
✓ Created book generator sub-workflow
✓ Created chapter generator sub-workflow

Step 2: Validating workflow
✓ No nested loops detected
✓ All parallel branches converge
✓ Proper state management via Data Tables
✓ No anti-patterns found

Step 3: Deploying to n8n
✓ Created workflow "Book Series Generator" (ID: wf_123)
✓ Created sub-workflow "Generate Book" (ID: wf_124)
✓ Created sub-workflow "Generate Chapter" (ID: wf_125)

Step 4: Activating workflows
✓ Activated all 3 workflows

Step 5: Running test execution
✓ Execution started (ID: exec_200)
Status: Running

User: Check the execution status

Claude: Execution exec_200:
Status: Success ✓
Duration: 1m 32s

Results:
- Series created: series_001
- Books generated: 3
- Total chapters: 30
- All content stored in Data Tables
```

## Workflow Structure Created

The deployment creates this hierarchy:

```
Main Workflow: "Book Series Generator"
├── Initialize Data Tables
├── Generate Series Foundation
├── Loop Over Books
│   └── Execute Sub-workflow: "Generate Book"
│       ├── Generate Book Outline
│       ├── Loop Over Chapters
│       │   └── Execute Sub-workflow: "Generate Chapter"
│       │       ├── Generate Chapter Content
│       │       └── Store in Data Table
│       └── Return Book Summary
├── Merge Results
└── Complete Series
```

## Generated Data Tables

The workflow automatically creates:

1. **execution_tracker** - Tracks all entity states
2. **content_storage** - Stores generated content
3. **dependency_tracker** - Manages hierarchical dependencies
4. **workflow_state** - Temporary processing state

## Customization Options

You can customize the generated workflow:

```
User: Modify the workflow to add parallel book generation

Claude: I'll update the workflow to process books in parallel...

Changes made:
✓ Changed "Loop Over Books" to "Split In Batches"
✓ Added "Merge (Wait All)" node after book generation
✓ Updated sub-workflow to handle parallel execution
✓ Added progress tracking per book

Deploying updated workflow...
✓ Updated workflow wf_123
```

## Best Practices

1. **Always validate** before deploying
2. **Test with minimal data** first (1 book, 2 chapters)
3. **Use sub-workflows** for nested operations
4. **Initialize Data Tables** before execution
5. **Monitor first execution** closely
6. **Version your workflows** with meaningful names

## Troubleshooting

### Deployment Failed
```
Error: Workflow validation failed - missing required field

Solution: Check that generated JSON includes all required fields:
- name
- nodes (array)
- connections (object)
```

### Workflow Inactive After Deploy
```
Solution: Activate it manually:
Claude, activate workflow "wf_123"
```

### Execution Fails Immediately
```
Error: Table 'execution_tracker' not found

Solution: Initialize tables first using table-manager sub-workflow
```

## See Also

- [01-execute-workflow.md](01-execute-workflow.md) - Execute existing workflows
- [03-monitor-executions.md](03-monitor-executions.md) - Monitor workflow executions
- [../scripts/generate-workflow.py](../scripts/generate-workflow.py) - Workflow generator source
