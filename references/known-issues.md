# n8n Known Issues & Workarounds

Active GitHub issues and their production workarounds (as of 2025).

## Critical Loop Execution Issues

### Issue #13400: Nested Loop Fails on Second Iteration
**Status**: Open (Feb 2025)  
**Description**: "On the second cycle of 'Loop Over User Values' it does not execute 'loop over questions' properly"

**Symptoms**:
- Inner loop runs correctly on first outer iteration
- Inner loop completely skipped on subsequent iterations
- No error messages, just silent failure

**Root Cause**: Execution context pollution between iterations

**Workaround**:
```javascript
// DON'T DO THIS:
Loop Over Items (Outer) → Loop Over Items (Inner)

// DO THIS INSTEAD:
Loop Over Items (Outer) → Execute Sub-workflow → [Inner loop in sub]
                                   ↓
                          [Clean execution context]
```

### Issue #21212: Loop Stops After First Iteration
**Status**: Open (3 weeks ago)  
**Description**: "The loop stops executing its internal nodes after the first iteration"

**Symptoms**:
- Loop appears to complete but only processes first item
- Execution time suspiciously fast for subsequent items
- Data from first iteration may appear in later items

**Workaround**:
```javascript
// Force new execution context
const forceNewContext = {
  workflow: 'sub_workflow_id',
  waitForSubWorkflow: false,
  options: {
    shareParentExecutionId: false // CRITICAL
  }
};
```

### Issue #13121: Loop Remembers Previous Execution
**Status**: Open (Feb 2025)  
**Description**: "The node appears to remember the previous execution's Done branch"

**Symptoms**:
- Loop merges results from different executions
- "Done" branch triggers prematurely
- State from previous runs affects current run

**Workaround**:
```javascript
// Clear state explicitly
Data Table: Delete where execution_id != current
// Then initialize fresh
Data Table: Insert new state for current execution
```

## Microsoft Excel Issues

### Excel Node Failures in Loops
**Status**: Confirmed  
**Description**: "Microsoft Excel node fails or does not process all iterations"

**Symptoms**:
- Works for single item, fails for multiple
- Silent failures with no error messages
- Partial data written, then stops

**Workaround**:
```javascript
// Don't use Excel in loops AT ALL
// Use Google Sheets instead:
Google Sheets (Append) // Works reliably
// OR export to CSV, then convert to Excel outside n8n
```

## State Management Issues

### No $workflow.staticData in Code Nodes
**Status**: By Design (Won't Fix)  
**Description**: Code nodes don't have access to workflow-level static data

**What Doesn't Work**:
```javascript
// This will fail in Code node:
$workflow.staticData.counter = 1; // undefined
```

**Workaround**:
```javascript
// Option 1: Pass through items
return [{
  json: {
    ...$json,
    counter: ($json.counter || 0) + 1
  }
}];

// Option 2: Use Data Tables
await $('Data Table').upsert({
  table: 'workflow_state',
  key: { execution_id: $execution.id },
  data: { counter: currentCount + 1 }
});

// Option 3: Use Function Node (has staticData access)
// But Function nodes have other limitations
```

## Parallel Execution Issues

### Parallel Branches May Not Execute
**Status**: Known Behavior  
**Description**: Parallel branches without convergence may be skipped

**Symptoms**:
- Webhook callbacks don't fire
- Logging nodes skipped
- Workflow continues before parallel completes

**Workaround**:
```javascript
// ALWAYS converge parallel branches
Split → Process A → Merge (Wait All) → Continue
     → Process B ↗

// For critical operations, keep inline
Process → HTTP Callback → Continue // Sequential
```

## Memory & Performance Issues

### 16MB Payload Limit
**Status**: Configurable (self-hosted only)  
**Description**: Default payload limit causes large workflow failures

**Symptoms**:
```
Error: Workflow execution data is too large
```

**Workaround**:
```javascript
// Split large datasets
Split In Batches (size: 100) → Process → Aggregate

// Or use Data Tables for storage
Store in Data Table → Process in chunks → Read results
```

### Memory Leaks in Long-Running Workflows
**Status**: Under Investigation  
**Description**: Memory usage grows over time in loops

**Symptoms**:
- Execution slows progressively
- Eventually crashes with OOM
- Affects workflows with 1000+ iterations

**Workaround**:
```javascript
// Break into smaller sub-workflows
Loop (max 100) → Execute Sub-workflow → Check if more → Loop back

// Clear variables explicitly
delete $json.large_data;
return [{ json: { ...essential_data_only } }];
```

## Webhook Issues

### Webhook Response Timeout
**Status**: Known Limitation  
**Description**: Webhooks timeout after 120 seconds

**Workaround**:
```javascript
// For long processes, respond immediately
Webhook → Respond Immediately → Process Async → Callback

// Not:
Webhook → Long Process → Respond // Timeout!
```

### Webhook Path Conflicts
**Status**: Open  
**Description**: Multiple workflows can't use same webhook path

**Workaround**:
```javascript
// Add unique identifiers
webhook_path: `process/${workflow_id}/${unique_id}`

// Or use single router workflow
Main Webhook → Route by Parameter → Execute Specific Workflow
```

## Data Table Issues

### Table Name Length Limit
**Status**: By Design  
**Description**: Table names limited to 63 characters

**Workaround**:
```javascript
// Truncate and ensure uniqueness
const tableName = longName.substring(0, 60) + '_' + hash.substring(0, 3);
```

### No Direct Table Listing
**Status**: Feature Request  
**Description**: Can't list all existing tables via API

**Workaround**:
```javascript
// Maintain table registry
const registry = {
  table: 'table_registry',
  data: {
    table_name: newTable,
    created_at: new Date(),
    schema: schemaJson
  }
};
```

## Expression Evaluation Issues

### Expressions in Loops Reference Wrong Item
**Status**: Open  
**Description**: {{ $item() }} references incorrect item in complex flows

**Workaround**:
```javascript
// Store data in JSON explicitly
const currentData = $json; // Capture current item
// Use currentData instead of $item() references
```

## IF Node Issues

### IF Node Conditions Not Resetting
**Status**: Under Investigation  
**Description**: IF conditions may retain previous evaluation

**Workaround**:
```javascript
// Use explicit boolean in data
return [{
  json: {
    ...$json,
    should_continue: iteration < max // Explicit boolean
  }
}];

// Then in IF node:
{{ $json.should_continue === true }}
```

## Merge Node Issues

### Merge Node Data Loss
**Status**: Sporadic  
**Description**: Merge sometimes loses data from branches

**Workaround**:
```javascript
// Store branch data in Data Table before merge
Branch A → Store in Table → Merge
Branch B → Store in Table ↗

// If data lost, recover from table
```

## Version-Specific Issues

### n8n 1.x Breaking Changes
- Webhook URL format changed
- Node type versions updated
- Expression syntax stricter

**Migration Pattern**:
```javascript
// Old (pre-1.0):
{{ $node["Node Name"].data }}

// New (1.0+):
{{ $('Node Name').item.json }}
```

## Platform-Specific Issues

### Docker Memory Limits
**Default**: 2GB (often insufficient)

**Fix**:
```bash
docker run -m 4g n8n
```

### Timezone Issues
**Symptom**: Scheduled workflows run at wrong time

**Fix**:
```javascript
// Set timezone explicitly
process.env.TZ = 'America/New_York';
// Or in workflow settings
```

## Debugging Techniques

### Enable Verbose Logging
```javascript
// Add debug nodes
Code Node: console.log(JSON.stringify($json, null, 2))

// Check execution data
{{ $execution.id }} // Current execution
{{ $execution.retryOf }} // If retry
```

### Test Patterns
```javascript
// Minimal test case
testData = [
  { id: 1 }, // Single item
  { id: 2 }, { id: 3 } // Multiple items
];

// Edge cases
emptyData = [];
largeData = Array(1000).fill({ data: 'test' });
```

## Community Workarounds

### "The Webhook Dance"
For complex webhook flows:
1. Main webhook receives request
2. Immediately responds with 200
3. Triggers async sub-workflow
4. Sub-workflow calls back when done

### "The State Machine Pattern"
For complex state management:
1. Every state change goes through central workflow
2. State stored in Data Table
3. Transitions validated before execution
4. Recovery points at each state

### "The Retry Wrapper"
For unreliable operations:
```javascript
Retry Loop (max 3) → Try Operation → Success?
         ↑                              ↓ No
         └──────── Exponential Wait ←───┘
                           ↓ Yes
                        Continue
```

## When to Escalate

Create GitHub issue if:
- Workaround causes significant performance impact
- No workaround exists
- Security implications
- Data loss occurs

Include:
- n8n version
- Deployment type (cloud/self-hosted)
- Minimal reproduction workflow
- Expected vs actual behavior

These workarounds keep production workflows running despite platform limitations!
