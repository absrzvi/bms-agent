/**
 * Similar Query Suggestion Dismiss Handler
 *
 * Handles user dismissal of similar query suggestions in Slack bot.
 *
 * Features:
 * - Store dismiss action in Redis with 7-day TTL
 * - Check dismissed suggestions before showing
 * - Optional global preference to disable all suggestions
 *
 * Usage in n8n Function node:
 *   const dismiss = require('./lib/similar-query-dismiss');
 *
 *   // Store dismiss action
 *   await dismiss.recordDismissal(userId, suggestionId);
 *
 *   // Check if suggestion was dismissed
 *   const wasDismissed = await dismiss.wasDismissed(userId, suggestionId);
 */

const Redis = require('ioredis');

// Redis client
const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  retryStrategy: (times) => {
    if (times > 3) return null;
    return Math.min(times * 100, 2000);
  }
});

// Redis key prefixes
const DISMISSED_PREFIX = 'bms:user:';
const DISMISSED_SUFFIX = ':dismissed_suggestions';
const GLOBAL_DISABLE_SUFFIX = ':disable_suggestions';

// TTL (7 days to match conversation TTL)
const DISMISS_TTL = 86400 * 7;

/**
 * Record a user's dismissal of a suggestion
 * @param {string} userId - User ID (Slack user ID)
 * @param {string} suggestionId - Unique suggestion ID (hash of similar query)
 * @param {object} metadata - Additional metadata
 * @returns {Promise<object>} Result object
 */
async function recordDismissal(userId, suggestionId, metadata = {}) {
  try {
    const key = buildDismissedKey(userId);
    const timestamp = new Date().toISOString();

    // Store as hash: suggestion_id -> {timestamp, query_text, etc}
    const value = JSON.stringify({
      dismissed_at: timestamp,
      suggestion_id: suggestionId,
      original_query: metadata.original_query,
      suggested_query: metadata.suggested_query
    });

    await redis.hset(key, suggestionId, value);

    // Set 7-day TTL on the hash
    await redis.expire(key, DISMISS_TTL);

    return {
      success: true,
      userId,
      suggestionId,
      dismissedAt: timestamp
    };

  } catch (error) {
    console.error('Error recording dismissal:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Check if a suggestion was dismissed by user
 * @param {string} userId - User ID
 * @param {string} suggestionId - Suggestion ID
 * @returns {Promise<boolean>} True if dismissed
 */
async function wasDismissed(userId, suggestionId) {
  try {
    const key = buildDismissedKey(userId);
    const exists = await redis.hexists(key, suggestionId);
    return exists === 1;
  } catch (error) {
    console.error('Error checking dismissal:', error);
    return false;
  }
}

/**
 * Get all dismissed suggestions for a user
 * @param {string} userId - User ID
 * @returns {Promise<array>} Array of dismissed suggestions
 */
async function getDismissedSuggestions(userId) {
  try {
    const key = buildDismissedKey(userId);
    const data = await redis.hgetall(key);

    return Object.entries(data).map(([suggestionId, value]) => ({
      suggestionId,
      ...JSON.parse(value)
    }));
  } catch (error) {
    console.error('Error retrieving dismissed suggestions:', error);
    return [];
  }
}

/**
 * Clear a specific dismissed suggestion
 * @param {string} userId - User ID
 * @param {string} suggestionId - Suggestion ID
 * @returns {Promise<boolean>} True if cleared
 */
async function clearDismissal(userId, suggestionId) {
  try {
    const key = buildDismissedKey(userId);
    const result = await redis.hdel(key, suggestionId);
    return result === 1;
  } catch (error) {
    console.error('Error clearing dismissal:', error);
    return false;
  }
}

/**
 * Clear all dismissed suggestions for a user
 * @param {string} userId - User ID
 * @returns {Promise<boolean>} True if cleared
 */
async function clearAllDismissals(userId) {
  try {
    const key = buildDismissedKey(userId);
    await redis.del(key);
    return true;
  } catch (error) {
    console.error('Error clearing all dismissals:', error);
    return false;
  }
}

/**
 * Enable global "disable all suggestions" preference for a user
 * @param {string} userId - User ID
 * @returns {Promise<object>} Result object
 */
async function disableAllSuggestions(userId) {
  try {
    const key = buildGlobalDisableKey(userId);
    await redis.set(key, 'true');
    // No expiry - permanent preference

    return {
      success: true,
      userId,
      message: 'Similar query suggestions disabled for all future queries'
    };
  } catch (error) {
    console.error('Error disabling suggestions:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Enable global suggestions for a user
 * @param {string} userId - User ID
 * @returns {Promise<object>} Result object
 */
async function enableAllSuggestions(userId) {
  try {
    const key = buildGlobalDisableKey(userId);
    await redis.del(key);

    return {
      success: true,
      userId,
      message: 'Similar query suggestions enabled'
    };
  } catch (error) {
    console.error('Error enabling suggestions:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Check if user has globally disabled suggestions
 * @param {string} userId - User ID
 * @returns {Promise<boolean>} True if disabled
 */
async function areSuggestionsDisabled(userId) {
  try {
    const key = buildGlobalDisableKey(userId);
    const value = await redis.get(key);
    return value === 'true';
  } catch (error) {
    console.error('Error checking global disable:', error);
    return false;
  }
}

/**
 * Should show suggestion to user?
 * Checks both global disable and specific dismissal
 * @param {string} userId - User ID
 * @param {string} suggestionId - Suggestion ID
 * @returns {Promise<boolean>} True if should show
 */
async function shouldShowSuggestion(userId, suggestionId) {
  try {
    // Check global disable first
    const globallyDisabled = await areSuggestionsDisabled(userId);
    if (globallyDisabled) {
      return false;
    }

    // Check specific dismissal
    const dismissed = await wasDismissed(userId, suggestionId);
    return !dismissed;

  } catch (error) {
    console.error('Error checking if should show suggestion:', error);
    // Default to showing on error
    return true;
  }
}

/**
 * Build Redis key for dismissed suggestions
 * @param {string} userId - User ID
 * @returns {string} Redis key
 */
function buildDismissedKey(userId) {
  return `${DISMISSED_PREFIX}${userId}${DISMISSED_SUFFIX}`;
}

/**
 * Build Redis key for global disable preference
 * @param {string} userId - User ID
 * @returns {string} Redis key
 */
function buildGlobalDisableKey(userId) {
  return `${DISMISSED_PREFIX}${userId}${GLOBAL_DISABLE_SUFFIX}`;
}

/**
 * Get dismissal statistics
 * @param {string} userId - User ID
 * @returns {Promise<object>} Statistics object
 */
async function getStatistics(userId) {
  try {
    const dismissed = await getDismissedSuggestions(userId);
    const globallyDisabled = await areSuggestionsDisabled(userId);

    return {
      totalDismissed: dismissed.length,
      globallyDisabled,
      dismissed: dismissed.map(d => ({
        suggestionId: d.suggestionId,
        dismissedAt: d.dismissed_at,
        suggestedQuery: d.suggested_query
      }))
    };
  } catch (error) {
    console.error('Error getting statistics:', error);
    return {
      error: error.message
    };
  }
}

/**
 * Close Redis connection
 */
async function close() {
  await redis.quit();
}

module.exports = {
  recordDismissal,
  wasDismissed,
  getDismissedSuggestions,
  clearDismissal,
  clearAllDismissals,
  disableAllSuggestions,
  enableAllSuggestions,
  areSuggestionsDisabled,
  shouldShowSuggestion,
  getStatistics,
  close
};
