/**
 * Workflow Instrumentation Helper
 *
 * Provides easy-to-use wrappers for instrumenting n8n workflows with metrics
 *
 * Usage in n8n Function node:
 *   const instrument = require('./lib/instrumentation');
 *
 *   // Track request
 *   await instrument.trackRequest('ask', $input.all());
 *
 *   // Track error
 *   await instrument.trackError('bms_api_timeout', error);
 *
 *   // Track latency
 *   const startTime = Date.now();
 *   // ... do work ...
 *   await instrument.trackLatency('bms_api_call', Date.now() - startTime, {endpoint: 'ask'});
 */

const metrics = require('./prometheus-exporter');

/**
 * Track an incoming request
 * @param {string} commandType - Type of command (ask, search, upload, admin, etc.)
 * @param {array} items - n8n input items
 */
async function trackRequest(commandType, items = []) {
  try {
    await metrics.incrementCounter('slack_bot_requests_total', {
      command_type: commandType
    });

    // Update active conversations gauge
    const conversationIds = new Set(items.map(item => item.json?.conversation_id).filter(Boolean));
    if (conversationIds.size > 0) {
      await metrics.setGauge('slack_bot_active_conversations', conversationIds.size);
    }
  } catch (error) {
    console.error('Failed to track request:', error.message);
  }
}

/**
 * Track an error
 * @param {string} errorType - Type of error (validation_error, bms_api_timeout, redis_error, etc.)
 * @param {Error|string} error - Error object or message
 * @param {object} labels - Additional labels
 */
async function trackError(errorType, error = {}, labels = {}) {
  try {
    await metrics.incrementCounter('slack_bot_errors_total', {
      error_type: errorType,
      ...labels
    });
  } catch (err) {
    console.error('Failed to track error:', err.message);
  }
}

/**
 * Track response latency
 * @param {string} operation - Operation name (bms_api_call, redis_query, total_response, etc.)
 * @param {number} latencyMs - Latency in milliseconds
 * @param {object} labels - Additional labels (endpoint, status, etc.)
 */
async function trackLatency(operation, latencyMs, labels = {}) {
  try {
    const metricName = operation === 'total_response'
      ? 'slack_bot_response_latency_seconds'
      : `slack_bot_${operation}_latency_seconds`;

    await metrics.recordLatency(metricName, latencyMs, labels);
  } catch (error) {
    console.error('Failed to track latency:', error.message);
  }
}

/**
 * Track document upload
 * @param {string} status - Upload status (success, failed, timeout)
 * @param {object} metadata - Upload metadata (file_type, size_kb, etc.)
 */
async function trackDocumentUpload(status, metadata = {}) {
  try {
    await metrics.incrementCounter('slack_bot_document_uploads_total', {
      status,
      file_type: metadata.file_type || 'unknown'
    });

    if (metadata.processing_time_ms) {
      await metrics.recordLatency('document_processing_latency_seconds', metadata.processing_time_ms);
    }
  } catch (error) {
    console.error('Failed to track document upload:', error.message);
  }
}

/**
 * Track BMS API call
 * @param {string} endpoint - API endpoint (ask, search, upload, etc.)
 * @param {number} latencyMs - Latency in milliseconds
 * @param {number} statusCode - HTTP status code
 */
async function trackBmsApiCall(endpoint, latencyMs, statusCode) {
  try {
    await metrics.recordLatency('bms_api_call_latency_seconds', latencyMs, {
      endpoint,
      status: Math.floor(statusCode / 100) + 'xx'
    });

    if (statusCode >= 400) {
      await trackError('bms_api_error', null, { endpoint, status_code: statusCode });
    }
  } catch (error) {
    console.error('Failed to track BMS API call:', error.message);
  }
}

/**
 * Create a timer for measuring operation duration
 * @param {string} operation - Operation name
 * @param {object} labels - Labels for the metric
 * @returns {function} Stop function that records the latency
 */
function startTimer(operation, labels = {}) {
  const startTime = Date.now();

  return async function stop() {
    const latencyMs = Date.now() - startTime;
    await trackLatency(operation, latencyMs, labels);
    return latencyMs;
  };
}

/**
 * Instrument a workflow execution
 * Usage:
 *   const stop = await instrument.instrumentWorkflow('query-analyzer', $input.all());
 *   // ... workflow logic ...
 *   await stop(); // Records latency and updates counters
 *
 * @param {string} workflowName - Name of the workflow
 * @param {array} items - n8n input items
 * @returns {function} Stop function
 */
async function instrumentWorkflow(workflowName, items = []) {
  const commandType = inferCommandType(items);
  await trackRequest(commandType, items);

  const stopTimer = startTimer('total_response', { workflow: workflowName });

  return async function stop(error = null) {
    const latencyMs = await stopTimer();

    if (error) {
      await trackError('workflow_error', error, { workflow: workflowName });
    }

    return latencyMs;
  };
}

/**
 * Infer command type from input items
 * @param {array} items - n8n input items
 * @returns {string} Command type
 */
function inferCommandType(items) {
  if (!items || items.length === 0) return 'unknown';

  const firstItem = items[0]?.json || {};
  const text = firstItem.text || firstItem.query || '';

  if (text.startsWith('/ask')) return 'ask';
  if (text.startsWith('/search')) return 'search';
  if (text.startsWith('/upload')) return 'upload';
  if (text.startsWith('/admin')) return 'admin';
  if (text.startsWith('/help')) return 'help';
  if (text.startsWith('/status')) return 'status';
  if (text.startsWith('/history')) return 'history';

  return firstItem.intent || firstItem.command_type || 'natural_language';
}

// ============================================================================
// Tool Call Logging (FR-034)
// ============================================================================

const fs = require('fs');
const path = require('path');

const TOOL_CALL_LOG_PATH = process.env.TOOL_CALL_LOG_PATH || '/workspace/logs/tool-calls.jsonl';
const MAX_LOG_SIZE_MB = parseInt(process.env.MAX_TOOL_LOG_SIZE_MB || '100', 10);

/**
 * Log a tool invocation with standard fields for analysis
 * @param {Object} toolCall - Tool call details
 * @param {string} toolCall.tool_name - Name of tool (ask_bms, search_hybrid, etc.)
 * @param {string} toolCall.query - User query text (sanitized)
 * @param {number} toolCall.response_time_ms - Response time in milliseconds
 * @param {number} toolCall.result_count - Number of results returned
 * @param {number} [toolCall.confidence_score] - Confidence score (0.0-1.0)
 * @param {boolean} toolCall.success - Whether call succeeded
 * @param {string} [toolCall.error_message] - Error message if failed
 * @param {Object} [toolCall.metadata] - Additional metadata
 */
function logToolCall(toolCall) {
  try {
    // Ensure logs directory exists
    const logDir = path.dirname(TOOL_CALL_LOG_PATH);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }

    // Build log entry with standard fields
    const logEntry = {
      timestamp: new Date().toISOString(),
      tool_name: toolCall.tool_name,
      query: sanitizeQuery(toolCall.query),
      response_time_ms: Math.round(toolCall.response_time_ms),
      result_count: toolCall.result_count || 0,
      confidence_score: toolCall.confidence_score !== undefined ? toolCall.confidence_score : null,
      success: toolCall.success,
      error_message: toolCall.error_message || null,
      metadata: toolCall.metadata || {}
    };

    // Append as newline-delimited JSON
    fs.appendFileSync(TOOL_CALL_LOG_PATH, JSON.stringify(logEntry) + '\n', 'utf8');

    // Check if log rotation needed
    checkLogRotation();
  } catch (err) {
    console.error('Failed to log tool call:', err);
  }
}

/**
 * Sanitize user query to remove PII
 * @param {string} query - Raw query text
 * @returns {string} Sanitized query
 */
function sanitizeQuery(query) {
  if (!query) return '';

  // Remove email addresses
  let sanitized = query.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL]');

  // Remove phone numbers (basic patterns)
  sanitized = sanitized.replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE]');

  // Remove potential usernames (Slack/Teams ID patterns)
  sanitized = sanitized.replace(/\b[U|C]\d{9,}\b/g, '[USER_ID]');

  return sanitized.substring(0, 500); // Truncate to 500 chars
}

/**
 * Check if log file needs rotation based on size
 */
function checkLogRotation() {
  try {
    if (!fs.existsSync(TOOL_CALL_LOG_PATH)) return;

    const stats = fs.statSync(TOOL_CALL_LOG_PATH);
    const sizeMB = stats.size / (1024 * 1024);

    if (sizeMB >= MAX_LOG_SIZE_MB) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const archivePath = TOOL_CALL_LOG_PATH.replace('.jsonl', `-${timestamp}.jsonl`);

      fs.renameSync(TOOL_CALL_LOG_PATH, archivePath);
      console.log(`Tool call log rotated: ${archivePath}`);
    }
  } catch (err) {
    console.error('Failed to rotate tool call log:', err);
  }
}

/**
 * Get tool call statistics from log file
 * @param {Object} options - Query options
 * @param {number} [options.hours] - Look back N hours (default: 24)
 * @param {string} [options.tool_name] - Filter by tool name
 * @returns {Object} Statistics summary
 */
function getToolStats(options = {}) {
  const hours = options.hours || 24;
  const toolNameFilter = options.tool_name;
  const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000);

  try {
    if (!fs.existsSync(TOOL_CALL_LOG_PATH)) {
      return { total: 0, by_tool: {}, avg_response_time: 0, success_rate: 0 };
    }

    const lines = fs.readFileSync(TOOL_CALL_LOG_PATH, 'utf8').split('\n').filter(Boolean);

    let total = 0;
    let successful = 0;
    let totalResponseTime = 0;
    const byTool = {};

    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        const entryTime = new Date(entry.timestamp);

        // Filter by time range
        if (entryTime < cutoffTime) continue;

        // Filter by tool name if specified
        if (toolNameFilter && entry.tool_name !== toolNameFilter) continue;

        total++;
        if (entry.success) successful++;
        totalResponseTime += entry.response_time_ms;

        // Aggregate by tool
        if (!byTool[entry.tool_name]) {
          byTool[entry.tool_name] = { count: 0, successes: 0, total_time: 0 };
        }
        byTool[entry.tool_name].count++;
        if (entry.success) byTool[entry.tool_name].successes++;
        byTool[entry.tool_name].total_time += entry.response_time_ms;
      } catch (parseErr) {
        // Skip malformed lines
        continue;
      }
    }

    // Calculate per-tool averages
    for (const tool in byTool) {
      const stats = byTool[tool];
      byTool[tool].avg_response_time = Math.round(stats.total_time / stats.count);
      byTool[tool].success_rate = (stats.successes / stats.count * 100).toFixed(2) + '%';
    }

    return {
      total,
      successful,
      failed: total - successful,
      success_rate: total > 0 ? (successful / total * 100).toFixed(2) + '%' : '0%',
      avg_response_time: total > 0 ? Math.round(totalResponseTime / total) : 0,
      by_tool: byTool,
      time_range_hours: hours
    };
  } catch (err) {
    console.error('Failed to get tool stats:', err);
    return { error: err.message };
  }
}

module.exports = {
  // Prometheus metrics (existing)
  trackRequest,
  trackError,
  trackLatency,
  trackDocumentUpload,
  trackBmsApiCall,
  startTimer,
  instrumentWorkflow,

  // Tool call logging (FR-034)
  logToolCall,
  getToolStats,
  sanitizeQuery
};
