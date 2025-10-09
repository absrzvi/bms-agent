/**
 * Prometheus Metrics Exporter for Slack Bot
 *
 * Provides Prometheus-compatible metrics endpoint for monitoring:
 * - Request counters
 * - Response latency histograms
 * - Error counters
 * - Active conversations gauge
 * - Document upload metrics
 *
 * Usage in n8n Function node:
 *   const metrics = require('./lib/prometheus-exporter');
 *   metrics.incrementCounter('slack_bot_requests_total', {command_type: 'ask'});
 *   metrics.recordLatency('slack_bot_response_latency_seconds', latencyMs);
 */

const Redis = require('ioredis');

// Metrics storage keys
const METRICS_PREFIX = 'metrics:';
const COUNTER_PREFIX = `${METRICS_PREFIX}counter:`;
const HISTOGRAM_PREFIX = `${METRICS_PREFIX}histogram:`;
const GAUGE_PREFIX = `${METRICS_PREFIX}gauge:`;

// Initialize Redis client
const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  retryStrategy: (times) => {
    if (times > 3) return null; // Stop retrying after 3 attempts
    return Math.min(times * 100, 2000); // Exponential backoff
  }
});

/**
 * Increment a counter metric
 * @param {string} metricName - Name of the metric
 * @param {object} labels - Labels for the metric (e.g., {command_type: 'ask'})
 * @param {number} value - Value to increment by (default: 1)
 */
async function incrementCounter(metricName, labels = {}, value = 1) {
  const key = buildMetricKey(COUNTER_PREFIX, metricName, labels);
  try {
    await redis.incrby(key, value);
    await redis.expire(key, 86400 * 7); // 7-day retention
  } catch (error) {
    console.error(`Failed to increment counter ${metricName}:`, error.message);
  }
}

/**
 * Record a histogram value (for latency measurements)
 * @param {string} metricName - Name of the metric
 * @param {number} value - Value in milliseconds
 * @param {object} labels - Labels for the metric
 */
async function recordLatency(metricName, value, labels = {}) {
  const key = buildMetricKey(HISTOGRAM_PREFIX, metricName, labels);
  const timestamp = Date.now();

  try {
    // Store as sorted set with timestamp as score
    await redis.zadd(key, timestamp, `${timestamp}:${value}`);

    // Keep only last 10000 measurements
    await redis.zremrangebyrank(key, 0, -10001);

    // Set 7-day expiration
    await redis.expire(key, 86400 * 7);
  } catch (error) {
    console.error(`Failed to record latency ${metricName}:`, error.message);
  }
}

/**
 * Set a gauge value (for current state measurements)
 * @param {string} metricName - Name of the metric
 * @param {number} value - Current value
 * @param {object} labels - Labels for the metric
 */
async function setGauge(metricName, value, labels = {}) {
  const key = buildMetricKey(GAUGE_PREFIX, metricName, labels);

  try {
    await redis.set(key, value);
    await redis.expire(key, 86400 * 7); // 7-day retention
  } catch (error) {
    console.error(`Failed to set gauge ${metricName}:`, error.message);
  }
}

/**
 * Build metric key with labels
 * @param {string} prefix - Metric type prefix
 * @param {string} metricName - Name of the metric
 * @param {object} labels - Labels for the metric
 * @returns {string} Redis key
 */
function buildMetricKey(prefix, metricName, labels) {
  const labelStr = Object.entries(labels)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}="${v}"`)
    .join(',');

  return labelStr ? `${prefix}${metricName}{${labelStr}}` : `${prefix}${metricName}`;
}

/**
 * Get all metrics in Prometheus text format
 * @returns {Promise<string>} Metrics in Prometheus format
 */
async function getMetrics() {
  try {
    const metrics = [];

    // Get all counter metrics
    const counterKeys = await redis.keys(`${COUNTER_PREFIX}*`);
    for (const key of counterKeys) {
      const value = await redis.get(key);
      const metricLine = formatMetric(key, COUNTER_PREFIX, value, 'counter');
      if (metricLine) metrics.push(metricLine);
    }

    // Get all gauge metrics
    const gaugeKeys = await redis.keys(`${GAUGE_PREFIX}*`);
    for (const key of gaugeKeys) {
      const value = await redis.get(key);
      const metricLine = formatMetric(key, GAUGE_PREFIX, value, 'gauge');
      if (metricLine) metrics.push(metricLine);
    }

    // Get all histogram metrics (calculate percentiles)
    const histogramKeys = await redis.keys(`${HISTOGRAM_PREFIX}*`);
    for (const key of histogramKeys) {
      const values = await redis.zrange(key, 0, -1);
      const histogramLines = formatHistogram(key, HISTOGRAM_PREFIX, values);
      metrics.push(...histogramLines);
    }

    // Add metadata
    const timestamp = Date.now();
    metrics.unshift(`# Generated at ${new Date(timestamp).toISOString()}`);
    metrics.unshift('# Slack Bot Metrics');

    return metrics.join('\n') + '\n';
  } catch (error) {
    console.error('Failed to get metrics:', error.message);
    return `# Error retrieving metrics: ${error.message}\n`;
  }
}

/**
 * Format a counter or gauge metric
 * @param {string} key - Redis key
 * @param {string} prefix - Metric prefix
 * @param {string} value - Metric value
 * @param {string} type - Metric type
 * @returns {string} Formatted metric line
 */
function formatMetric(key, prefix, value, type) {
  const metricName = key.replace(prefix, '');
  return `# TYPE ${metricName.split('{')[0]} ${type}\n${metricName} ${value}`;
}

/**
 * Format histogram metrics with percentiles
 * @param {string} key - Redis key
 * @param {string} prefix - Metric prefix
 * @param {array} values - Array of timestamp:value strings
 * @returns {array} Formatted metric lines
 */
function formatHistogram(key, prefix, values) {
  const metricName = key.replace(prefix, '');
  const baseName = metricName.split('{')[0];
  const labels = metricName.match(/\{.*\}/)?.[0] || '';

  if (values.length === 0) {
    return [`# TYPE ${baseName} histogram\n${metricName}_count 0\n${metricName}_sum 0`];
  }

  // Extract numeric values
  const nums = values.map(v => parseFloat(v.split(':')[1])).filter(n => !isNaN(n)).sort((a, b) => a - b);

  if (nums.length === 0) {
    return [`# TYPE ${baseName} histogram\n${metricName}_count 0\n${metricName}_sum 0`];
  }

  // Calculate percentiles
  const p50 = calculatePercentile(nums, 0.50);
  const p95 = calculatePercentile(nums, 0.95);
  const p99 = calculatePercentile(nums, 0.99);
  const sum = nums.reduce((a, b) => a + b, 0);
  const count = nums.length;

  // Format as Prometheus histogram
  const baseLabels = labels.slice(0, -1); // Remove closing }
  const labelPrefix = baseLabels ? `${baseLabels},` : '{';

  return [
    `# TYPE ${baseName} histogram`,
    `${baseName}_bucket${labelPrefix}le="0.5"} ${nums.filter(v => v <= 500).length}`,
    `${baseName}_bucket${labelPrefix}le="1"} ${nums.filter(v => v <= 1000).length}`,
    `${baseName}_bucket${labelPrefix}le="2"} ${nums.filter(v => v <= 2000).length}`,
    `${baseName}_bucket${labelPrefix}le="3"} ${nums.filter(v => v <= 3000).length}`,
    `${baseName}_bucket${labelPrefix}le="+Inf"} ${count}`,
    `${baseName}_sum${labels} ${(sum / 1000).toFixed(3)}`,
    `${baseName}_count${labels} ${count}`,
    `# p50 latency: ${p50.toFixed(2)}ms`,
    `# p95 latency: ${p95.toFixed(2)}ms`,
    `# p99 latency: ${p99.toFixed(2)}ms`
  ];
}

/**
 * Calculate percentile from sorted array
 * @param {array} sortedArray - Sorted array of numbers
 * @param {number} percentile - Percentile (0-1)
 * @returns {number} Percentile value
 */
function calculatePercentile(sortedArray, percentile) {
  const index = Math.ceil(sortedArray.length * percentile) - 1;
  return sortedArray[Math.max(0, index)];
}

/**
 * Close Redis connection
 */
async function close() {
  await redis.quit();
}

module.exports = {
  incrementCounter,
  recordLatency,
  setGauge,
  getMetrics,
  close
};
