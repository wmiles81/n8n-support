# Hierarchical Workflow Patterns

Complex multi-tier workflow architectures for n8n (series → books → chapters example).

## Multi-Level Data Architecture

### Core Concept: Multiple Linked Tables

```javascript
// Level 1: Master Execution Tracking
execution_master = {
  execution_id: "exec_123",
  entity_type: "series|book|chapter",
  entity_id: "series_001",
  hierarchy_level: 1,  // 1=series, 2=book, 3=chapter
  parent_id: null,     // null for top level
  status: "processing",
  metadata: {
    total_children: 3,
    completed_children: 0
  }
}

// Level 2: Content Storage
content_storage = {
  content_id: "content_456",
  entity_id: "series_001",
  content_type: "premise|characters|outline",
  hierarchy_path: ["series_001"],  // Full path
  content: { /* actual content */ },
  dependencies: ["content_123"],   // Required before this
}

// Level 3: Dependency Management
dependency_tracker = {
  dependency_id: "dep_789",
  source_entity: "book_001",
  requires: ["series_001_premise", "series_001_characters"],
  satisfied: false,
  last_check: "2025-01-01T00:00:00Z"
}
```

## Three-Tier Generation Pattern

### Overview: Series → Books → Chapters

```
[Series Generation]
        ↓
[Parallel Book Generation]
        ↓
[Sequential Chapter Generation per Book]
```

### Phase 1: Top-Level Generation

```javascript
// Initialize Series Workflow
const initializeSeries = {
  // Create master record
  execution_id: $execution.id,
  entity_id: `series_${Date.now()}`,
  entity_type: "series",
  hierarchy_level: 1,
  parent_id: null,
  
  // Define children
  planned_books: $json.num_books || 3,
  books: Array(planned_books).fill(null).map((_, i) => ({
    book_id: `${entity_id}_book_${i+1}`,
    book_number: i + 1,
    status: "pending"
  }))
};

// Generate series-level content
→ Sub-workflow: Generate Premise
→ Sub-workflow: Generate World
→ Sub-workflow: Generate Core Characters
→ Data Table: Store all series content
```

### Phase 2: Parallel Mid-Level Generation

```javascript
// Split books for parallel processing
const bookBatches = $json.books.map(book => ({
  book_id: book.book_id,
  parent_id: $json.series_id,
  hierarchy_level: 2,
  
  // Inherit parent context
  series_context: {
    premise: $json.series_premise,
    world: $json.series_world,
    characters: $json.series_characters
  },
  
  // Previous book summaries (for continuity)
  previous_books: $json.books
    .filter(b => b.book_number < book.book_number)
    .map(b => b.summary)
}));

// Parallel execution with convergence
[Loop Over Books]
    ↓
[Execute Sub-workflow: Generate Book] // Wait: false
    ↓
[Webhook callback per book]
    ↓
[Merge (Wait for All Books)] // CRITICAL convergence
    ↓
[Aggregate all book data]
```

### Phase 3: Deep-Level Sequential Generation

```javascript
// For each book's chapters (sequential for context)
const generateChapters = async (book) => {
  const chapters = [];
  
  for (let i = 0; i < book.num_chapters; i++) {
    const chapter = {
      chapter_id: `${book.book_id}_ch_${i+1}`,
      hierarchy_level: 3,
      parent_id: book.book_id,
      
      // Accumulate ALL context
      context: {
        series: await getSeriesContext(book.series_id),
        book: await getBookContext(book.book_id),
        previous_chapters: chapters.slice(0, i),
        chapter_number: i + 1
      }
    };
    
    // Generate with full context
    const result = await generateChapter(chapter);
    chapters.push(result);
    
    // Update progress
    await updateProgress(book.book_id, i + 1, book.num_chapters);
  }
  
  return chapters;
};
```

## Context Accumulation Strategy

### The Context Pyramid

```
        [Series Context]
              ↓
      [+ Book Context]
              ↓
    [+ Chapter Context]
              ↓
   [+ Previous Chapters]
```

### Implementation Pattern

```javascript
// Build complete context at each level
const buildContext = async (entity) => {
  const context = {
    immediate: await getEntity(entity.entity_id),
    parent: null,
    ancestors: [],
    siblings: [],
    children: []
  };
  
  // Walk up the hierarchy
  let currentParent = entity.parent_id;
  while (currentParent) {
    const parent = await getEntity(currentParent);
    context.ancestors.unshift(parent);
    currentParent = parent.parent_id;
  }
  
  // Get siblings (same parent, different ID)
  if (entity.parent_id) {
    context.siblings = await getSiblings(entity);
  }
  
  // Get completed children
  context.children = await getChildren(entity.entity_id, 'complete');
  
  return context;
};
```

## Dependency Management

### Dependency Types

```javascript
// Hard dependency - MUST complete before starting
{
  type: "hard",
  source: "book_001_outline",
  requires: ["series_001_premise", "series_001_characters"],
  block_until_satisfied: true
}

// Soft dependency - SHOULD have but can proceed
{
  type: "soft", 
  source: "chapter_010",
  prefers: ["chapter_009_summary"],
  block_until_satisfied: false
}

// Conditional dependency - Required IF condition met
{
  type: "conditional",
  source: "epilogue",
  requires_if: {
    condition: "book.has_epilogue === true",
    dependencies: ["all_chapters_complete"]
  }
}
```

### Dependency Resolution Pattern

```javascript
// Check and wait for dependencies
const waitForDependencies = async (entity) => {
  const deps = await getDependencies(entity.entity_id);
  const maxWait = 300000; // 5 minutes
  const startTime = Date.now();
  
  while (true) {
    const unsatisfied = [];
    
    for (const dep of deps) {
      const required = await getEntity(dep.requires);
      if (!required || required.status !== 'complete') {
        unsatisfied.push(dep);
      }
    }
    
    if (unsatisfied.length === 0) {
      return true; // All satisfied
    }
    
    if (Date.now() - startTime > maxWait) {
      throw new Error(`Dependencies timeout: ${unsatisfied.map(d => d.requires)}`);
    }
    
    await wait(5000); // Check every 5 seconds
  }
};
```

## Progress Tracking

### Multi-Level Progress Aggregation

```javascript
// Track progress at each level
const updateProgress = async (entity_id, level) => {
  const entity = await getEntity(entity_id);
  
  if (level === 3) { // Chapter level
    const bookProgress = await calculateBookProgress(entity.parent_id);
    await updateEntity(entity.parent_id, { progress: bookProgress });
    
    const seriesProgress = await calculateSeriesProgress(entity.ancestors[0]);
    await updateEntity(entity.ancestors[0], { progress: seriesProgress });
  }
  
  // Send progress webhook
  await sendProgressUpdate({
    entity_id,
    level,
    progress: entity.progress,
    timestamp: new Date().toISOString()
  });
};

// Calculate aggregate progress
const calculateProgress = (children) => {
  const weights = {
    'premise': 0.2,
    'characters': 0.2,
    'outline': 0.3,
    'chapters': 0.3
  };
  
  let totalWeight = 0;
  let completedWeight = 0;
  
  for (const child of children) {
    const weight = weights[child.type] || 0.1;
    totalWeight += weight;
    if (child.status === 'complete') {
      completedWeight += weight;
    }
  }
  
  return Math.round((completedWeight / totalWeight) * 100);
};
```

## Recovery Patterns

### Resume from Failure

```javascript
// Find last successful point
const findResumePoint = async (series_id) => {
  // Get all entities for this series
  const entities = await getAllEntities(series_id);
  
  // Find incomplete entities
  const incomplete = entities.filter(e => 
    e.status !== 'complete' && e.status !== 'error'
  );
  
  if (incomplete.length === 0) {
    return { status: 'complete', resume_point: null };
  }
  
  // Sort by hierarchy and creation order
  incomplete.sort((a, b) => {
    if (a.hierarchy_level !== b.hierarchy_level) {
      return a.hierarchy_level - b.hierarchy_level;
    }
    return a.created_at - b.created_at;
  });
  
  return {
    status: 'resume_required',
    resume_point: incomplete[0],
    pending_count: incomplete.length
  };
};
```

### Rollback Strategy

```javascript
// Rollback to checkpoint
const rollbackToCheckpoint = async (series_id, checkpoint_id) => {
  // Mark all entities after checkpoint as invalid
  const entities = await getAllEntitiesAfter(checkpoint_id);
  
  for (const entity of entities) {
    await updateEntity(entity.entity_id, {
      status: 'rolled_back',
      rollback_from: entity.status,
      rollback_at: new Date().toISOString()
    });
  }
  
  // Reset to checkpoint state
  await restoreFromCheckpoint(checkpoint_id);
  
  return {
    rolled_back: entities.length,
    checkpoint: checkpoint_id
  };
};
```

## Optimization Patterns

### Batch Context Loading

```javascript
// Load context efficiently
const batchLoadContext = async (entity_ids) => {
  // Single query instead of N queries
  const contexts = await DataTable.query({
    entity_id: { $in: entity_ids },
    content_type: 'context'
  });
  
  // Build context map
  return contexts.reduce((map, ctx) => {
    map[ctx.entity_id] = ctx;
    return map;
  }, {});
};
```

### Parallel Parent, Sequential Children

```javascript
// Optimize by parallelizing at parent level
const optimizedGeneration = async (series) => {
  // Parallel: Generate all book outlines
  const bookOutlines = await Promise.all(
    series.books.map(book => generateBookOutline(book))
  );
  
  // Sequential: Generate chapters per book (for context)
  for (const book of bookOutlines) {
    await generateBookChaptersSequentially(book);
  }
  
  return series;
};
```

## Testing Strategies

### Test Data Hierarchies

```javascript
// Minimal test hierarchy
{
  series: 1,
  books: 2,
  chapters_per_book: 3
}

// Stress test hierarchy
{
  series: 1,
  books: 10,
  chapters_per_book: 30
}

// Edge case: Single chain
{
  series: 1,
  books: 1,
  chapters_per_book: 1
}

// Edge case: Wide and shallow
{
  series: 1,
  books: 100,
  chapters_per_book: 1
}
```

### Validation Checks

```javascript
// Validate hierarchy integrity
const validateHierarchy = async (series_id) => {
  const issues = [];
  
  // Check parent-child relationships
  const entities = await getAllEntities(series_id);
  
  for (const entity of entities) {
    if (entity.parent_id) {
      const parent = entities.find(e => e.entity_id === entity.parent_id);
      if (!parent) {
        issues.push(`Orphan entity: ${entity.entity_id}`);
      }
      if (parent && parent.hierarchy_level >= entity.hierarchy_level) {
        issues.push(`Invalid hierarchy: ${entity.entity_id}`);
      }
    }
  }
  
  // Check circular dependencies
  const visited = new Set();
  const checkCircular = (id, path = []) => {
    if (path.includes(id)) {
      issues.push(`Circular dependency: ${path.join(' → ')} → ${id}`);
      return;
    }
    visited.add(id);
    // Check dependencies...
  };
  
  return issues;
};
```

## Complete Example: Book Series Generator

### Master Orchestrator
```javascript
// Main workflow entry point
const generateBookSeries = async (config) => {
  // Initialize tracking
  const series_id = `series_${Date.now()}`;
  await initializeTables(series_id);
  
  // Phase 1: Series foundation
  const series = await generateSeriesFoundation(config);
  
  // Phase 2: Book outlines (parallel)
  const books = await generateBookOutlines(series);
  
  // Phase 3: Book details (parallel)  
  const detailedBooks = await generateBookDetails(books);
  
  // Phase 4: Chapters (sequential per book)
  for (const book of detailedBooks) {
    await generateBookChapters(book);
  }
  
  // Phase 5: Final assembly
  const complete = await assembleSeries(series_id);
  
  return complete;
};
```

This hierarchical pattern scales to any multi-level generation task!
