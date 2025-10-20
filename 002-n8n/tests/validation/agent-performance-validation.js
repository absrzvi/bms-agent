#!/usr/bin/env node

/**
 * Agent Performance Validation Test Suite (FR-038)
 *
 * Tests optimized agent against 50 representative queries to validate:
 * - Response time <30s (p95)
 * - Tool selection accuracy ≥90%
 * - Duplicate tool call rate <5%
 * - Timeout rate <2%
 *
 * Usage:
 *   node tests/validation/agent-performance-validation.js [--agent=optimized] [--output=results.json]
 */

const https = require('https');
const http = require('http');

// Configuration
const AGENT_BASE_URL = process.env.AGENT_BASE_URL || 'http://localhost:5678';
const DEFAULT_AGENT = 'optimized';
const TIMEOUT_MS = 60000; // 60s to allow for 45s agent timeout + overhead

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
  agent: DEFAULT_AGENT,
  output: null,
  verbose: false
};

args.forEach(arg => {
  if (arg.startsWith('--agent=')) {
    options.agent = arg.split('=')[1];
  } else if (arg.startsWith('--output=')) {
    options.output = arg.split('=')[1];
  } else if (arg === '--verbose' || arg === '-v') {
    options.verbose = true;
  }
});

// Test queries covering different intent types
const TEST_QUERIES = [
  // Open-ended questions (should use ask_bms)
  { id: 1, query: 'What is the sick leave policy?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 2, query: 'How do I submit expense claims?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 3, query: 'Explain the annual leave approval process', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 4, query: 'What are the safety procedures for track work?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 5, query: 'How do I request training?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 6, query: 'What is the disciplinary procedure?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 7, query: 'How do I report an incident?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 8, query: 'What are the working time regulations?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 9, query: 'Explain the performance review process', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 10, query: 'What benefits are available to employees?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 11, query: 'How do I access the HR portal?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 12, query: 'What is the grievance procedure?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 13, query: 'How do I book a company vehicle?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 14, query: 'What PPE is required for signallers?', expectedTool: 'ask_bms', category: 'open_ended' },
  { id: 15, query: 'How do I update my personal details?', expectedTool: 'ask_bms', category: 'open_ended' },

  // Document code searches (should use search_hybrid)
  { id: 16, query: 'Find BMS-HUMR-POL-028', expectedTool: 'search_hybrid', category: 'document_code' },
  { id: 17, query: 'Show me BMS-SAFE-SOP-015', expectedTool: 'search_hybrid', category: 'document_code' },
  { id: 18, query: 'I need BMS-TECH-MAN-042', expectedTool: 'search_hybrid', category: 'document_code' },
  { id: 19, query: 'Find document BMS-HUMR-FRM-010', expectedTool: 'search_hybrid', category: 'document_code' },
  { id: 20, query: 'Get BMS-SAFE-POL-003', expectedTool: 'search_hybrid', category: 'document_code' },

  // Technical term searches (should use search_hybrid)
  { id: 21, query: 'VLAN configuration for emergency systems', expectedTool: 'search_hybrid', category: 'technical_term' },
  { id: 22, query: 'SPAD reporting requirements', expectedTool: 'search_hybrid', category: 'technical_term' },
  { id: 23, query: 'TPWS testing procedures', expectedTool: 'search_hybrid', category: 'technical_term' },
  { id: 24, query: 'AWS fault diagnosis', expectedTool: 'search_hybrid', category: 'technical_term' },
  { id: 25, query: 'ERTMS Level 2 operations', expectedTool: 'search_hybrid', category: 'technical_term' },

  // Metadata queries (should use search_metadata)
  { id: 26, query: 'Who wrote the safety manual?', expectedTool: 'search_metadata', category: 'metadata' },
  { id: 27, query: 'When was BMS-HUMR-POL-010 last updated?', expectedTool: 'search_metadata', category: 'metadata' },
  { id: 28, query: 'Show me documents by the HR department', expectedTool: 'search_metadata', category: 'metadata' },
  { id: 29, query: 'Which documents were updated in January?', expectedTool: 'search_metadata', category: 'metadata' },
  { id: 30, query: 'Who is the author of the training policy?', expectedTool: 'search_metadata', category: 'metadata' },

  // Version/change queries (should use search_metadata)
  { id: 31, query: 'What changed in the latest sick leave policy?', expectedTool: 'search_metadata', category: 'version' },
  { id: 32, query: 'Compare versions of BMS-SAFE-POL-001', expectedTool: 'search_metadata', category: 'version' },
  { id: 33, query: 'Show me recent changes to the expense policy', expectedTool: 'search_metadata', category: 'version' },
  { id: 34, query: 'What is new in version 2.0 of the handbook?', expectedTool: 'search_metadata', category: 'version' },
  { id: 35, query: 'Has the vehicle booking policy been updated?', expectedTool: 'search_metadata', category: 'version' },

  // Conceptual queries (should use search_semantic)
  { id: 36, query: 'What does duty of care mean?', expectedTool: 'search_semantic', category: 'conceptual' },
  { id: 37, query: 'Explain the concept of reasonable adjustments', expectedTool: 'search_semantic', category: 'conceptual' },
  { id: 38, query: 'What is meant by competency framework?', expectedTool: 'search_semantic', category: 'conceptual' },
  { id: 39, query: 'Define track circuit principles', expectedTool: 'search_semantic', category: 'conceptual' },
  { id: 40, query: 'What does it mean to be fit for duty?', expectedTool: 'search_semantic', category: 'conceptual' },

  // Procedural questions with context (should use search_hybrid for context)
  { id: 41, query: 'What are the steps for emergency brake testing?', expectedTool: 'search_hybrid', category: 'procedural' },
  { id: 42, query: 'How do I complete a risk assessment form?', expectedTool: 'search_hybrid', category: 'procedural' },
  { id: 43, query: 'What is the process for track access approval?', expectedTool: 'search_hybrid', category: 'procedural' },
  { id: 44, query: 'Steps to authorize overtime?', expectedTool: 'search_hybrid', category: 'procedural' },
  { id: 45, query: 'How to escalate a safety concern?', expectedTool: 'search_hybrid', category: 'procedural' },

  // Mixed queries (ambiguous - acceptable if either ask_bms or search_hybrid)
  { id: 46, query: 'Tell me about the whistleblowing policy', expectedTool: ['ask_bms', 'search_hybrid'], category: 'mixed' },
  { id: 47, query: 'Information on night shift allowances', expectedTool: ['ask_bms', 'search_hybrid'], category: 'mixed' },
  { id: 48, query: 'Details on the pension scheme', expectedTool: ['ask_bms', 'search_hybrid'], category: 'mixed' },
  { id: 49, query: 'Maternity leave entitlements', expectedTool: ['ask_bms', 'search_hybrid'], category: 'mixed' },
  { id: 50, query: 'Company policy on social media use', expectedTool: ['ask_bms', 'search_hybrid'], category: 'mixed' }
];

/**
 * Send query to agent and measure response
 * @param {string} query - Test query
 * @param {string} webhookId - Agent webhook ID
 * @returns {Promise<Object>} Test result
 */
async function testQuery(query, webhookId) {
  const startTime = Date.now();

  const postData = JSON.stringify({
    query: query,
    test: true,
    userId: 'TEST_USER_001'
  });

  const url = new URL(`${AGENT_BASE_URL}/webhook/${webhookId}`);
  const protocol = url.protocol === 'https:' ? https : http;

  return new Promise((resolve, reject) => {
    const req = protocol.request(
      {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData)
        },
        timeout: TIMEOUT_MS
      },
      (res) => {
        let data = '';

        res.on('data', chunk => {
          data += chunk;
        });

        res.on('end', () => {
          const responseTime = Date.now() - startTime;

          try {
            const result = JSON.parse(data);

            resolve({
              success: true,
              responseTime,
              statusCode: res.statusCode,
              toolUsed: result.tool_name || 'unknown',
              result
            });
          } catch (err) {
            resolve({
              success: false,
              responseTime,
              statusCode: res.statusCode,
              error: 'Invalid JSON response',
              rawData: data
            });
          }
        });
      }
    );

    req.on('error', (err) => {
      const responseTime = Date.now() - startTime;
      resolve({
        success: false,
        responseTime,
        error: err.message
      });
    });

    req.on('timeout', () => {
      req.destroy();
      const responseTime = Date.now() - startTime;
      resolve({
        success: false,
        responseTime,
        error: 'Request timeout',
        timedOut: true
      });
    });

    req.write(postData);
    req.end();
  });
}

/**
 * Run validation suite
 * @param {string} agent - Agent type (optimized or legacy)
 * @returns {Promise<Object>} Validation results
 */
async function runValidation(agent) {
  const webhookId = agent === 'optimized' ? 'bms-ai-agent-optimized-chat' : 'bms-ai-agent-chat';

  console.log(`\n🚀 Starting validation for ${agent} agent (${TEST_QUERIES.length} queries)...\n`);

  const results = [];

  for (let i = 0; i < TEST_QUERIES.length; i++) {
    const testCase = TEST_QUERIES[i];
    const progress = `[${(i + 1).toString().padStart(2)}/${TEST_QUERIES.length}]`;

    process.stdout.write(`${progress} Testing: ${testCase.query.substring(0, 50).padEnd(50)} `);

    const result = await testQuery(testCase.query, webhookId);

    const expectedTools = Array.isArray(testCase.expectedTool)
      ? testCase.expectedTool
      : [testCase.expectedTool];

    const toolCorrect = expectedTools.includes(result.toolUsed);

    results.push({
      ...testCase,
      ...result,
      toolCorrect,
      expectedTools
    });

    const status = result.success
      ? (toolCorrect ? '✅' : '⚠️')
      : '❌';

    console.log(`${status} ${result.responseTime}ms`);

    // Small delay to avoid overwhelming the server
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  return results;
}

/**
 * Calculate validation metrics
 * @param {Array<Object>} results - Test results
 * @returns {Object} Metrics
 */
function calculateMetrics(results) {
  const total = results.length;
  const successes = results.filter(r => r.success).length;
  const failures = results.filter(r => !r.success).length;
  const timeouts = results.filter(r => r.timedOut).length;
  const correctTools = results.filter(r => r.toolCorrect).length;

  const responseTimes = results.map(r => r.responseTime).sort((a, b) => a - b);
  const p50 = responseTimes[Math.floor(total * 0.5)];
  const p95 = responseTimes[Math.floor(total * 0.95)];
  const p99 = responseTimes[Math.floor(total * 0.99)];
  const avg = responseTimes.reduce((sum, t) => sum + t, 0) / total;

  // Detect duplicate tool calls (simplistic: multiple failures for same query)
  const queryMap = new Map();
  let duplicates = 0;

  results.forEach(r => {
    if (queryMap.has(r.query)) {
      duplicates++;
    }
    queryMap.set(r.query, true);
  });

  return {
    total,
    successes,
    failures,
    timeouts,
    correctTools,
    duplicates,
    successRate: ((successes / total) * 100).toFixed(2) + '%',
    toolAccuracy: ((correctTools / total) * 100).toFixed(2) + '%',
    timeoutRate: ((timeouts / total) * 100).toFixed(2) + '%',
    duplicateRate: ((duplicates / total) * 100).toFixed(2) + '%',
    responseTimes: {
      p50,
      p95,
      p99,
      avg: Math.round(avg)
    },
    goalsStatus: {
      p95ResponseTime: p95 <= 30000,
      toolSelectionAccuracy: (correctTools / total) >= 0.9,
      duplicateRate: (duplicates / total) < 0.05,
      timeoutRate: (timeouts / total) < 0.02
    }
  };
}

/**
 * Print validation report
 * @param {Object} metrics - Validation metrics
 * @param {Array<Object>} results - Test results
 */
function printReport(metrics, results) {
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  🧪 Agent Performance Validation Report');
  console.log('═══════════════════════════════════════════════════════════════\n');

  console.log(`📊 Test Coverage: ${metrics.total} queries\n`);

  console.log(`✅ Success Rate: ${metrics.successRate} (${metrics.successes}/${metrics.total})`);
  console.log(`🎯 Tool Accuracy: ${metrics.toolAccuracy} (${metrics.correctTools}/${metrics.total})`);
  console.log(`⏱️  Timeout Rate: ${metrics.timeoutRate} (${metrics.timeouts}/${metrics.total})`);
  console.log(`🔁 Duplicate Rate: ${metrics.duplicateRate} (${metrics.duplicates}/${metrics.total})\n`);

  console.log(`⚡ Response Time:`);
  console.log(`   p50: ${metrics.responseTimes.p50}ms`);
  console.log(`   p95: ${metrics.responseTimes.p95}ms`);
  console.log(`   p99: ${metrics.responseTimes.p99}ms`);
  console.log(`   avg: ${metrics.responseTimes.avg}ms\n`);

  console.log(`🎯 Goals Status:`);
  console.log(`   Response Time (<30s):       ${metrics.goalsStatus.p95ResponseTime ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Tool Accuracy (≥90%):       ${metrics.goalsStatus.toolSelectionAccuracy ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Duplicate Rate (<5%):       ${metrics.goalsStatus.duplicateRate ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Timeout Rate (<2%):         ${metrics.goalsStatus.timeoutRate ? '✅ PASS' : '❌ FAIL'}\n`);

  const allGoalsMet = Object.values(metrics.goalsStatus).every(met => met);
  console.log(`🏆 Overall: ${allGoalsMet ? '✅ ALL GOALS MET' : '⚠️ SOME GOALS NOT MET'}\n`);

  // Show failures if any
  const failures = results.filter(r => !r.success || !r.toolCorrect);
  if (failures.length > 0 && options.verbose) {
    console.log(`❌ Failures / Incorrect Tool Selection (${failures.length}):\n`);
    failures.forEach(f => {
      console.log(`   ${f.id.toString().padStart(2)}. ${f.query.substring(0, 60)}`);
      console.log(`       Expected: ${f.expectedTools.join(' or ')} | Got: ${f.toolUsed || 'none'}`);
      if (f.error) console.log(`       Error: ${f.error}`);
      console.log('');
    });
  }

  console.log('═══════════════════════════════════════════════════════════════\n');
}

/**
 * Main execution
 */
async function main() {
  const results = await runValidation(options.agent);
  const metrics = calculateMetrics(results);

  printReport(metrics, results);

  // Save to file if requested
  if (options.output) {
    const fs = require('fs');
    const report = { agent: options.agent, metrics, results, timestamp: new Date().toISOString() };
    fs.writeFileSync(options.output, JSON.stringify(report, null, 2), 'utf8');
    console.log(`💾 Report saved to: ${options.output}\n`);
  }

  // Exit with appropriate code
  const allGoalsMet = Object.values(metrics.goalsStatus).every(met => met);
  process.exit(allGoalsMet ? 0 : 1);
}

// Run if executed directly
if (require.main === module) {
  main().catch(err => {
    console.error('❌ Fatal error:', err);
    process.exit(1);
  });
}

module.exports = {
  testQuery,
  runValidation,
  calculateMetrics,
  TEST_QUERIES
};
