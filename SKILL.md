---
name: n8n-support
description: Comprehensive n8n workflow engineering support for creating production-ready workflows. Use when users need to generate n8n workflows, debug loop execution issues, implement nested operations, design data table architectures, fix anti-patterns, create parallel processing patterns, handle webhook callbacks, or build complex multi-tier workflows. Provides battle-tested patterns that work around known n8n bugs and limitations.
---

# n8n Workflow Support

Production-ready patterns for n8n workflow automation that work around platform limitations.

## Quick Start Checklist

Before generating ANY n8n workflow:

1. **Nested loops?** → Use sub-workflows (ONLY reliable method)
2. **Need state?** → Use Data Tables (50MB limit per table)
3. **Parallel processing?** → Must have Merge node to converge
4. **Status updates?** → Keep HTTP callbacks inline, never parallel
5. **Google Sheets?** → Use Append in loops, not Update
6. **Complex data flow?** → Create multiple specialized Data Tables

## Critical Platform Knowledge

### ✅ What Actually Works
- **Sub-workflows**: Clean execution contexts for nested operations
- **Native Data Tables**: Primary state management solution
- **Conditional Loop-Back**: Using IF nodes to branch back
- **Webhook Callbacks**: For async coordination (inline only)
- **Pass-Through State**: State in item JSON data
- **Merge Nodes**: Left joins instead of nested loops
- **Google Sheets Append**: For data capture in loops

### ❌ Broken Features (DO NOT USE)
- Direct nested Loop Over Items → State corruption guaranteed
- $workflow.staticData in Code nodes → Does not exist
- Microsoft Excel in loops → Fails silently
- Loop state auto-reset → Doesn't happen
- Parallel callbacks → May never execute
- Memory-based state → Not persistent

## Core Workflow Patterns

### Pattern 1: Simple Loop with State
```
[Initialize Data] → [Data Table: Init] → [Process] → [IF: Continue?]
                            ↑                              ↓ false
                            └──────────── true ────────────┘
                                                           ↓
                                                      [Continue]
```

### Pattern 2: Nested Operations (Sub-workflows Required)
```
Main: [Loop Over Items] → [Execute Sub-workflow] → [Merge/Wait] → [Continue]
                                    ↓
                            [Clean Context]
                                    ↓
Sub: [Inner Loop] → [Process] → [Webhook Callback]
```

### Pattern 3: Parallel Processing with Convergence
```
[Split In Batches] → [Execute Workflow] → [Merge (Wait All)] → [Aggregate]
         ↓                                         ↑
    [Parallel Branches] ───────────────────────────┘
```

### Pattern 4: Data Enrichment Without Nesting
```
[Load Reference] → [Store in Table] → [Process Items] → [Merge by Key]
                                              ↓
                                    [Enrich Input 1 Mode]
```

## Data Table Architecture

### Essential Tables Structure

Create multiple tables for complex workflows:

```javascript
// execution_tracker - Core execution state
{
  execution_id: "string (PK)",
  entity_type: "string",
  entity_id: "string", 
  status: "processing|complete|error",
  parent_id: "string",
  metadata: "json",
  created_at: "datetime"
}

// content_storage - Generated content
{
  content_id: "string (PK)",
  entity_id: "string",
  content_type: "string",
  content: "json",
  version: "number",
  created_at: "datetime"
}

// workflow_state - Temporary state
{
  state_id: "string (PK)",
  execution_id: "string",
  state_key: "string",
  state_value: "json",
  expires_at: "datetime"
}
```

## Code Node Patterns

### Initialize Loop State
```javascript
// Always pass state through items
return [{
  json: {
    _execution_id: $execution.id,
    _iteration: 0,
    _max_iterations: 10,
    data: $json,
    _continue: true
  }
}];
```

### Increment Counter
```javascript
// State in item, not static variables
return [{
  json: {
    ...$json,
    _iteration: ($json._iteration || 0) + 1,
    _continue: ($json._iteration + 1) < $json._max_iterations
  }
}];
```

### Check Dependencies
```javascript
// For complex workflows with dependencies
const canProceed = $json.required_items?.every(
  item => $json.completed_items?.includes(item)
);
return [{
  json: {
    ...$json,
    can_proceed: canProceed,
    status: canProceed ? "ready" : "waiting"
  }
}];
```

## Error Handling

Every workflow needs:
1. Error Trigger workflow (separate)
2. Exponential backoff: `Wait = 2^retry_count` seconds
3. Max retries: 3
4. Error logging in Data Table
5. Dead letter pattern for failures

## Node Configurations

### Loop Over Items
```json
{
  "batchSize": 1,
  "options": {
    "pauseBetweenItems": 100
  }
}
```

### Execute Sub-workflow
```json
{
  "source": "database",
  "workflow": "{{ $json.workflow_id }}",
  "waitForSubWorkflow": false,
  "options": {
    "shareParentExecutionId": false
  }
}
```

### Merge Node (for parallel convergence)
```json
{
  "mode": "waitForAll",
  "outputKey": "combined",
  "keepOnlyProperties": false
}
```

### Data Table Upsert
```json
{
  "operation": "upsert",
  "tableId": "{{ $json.table_name }}",
  "fieldsToMatch": ["execution_id", "entity_id"],
  "options": {
    "returnData": true
  }
}
```

## Testing Checklist

Before deployment:
- [ ] All nested loops use sub-workflows
- [ ] Data Tables initialized properly
- [ ] No staticData in Code nodes
- [ ] Google Sheets uses Append in loops
- [ ] All parallel branches converge
- [ ] HTTP callbacks are inline
- [ ] Max iteration safeguards in place
- [ ] Error handling implemented
- [ ] Tested with 0, 1, and many items

## Advanced Patterns

For complex patterns, see references:
- **Multi-tier workflows**: See [references/hierarchical-workflows.md](references/hierarchical-workflows.md)
- **Table management**: See [references/table-manager.md](references/table-manager.md)  
- **Anti-patterns**: See [references/anti-patterns.md](references/anti-patterns.md)
- **GitHub issues**: See [references/known-issues.md](references/known-issues.md)

## Webhook Patterns

### Status Update (Inline)
```
[Process] → [HTTP: Update Status] → [Check Response] → [Continue]
                    ↓
            [Must wait for response]
```

### Async Callback
```
Main: [Execute Sub] → [Wait Node (Resume on Webhook)] → [Process Result]
                                    ↑
Sub: [Process] → [HTTP: Callback] ─┘
```

## Quick Fixes

### Loop Only Runs Once?
- Solution: Use sub-workflow for inner loop
- Why: Execution context pollution

### Parallel Tasks Not Completing?
- Solution: Add Merge node with waitForAll
- Why: n8n needs explicit convergence

### Callbacks Not Firing?
- Solution: Move HTTP callback inline
- Why: Parallel branches may not execute

### State Not Persisting?
- Solution: Use Data Tables, not variables
- Why: No static data in Code nodes

## Working with n8n API

### Quick Start

```bash
# 1. One-time setup (add credentials to .mcp.json)
cp .mcp.json.example .mcp.json
# Edit .mcp.json with your N8N_API_URL and N8N_API_KEY

# 2. Load API helpers
source scripts/n8n-api.sh

# 3. Start using
n8n_list_workflows
```

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for all commands.

### Common Operations

**List Workflows:**
```bash
n8n_list_workflows
```

**Execute Workflow:**
```bash
# Simple execution
n8n_execute_workflow "workflow_id"

# With data
n8n_execute_workflow "workflow_id" '{"num_books": 3, "chapters_per_book": 10}'
```

**Monitor Execution:**
```bash
# Auto-polls every 5 seconds and shows status updates
n8n_monitor_execution "execution_id"
```

**Deploy Generated Workflow:**
```bash
# Generate
python scripts/generate-workflow.py > workflow.json

# Validate
python scripts/validate-workflow.py workflow.json

# Deploy
n8n_create_workflow workflow.json

# Activate
n8n_activate_workflow "new_workflow_id"
```

### Full Workflow: Generate → Deploy → Execute

```bash
# Generate hierarchical workflow
python scripts/generate-workflow.py > hierarchical.json

# Validate for anti-patterns
python scripts/validate-workflow.py hierarchical.json

# Deploy to n8n
WORKFLOW_ID=$(n8n_create_workflow hierarchical.json | jq -r '.id')

# Activate it
n8n_activate_workflow "$WORKFLOW_ID"

# Execute with data
EXEC_ID=$(n8n_execute_workflow "$WORKFLOW_ID" '{"num_books": 3}' | jq -r '.id')

# Monitor until complete
n8n_monitor_execution "$EXEC_ID"
```

### Available API Functions

All functions are in `scripts/n8n-api.sh`:

**Workflow Management:**
- `n8n_list_workflows` - List all workflows
- `n8n_get_workflow <id>` - Get workflow details
- `n8n_create_workflow <file.json>` - Create from JSON
- `n8n_update_workflow <id> <file.json>` - Update workflow
- `n8n_activate_workflow <id>` - Activate
- `n8n_deactivate_workflow <id>` - Deactivate
- `n8n_delete_workflow <id>` - Delete (with confirmation)

**Execution Management:**
- `n8n_execute_workflow <id> [data]` - Execute workflow
- `n8n_get_execution <id>` - Get execution details
- `n8n_list_executions [workflow_id] [limit]` - List executions
- `n8n_stop_execution <id>` - Stop running execution
- `n8n_monitor_execution <id> [interval]` - Poll until complete

### Direct curl (for scripts/automation)

If you need raw API calls:

```bash
# List workflows
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_API_URL/workflows" | jq

# Execute workflow
curl -s -X POST \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"data": {"key": "value"}}' \
  "$N8N_API_URL/workflows/WORKFLOW_ID/execute" | jq

# Get execution status
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_API_URL/executions/EXECUTION_ID" | jq
```

## When to Use Scripts

- **Workflow generation**: `scripts/generate-workflow.py` - Creates production-ready workflow JSON
- **Validation**: `scripts/validate-workflow.py` - Detects anti-patterns before deployment
- **Table management**: `scripts/table-manager.py` - Generate Data Table schemas
- **Deployment**: `n8n_create_workflow` - Upload generated workflows to n8n
- **Execution**: `n8n_execute_workflow` - Run workflows with parameters

## Decision Tree

### Should I generate a new workflow or use existing?

**Use existing workflow when:**
- ✅ You have a pre-built workflow that does what you need
- ✅ Minor parameter changes are sufficient
- ✅ The workflow is proven and tested
- ✅ Quick execution is the goal

**Generate new workflow when:**
- ✅ Custom logic required
- ✅ Unique requirements not covered by existing workflows
- ✅ Learning n8n patterns
- ✅ Building reusable components
- ✅ Need to understand workflow internals

### Should I use sub-workflows?

**YES - Use sub-workflows when:**
- 🔴 **CRITICAL**: ANY nested loops (Loop Over Items inside Loop Over Items)
- ✅ Reusable components used in multiple workflows
- ✅ Complex logic that benefits from modular separation
- ✅ Workflow has >30 nodes (consider breaking up)
- ✅ Testing individual components separately

**NO - Direct workflow is fine when:**
- ✅ Simple single-level processing
- ✅ One-off workflow not reused elsewhere
- ✅ Linear flow with no nesting
- ✅ Small workflow (<15 nodes)

**Remember**: n8n's Loop Over Items CANNOT be nested directly. Always use sub-workflows for nested iteration!

### Should I use Data Tables or pass-through state?

**Data Tables when:**
- ✅ Need persistence across executions
- ✅ Data >50MB
- ✅ Complex queries (filtering, sorting, aggregation)
- ✅ Multiple workflows accessing same data
- ✅ Audit trail required
- ✅ State must survive workflow errors
- ✅ Hierarchical relationships (series → books → chapters)

**Pass-through items when:**
- ✅ Simple counters or flags
- ✅ Temporary state within single execution
- ✅ Small data sets (<1MB)
- ✅ No cross-workflow sharing needed
- ✅ Data doesn't need to persist

**Note**: `$workflow.staticData` does NOT work in Code nodes - always use Data Tables for persistence!

### When to use which loop pattern?

**Loop Over Items:**
- ✅ Simple iteration over array
- ✅ Single-level processing
- ✅ No nesting required
- ❌ NEVER nest these directly!

**Split in Batches:**
- ✅ Processing large datasets in chunks
- ✅ Rate limiting (process N items at a time)
- ✅ Memory management for huge datasets
- ✅ Progress tracking with pauses

**Sub-workflow + Loop:**
- ✅ **REQUIRED** for any nested iteration
- ✅ Series → Books → Chapters hierarchy
- ✅ Any multi-level data structure
- ✅ Complex per-item processing

**Conditional Loop-back:**
- ✅ Polling/waiting patterns
- ✅ Retry logic
- ✅ While-loop equivalent
- ⚠️ Always add max iteration limit!

### Should I use Google Sheets or Excel?

**Google Sheets:**
- ✅ **USE THIS** in loops
- ✅ Append operation is reliable
- ✅ Works with parallel operations
- ✅ Better for automation

**Microsoft Excel:**
- ❌ **BROKEN** in loops
- ❌ Fails unpredictably
- ❌ Only use for one-off, non-looped operations
- ⚠️ Validation script will warn you!

### How should error handling work?

**Always include:**
- ✅ Error Trigger workflow for critical workflows
- ✅ Try-catch in Code nodes with complex logic
- ✅ Max iteration limits in loop-back patterns
- ✅ Validation before deployment

**Error recovery strategies:**
- Data Tables preserve state → restart from last good point
- Error Trigger workflow → notification + cleanup
- Conditional branches → graceful degradation

### What's my workflow complexity?

**Simple (<15 nodes):**
- Single workflow, no sub-workflows needed
- Direct deployment and testing

**Medium (15-30 nodes):**
- Consider modular sub-workflows
- Add validation step
- Include error handling

**Complex (>30 nodes):**
- **MUST** use sub-workflows
- Comprehensive validation required
- Error Trigger workflow essential
- Consider splitting into multiple workflows
- Performance testing needed

## Optional: MCP Tools (Desktop Only)

For users of Claude Desktop, MCP tools provide an alternative interface. See [MCP_SETUP.md](MCP_SETUP.md) for setup.

MCP tools like `mcp__n8n__workflow_list` do the same thing as the bash helpers, but:
- ❌ Only work in Claude Desktop
- ❌ Require installation and configuration
- ❌ Less transparent (you don't see the API calls)
- ✅ Slightly more convenient for desktop users

**Recommendation**: Use bash helpers for better transparency and universal compatibility
