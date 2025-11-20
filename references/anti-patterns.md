# n8n Anti-Patterns Reference

Complete guide to what DOESN'T work in n8n and why.

## The Big Three Failures

### 1. Direct Nested Loop Over Items

**What People Try:**
```
Loop Over Items (Outer) → Loop Over Items (Inner) → Process
```

**What Actually Happens:**
- First iteration: Inner loop runs correctly
- Second iteration: Inner loop thinks it already ran, skips entirely
- GitHub Issues: #13400, #21212, #13121

**The Fix:**
```
Loop Over Items (Outer) → Execute Sub-workflow → [Inner loop in sub]
```

### 2. Using $workflow.staticData in Code Nodes

**What People Try:**
```javascript
// Code node
$workflow.staticData.counter = ($workflow.staticData.counter || 0) + 1;
```

**What Actually Happens:**
- Error: $workflow.staticData is undefined
- Code nodes don't have access to workflow-level storage

**The Fix:**
```javascript
// Pass state through items
return [{
  json: {
    ...$json,
    counter: ($json.counter || 0) + 1
  }
}];
```

### 3. Parallel Operations Without Convergence

**What People Try:**
```
Split → Process A → Continue
     → Process B ↗ (hoping they merge)
```

**What Actually Happens:**
- Flow continues before Process B completes
- Process B might not even execute
- Results get lost

**The Fix:**
```
Split → Process A → Merge (Wait All) → Continue
     → Process B ↗
```

## Loop-Specific Anti-Patterns

### Excel in Loops
- **Issue**: Microsoft Excel node fails or doesn't process all iterations
- **Alternative**: Use Google Sheets with Append operation

### Update Without Keys
```javascript
// BAD - Update needs matching criteria
Google Sheets: Update Row (where? which row?)

// GOOD - Append adds new rows
Google Sheets: Append Row
```

### Missing Iteration Limits
```javascript
// BAD - Infinite loop risk
while (condition) { /* process */ }

// GOOD - Always have safety limit
while (condition && iteration < 100) { /* process */ }
```

## State Management Failures

### Expecting State to Persist
```javascript
// BAD - State lost between executions
let counter = 0; // Reset every time

// GOOD - Use Data Tables
Data Table: Upsert with execution_id
```

### Memory Between Iterations
```javascript
// BAD - No memory between loop iterations
const previousResult = /* somehow remember? */

// GOOD - Pass through items
return [{
  json: {
    current: process($json.current),
    history: [...$json.history, $json.current]
  }
}];
```

## Webhook Anti-Patterns

### Parallel Callbacks
```
Process → Continue
      ↘ HTTP Callback (parallel) // May never run!
```

**Fix**: Always inline critical operations

### Missing Response Handling
```javascript
// BAD - Fire and forget
HTTP Request → Continue

// GOOD - Check response
HTTP Request → IF (success?) → Continue/Error
```

## Data Table Anti-Patterns

### Single Monolithic Table
```javascript
// BAD - Everything in one table
{
  type: "execution|content|state|config",
  data: { /* mixed schemas */ }
}
```

**Fix**: Use multiple specialized tables

### No Expiry for Temporary Data
```javascript
// BAD - Accumulates forever
{ state: "temporary", data: "..." }

// GOOD - Include TTL
{ state: "temporary", expires_at: "...", data: "..." }
```

## Performance Anti-Patterns

### Loading Everything into Memory
```javascript
// BAD - Memory overflow
const allData = loadEntireDatabase();

// GOOD - Process in batches
Split In Batches (size: 100) → Process
```

### No Rate Limiting
```javascript
// BAD - Hammers API
Loop → HTTP Request → Loop

// GOOD - Respect limits
Loop → Wait (1s) → HTTP Request → Loop
```

## Common Misconceptions

### "Loops Work Like Normal Programming"
- **Reality**: n8n uses implicit iteration with stateful nodes
- **Implication**: Direct nesting breaks

### "All Nodes Process Items the Same"
- **Reality**: RSS, HTTP (paginated) only process first item
- **Implication**: Need explicit loops for some nodes

### "Workflow Variables Are Global"
- **Reality**: Each execution is isolated
- **Implication**: Use Data Tables for persistence

### "Parallel Is Always Faster"
- **Reality**: Overhead of sub-workflows can slow things
- **Implication**: Test performance, might need sequential

## Error Handling Anti-Patterns

### No Error Recovery
```
Process → Continue (what if error?)
```

**Fix**: Always handle errors
```
Process → Error Trigger → Log → Retry/Alert
```

### Silent Failures
```javascript
try {
  process();
} catch (e) {
  // Nothing - error hidden
}
```

**Fix**: Always log errors to Data Table

## The "It Works in Test" Trap

### Works with 1 Item, Fails with Many
- Test with: 0 items, 1 item, 2 items, 100 items
- Memory limits appear at scale
- Race conditions emerge

### Works Sequentially, Fails in Parallel
- Parallel needs explicit coordination
- Shared resources need locking
- Order matters more than expected

## Platform Limitations (Not Your Fault)

### Things That Should Work But Don't
1. Nested Loop Over Items - Broken since forever
2. Excel in loops - Microsoft node issue
3. State reset between iterations - Doesn't happen
4. StaticData in Code nodes - Not available

### Workarounds Are Mandatory
These aren't "nice to have" - they're required for production:
- Sub-workflows for ANY nesting
- Data Tables for ALL state
- Merge nodes for ALL parallel ops
- Inline for ALL critical paths
