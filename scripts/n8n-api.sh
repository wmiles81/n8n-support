#!/bin/bash
# n8n API Helper Functions
# Reads credentials from .mcp.json and provides convenient API wrappers

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load credentials from .mcp.json
load_credentials() {
    local mcp_file="${1:-.mcp.json}"

    if [[ ! -f "$mcp_file" ]]; then
        echo -e "${RED}Error: .mcp.json not found${NC}" >&2
        echo "Create it from .mcp.json.example and add your credentials" >&2
        return 1
    fi

    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq is required but not installed${NC}" >&2
        echo "Install with: sudo apt-get install jq (or brew install jq on Mac)" >&2
        return 1
    fi

    export N8N_API_URL=$(jq -r '.mcpServers.n8n.env.N8N_API_URL' "$mcp_file")
    export N8N_API_KEY=$(jq -r '.mcpServers.n8n.env.N8N_API_KEY' "$mcp_file")

    if [[ "$N8N_API_URL" == "null" ]] || [[ "$N8N_API_KEY" == "null" ]]; then
        echo -e "${RED}Error: Invalid credentials in .mcp.json${NC}" >&2
        return 1
    fi

    echo -e "${GREEN}✓ Credentials loaded from $mcp_file${NC}" >&2
    echo -e "${BLUE}  API URL: $N8N_API_URL${NC}" >&2
}

# List all workflows
n8n_list_workflows() {
    echo -e "${BLUE}Fetching workflows...${NC}" >&2
    curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
        "$N8N_API_URL/workflows" | jq -r '
        .data[] |
        "[\(if .active then "✓ ACTIVE" else "○ INACTIVE" end)] \(.name)\n  ID: \(.id)\n  Updated: \(.updatedAt)\n"'
}

# Get workflow by ID
n8n_get_workflow() {
    local workflow_id=$1

    if [[ -z "$workflow_id" ]]; then
        echo -e "${RED}Usage: n8n_get_workflow <workflow_id>${NC}" >&2
        return 1
    fi

    echo -e "${BLUE}Fetching workflow $workflow_id...${NC}" >&2
    curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
        "$N8N_API_URL/workflows/$workflow_id" | jq
}

# Execute workflow
n8n_execute_workflow() {
    local workflow_id=$1
    local data=${2:-'{}'}

    if [[ -z "$workflow_id" ]]; then
        echo -e "${RED}Usage: n8n_execute_workflow <workflow_id> [json_data]${NC}" >&2
        return 1
    fi

    echo -e "${BLUE}Executing workflow $workflow_id...${NC}" >&2
    curl -s -X POST \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$data" \
        "$N8N_API_URL/workflows/$workflow_id/execute" | jq
}

# Get execution by ID
n8n_get_execution() {
    local execution_id=$1

    if [[ -z "$execution_id" ]]; then
        echo -e "${RED}Usage: n8n_get_execution <execution_id>${NC}" >&2
        return 1
    fi

    echo -e "${BLUE}Fetching execution $execution_id...${NC}" >&2
    curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
        "$N8N_API_URL/executions/$execution_id" | jq
}

# List executions for a workflow
n8n_list_executions() {
    local workflow_id=$1
    local limit=${2:-10}

    echo -e "${BLUE}Fetching last $limit executions...${NC}" >&2

    if [[ -n "$workflow_id" ]]; then
        curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
            "$N8N_API_URL/executions?workflowId=$workflow_id&limit=$limit" | jq
    else
        curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
            "$N8N_API_URL/executions?limit=$limit" | jq
    fi
}

# Stop execution
n8n_stop_execution() {
    local execution_id=$1

    if [[ -z "$execution_id" ]]; then
        echo -e "${RED}Usage: n8n_stop_execution <execution_id>${NC}" >&2
        return 1
    fi

    echo -e "${YELLOW}Stopping execution $execution_id...${NC}" >&2
    curl -s -X POST \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        "$N8N_API_URL/executions/$execution_id/stop" | jq
}

# Create workflow
n8n_create_workflow() {
    local workflow_file=$1

    if [[ -z "$workflow_file" ]] || [[ ! -f "$workflow_file" ]]; then
        echo -e "${RED}Usage: n8n_create_workflow <workflow.json>${NC}" >&2
        return 1
    fi

    echo -e "${BLUE}Creating workflow from $workflow_file...${NC}" >&2
    curl -s -X POST \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d @"$workflow_file" \
        "$N8N_API_URL/workflows" | jq
}

# Update workflow
n8n_update_workflow() {
    local workflow_id=$1
    local workflow_file=$2

    if [[ -z "$workflow_id" ]] || [[ -z "$workflow_file" ]] || [[ ! -f "$workflow_file" ]]; then
        echo -e "${RED}Usage: n8n_update_workflow <workflow_id> <workflow.json>${NC}" >&2
        return 1
    fi

    echo -e "${BLUE}Updating workflow $workflow_id from $workflow_file...${NC}" >&2
    curl -s -X PUT \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d @"$workflow_file" \
        "$N8N_API_URL/workflows/$workflow_id" | jq
}

# Activate workflow
n8n_activate_workflow() {
    local workflow_id=$1

    if [[ -z "$workflow_id" ]]; then
        echo -e "${RED}Usage: n8n_activate_workflow <workflow_id>${NC}" >&2
        return 1
    fi

    echo -e "${GREEN}Activating workflow $workflow_id...${NC}" >&2

    # Get current workflow
    local workflow=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
        "$N8N_API_URL/workflows/$workflow_id")

    # Update with active=true
    echo "$workflow" | jq '.active = true' | \
        curl -s -X PUT \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d @- \
        "$N8N_API_URL/workflows/$workflow_id" | jq
}

# Deactivate workflow
n8n_deactivate_workflow() {
    local workflow_id=$1

    if [[ -z "$workflow_id" ]]; then
        echo -e "${RED}Usage: n8n_deactivate_workflow <workflow_id>${NC}" >&2
        return 1
    fi

    echo -e "${YELLOW}Deactivating workflow $workflow_id...${NC}" >&2

    # Get current workflow
    local workflow=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
        "$N8N_API_URL/workflows/$workflow_id")

    # Update with active=false
    echo "$workflow" | jq '.active = false' | \
        curl -s -X PUT \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d @- \
        "$N8N_API_URL/workflows/$workflow_id" | jq
}

# Delete workflow
n8n_delete_workflow() {
    local workflow_id=$1

    if [[ -z "$workflow_id" ]]; then
        echo -e "${RED}Usage: n8n_delete_workflow <workflow_id>${NC}" >&2
        return 1
    fi

    echo -e "${RED}Deleting workflow $workflow_id...${NC}" >&2
    read -p "Are you sure? (yes/no): " confirm

    if [[ "$confirm" != "yes" ]]; then
        echo -e "${YELLOW}Cancelled.${NC}" >&2
        return 0
    fi

    curl -s -X DELETE \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        "$N8N_API_URL/workflows/$workflow_id" | jq
}

# Monitor execution with polling
n8n_monitor_execution() {
    local execution_id=$1
    local poll_interval=${2:-5}

    if [[ -z "$execution_id" ]]; then
        echo -e "${RED}Usage: n8n_monitor_execution <execution_id> [poll_interval_seconds]${NC}" >&2
        return 1
    fi

    echo -e "${BLUE}Monitoring execution $execution_id (polling every ${poll_interval}s)...${NC}" >&2
    echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}" >&2
    echo ""

    while true; do
        local response=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
            "$N8N_API_URL/executions/$execution_id")

        local status=$(echo "$response" | jq -r '.status // "unknown"')
        local started=$(echo "$response" | jq -r '.startedAt // "unknown"')

        echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} Status: $status | Started: $started"

        if [[ "$status" == "success" ]]; then
            echo -e "${GREEN}✓ Execution completed successfully!${NC}"
            echo "$response" | jq
            break
        elif [[ "$status" == "error" ]]; then
            echo -e "${RED}✗ Execution failed!${NC}"
            echo "$response" | jq
            break
        elif [[ "$status" == "crashed" ]]; then
            echo -e "${RED}✗ Execution crashed!${NC}"
            echo "$response" | jq
            break
        fi

        sleep "$poll_interval"
    done
}

# Show help
n8n_help() {
    cat << 'EOF'
n8n API Helper Functions

Setup:
  source scripts/n8n-api.sh        # Load this file
  load_credentials [.mcp.json]     # Load API credentials

Workflow Operations:
  n8n_list_workflows                       # List all workflows
  n8n_get_workflow <id>                    # Get workflow details
  n8n_create_workflow <file.json>          # Create workflow from JSON
  n8n_update_workflow <id> <file.json>     # Update workflow
  n8n_activate_workflow <id>               # Activate workflow
  n8n_deactivate_workflow <id>             # Deactivate workflow
  n8n_delete_workflow <id>                 # Delete workflow (with confirmation)

Execution Operations:
  n8n_execute_workflow <id> [data]         # Execute workflow
  n8n_get_execution <id>                   # Get execution details
  n8n_list_executions [workflow_id] [limit] # List executions
  n8n_stop_execution <id>                  # Stop running execution
  n8n_monitor_execution <id> [interval]    # Monitor execution with polling

Examples:
  # Setup
  source scripts/n8n-api.sh
  load_credentials

  # List and execute
  n8n_list_workflows
  n8n_execute_workflow "abc123" '{"num_books": 3}'

  # Monitor execution
  n8n_monitor_execution "exec_456" 5

  # Deploy workflow
  python scripts/generate-workflow.py > workflow.json
  n8n_create_workflow workflow.json

EOF
}

# Auto-load credentials if .mcp.json exists in current directory
if [[ -f ".mcp.json" ]] && [[ -z "$N8N_API_KEY" ]]; then
    load_credentials .mcp.json
fi

# Show help if sourced directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    n8n_help
fi
