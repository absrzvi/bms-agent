#!/usr/bin/env python3
"""
Workflow JSON validation script for T031b
Validates all n8n workflow files for structural integrity
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color

def validate_json_syntax(file_path: Path) -> Tuple[bool, str]:
    """Validate JSON syntax"""
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        return True, "Valid JSON"
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error: {str(e)}"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def validate_workflow_structure(workflow_data: dict, filename: str) -> Tuple[str, List[str]]:
    """
    Validate workflow structure
    Returns: (status, messages)
    status: VALID, WARNING, or INVALID
    """
    messages = []
    has_errors = False
    has_warnings = False

    # Check required top-level fields
    if 'name' not in workflow_data:
        messages.append("Missing required field: name")
        has_errors = True

    if 'nodes' not in workflow_data:
        messages.append("Missing required field: nodes")
        has_errors = True
    elif not isinstance(workflow_data['nodes'], list):
        messages.append("nodes field must be an array")
        has_errors = True
    elif len(workflow_data['nodes']) == 0:
        messages.append("Warning: nodes array is empty")
        has_warnings = True

    if 'connections' not in workflow_data:
        messages.append("Missing required field: connections")
        has_errors = True
    elif not isinstance(workflow_data['connections'], dict):
        messages.append("connections field must be an object")
        has_errors = True

    # Validate each node
    if 'nodes' in workflow_data and isinstance(workflow_data['nodes'], list):
        for idx, node in enumerate(workflow_data['nodes']):
            node_name = node.get('name', f'node_{idx}')

            if 'id' not in node:
                messages.append(f"Node '{node_name}' missing required field: id")
                has_errors = True

            if 'name' not in node:
                messages.append(f"Node at index {idx} missing required field: name")
                has_errors = True

            if 'type' not in node:
                messages.append(f"Node '{node_name}' missing required field: type")
                has_errors = True

            if 'position' not in node:
                messages.append(f"Node '{node_name}' missing required field: position")
                has_errors = True

            if 'typeVersion' not in node:
                messages.append(f"Node '{node_name}' missing typeVersion")
                has_warnings = True

            if 'parameters' not in node or node['parameters'] is None:
                messages.append(f"Node '{node_name}' has empty/null parameters")
                has_warnings = True

    if has_errors:
        return "INVALID", messages
    elif has_warnings:
        return "WARNING", messages
    else:
        return "VALID", ["All checks passed"]

def check_common_issues(workflow_data: dict) -> Tuple[bool, List[str]]:
    """
    Check for common workflow issues
    Returns: (has_issues, messages)
    """
    messages = []

    if 'nodes' not in workflow_data or not isinstance(workflow_data['nodes'], list):
        return False, messages

    # Check for duplicate node IDs
    node_ids = [node.get('id') for node in workflow_data['nodes'] if 'id' in node]
    duplicate_ids = [nid for nid in set(node_ids) if node_ids.count(nid) > 1]

    if duplicate_ids:
        messages.append(f"Duplicate node IDs found: {', '.join(duplicate_ids)}")

    # Check for orphaned nodes (no connections)
    if 'connections' in workflow_data:
        connected_nodes = set()
        for source_id, connections in workflow_data['connections'].items():
            connected_nodes.add(source_id)
            for output_type, output_connections in connections.items():
                for connection_list in output_connections:
                    for connection in connection_list:
                        if 'node' in connection:
                            connected_nodes.add(connection['node'])

        all_node_names = {node.get('name') for node in workflow_data['nodes'] if 'name' in node}
        orphaned = all_node_names - connected_nodes

        # Filter out trigger nodes and output nodes (they may not have connections)
        trigger_types = {'webhook', 'trigger', 'manual'}
        orphaned_non_triggers = []

        for node in workflow_data['nodes']:
            node_name = node.get('name')
            node_type = node.get('type', '').lower()

            if node_name in orphaned and not any(t in node_type for t in trigger_types):
                orphaned_non_triggers.append(node_name)

        if orphaned_non_triggers:
            messages.append(f"Potentially orphaned nodes: {', '.join(orphaned_non_triggers)}")

    return len(messages) > 0, messages

def main():
    """Main validation function"""
    workflows_dir = Path(__file__).parent.parent / 'workflows'
    report_file = Path(__file__).parent.parent / 'validation-report.json'

    print("=" * 48)
    print("n8n Workflow Validation Script")
    print("=" * 48)
    print()
    print(f"Scanning workflows directory: {workflows_dir}")
    print()

    # Counters
    total_files = 0
    valid_files = 0
    warning_files = 0
    invalid_files = 0

    # Results
    validation_results = []

    # Find all JSON files
    workflow_files = sorted(workflows_dir.glob('*.json'))

    for workflow_file in workflow_files:
        total_files += 1
        filename = workflow_file.name

        print(f"[{total_files}] Validating: {filename}")

        # Step 1: JSON syntax validation
        is_valid_json, json_message = validate_json_syntax(workflow_file)

        if not is_valid_json:
            print(f"  {Colors.RED}✗{Colors.NC} {json_message}")
            invalid_files += 1
            validation_results.append({
                "file": filename,
                "status": "INVALID",
                "message": json_message,
                "issues": []
            })
            print()
            continue

        # Load workflow data
        with open(workflow_file, 'r') as f:
            workflow_data = json.load(f)

        # Step 2: Structure validation
        status, structure_messages = validate_workflow_structure(workflow_data, filename)

        # Step 3: Common issues check
        has_issues, issue_messages = check_common_issues(workflow_data)

        # Combine messages
        all_messages = structure_messages + issue_messages

        # Print results
        for msg in all_messages:
            if status == "INVALID":
                print(f"  {Colors.RED}✗{Colors.NC} {msg}")
            elif "Warning" in msg or "warning" in msg.lower():
                print(f"  {Colors.YELLOW}⚠{Colors.NC} {msg}")
            else:
                print(f"  {Colors.GREEN}✓{Colors.NC} {msg}")

        # Update counters
        if status == "INVALID":
            invalid_files += 1
        elif status == "WARNING" or has_issues:
            warning_files += 1
            valid_files += 1
            status = "WARNING"
        else:
            valid_files += 1

        # Store result
        validation_results.append({
            "file": filename,
            "status": status,
            "message": structure_messages[0] if structure_messages else "Validated",
            "issues": all_messages
        })

        print()

    # Print summary
    print("=" * 48)
    print("Validation Summary")
    print("=" * 48)
    print()
    print(f"Total files validated: {total_files}")
    print(f"{Colors.GREEN}Valid:{Colors.NC} {valid_files}")
    print(f"{Colors.YELLOW}Warnings:{Colors.NC} {warning_files}")
    print(f"{Colors.RED}Invalid:{Colors.NC} {invalid_files}")
    print()

    # Generate JSON report
    report_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_files": total_files,
        "valid_files": valid_files,
        "warning_files": warning_files,
        "invalid_files": invalid_files,
        "results": validation_results
    }

    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"Validation report saved to: {report_file}")
    print()

    # Exit with appropriate code
    if invalid_files > 0:
        print(f"{Colors.RED}Validation failed: {invalid_files} invalid file(s) found{Colors.NC}")
        sys.exit(1)
    elif warning_files > 0:
        print(f"{Colors.YELLOW}Validation passed with warnings: {warning_files} file(s) have warnings{Colors.NC}")
        sys.exit(0)
    else:
        print(f"{Colors.GREEN}All workflows validated successfully!{Colors.NC}")
        sys.exit(0)

if __name__ == '__main__':
    main()
