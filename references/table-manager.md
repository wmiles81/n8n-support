# Table Manager Sub-Workflow

Complete implementation for dynamic table management in n8n.

## Overview

A reusable sub-workflow that handles all Data Table operations:
- Create tables dynamically
- Check table existence
- Migrate schemas
- Reset/clear data
- Manage multiple table sets

## Entry Point Structure

### Webhook Trigger Configuration

```json
{
  "path": "table-manager",
  "method": "POST",
  "responseMode": "responseNode",
  "schema": {
    "operation": "ensure|create|check|migrate|reset",
    "tables": [{
      "name": "string",
      "schema": {},
      "indexes": [],
      "ttl": "number (optional)"
    }],
    "entity_id": "string (optional prefix)",
    "force": false,
    "response_url": "string (optional callback)"
  }
}
```

## Core Operations

### Operation: ENSURE (Most Common)

Creates tables if they don't exist, skips if they do.

```javascript
// Node 1: Validate Request
const operation = $json.operation || 'ensure';
const tables = $json.tables || getDefaultTables();

// Add entity prefix if provided
if ($json.entity_id) {
  tables.forEach(table => {
    table.name = `${$json.entity_id}_${table.name}`.substring(0, 63);
  });
}

return [{
  json: {
    operation,
    tables,
    execution_context: {
      timestamp: new Date().toISOString(),
      parent_execution: $execution.id
    }
  }
}];

// Node 2: Check Existing Tables
const results = {
  existing: [],
  missing: [],
  errors: []
};

for (const table of $json.tables) {
  try {
    // Try to query the table
    const test = await $('Data Table').get({
      table: table.name,
      limit: 1
    });
    results.existing.push(table.name);
  } catch (error) {
    if (error.message.includes('not found')) {
      results.missing.push(table);
    } else {
      results.errors.push({
        table: table.name,
        error: error.message
      });
    }
  }
}

return [{ json: results }];

// Node 3: Create Missing Tables
for (const table of $json.missing) {
  const fields = Object.entries(table.schema).map(([name, type]) => ({
    name,
    type: mapType(type),
    required: name.includes('_id'),
    unique: name.endsWith('_id') && !name.includes('parent'),
    indexed: table.indexes?.includes(name)
  }));
  
  await createTable(table.name, fields);
}
```

### Operation: CREATE

Creates new tables, errors if they exist.

```javascript
// Node: Create Tables with Error Checking
const created = [];
const failed = [];

for (const table of $json.tables) {
  try {
    // Check if exists first
    const exists = await tableExists(table.name);
    if (exists) {
      if (!$json.force) {
        failed.push({
          table: table.name,
          reason: 'already_exists'
        });
        continue;
      }
    }
    
    // Create table
    await createTable(table.name, table.schema);
    created.push(table.name);
    
  } catch (error) {
    failed.push({
      table: table.name,
      reason: error.message
    });
  }
}

return [{
  json: {
    success: failed.length === 0,
    created,
    failed
  }
}];
```

### Operation: CHECK

Returns detailed status report.

```javascript
// Node: Generate Health Report
const report = {
  timestamp: new Date().toISOString(),
  tables: []
};

for (const table of $json.tables) {
  const status = {
    name: table.name,
    exists: false,
    healthy: false,
    row_count: 0,
    last_modified: null,
    size_bytes: 0,
    indexes: [],
    issues: []
  };
  
  try {
    // Get table stats
    const stats = await getTableStats(table.name);
    status.exists = true;
    status.row_count = stats.count;
    status.last_modified = stats.last_modified;
    
    // Check health
    if (stats.count > 1000000) {
      status.issues.push('large_table');
    }
    if (daysSince(stats.last_modified) > 30) {
      status.issues.push('stale_data');
    }
    
    status.healthy = status.issues.length === 0;
    
  } catch (error) {
    status.exists = false;
    status.issues.push('not_found');
  }
  
  report.tables.push(status);
}

// Generate summary
report.summary = {
  total: report.tables.length,
  existing: report.tables.filter(t => t.exists).length,
  healthy: report.tables.filter(t => t.healthy).length,
  issues: report.tables.filter(t => t.issues.length > 0).length
};

return [{ json: report }];
```

### Operation: MIGRATE

Updates table schemas safely.

```javascript
// Node: Schema Migration Logic
const migrations = [];

for (const table of $json.tables) {
  const current = await getTableSchema(table.name);
  const target = table.schema;
  
  const changes = {
    table: table.name,
    add_fields: [],
    modify_fields: [],
    remove_fields: [],
    add_indexes: [],
    remove_indexes: []
  };
  
  // Find new fields
  for (const [field, type] of Object.entries(target)) {
    if (!current.fields[field]) {
      changes.add_fields.push({ field, type });
    } else if (current.fields[field] !== type) {
      changes.modify_fields.push({
        field,
        from: current.fields[field],
        to: type
      });
    }
  }
  
  // Find removed fields (only if force=true)
  if ($json.force) {
    for (const field of Object.keys(current.fields)) {
      if (!target[field]) {
        changes.remove_fields.push(field);
      }
    }
  }
  
  // Check indexes
  const targetIndexes = table.indexes || [];
  const currentIndexes = current.indexes || [];
  
  changes.add_indexes = targetIndexes.filter(i => !currentIndexes.includes(i));
  changes.remove_indexes = currentIndexes.filter(i => !targetIndexes.includes(i));
  
  // Only add if changes exist
  if (changes.add_fields.length || changes.modify_fields.length || 
      changes.remove_fields.length || changes.add_indexes.length || 
      changes.remove_indexes.length) {
    migrations.push(changes);
  }
}

// Apply migrations if confirmed
if (migrations.length > 0 && $json.apply_migrations) {
  for (const migration of migrations) {
    await applyMigration(migration);
  }
}

return [{
  json: {
    migrations_needed: migrations.length,
    migrations,
    applied: $json.apply_migrations || false
  }
}];
```

### Operation: RESET

Clears or drops tables (dangerous!).

```javascript
// Node: Reset Tables with Safety Checks
if (!$json.force || !$json.confirm_reset) {
  throw new Error('Reset requires force=true and confirm_reset=true');
}

// Additional safety: Check for specific confirmation phrase
if ($json.confirmation_phrase !== `reset_${$json.entity_id || 'all'}_tables`) {
  throw new Error('Invalid confirmation phrase');
}

const results = [];

for (const table of $json.tables) {
  const result = {
    table: table.name,
    operation: $json.reset_type || 'truncate',
    backup_created: false,
    rows_affected: 0
  };
  
  try {
    // Create backup first
    if ($json.create_backup) {
      const backupName = `${table.name}_backup_${Date.now()}`;
      const backed = await backupTable(table.name, backupName);
      result.backup_created = backed;
      result.backup_name = backupName;
    }
    
    // Get count before reset
    const stats = await getTableStats(table.name);
    result.rows_affected = stats.count;
    
    // Perform reset
    if (result.operation === 'truncate') {
      await truncateTable(table.name);
      result.status = 'truncated';
    } else if (result.operation === 'drop') {
      await dropTable(table.name);
      result.status = 'dropped';
    }
    
    results.push(result);
    
  } catch (error) {
    result.status = 'error';
    result.error = error.message;
    results.push(result);
  }
}

return [{
  json: {
    operation: 'reset',
    results,
    total_rows_affected: results.reduce((sum, r) => sum + r.rows_affected, 0),
    timestamp: new Date().toISOString()
  }
}];
```

## Default Table Schemas

```javascript
function getDefaultTables() {
  return [
    {
      name: 'execution_tracker',
      schema: {
        execution_id: 'string',
        workflow_name: 'string',
        entity_type: 'string',
        entity_id: 'string',
        status: 'string',
        parent_id: 'string',
        hierarchy_level: 'number',
        metadata: 'json',
        error_count: 'number',
        last_error: 'string',
        created_at: 'datetime',
        updated_at: 'datetime'
      },
      indexes: ['entity_id', 'parent_id', 'status', 'entity_type']
    },
    {
      name: 'content_storage',
      schema: {
        content_id: 'string',
        entity_id: 'string',
        content_type: 'string',
        content: 'json',
        hash: 'string',
        version: 'number',
        size_bytes: 'number',
        created_at: 'datetime',
        created_by: 'string'
      },
      indexes: ['entity_id', 'content_type', 'hash']
    },
    {
      name: 'workflow_state',
      schema: {
        state_id: 'string',
        execution_id: 'string',
        state_key: 'string',
        state_value: 'json',
        ttl: 'number',
        created_at: 'datetime',
        expires_at: 'datetime'
      },
      indexes: ['execution_id', 'state_key', 'expires_at']
    },
    {
      name: 'dependency_tracker',
      schema: {
        dependency_id: 'string',
        source_entity: 'string',
        required_entity: 'string',
        dependency_type: 'string',
        satisfied: 'boolean',
        checked_at: 'datetime',
        satisfied_at: 'datetime'
      },
      indexes: ['source_entity', 'required_entity', 'satisfied']
    }
  ];
}
```

## Helper Functions

```javascript
// Type mapping for n8n Data Tables
function mapType(type) {
  const typeMap = {
    'string': 'string',
    'number': 'number',
    'boolean': 'boolean',
    'json': 'json',
    'array': 'json',
    'object': 'json',
    'datetime': 'dateTime',
    'date': 'dateTime',
    'timestamp': 'dateTime'
  };
  return typeMap[type.toLowerCase()] || 'string';
}

// Check if table exists
async function tableExists(tableName) {
  try {
    await $('Data Table').get({
      table: tableName,
      limit: 1
    });
    return true;
  } catch (error) {
    return false;
  }
}

// Get table statistics
async function getTableStats(tableName) {
  const result = await $('Data Table').get({
    table: tableName,
    aggregate: true
  });
  
  return {
    count: result.total || 0,
    last_modified: result.last_modified || null,
    size_estimate: (result.total || 0) * 1024 // Rough estimate
  };
}

// Backup table data
async function backupTable(source, destination) {
  // Get all data
  const data = await $('Data Table').getAll({
    table: source
  });
  
  // Create backup table
  await createTable(destination, getTableSchema(source));
  
  // Copy data
  for (const row of data) {
    await $('Data Table').insert({
      table: destination,
      data: row
    });
  }
  
  return true;
}

// Days since date
function daysSince(date) {
  if (!date) return Infinity;
  const diff = Date.now() - new Date(date).getTime();
  return Math.floor(diff / (1000 * 60 * 60 * 24));
}
```

## Usage Examples

### Basic Table Creation

```javascript
// From any workflow
const tables = await $('Execute Workflow').run({
  workflow: 'table-manager',
  data: {
    operation: 'ensure',
    tables: [{
      name: 'my_data',
      schema: {
        id: 'string',
        value: 'json',
        created: 'datetime'
      },
      indexes: ['id']
    }]
  }
});
```

### Entity-Specific Tables

```javascript
// Create tables for specific entity
const entityTables = await $('Execute Workflow').run({
  workflow: 'table-manager',
  data: {
    operation: 'ensure',
    entity_id: 'series_12345',
    tables: getDefaultTables()
  }
});

// Results in tables named:
// - series_12345_execution_tracker
// - series_12345_content_storage
// - series_12345_workflow_state
// - series_12345_dependency_tracker
```

### Health Check

```javascript
// Check table health
const health = await $('Execute Workflow').run({
  workflow: 'table-manager',
  data: {
    operation: 'check',
    tables: [{
      name: 'execution_tracker'
    }]
  }
});

if (health.summary.issues > 0) {
  // Handle issues
}
```

### Safe Reset with Backup

```javascript
// Reset tables with backup
const reset = await $('Execute Workflow').run({
  workflow: 'table-manager',
  data: {
    operation: 'reset',
    reset_type: 'truncate',
    create_backup: true,
    force: true,
    confirm_reset: true,
    confirmation_phrase: 'reset_series_12345_tables',
    entity_id: 'series_12345',
    tables: ['series_12345_content_storage']
  }
});
```

## Error Handling

### Retry Pattern

```javascript
// Retry table creation on failure
const maxRetries = 3;
let retries = 0;
let success = false;

while (retries < maxRetries && !success) {
  try {
    await $('Execute Workflow').run({
      workflow: 'table-manager',
      data: {
        operation: 'ensure',
        tables: requiredTables
      }
    });
    success = true;
  } catch (error) {
    retries++;
    if (retries >= maxRetries) {
      throw new Error(`Table creation failed after ${maxRetries} attempts: ${error.message}`);
    }
    await wait(2 ** retries * 1000); // Exponential backoff
  }
}
```

### Validation Before Use

```javascript
// Always validate tables exist before use
const validation = await $('Execute Workflow').run({
  workflow: 'table-manager',
  data: {
    operation: 'check',
    tables: requiredTables
  }
});

if (validation.summary.existing < requiredTables.length) {
  // Create missing tables
  await $('Execute Workflow').run({
    workflow: 'table-manager',
    data: {
      operation: 'ensure',
      tables: requiredTables
    }
  });
}
```

## Performance Considerations

### Batch Operations

```javascript
// Create multiple table sets efficiently
const tableSets = [
  { entity_id: 'series_001', tables: defaultTables },
  { entity_id: 'series_002', tables: defaultTables },
  { entity_id: 'series_003', tables: defaultTables }
];

// Parallel creation
const results = await Promise.all(
  tableSets.map(set => 
    $('Execute Workflow').run({
      workflow: 'table-manager',
      data: {
        operation: 'ensure',
        ...set
      }
    })
  )
);
```

### TTL for Temporary Tables

```javascript
// Create temporary table with TTL
const tempTable = {
  name: `temp_${Date.now()}`,
  schema: {
    id: 'string',
    data: 'json',
    expires_at: 'datetime'
  },
  ttl: 3600 // 1 hour
};

// Automatic cleanup job (separate workflow)
const cleanupExpired = async () => {
  const expired = await $('Data Table').query({
    table: 'temp_*',
    where: {
      expires_at: { $lt: new Date().toISOString() }
    }
  });
  
  for (const row of expired) {
    await $('Data Table').delete({
      table: row.table_name,
      id: row.id
    });
  }
};
```

This Table Manager pattern provides complete database infrastructure management for n8n workflows!
