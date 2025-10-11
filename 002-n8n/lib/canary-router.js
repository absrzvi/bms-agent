/**
 * Canary Routing Logic (FR-037)
 *
 * Routes 20% of users to optimized agent (4-tool version) and 80% to legacy (8-tool version)
 * using consistent hashing based on Slack user ID for stable routing.
 *
 * Usage in n8n Function node:
 *   const canaryRouter = require('./lib/canary-router');
 *
 *   const route = canaryRouter.getAgentRoute(userId);
 *   // Returns: { agent: 'optimized', version: '2.0', workflowId: '...' }
 */

const crypto = require('crypto');

// Configuration
const CANARY_PERCENTAGE = parseInt(process.env.CANARY_PERCENTAGE || '20', 10);
const FORCE_CANARY_USERS = (process.env.FORCE_CANARY_USERS || '').split(',').filter(Boolean);
const FORCE_LEGACY_USERS = (process.env.FORCE_LEGACY_USERS || '').split(',').filter(Boolean);

// Agent workflow configurations
const AGENTS = {
  legacy: {
    name: 'legacy',
    version: '1.0',
    description: '8-tool agent (baseline)',
    workflowId: 'bms-ai-agent-chat', // Original webhook ID
    toolCount: 8
  },
  optimized: {
    name: 'optimized',
    version: '2.0',
    description: '4-tool agent (optimized)',
    workflowId: 'bms-ai-agent-optimized-chat', // Optimized webhook ID
    toolCount: 4
  }
};

/**
 * Get agent route for a user using consistent hashing
 * @param {string} userId - Slack user ID (format: U#########)
 * @param {Object} [options] - Routing options
 * @param {number} [options.canaryPercentage] - Override canary percentage (default: 20)
 * @param {boolean} [options.logDecision] - Log routing decision (default: false)
 * @returns {Object} Agent configuration
 */
function getAgentRoute(userId, options = {}) {
  const {
    canaryPercentage = CANARY_PERCENTAGE,
    logDecision = false
  } = options;

  // Check force lists first
  if (FORCE_CANARY_USERS.includes(userId)) {
    if (logDecision) {
      console.log(`🎯 Canary routing: ${userId} → OPTIMIZED (force list)`);
    }
    return { ...AGENTS.optimized, reason: 'force_canary' };
  }

  if (FORCE_LEGACY_USERS.includes(userId)) {
    if (logDecision) {
      console.log(`🎯 Canary routing: ${userId} → LEGACY (force list)`);
    }
    return { ...AGENTS.legacy, reason: 'force_legacy' };
  }

  // Consistent hashing based on user ID
  const hash = hashUserId(userId);
  const bucket = hash % 100; // Hash to 0-99 range

  // Route to optimized if bucket < canaryPercentage
  const isCanary = bucket < canaryPercentage;
  const agent = isCanary ? AGENTS.optimized : AGENTS.legacy;

  if (logDecision) {
    console.log(
      `🎯 Canary routing: ${userId} (hash: ${hash}, bucket: ${bucket}) → ${agent.name.toUpperCase()}`
    );
  }

  return {
    ...agent,
    reason: isCanary ? 'canary_hash' : 'legacy_hash',
    bucket
  };
}

/**
 * Hash user ID to consistent integer for bucketing
 * @param {string} userId - Slack user ID
 * @returns {number} Hash value (0-99)
 */
function hashUserId(userId) {
  // Use MD5 for fast, consistent hashing
  const hash = crypto.createHash('md5').update(userId).digest('hex');
  // Take first 8 hex chars and convert to int, then mod 100
  const intHash = parseInt(hash.substring(0, 8), 16);
  return intHash % 100;
}

/**
 * Get canary statistics based on user set
 * @param {Array<string>} userIds - List of Slack user IDs
 * @returns {Object} Statistics
 */
function getCanaryStats(userIds) {
  const stats = {
    total: userIds.length,
    optimized: 0,
    legacy: 0,
    forced_canary: 0,
    forced_legacy: 0,
    percentage: 0
  };

  userIds.forEach(userId => {
    const route = getAgentRoute(userId);
    if (route.name === 'optimized') {
      stats.optimized++;
      if (route.reason === 'force_canary') stats.forced_canary++;
    } else {
      stats.legacy++;
      if (route.reason === 'force_legacy') stats.forced_legacy++;
    }
  });

  stats.percentage = stats.total > 0
    ? ((stats.optimized / stats.total) * 100).toFixed(2)
    : 0;

  return stats;
}

/**
 * Check if canary rollout is healthy based on error rates
 * @param {Object} metrics - Error rate metrics
 * @param {number} metrics.optimizedErrors - Error count for optimized agent
 * @param {number} metrics.optimizedTotal - Total requests for optimized agent
 * @param {number} metrics.legacyErrors - Error count for legacy agent
 * @param {number} metrics.legacyTotal - Total requests for legacy agent
 * @param {number} [threshold] - Max acceptable error rate delta (default: 0.05 = 5%)
 * @returns {Object} Health check result
 */
function checkCanaryHealth(metrics, threshold = 0.05) {
  const {
    optimizedErrors = 0,
    optimizedTotal = 0,
    legacyErrors = 0,
    legacyTotal = 0
  } = metrics;

  if (optimizedTotal === 0 || legacyTotal === 0) {
    return {
      healthy: false,
      reason: 'insufficient_data',
      message: 'Not enough requests to compare error rates'
    };
  }

  const optimizedErrorRate = optimizedErrors / optimizedTotal;
  const legacyErrorRate = legacyErrors / legacyTotal;
  const delta = optimizedErrorRate - legacyErrorRate;

  const healthy = delta <= threshold;

  return {
    healthy,
    optimizedErrorRate: (optimizedErrorRate * 100).toFixed(2) + '%',
    legacyErrorRate: (legacyErrorRate * 100).toFixed(2) + '%',
    delta: (delta * 100).toFixed(2) + '%',
    threshold: (threshold * 100).toFixed(2) + '%',
    reason: healthy ? 'within_threshold' : 'exceeded_threshold',
    message: healthy
      ? `Canary is healthy (delta: ${(delta * 100).toFixed(2)}% ≤ ${(threshold * 100).toFixed(2)}%)`
      : `⚠️ Canary error rate is ${(delta * 100).toFixed(2)}% higher than legacy (threshold: ${(threshold * 100).toFixed(2)}%)`
  };
}

/**
 * Get webhook URL for agent route
 * @param {string} userId - Slack user ID
 * @param {string} baseUrl - Base n8n URL (e.g., https://n8n.runpod.io)
 * @returns {string} Full webhook URL
 */
function getAgentWebhookUrl(userId, baseUrl) {
  const route = getAgentRoute(userId);
  return `${baseUrl}/webhook/${route.workflowId}`;
}

/**
 * Export canary routing decision for logging
 * @param {string} userId - Slack user ID
 * @param {string} query - User query
 * @param {Object} result - Agent execution result
 * @returns {Object} Log entry
 */
function logCanaryDecision(userId, query, result) {
  const route = getAgentRoute(userId);

  return {
    timestamp: new Date().toISOString(),
    userId,
    query: query.substring(0, 100), // Truncate for logging
    agent: route.name,
    version: route.version,
    reason: route.reason,
    bucket: route.bucket,
    success: result.success || false,
    executionTime: result.executionTime || null,
    toolName: result.toolName || null
  };
}

module.exports = {
  getAgentRoute,
  getCanaryStats,
  checkCanaryHealth,
  getAgentWebhookUrl,
  logCanaryDecision,
  hashUserId,
  AGENTS,
  CANARY_PERCENTAGE
};
