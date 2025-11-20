#!/usr/bin/env python3
"""
n8n Workflow Validator
Checks workflows for common anti-patterns and issues
"""

import json
import sys
from typing import Dict, List, Tuple, Any

class WorkflowValidator:
    """Validate n8n workflows for common issues"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
    
    def validate_workflow(self, workflow: Dict) -> Tuple[bool, List[str], List[str], List[str]]:
        """
        Validate entire workflow
        Returns: (is_valid, errors, warnings, info)
        """
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Check basic structure
        if not workflow.get('nodes'):
            self.errors.append("No nodes found in workflow")
            return False, self.errors, self.warnings, self.info
        
        # Run all validators
        self._check_nested_loops(workflow)
        self._check_static_data_usage(workflow)
        self._check_parallel_convergence(workflow)
        self._check_excel_in_loops(workflow)
        self._check_webhook_callbacks(workflow)
        self._check_google_sheets_operations(workflow)
        self._check_error_handling(workflow)
        self._check_loop_limits(workflow)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings, self.info
    
    def _check_nested_loops(self, workflow: Dict):
        """Check for direct nested Loop Over Items (anti-pattern)"""
        loop_nodes = [n for n in workflow['nodes'] 
                     if n['type'] == 'n8n-nodes-base.loopOverItems']
        
        if len(loop_nodes) > 1:
            # Check if loops are nested (connected directly)
            connections = workflow.get('connections', {})
            for loop in loop_nodes:
                loop_id = loop['id']
                if loop_id in connections:
                    # Check if this loop connects to another loop
                    for conn_list in connections[loop_id].get('main', []):
                        for conn in conn_list:
                            target_node = next((n for n in workflow['nodes'] 
                                              if n['id'] == conn['node']), None)
                            if target_node and target_node['type'] == 'n8n-nodes-base.loopOverItems':
                                self.errors.append(
                                    f"CRITICAL: Nested Loop Over Items detected: "
                                    f"'{loop['name']}' → '{target_node['name']}'. "
                                    "Use sub-workflows instead!"
                                )
    
    def _check_static_data_usage(self, workflow: Dict):
        """Check for $workflow.staticData usage in Code nodes"""
        code_nodes = [n for n in workflow['nodes'] 
                     if n['type'] == 'n8n-nodes-base.code']
        
        for node in code_nodes:
            code = node.get('parameters', {}).get('code', '')
            if '$workflow.staticData' in code:
                self.errors.append(
                    f"ERROR: Code node '{node['name']}' uses $workflow.staticData "
                    "which is not available. Use Data Tables or pass through items."
                )
    
    def _check_parallel_convergence(self, workflow: Dict):
        """Check if parallel branches converge properly"""
        split_nodes = [n for n in workflow['nodes'] 
                      if n['type'] in ['n8n-nodes-base.splitInBatches', 
                                       'n8n-nodes-base.if']]
        merge_nodes = [n for n in workflow['nodes'] 
                      if n['type'] == 'n8n-nodes-base.merge']
        
        if len(split_nodes) > len(merge_nodes):
            self.warnings.append(
                f"WARNING: {len(split_nodes)} split/branch nodes but only "
                f"{len(merge_nodes)} merge nodes. Parallel branches may not converge!"
            )
    
    def _check_excel_in_loops(self, workflow: Dict):
        """Check for Microsoft Excel usage in loops"""
        excel_nodes = [n for n in workflow['nodes'] 
                      if 'excel' in n['type'].lower()]
        
        if excel_nodes:
            # Check if any Excel node is inside a loop
            loop_nodes = [n for n in workflow['nodes'] 
                         if n['type'] == 'n8n-nodes-base.loopOverItems']
            if loop_nodes and excel_nodes:
                self.errors.append(
                    "ERROR: Microsoft Excel detected in workflow with loops. "
                    "Excel fails in loops - use Google Sheets instead!"
                )
    
    def _check_webhook_callbacks(self, workflow: Dict):
        """Check for parallel webhook callbacks"""
        http_nodes = [n for n in workflow['nodes'] 
                     if n['type'] == 'n8n-nodes-base.httpRequest']
        
        connections = workflow.get('connections', {})
        for http_node in http_nodes:
            # Check if HTTP node is on a parallel branch
            http_id = http_node['id']
            is_inline = False
            
            # Check if any node connects to this HTTP node
            for node_id, conns in connections.items():
                for conn_list in conns.get('main', []):
                    for conn in conn_list:
                        if conn['node'] == http_id:
                            # Check if there's a path forward from HTTP node
                            if http_id in connections:
                                is_inline = True
                                break
            
            if not is_inline and 'callback' in http_node.get('name', '').lower():
                self.warnings.append(
                    f"WARNING: HTTP callback '{http_node['name']}' may be on parallel branch. "
                    "Keep callbacks inline for reliability!"
                )
    
    def _check_google_sheets_operations(self, workflow: Dict):
        """Check Google Sheets operations in loops"""
        sheets_nodes = [n for n in workflow['nodes'] 
                       if n['type'] == 'n8n-nodes-base.googleSheets']
        
        for node in sheets_nodes:
            operation = node.get('parameters', {}).get('operation', '')
            if operation == 'update':
                # Check if in a loop context
                self.warnings.append(
                    f"WARNING: Google Sheets '{node['name']}' uses 'update' operation. "
                    "Use 'append' in loops for reliability!"
                )
    
    def _check_error_handling(self, workflow: Dict):
        """Check for error handling patterns"""
        error_triggers = [n for n in workflow['nodes'] 
                         if n['type'] == 'n8n-nodes-base.errorTrigger']
        
        if not error_triggers:
            self.info.append(
                "INFO: No error trigger found. Consider adding error handling."
            )
        
        # Check for try-catch patterns in code nodes
        code_nodes = [n for n in workflow['nodes'] 
                     if n['type'] == 'n8n-nodes-base.code']
        
        for node in code_nodes:
            code = node.get('parameters', {}).get('code', '')
            if 'try' not in code and len(code) > 100:
                self.info.append(
                    f"INFO: Code node '{node['name']}' lacks try-catch. "
                    "Consider adding error handling."
                )
    
    def _check_loop_limits(self, workflow: Dict):
        """Check for missing iteration limits in loops"""
        code_nodes = [n for n in workflow['nodes'] 
                     if n['type'] == 'n8n-nodes-base.code']
        
        for node in code_nodes:
            code = node.get('parameters', {}).get('code', '')
            if 'while' in code and 'max' not in code.lower():
                self.warnings.append(
                    f"WARNING: Code node '{node['name']}' has while loop without "
                    "apparent max iteration limit. Add safety limits!"
                )


def validate_file(filename: str):
    """Validate a workflow file"""
    try:
        with open(filename, 'r') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return False
    
    validator = WorkflowValidator()
    is_valid, errors, warnings, info = validator.validate_workflow(workflow)
    
    print(f"\n=== Validating: {filename} ===\n")
    
    if errors:
        print("❌ ERRORS (Must fix):")
        for error in errors:
            print(f"  - {error}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS (Should fix):")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if info:
        print("ℹ️  INFO (Consider):")
        for i in info:
            print(f"  - {i}")
        print()
    
    if is_valid:
        print("✅ Workflow passes basic validation")
    else:
        print("❌ Workflow has critical errors")
    
    return is_valid


def generate_report(workflow: Dict) -> Dict:
    """Generate detailed validation report"""
    validator = WorkflowValidator()
    is_valid, errors, warnings, info = validator.validate_workflow(workflow)
    
    # Analyze workflow complexity
    node_count = len(workflow.get('nodes', []))
    connection_count = sum(
        len(conns.get('main', [])[0]) if conns.get('main') else 0
        for conns in workflow.get('connections', {}).values()
    )
    
    # Find anti-patterns
    anti_patterns = []
    if any('loopOverItems' in str(workflow)):
        if workflow.get('connections', {}).values():
            # Simplified check for nested loops
            anti_patterns.append("Potential nested loops detected")
    
    report = {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "stats": {
            "node_count": node_count,
            "connection_count": connection_count,
            "complexity": "high" if node_count > 20 else "medium" if node_count > 10 else "low"
        },
        "anti_patterns": anti_patterns,
        "recommendations": []
    }
    
    # Add recommendations
    if node_count > 30:
        report["recommendations"].append("Consider splitting into sub-workflows")
    if not any('errorTrigger' in str(workflow)):
        report["recommendations"].append("Add error handling workflow")
    if any('excel' in str(workflow).lower()):
        report["recommendations"].append("Replace Excel with Google Sheets")
    
    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate-workflow.py <workflow.json>")
        sys.exit(1)
    
    filename = sys.argv[1]
    is_valid = validate_file(filename)
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)
