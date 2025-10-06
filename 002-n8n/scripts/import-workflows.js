#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();

const DB_PATH = '/workspace/n8n/.n8n/database.sqlite';
const WORKFLOWS_DIR = '/workspace/002-n8n/workflows';

// Open database
const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) {
    console.error('Error opening database:', err.message);
    process.exit(1);
  }
  console.log('Connected to n8n database');
});

// Get all workflow JSON files
const workflowFiles = fs.readdirSync(WORKFLOWS_DIR).filter(f => f.endsWith('.json'));

console.log(`Found ${workflowFiles.length} workflow files to import`);

let imported = 0;
let failed = 0;

// Import each workflow
workflowFiles.forEach((file, index) => {
  const filePath = path.join(WORKFLOWS_DIR, file);
  const workflowData = JSON.parse(fs.readFileSync(filePath, 'utf8'));

  const id = index + 1;
  const name = workflowData.name;
  const active = workflowData.active !== undefined ? (workflowData.active ? 1 : 0) : 1;
  const nodes = JSON.stringify(workflowData.nodes || []);
  const connections = JSON.stringify(workflowData.connections || {});
  const settings = JSON.stringify(workflowData.settings || {});
  const staticData = workflowData.staticData ? JSON.stringify(workflowData.staticData) : null;
  const tags = JSON.stringify(workflowData.tags || []);
  const createdAt = new Date().toISOString();
  const updatedAt = new Date().toISOString();

  const sql = `INSERT INTO workflow_entity (
    id, name, active, nodes, connections, settings, staticData, tags, createdAt, updatedAt
  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;

  db.run(sql, [id, name, active, nodes, connections, settings, staticData, tags, createdAt, updatedAt], (err) => {
    if (err) {
      console.error(`Failed to import ${file}:`, err.message);
      failed++;
    } else {
      console.log(`✓ Imported ${name} (${file}) - Active: ${active === 1 ? 'Yes' : 'No'}`);
      imported++;
    }

    // Close database after last workflow
    if (index === workflowFiles.length - 1) {
      setTimeout(() => {
        db.close((err) => {
          if (err) {
            console.error('Error closing database:', err.message);
          } else {
            console.log(`\n${imported} workflows imported successfully, ${failed} failed`);
          }
        });
      }, 100);
    }
  });
});
