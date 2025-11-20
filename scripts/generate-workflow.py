#!/usr/bin/env python3
"""
n8n Workflow Generator
Generates production-ready n8n workflows with proper patterns
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class N8NWorkflowGenerator:
    """Generate n8n workflows that actually work in production"""
    
    def __init__(self):
        self.nodes = []
        self.connections = {}
        self.node_counter = 0
        self.workflow = {
            "name": "",
            "nodes": [],
            "connections": {},
            "active": False,
            "settings": {
                "executionOrder": "v1"
            },
            "id": str(uuid.uuid4())
        }
    
    def create_workflow(self, name: str, description: str = "") -> Dict:
        """Initialize a new workflow"""
        self.workflow["name"] = name
        self.workflow["description"] = description
        return self
    
    def add_webhook_trigger(self, path: str, method: str = "POST") -> str:
        """Add webhook trigger node"""
        node_id = self._create_node_id("Webhook")
        node = {
            "id": node_id,
            "name": "Webhook",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1.1,
            "position": [250, 300],
            "parameters": {
                "httpMethod": method,
                "path": path,
                "responseMode": "responseNode",
                "options": {}
            }
        }
        self.nodes.append(node)
        return node_id
    
    def add_data_table_init(self, table_name: str, prev_node: str) -> str:
        """Add data table initialization node"""
        node_id = self._create_node_id("Initialize State")
        node = {
            "id": node_id,
            "name": "Initialize State",
            "type": "n8n-nodes-base.dataTable",
            "typeVersion": 1,
            "position": [450, 300],
            "parameters": {
                "operation": "insert",
                "table": table_name,
                "data": {
                    "execution_id": "={{ $execution.id }}",
                    "status": "processing",
                    "iteration": 0,
                    "created_at": "={{ new Date().toISOString() }}"
                }
            }
        }
        self.nodes.append(node)
        self._add_connection(prev_node, node_id)
        return node_id
    
    def add_loop_over_items(self, batch_size: int = 1, prev_node: str = None) -> str:
        """Add Loop Over Items node with proper configuration"""
        node_id = self._create_node_id("Loop Over Items")
        node = {
            "id": node_id,
            "name": "Loop Over Items",
            "type": "n8n-nodes-base.loopOverItems",
            "typeVersion": 1,
            "position": [650, 300],
            "parameters": {
                "batchSize": batch_size,
                "options": {
                    "pauseBetweenIterations": 100  # Rate limiting
                }
            }
        }
        self.nodes.append(node)
        if prev_node:
            self._add_connection(prev_node, node_id)
        return node_id
    
    def add_sub_workflow(self, workflow_id: str, wait: bool = False, prev_node: str = None) -> str:
        """Add Execute Workflow node for sub-workflow pattern"""
        node_id = self._create_node_id("Execute Sub-workflow")
        node = {
            "id": node_id,
            "name": "Execute Sub-workflow",
            "type": "n8n-nodes-base.executeWorkflow",
            "typeVersion": 1,
            "position": [850, 300],
            "parameters": {
                "source": "database",
                "workflowId": workflow_id,
                "waitForSubWorkflow": wait,
                "options": {
                    "shareParentExecutionId": False  # CRITICAL for isolation
                }
            }
        }
        self.nodes.append(node)
        if prev_node:
            self._add_connection(prev_node, node_id)
        return node_id
    
    def add_code_node(self, code: str, name: str = "Process Data", prev_node: str = None) -> str:
        """Add Code node with proper state handling"""
        node_id = self._create_node_id(name)
        node = {
            "id": node_id,
            "name": name,
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1050, 300],
            "parameters": {
                "mode": "runOnceForEachItem",
                "code": code
            }
        }
        self.nodes.append(node)
        if prev_node:
            self._add_connection(prev_node, node_id)
        return node_id
    
    def add_if_node(self, condition: str, prev_node: str = None) -> tuple[str, str, str]:
        """Add IF node for conditional branching. Returns (node_id, true_branch, false_branch)"""
        node_id = self._create_node_id("Check Condition")
        node = {
            "id": node_id,
            "name": "Check Condition",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [1250, 300],
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "strict"
                    },
                    "conditions": [
                        {
                            "leftValue": condition,
                            "rightValue": "",
                            "operator": {
                                "type": "boolean",
                                "operation": "true"
                            }
                        }
                    ],
                    "combinator": "and"
                }
            }
        }
        self.nodes.append(node)
        if prev_node:
            self._add_connection(prev_node, node_id)
        
        # Return node_id and branch identifiers
        return node_id, f"{node_id}_true", f"{node_id}_false"
    
    def add_merge_node(self, wait_all: bool = True, prev_nodes: List[str] = None) -> str:
        """Add Merge node for parallel convergence"""
        node_id = self._create_node_id("Merge Branches")
        node = {
            "id": node_id,
            "name": "Merge Branches",
            "type": "n8n-nodes-base.merge",
            "typeVersion": 3,
            "position": [1450, 300],
            "parameters": {
                "mode": "waitForAll" if wait_all else "passThrough",
                "outputKey": "combined",
                "options": {
                    "keepOnlyProperties": False
                }
            }
        }
        self.nodes.append(node)
        if prev_nodes:
            for prev_node in prev_nodes:
                self._add_connection(prev_node, node_id)
        return node_id
    
    def add_google_sheets(self, operation: str = "append", prev_node: str = None) -> str:
        """Add Google Sheets node (using append for loops)"""
        node_id = self._create_node_id("Google Sheets")
        node = {
            "id": node_id,
            "name": "Google Sheets",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4,
            "position": [1650, 300],
            "parameters": {
                "operation": operation,  # Use 'append' in loops, not 'update'
                "documentId": "{{ $json.spreadsheet_id }}",
                "sheetName": "Sheet1",
                "options": {}
            },
            "credentials": {
                "googleSheetsOAuth2Api": {
                    "id": "google_sheets_cred_id",
                    "name": "Google Sheets Account"
                }
            }
        }
        self.nodes.append(node)
        if prev_node:
            self._add_connection(prev_node, node_id)
        return node_id
    
    def add_http_request(self, url: str, method: str = "POST", inline: bool = True, prev_node: str = None) -> str:
        """Add HTTP Request node (inline for callbacks)"""
        node_id = self._create_node_id("HTTP Request")
        node = {
            "id": node_id,
            "name": "HTTP Request",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [1850, 300],
            "parameters": {
                "method": method,
                "url": url,
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "status",
                            "value": "={{ $json.status }}"
                        },
                        {
                            "name": "execution_id",
                            "value": "={{ $execution.id }}"
                        }
                    ]
                },
                "options": {
                    "timeout": 10000,
                    "batching": {
                        "batch": {
                            "batchSize": 1  # Process one at a time for callbacks
                        }
                    }
                }
            }
        }
        self.nodes.append(node)
        if prev_node and inline:
            self._add_connection(prev_node, node_id)
        return node_id
    
    def create_loop_pattern(self, max_iterations: int = 10) -> Dict:
        """Create a working loop pattern with conditional branching"""
        code = f"""
// Initialize or increment counter
const iteration = ($json._iteration || 0) + 1;
const maxIterations = {max_iterations};

return [{{
  json: {{
    ...$json,
    _iteration: iteration,
    _continue: iteration < maxIterations,
    _status: iteration >= maxIterations ? 'complete' : 'processing'
  }}
}}];
"""
        return {
            "pattern": "conditional_loop",
            "code": code,
            "if_condition": "{{ $json._continue === true }}"
        }
    
    def create_nested_loop_pattern(self) -> Dict:
        """Create pattern for nested loops using sub-workflows"""
        return {
            "pattern": "nested_loop",
            "main_workflow": {
                "description": "Main workflow with outer loop",
                "nodes": ["Loop Over Items", "Execute Sub-workflow", "Merge Results"]
            },
            "sub_workflow": {
                "description": "Sub-workflow with inner loop (clean context)",
                "nodes": ["Webhook Trigger", "Loop Over Items", "Process", "Return Result"]
            },
            "critical_settings": {
                "waitForSubWorkflow": False,
                "shareParentExecutionId": False
            }
        }
    
    def create_table_schema(self, entity_type: str = "generic") -> Dict:
        """Create Data Table schemas for different entity types"""
        schemas = {
            "execution_tracker": {
                "execution_id": "string",
                "entity_type": "string",
                "entity_id": "string",
                "status": "string",
                "parent_id": "string",
                "iteration": "number",
                "metadata": "json",
                "created_at": "datetime",
                "updated_at": "datetime"
            },
            "content_storage": {
                "content_id": "string",
                "entity_id": "string",
                "content_type": "string",
                "content": "json",
                "version": "number",
                "hash": "string",
                "created_at": "datetime"
            },
            "workflow_state": {
                "state_id": "string",
                "execution_id": "string",
                "state_key": "string",
                "state_value": "json",
                "expires_at": "datetime"
            }
        }
        return schemas
    
    def build(self) -> Dict:
        """Build the final workflow JSON"""
        self.workflow["nodes"] = self.nodes
        self.workflow["connections"] = self.connections
        return self.workflow
    
    def export(self, filename: str = None) -> str:
        """Export workflow to JSON file"""
        workflow = self.build()
        if filename:
            with open(filename, 'w') as f:
                json.dump(workflow, f, indent=2)
            return f"Workflow exported to {filename}"
        return json.dumps(workflow, indent=2)
    
    # Helper methods
    def _create_node_id(self, name: str) -> str:
        """Create unique node ID"""
        self.node_counter += 1
        return f"node_{self.node_counter}_{name.replace(' ', '_')}"
    
    def _add_connection(self, from_node: str, to_node: str, output_index: int = 0):
        """Add connection between nodes"""
        if from_node not in self.connections:
            self.connections[from_node] = {"main": [[]]}
        
        if output_index >= len(self.connections[from_node]["main"]):
            self.connections[from_node]["main"].extend(
                [[] for _ in range(output_index - len(self.connections[from_node]["main"]) + 1)]
            )
        
        self.connections[from_node]["main"][output_index].append({
            "node": to_node,
            "type": "main",
            "index": 0
        })


def generate_example_workflow():
    """Generate an example workflow with proper patterns"""
    
    # Create generator
    gen = N8NWorkflowGenerator()
    gen.create_workflow(
        "Production Loop Example",
        "Demonstrates proper loop patterns with state management"
    )
    
    # Build workflow
    webhook = gen.add_webhook_trigger("/process", "POST")
    init_state = gen.add_data_table_init("workflow_state", webhook)
    
    # Add loop pattern
    loop_pattern = gen.create_loop_pattern(max_iterations=10)
    process = gen.add_code_node(loop_pattern["code"], "Process with Counter", init_state)
    
    # Add conditional branching
    if_node, true_branch, false_branch = gen.add_if_node(loop_pattern["if_condition"], process)
    
    # Loop back connection (would be done manually in n8n UI)
    # For false branch, connect back to process node
    
    # Add completion node for true branch
    complete = gen.add_code_node(
        "return [{ json: { status: 'complete', result: $json } }];",
        "Complete",
        true_branch
    )
    
    return gen.build()


def generate_hierarchical_workflow():
    """Generate a multi-tier workflow structure"""
    
    gen = N8NWorkflowGenerator()
    gen.create_workflow(
        "Hierarchical Series Generator",
        "Multi-tier workflow for series->books->chapters"
    )
    
    # Main orchestrator
    webhook = gen.add_webhook_trigger("/generate-series", "POST")
    
    # Initialize multiple tables
    init_tables = gen.add_code_node("""
// Initialize table structures for hierarchical data
const tables = [
  'execution_tracker',
  'content_storage',
  'dependency_tracker'
];

const entity_id = `series_${Date.now()}`;

return [{
  json: {
    entity_id,
    tables,
    hierarchy: {
      series: 1,
      books: $json.num_books || 3,
      chapters_per_book: $json.chapters_per_book || 10
    }
  }
}];
""", "Initialize Hierarchy", webhook)
    
    # Add sub-workflow for parallel book generation
    books = gen.add_sub_workflow("generate_book_workflow", wait=False, prev_node=init_tables)
    
    # Add merge to wait for all books
    merge = gen.add_merge_node(wait_all=True, prev_nodes=[books])
    
    # Add final aggregation
    aggregate = gen.add_code_node("""
// Aggregate all results
const results = $items().map(item => item.json);
return [{
  json: {
    series_id: $json.entity_id,
    books_generated: results.length,
    status: 'complete',
    data: results
  }
}];
""", "Aggregate Results", merge)
    
    return gen.build()


if __name__ == "__main__":
    # Generate example workflows
    
    # Example 1: Loop pattern
    loop_workflow = generate_example_workflow()
    with open("loop_example.json", "w") as f:
        json.dump(loop_workflow, f, indent=2)
    print("Generated: loop_example.json")
    
    # Example 2: Hierarchical pattern
    hierarchical = generate_hierarchical_workflow()
    with open("hierarchical_example.json", "w") as f:
        json.dump(hierarchical, f, indent=2)
    print("Generated: hierarchical_example.json")
    
    # Show patterns
    gen = N8NWorkflowGenerator()
    print("\nNested Loop Pattern:")
    print(json.dumps(gen.create_nested_loop_pattern(), indent=2))
    
    print("\nTable Schemas:")
    print(json.dumps(gen.create_table_schema(), indent=2))
