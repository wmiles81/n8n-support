#!/usr/bin/env python3
"""
n8n Table Manager
Manages Data Table schemas and operations for n8n workflows
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class TableManager:
    """Manage n8n Data Table operations and schemas"""
    
    # Default table schemas
    SCHEMAS = {
        "execution_tracker": {
            "fields": {
                "execution_id": "string",
                "workflow_name": "string",
                "entity_type": "string",
                "entity_id": "string",
                "status": "string",
                "parent_id": "string",
                "hierarchy_level": "number",
                "iteration": "number",
                "metadata": "json",
                "error_count": "number",
                "last_error": "string",
                "created_at": "datetime",
                "updated_at": "datetime"
            },
            "indexes": ["entity_id", "parent_id", "status", "entity_type"],
            "description": "Tracks workflow execution state and hierarchy"
        },
        "content_storage": {
            "fields": {
                "content_id": "string",
                "entity_id": "string",
                "content_type": "string",
                "content": "json",
                "hash": "string",
                "version": "number",
                "size_bytes": "number",
                "created_at": "datetime",
                "created_by": "string"
            },
            "indexes": ["entity_id", "content_type", "hash"],
            "description": "Stores generated content with versioning"
        },
        "workflow_state": {
            "fields": {
                "state_id": "string",
                "execution_id": "string",
                "state_key": "string",
                "state_value": "json",
                "ttl": "number",
                "created_at": "datetime",
                "expires_at": "datetime"
            },
            "indexes": ["execution_id", "state_key", "expires_at"],
            "description": "Temporary state storage with TTL"
        },
        "dependency_tracker": {
            "fields": {
                "dependency_id": "string",
                "source_entity": "string",
                "required_entity": "string",
                "dependency_type": "string",
                "satisfied": "boolean",
                "checked_at": "datetime",
                "satisfied_at": "datetime"
            },
            "indexes": ["source_entity", "required_entity", "satisfied"],
            "description": "Tracks entity dependencies for complex workflows"
        },
        "webhook_callbacks": {
            "fields": {
                "callback_id": "string",
                "execution_id": "string",
                "webhook_url": "string",
                "status": "string",
                "payload": "json",
                "retry_count": "number",
                "last_attempt": "datetime",
                "next_retry": "datetime"
            },
            "indexes": ["execution_id", "status", "next_retry"],
            "description": "Manages webhook callbacks and retries"
        }
    }
    
    @classmethod
    def get_schema(cls, table_type: str, entity_id: str = None) -> Dict:
        """Get schema for a table type, optionally with entity prefix"""
        if table_type not in cls.SCHEMAS:
            raise ValueError(f"Unknown table type: {table_type}")
        
        schema = cls.SCHEMAS[table_type].copy()
        
        if entity_id:
            # Add entity prefix to table name
            table_name = f"{entity_id}_{table_type}"[:63]  # n8n limit
            schema["name"] = table_name
        else:
            schema["name"] = table_type
        
        return schema
    
    @classmethod
    def get_all_schemas(cls, entity_id: str = None) -> List[Dict]:
        """Get all default schemas, optionally with entity prefix"""
        return [cls.get_schema(table_type, entity_id) 
                for table_type in cls.SCHEMAS.keys()]
    
    @classmethod
    def generate_create_script(cls, table_type: str, entity_id: str = None) -> str:
        """Generate n8n code for creating a table"""
        schema = cls.get_schema(table_type, entity_id)
        
        code = f"""
// Create {schema['name']} table
const tableSchema = {{
    name: "{schema['name']}",
    fields: {json.dumps(schema['fields'], indent=8)},
    indexes: {json.dumps(schema['indexes'])},
    description: "{schema['description']}"
}};

// This would be used in a Data Table node or custom function
return [{{
    json: {{
        operation: "create_table",
        schema: tableSchema,
        created_at: new Date().toISOString()
    }}
}}];
"""
        return code
    
    @classmethod
    def generate_entity_id(cls, prefix: str = "entity") -> str:
        """Generate unique entity ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:6]
        return f"{prefix}_{timestamp}_{random_hash}"
    
    @classmethod
    def generate_migration(cls, from_schema: Dict, to_schema: Dict) -> Dict:
        """Generate migration plan between schemas"""
        migration = {
            "add_fields": [],
            "remove_fields": [],
            "modify_fields": [],
            "add_indexes": [],
            "remove_indexes": []
        }
        
        from_fields = from_schema.get("fields", {})
        to_fields = to_schema.get("fields", {})
        from_indexes = set(from_schema.get("indexes", []))
        to_indexes = set(to_schema.get("indexes", []))
        
        # Find field changes
        for field, field_type in to_fields.items():
            if field not in from_fields:
                migration["add_fields"].append({"field": field, "type": field_type})
            elif from_fields[field] != field_type:
                migration["modify_fields"].append({
                    "field": field,
                    "from": from_fields[field],
                    "to": field_type
                })
        
        for field in from_fields:
            if field not in to_fields:
                migration["remove_fields"].append(field)
        
        # Find index changes
        migration["add_indexes"] = list(to_indexes - from_indexes)
        migration["remove_indexes"] = list(from_indexes - to_indexes)
        
        return migration


class TableOperations:
    """Generate n8n code for table operations"""
    
    @staticmethod
    def insert_code(table_name: str, data: Dict) -> str:
        """Generate code for inserting data"""
        return f"""
// Insert into {table_name}
const data = {json.dumps(data, indent=4)};
data.created_at = new Date().toISOString();
data.execution_id = $execution.id;

return [{{
    json: {{
        operation: "insert",
        table: "{table_name}",
        data: data
    }}
}}];
"""
    
    @staticmethod
    def upsert_code(table_name: str, key_fields: List[str], data: Dict) -> str:
        """Generate code for upserting data"""
        return f"""
// Upsert into {table_name}
const data = {json.dumps(data, indent=4)};
data.updated_at = new Date().toISOString();

const keyFields = {json.dumps(key_fields)};
const key = {{}};
keyFields.forEach(field => {{
    key[field] = data[field] || $json[field];
}});

return [{{
    json: {{
        operation: "upsert",
        table: "{table_name}",
        key: key,
        data: data
    }}
}}];
"""
    
    @staticmethod
    def query_code(table_name: str, conditions: Dict = None) -> str:
        """Generate code for querying data"""
        conditions = conditions or {}
        return f"""
// Query {table_name}
const conditions = {json.dumps(conditions, indent=4)};

// Add dynamic conditions
if ($json.status) {{
    conditions.status = $json.status;
}}
if ($json.entity_id) {{
    conditions.entity_id = $json.entity_id;
}}

return [{{
    json: {{
        operation: "query",
        table: "{table_name}",
        conditions: conditions,
        limit: 100
    }}
}}];
"""
    
    @staticmethod
    def cleanup_expired_code(table_name: str) -> str:
        """Generate code for cleaning up expired entries"""
        return f"""
// Cleanup expired entries in {table_name}
const now = new Date().toISOString();

return [{{
    json: {{
        operation: "delete",
        table: "{table_name}",
        conditions: {{
            expires_at: {{ $lt: now }}
        }}
    }}
}}];
"""


class HierarchicalTableManager:
    """Manage tables for hierarchical workflows (series/books/chapters)"""
    
    @staticmethod
    def generate_hierarchy_schema(levels: List[str]) -> Dict:
        """Generate schema for hierarchical data"""
        schema = {
            "hierarchy_metadata": {
                "fields": {
                    "entity_id": "string",
                    "parent_id": "string",
                    "hierarchy_level": "number",
                    "entity_type": "string",
                    "path": "json",  # Array of parent IDs
                    "children": "json",  # Array of child IDs
                    "metadata": "json"
                },
                "indexes": ["entity_id", "parent_id", "hierarchy_level"]
            }
        }
        
        # Add level-specific tables
        for i, level in enumerate(levels):
            schema[f"{level}_data"] = {
                "fields": {
                    f"{level}_id": "string",
                    "parent_id": "string" if i > 0 else "null",
                    "sequence_number": "number",
                    "title": "string",
                    "content": "json",
                    "status": "string",
                    "metadata": "json",
                    "created_at": "datetime"
                },
                "indexes": [f"{level}_id", "parent_id", "sequence_number"]
            }
        
        return schema
    
    @staticmethod
    def generate_dependency_check_code() -> str:
        """Generate code to check dependencies before processing"""
        return """
// Check dependencies before processing
const entity_id = $json.entity_id;

// Query dependency tracker
const dependencies = await $('Data Table').query({
    table: 'dependency_tracker',
    conditions: {
        source_entity: entity_id,
        satisfied: false
    }
});

if (dependencies.length > 0) {
    // Check if required entities are complete
    for (const dep of dependencies) {
        const required = await $('Data Table').get({
            table: 'execution_tracker',
            conditions: {
                entity_id: dep.required_entity
            }
        });
        
        if (required && required.status === 'complete') {
            // Update dependency as satisfied
            await $('Data Table').update({
                table: 'dependency_tracker',
                key: { dependency_id: dep.dependency_id },
                data: { 
                    satisfied: true, 
                    satisfied_at: new Date().toISOString() 
                }
            });
        }
    }
}

// Re-check unsatisfied dependencies
const unsatisfied = await $('Data Table').query({
    table: 'dependency_tracker',
    conditions: {
        source_entity: entity_id,
        satisfied: false
    }
});

return [{
    json: {
        entity_id: entity_id,
        can_proceed: unsatisfied.length === 0,
        unsatisfied_dependencies: unsatisfied
    }
}];
"""


def main():
    """Example usage and demonstrations"""
    
    print("n8n Table Manager - Schema Generator\n")
    print("=" * 50)
    
    # 1. Show available schemas
    print("\n1. Available Table Schemas:")
    for table_type in TableManager.SCHEMAS.keys():
        schema = TableManager.get_schema(table_type)
        print(f"   - {table_type}: {schema['description']}")
    
    # 2. Generate creation script for a specific table
    print("\n2. Example Table Creation Script:")
    print(TableManager.generate_create_script("execution_tracker", "series_001"))
    
    # 3. Generate operation examples
    print("\n3. Example Operations:")
    
    print("\n   Insert Operation:")
    insert_data = {
        "entity_id": "book_001",
        "entity_type": "book",
        "status": "processing"
    }
    print(TableOperations.insert_code("content_storage", insert_data))
    
    print("\n   Upsert Operation:")
    upsert_data = {
        "state_key": "current_chapter",
        "state_value": {"chapter": 5, "progress": 0.5}
    }
    print(TableOperations.upsert_code("workflow_state", ["execution_id", "state_key"], upsert_data))
    
    # 4. Generate hierarchical schema
    print("\n4. Hierarchical Schema for Series/Books/Chapters:")
    hierarchy = HierarchicalTableManager.generate_hierarchy_schema(["series", "book", "chapter"])
    for table_name, schema in hierarchy.items():
        print(f"   {table_name}:")
        print(f"      Fields: {list(schema['fields'].keys())}")
        print(f"      Indexes: {schema['indexes']}")
    
    # 5. Generate dependency check
    print("\n5. Dependency Check Code:")
    print(HierarchicalTableManager.generate_dependency_check_code())
    
    # 6. Export schemas to file
    all_schemas = {
        "default_tables": TableManager.SCHEMAS,
        "operations": {
            "insert": "Use for new records",
            "upsert": "Use for updates or insert if not exists",
            "query": "Use for retrieving data",
            "delete": "Use for removing records"
        },
        "best_practices": [
            "Always use entity_id prefix for entity-specific tables",
            "Include execution_id in all records for traceability",
            "Add indexes for frequently queried fields",
            "Use TTL for temporary state data",
            "Implement retry logic for critical operations"
        ]
    }
    
    with open("table_schemas.json", "w") as f:
        json.dump(all_schemas, f, indent=2)
    print("\n6. Schemas exported to table_schemas.json")


if __name__ == "__main__":
    main()
