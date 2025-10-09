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

module.exports = {
  trackRequest,
  trackError,
  trackLatency,
  trackDocumentUpload,
  trackBmsApiCall,
  startTimer,
  instrumentWorkflow
};
