#!/usr/bin/env python3
import sqlite3
import json
import os
import uuid
from datetime import datetime

DB_PATH = '/workspace/n8n/.n8n/database.sqlite'
WORKFLOWS_DIR = '/workspace/002-n8n/workflows'

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all workflow JSON files
workflow_files = [f for f in os.listdir(WORKFLOWS_DIR) if f.endswith('.json')]
print(f"Found {len(workflow_files)} workflow files to import")

imported = 0
failed = 0

for file in workflow_files:
    try:
        file_path = os.path.join(WORKFLOWS_DIR, file)
        with open(file_path, 'r') as f:
            workflow_data = json.load(f)

        # Prepare workflow data
        workflow_id = str(uuid.uuid4())
        name = workflow_data.get('name', file.replace('.json', ''))
        active = 1 if workflow_data.get('active', True) else 0
        nodes = json.dumps(workflow_data.get('nodes', []))
        connections = json.dumps(workflow_data.get('connections', {}))
        settings = json.dumps(workflow_data.get('settings', {}))
        static_data = json.dumps(workflow_data.get('staticData')) if workflow_data.get('staticData') else None
        version_id = workflow_data.get('versionId', str(uuid.uuid4()))
        trigger_count = workflow_data.get('triggerCount', 0)
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        updated_at = created_at

        # Insert workflow
        cursor.execute('''
            INSERT INTO workflow_entity (
                id, name, active, nodes, connections, settings, staticData,
                versionId, triggerCount, createdAt, updatedAt, isArchived
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (
            workflow_id, name, active, nodes, connections, settings, static_data,
            version_id, trigger_count, created_at, updated_at
        ))

        print(f"✓ Imported {name} ({file}) - Active: {'Yes' if active else 'No'}")
        imported += 1

    except Exception as e:
        print(f"✗ Failed to import {file}: {str(e)}")
        failed += 1

# Commit and close
conn.commit()
conn.close()

print(f"\n{imported} workflows imported successfully, {failed} failed")
