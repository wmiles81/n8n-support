# Example: Monitor Workflow Executions

This example shows how to monitor, debug, and analyze n8n workflow executions.

## Scenario

You have long-running workflows and need to monitor their progress, debug failures, and analyze performance.

## Basic Monitoring

### Check Single Execution

```
Claude, check execution "exec_123"
```

Uses:
```javascript
mcp__n8n__execution_get({
  executionId: "exec_123"
})
```

Returns:
- Status (running/success/failed/waiting)
- Start time
- End time (if complete)
- Duration
- Input data
- Output data
- Error details (if failed)

### List Recent Executions

```
Claude, show me the last 10 executions for workflow "wf_456"
```

Uses:
```javascript
mcp__n8n__execution_list({
  workflowId: "wf_456",
  limit: 10
})
```

## Advanced Monitoring

### Monitor Long-Running Execution

For workflows that take minutes/hours:

```
User: Execute the Book Series Generator for 10 books

Claude: Starting execution...
Execution ID: exec_789
Status: Running
Started: 10:00:00

User: What's the progress?

Claude: Execution exec_789:
Status: Running
Duration: 2m 15s
Current step: Generating book 3 of 10

User: Check again in 5 minutes

Claude: Execution exec_789:
Status: Running
Duration: 7m 30s
Current step: Generating book 7 of 10
Progress: ~70%
```

### Query Data Tables for Progress

For hierarchical workflows, check intermediate results:

```
User: Show me how many chapters have been generated so far

Claude: Querying content_storage table...

Results for execution exec_789:
- Books completed: 6
- Chapters completed: 58
- Chapters in progress: 2
- Total expected: 100
Progress: 58%
```

## Debugging Failed Executions

### Identify Failure Point

```
User: Execution exec_999 failed, what went wrong?

Claude: Analyzing execution exec_999...

Failure Details:
- Status: Failed
- Failed at: Node "Generate Chapter Content"
- Error: "OpenAI API rate limit exceeded"
- Iteration: Chapter 23 of 30
- Time of failure: 10:45:32

Successful before failure:
✓ Books 1-2: Complete (20 chapters)
✓ Book 3: Partial (2 of 10 chapters)
✗ Failed on Book 3, Chapter 3
```

### Review Execution Data

```
User: Show me the input that caused the error

Claude: Input data for failed node:

{
  "chapter_number": 3,
  "book_id": "book_003",
  "previous_chapters": [...], // 22 chapters
  "context_size": "45,000 tokens" // ISSUE: Exceeds API limit
}

Issue identified: Context accumulation caused token limit exceeded.

Recommendation: Implement context truncation in the workflow.
```

### Compare Failed vs Successful

```
User: Compare exec_999 (failed) with exec_888 (success)

Claude: Comparison:

exec_888 (Success):
- Input: 3 books, 10 chapters each
- Duration: 5m 12s
- Max context: 15,000 tokens ✓

exec_999 (Failed):
- Input: 10 books, 10 chapters each
- Duration: 45m 32s (before failure)
- Max context: 45,000 tokens ✗

Difference: exec_999 accumulated too much context over 23 chapters.
```

## Performance Analysis

### Execution Time Trends

```
User: How long do executions typically take for this workflow?

Claude: Analyzing last 20 executions of "Book Series Generator":

Average duration by book count:
- 1 book: 1m 30s
- 3 books: 4m 45s
- 5 books: 8m 20s
- 10 books: 17m 15s

Trend: ~1m 45s per book
Recommendation: For 20 books, expect ~35 minutes
```

### Bottleneck Identification

```
User: Which step takes the longest?

Claude: Time analysis for execution exec_888:

Node execution times:
1. Initialize Data Tables: 2s
2. Generate Series Foundation: 15s
3. Generate Book (x3): 4m 20s (87% of total)
   ├─ Generate Outline: 12s each
   └─ Generate Chapters: 3m 45s each ← BOTTLENECK

Bottleneck: Chapter generation takes 87% of execution time.
Opportunity: Parallelize chapter generation within books.
```

## Stopping Runaway Executions

### Stop Long-Running Execution

```
User: Stop execution exec_789, it's taking too long

Claude: Stopping execution exec_789...

✓ Execution stopped
Status: Stopped
Duration before stop: 45m 12s
Partial results saved: 67 of 100 chapters

Data preserved in tables:
- execution_tracker: Status updated to "stopped"
- content_storage: 67 chapters available
```

## Execution History Analysis

### Find Patterns in Failures

```
User: Show me all failed executions this week

Claude: Failed executions (last 7 days):

Total: 8 failures out of 45 executions (17.7% failure rate)

Failure reasons:
- API rate limits: 5 (62.5%)
- Timeout errors: 2 (25%)
- Invalid input: 1 (12.5%)

Time pattern:
- Peak failures: 2pm-4pm (API rate limits)
- No failures: 10pm-6am

Recommendation: Schedule large batches during off-peak hours.
```

### Success Rate by Configuration

```
User: Which workflow configuration has the best success rate?

Claude: Analyzing executions by configuration:

3 books, 10 chapters:
- Executions: 15
- Success: 15 (100%)
- Avg duration: 4m 45s
- Recommended ✓

5 books, 15 chapters:
- Executions: 12
- Success: 10 (83%)
- Avg duration: 12m 30s
- Acceptable

10 books, 20 chapters:
- Executions: 8
- Success: 3 (37.5%)
- Avg duration: 35m+ (often fails)
- Not recommended ✗

Recommendation: Keep under 5 books or 75 total chapters for reliability.
```

## Monitoring Dashboard

### Create Summary Report

```
User: Give me a status report on all active workflows

Claude: n8n Workflow Status Report
Generated: 2025-01-20 15:30

Active Workflows: 5
Total Executions (24h): 67

By Workflow:
1. "Book Series Generator"
   - Executions: 25
   - Success: 22 (88%)
   - Running: 1
   - Failed: 2

2. "Content Pipeline"
   - Executions: 18
   - Success: 18 (100%)
   - Running: 0

3. "Data Sync"
   - Executions: 24
   - Success: 20 (83%)
   - Running: 2
   - Failed: 2

Attention Needed:
⚠️ "Book Series Generator" - 2 recent failures (API limits)
⚠️ "Data Sync" - 2 executions running >30 minutes
```

## Best Practices

1. **Monitor long-running workflows** every 5-10 minutes
2. **Check Data Tables** for intermediate progress
3. **Stop runaway executions** before they consume resources
4. **Analyze failure patterns** to improve workflows
5. **Set up alerts** for critical failures (external to n8n)

## See Also

- [01-execute-workflow.md](01-execute-workflow.md) - Execute workflows
- [02-deploy-workflow.md](02-deploy-workflow.md) - Deploy workflows
- [../references/known-issues.md](../references/known-issues.md) - Common issues
