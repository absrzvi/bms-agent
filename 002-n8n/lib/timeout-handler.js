/**
 * Timeout Handler with Partial Result Caching (FR-033)
 *
 * Implements 45-second hard timeout for AI agent tool calls with Redis caching
 * to enable resume functionality via /continue command.
 *
 * Usage in n8n Function node:
 *   const timeoutHandler = require('./lib/timeout-handler');
 *
 *   const result = await timeoutHandler.executeWithTimeout(
 *     async () => { return await toolCall(); },
 *     { query, userId, conversationId }
 *   );
 */

const redis = require('redis');

// Redis client (lazy initialization)
let redisClient = null;

const TIMEOUT_MS = parseInt(process.env.AGENT_TIMEOUT_MS || '45000', 10); // 45 seconds
const PARTIAL_RESULT_TTL = parseInt(process.env.PARTIAL_RESULT_TTL || '300', 10); // 5 minutes

/**
 * Get or create Redis client
 * @returns {Promise<Object>} Redis client
 */
async function getRedisClient() {
  if (redisClient && redisClient.isOpen) {
    return redisClient;
  }

  const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';

  redisClient = redis.createClient({ url: redisUrl });

  redisClient.on('error', (err) => {
    console.error('Redis client error:', err);
  });

  await redisClient.connect();
  return redisClient;
}

/**
 * Execute function with timeout and partial result caching
 * @param {Function} fn - Async function to execute
 * @param {Object} context - Execution context
 * @param {string} context.query - User query
 * @param {string} context.userId - Slack user ID
 * @param {string} context.conversationId - Conversation thread_ts
 * @param {string} [context.toolName] - Tool being called
 * @param {number} [context.timeoutMs] - Custom timeout (default: 45000ms)
 * @returns {Promise<Object>} Result object with status
 */
async function executeWithTimeout(fn, context) {
  const {
    query,
    userId,
    conversationId,
    toolName = 'unknown',
    timeoutMs = TIMEOUT_MS
  } = context;

  const startTime = Date.now();
  const cacheKey = `bms:timeout:partial:${conversationId}`;

  try {
    // Create timeout promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('TIMEOUT'));
      }, timeoutMs);
    });

    // Race between function execution and timeout
    const result = await Promise.race([
      fn(),
      timeoutPromise
    ]);

    // Success - clear any partial cache
    await clearPartialResult(cacheKey);

    return {
      success: true,
      result,
      timedOut: false,
      executionTime: Date.now() - startTime
    };

  } catch (error) {
    const executionTime = Date.now() - startTime;

    if (error.message === 'TIMEOUT') {
      // Timeout occurred - save partial results if available
      console.warn(`⏱️ Timeout after ${executionTime}ms for ${toolName}: ${query.substring(0, 50)}`);

      const partialData = {
        query,
        userId,
        conversationId,
        toolName,
        timedOutAt: new Date().toISOString(),
        executionTime,
        partialResult: null, // Will be populated by tool if available
        canResume: false // Will be set to true if partial results exist
      };

      await savePartialResult(cacheKey, partialData);

      return {
        success: false,
        timedOut: true,
        executionTime,
        error: 'Request timed out after 45 seconds',
        partialCacheKey: cacheKey,
        message: 'Your request is taking longer than expected. I\'ve saved your progress - use `/continue` to resume.'
      };
    }

    // Other error
    console.error(`❌ Error in ${toolName}:`, error);
    return {
      success: false,
      timedOut: false,
      executionTime,
      error: error.message
    };
  }
}

/**
 * Save partial result to Redis cache
 * @param {string} cacheKey - Redis key
 * @param {Object} partialData - Partial result data
 */
async function savePartialResult(cacheKey, partialData) {
  try {
    const client = await getRedisClient();
    await client.setEx(
      cacheKey,
      PARTIAL_RESULT_TTL,
      JSON.stringify(partialData)
    );
    console.log(`💾 Saved partial result: ${cacheKey}`);
  } catch (err) {
    console.error('Failed to save partial result:', err);
  }
}

/**
 * Retrieve partial result from cache (for /continue command)
 * @param {string} conversationId - Conversation ID (thread_ts)
 * @returns {Promise<Object|null>} Partial result or null
 */
async function getPartialResult(conversationId) {
  try {
    const cacheKey = `bms:timeout:partial:${conversationId}`;
    const client = await getRedisClient();
    const data = await client.get(cacheKey);

    if (!data) {
      return null;
    }

    return JSON.parse(data);
  } catch (err) {
    console.error('Failed to retrieve partial result:', err);
    return null;
  }
}

/**
 * Clear partial result cache
 * @param {string} cacheKey - Redis key
 */
async function clearPartialResult(cacheKey) {
  try {
    const client = await getRedisClient();
    await client.del(cacheKey);
  } catch (err) {
    console.error('Failed to clear partial result:', err);
  }
}

/**
 * Update partial result with progress (called by tool during execution)
 * @param {string} cacheKey - Redis key
 * @param {Object} progressData - Progress update
 */
async function updatePartialProgress(cacheKey, progressData) {
  try {
    const client = await getRedisClient();
    const existing = await client.get(cacheKey);

    if (existing) {
      const data = JSON.parse(existing);
      data.partialResult = progressData;
      data.canResume = true;
      data.lastUpdate = new Date().toISOString();

      await client.setEx(cacheKey, PARTIAL_RESULT_TTL, JSON.stringify(data));
    }
  } catch (err) {
    console.error('Failed to update partial progress:', err);
  }
}

/**
 * Check if timeout is approaching and should warn user
 * @param {number} startTime - Execution start timestamp
 * @param {number} warningThreshold - Warn at N% of timeout (default: 80%)
 * @returns {boolean} True if warning threshold exceeded
 */
function shouldWarnTimeout(startTime, warningThreshold = 0.8) {
  const elapsed = Date.now() - startTime;
  return elapsed >= (TIMEOUT_MS * warningThreshold);
}

/**
 * Get remaining time before timeout
 * @param {number} startTime - Execution start timestamp
 * @returns {number} Remaining milliseconds
 */
function getRemainingTime(startTime) {
  const elapsed = Date.now() - startTime;
  return Math.max(0, TIMEOUT_MS - elapsed);
}

/**
 * Cleanup - close Redis connection
 */
async function cleanup() {
  if (redisClient && redisClient.isOpen) {
    await redisClient.quit();
    redisClient = null;
  }
}

module.exports = {
  executeWithTimeout,
  getPartialResult,
  clearPartialResult,
  updatePartialProgress,
  shouldWarnTimeout,
  getRemainingTime,
  cleanup,
  TIMEOUT_MS
};
