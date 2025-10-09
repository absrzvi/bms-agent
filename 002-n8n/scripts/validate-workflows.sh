#!/bin/bash
# Workflow JSON validation script for T031b
# Validates all n8n workflow files for structural integrity

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOWS_DIR="${SCRIPT_DIR}/../workflows"
REPORT_FILE="${SCRIPT_DIR}/../validation-report.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "n8n Workflow Validation Script"
echo "================================================"
echo ""

# Counter variables
TOTAL_FILES=0
VALID_FILES=0
INVALID_FILES=0
WARNING_FILES=0

# Validation results array
declare -a VALIDATION_RESULTS

# Function to validate JSON syntax
validate_json_syntax() {
    local file="$1"
    if ! jq empty "$file" 2>/dev/null; then
        return 1
    fi
    return 0
}

# Function to validate workflow structure
validate_workflow_structure() {
    local file="$1"
    local filename=$(basename "$file")

    # Check required top-level fields
    local has_name=$(jq -e '.name' "$file" >/dev/null 2>&1 && echo "true" || echo "false")
    local has_nodes=$(jq -e '.nodes' "$file" >/dev/null 2>&1 && echo "true" || echo "false")
    local has_connections=$(jq -e '.connections' "$file" >/dev/null 2>&1 && echo "true" || echo "false")

    if [[ "$has_name" != "true" ]]; then
        echo "  ${RED}✗${NC} Missing required field: name"
        return 1
    fi

    if [[ "$has_nodes" != "true" ]]; then
        echo "  ${RED}✗${NC} Missing required field: nodes"
        return 1
    fi

    if [[ "$has_connections" != "true" ]]; then
        echo "  ${RED}✗${NC} Missing required field: connections"
        return 1
    fi

    # Check nodes array is not empty
    local node_count=$(jq '.nodes | length' "$file")
    if [[ "$node_count" -eq 0 ]]; then
        echo "  ${YELLOW}⚠${NC} Warning: nodes array is empty"
        return 2
    fi

    # Validate each node has required fields
    local invalid_nodes=$(jq -r '.nodes[] | select(.id == null or .name == null or .type == null or .position == null) | .name // "unknown"' "$file")
    if [[ -n "$invalid_nodes" ]]; then
        echo "  ${RED}✗${NC} Invalid nodes found (missing id/name/type/position):"
        echo "$invalid_nodes" | while read -r node; do
            echo "    - $node"
        done
        return 1
    fi

    return 0
}

# Function to check for common issues
check_common_issues() {
    local file="$1"
    local issues_found=false

    # Check for duplicate node IDs
    local duplicate_ids=$(jq -r '.nodes | group_by(.id) | map(select(length > 1)) | .[].id // empty' "$file")
    if [[ -n "$duplicate_ids" ]]; then
        echo "  ${RED}✗${NC} Duplicate node IDs found:"
        echo "$duplicate_ids" | while read -r id; do
            echo "    - $id"
        done
        issues_found=true
    fi

    # Check for missing typeVersion
    local missing_typeversion=$(jq -r '.nodes[] | select(.typeVersion == null) | .name // "unknown"' "$file")
    if [[ -n "$missing_typeversion" ]]; then
        echo "  ${YELLOW}⚠${NC} Nodes missing typeVersion:"
        echo "$missing_typeversion" | while read -r node; do
            echo "    - $node"
        done
        issues_found=true
    fi

    # Check for empty parameters
    local empty_params=$(jq -r '.nodes[] | select(.parameters == null or (.parameters | length == 0)) | .name // "unknown"' "$file")
    if [[ -n "$empty_params" ]]; then
        echo "  ${YELLOW}⚠${NC} Nodes with empty/null parameters:"
        echo "$empty_params" | while read -r node; do
            echo "    - $node"
        done
        issues_found=true
    fi

    if [[ "$issues_found" == "true" ]]; then
        return 2  # Return 2 for warnings
    fi

    return 0
}

# Main validation loop
echo "Scanning workflows directory: $WORKFLOWS_DIR"
echo ""

for workflow_file in "$WORKFLOWS_DIR"/*.json; do
    if [[ ! -f "$workflow_file" ]]; then
        continue
    fi

    TOTAL_FILES=$((TOTAL_FILES + 1))
    filename=$(basename "$workflow_file")

    echo "[$TOTAL_FILES] Validating: $filename"

    # Step 1: JSON syntax validation
    if ! validate_json_syntax "$workflow_file"; then
        echo "  ${RED}✗${NC} Invalid JSON syntax"
        INVALID_FILES=$((INVALID_FILES + 1))
        VALIDATION_RESULTS+=("$filename:INVALID:JSON syntax error")
        echo ""
        continue
    fi

    # Step 2: Workflow structure validation
    validate_workflow_structure "$workflow_file"
    structure_result=$?

    if [[ $structure_result -eq 1 ]]; then
        INVALID_FILES=$((INVALID_FILES + 1))
        VALIDATION_RESULTS+=("$filename:INVALID:Structure validation failed")
        echo ""
        continue
    elif [[ $structure_result -eq 2 ]]; then
        WARNING_FILES=$((WARNING_FILES + 1))
    fi

    # Step 3: Common issues check
    check_common_issues "$workflow_file"
    issues_result=$?

    if [[ $issues_result -eq 2 ]]; then
        WARNING_FILES=$((WARNING_FILES + 1))
        VALIDATION_RESULTS+=("$filename:WARNING:Common issues detected")
    fi

    # If no errors, mark as valid
    if [[ $structure_result -eq 0 ]] && [[ $issues_result -eq 0 ]]; then
        echo "  ${GREEN}✓${NC} Valid workflow"
        VALID_FILES=$((VALID_FILES + 1))
        VALIDATION_RESULTS+=("$filename:VALID:All checks passed")
    elif [[ $structure_result -eq 0 ]] || [[ $structure_result -eq 2 ]]; then
        # Structure is OK but has warnings
        VALID_FILES=$((VALID_FILES + 1))
        if [[ $issues_result -ne 2 ]]; then
            VALIDATION_RESULTS+=("$filename:VALID:Minor warnings")
        fi
    fi

    echo ""
done

# Generate summary report
echo "================================================"
echo "Validation Summary"
echo "================================================"
echo ""
echo "Total files validated: $TOTAL_FILES"
echo "${GREEN}Valid:${NC} $VALID_FILES"
echo "${YELLOW}Warnings:${NC} $WARNING_FILES"
echo "${RED}Invalid:${NC} $INVALID_FILES"
echo ""

# Generate JSON report
cat > "$REPORT_FILE" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "total_files": $TOTAL_FILES,
  "valid_files": $VALID_FILES,
  "warning_files": $WARNING_FILES,
  "invalid_files": $INVALID_FILES,
  "results": [
EOF

# Add validation results to JSON
for i in "${!VALIDATION_RESULTS[@]}"; do
    result="${VALIDATION_RESULTS[$i]}"
    IFS=':' read -r filename status message <<< "$result"

    if [[ $i -gt 0 ]]; then
        echo "," >> "$REPORT_FILE"
    fi

    cat >> "$REPORT_FILE" <<EOF
    {
      "file": "$filename",
      "status": "$status",
      "message": "$message"
    }
EOF
done

cat >> "$REPORT_FILE" <<EOF

  ]
}
EOF

echo "Validation report saved to: $REPORT_FILE"
echo ""

# Exit with appropriate code
if [[ $INVALID_FILES -gt 0 ]]; then
    echo "${RED}Validation failed: $INVALID_FILES invalid file(s) found${NC}"
    exit 1
elif [[ $WARNING_FILES -gt 0 ]]; then
    echo "${YELLOW}Validation passed with warnings: $WARNING_FILES file(s) have warnings${NC}"
    exit 0
else
    echo "${GREEN}All workflows validated successfully!${NC}"
    exit 0
fi
