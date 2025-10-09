/**
 * Admin Reset Command with Audit Logging
 *
 * Provides secure admin privilege reset mechanism with comprehensive audit trail.
 *
 * Security Features:
 * - Secret key validation (64-character hex string)
 * - Mandatory audit logging (all attempts, successful or failed)
 * - 90-day retention for compliance
 * - IP address tracking (if available)
 * - No information disclosure on failure
 *
 * Setup:
 *   1. Generate secret key: openssl rand -hex 32
 *   2. Add to .env: ADMIN_RESET_SECRET=<generated_key>
 *   3. Store .env securely (not in version control)
 *
 * Usage in n8n Function node:
 *   const adminReset = require('./lib/admin-reset');
 *   const result = await adminReset.executeReset(userId, displayName, secretKey, metadata);
 *   if (result.success) {
 *     // Grant admin privileges
 *   } else {
 *     // Failed attempt logged
 *   }
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');
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

// Paths and keys
const WHITELIST_PATH = path.join(__dirname, '../config/whitelist.json');
const REDIS_AUDIT_KEY = 'audit:admin_resets';
const REDIS_FAILED_ATTEMPTS_KEY = 'security:admin_reset_failures';

// Load secret from environment
const ADMIN_RESET_SECRET = process.env.ADMIN_RESET_SECRET;

/**
 * Execute admin reset command
 * @param {string} userId - User ID requesting reset
 * @param {string} displayName - User display name
 * @param {string} providedSecret - Secret key provided by user
 * @param {object} metadata - Additional metadata (ip_address, team_id, etc.)
 * @returns {Promise<object>} Result object
 */
async function executeReset(userId, displayName, providedSecret, metadata = {}) {
  const timestamp = new Date().toISOString();
  const ipAddress = metadata.ip_address || 'unknown';

  try {
    // Validate secret key
    const isValid = validateSecret(providedSecret);

    // Log attempt (MANDATORY - both success and failure)
    await logResetAttempt(userId, displayName, isValid, ipAddress, timestamp, metadata);

    if (!isValid) {
      // Track failed attempts
      await trackFailedAttempt(userId, ipAddress);

      return {
        success: false,
        message: 'Invalid reset key', // Generic error - no hints
        timestamp,
        logged: true
      };
    }

    // Valid secret - grant admin privileges
    const whitelist = await readWhitelist();

    // Add user to admins if not already present
    if (!whitelist.admins) {
      whitelist.admins = [];
    }

    if (!whitelist.admins.includes(userId)) {
      whitelist.admins.push(userId);
      await writeWhitelist(whitelist);
    }

    return {
      success: true,
      message: 'Admin privileges granted. This action has been logged.',
      userId,
      displayName,
      timestamp,
      logged: true
    };

  } catch (error) {
    console.error('Admin reset error:', error);

    // Log error attempt
    await logResetAttempt(userId, displayName, false, ipAddress, timestamp, {
      ...metadata,
      error: error.message
    });

    return {
      success: false,
      message: 'An error occurred processing your request',
      error: error.message,
      logged: true
    };
  }
}

/**
 * Validate provided secret against stored secret
 * @param {string} providedSecret - Secret provided by user
 * @returns {boolean} True if valid
 */
function validateSecret(providedSecret) {
  if (!ADMIN_RESET_SECRET) {
    console.error('ADMIN_RESET_SECRET not configured in environment');
    return false;
  }

  if (!providedSecret || typeof providedSecret !== 'string') {
    return false;
  }

  // Constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(providedSecret.padEnd(64, '0')),
    Buffer.from(ADMIN_RESET_SECRET.padEnd(64, '0'))
  );
}

/**
 * Log reset attempt to Redis audit trail
 * @param {string} userId - User ID
 * @param {string} displayName - User display name
 * @param {boolean} success - Whether attempt was successful
 * @param {string} ipAddress - IP address (if available)
 * @param {string} timestamp - ISO timestamp
 * @param {object} metadata - Additional metadata
 */
async function logResetAttempt(userId, displayName, success, ipAddress, timestamp, metadata = {}) {
  const auditEntry = {
    timestamp,
    event_type: 'admin_reset_attempt',
    user_id: userId,
    display_name: displayName,
    success,
    ip_address: ipAddress,
    team_id: metadata.team_id || 'unknown',
    channel_id: metadata.channel_id || 'unknown',
    // DO NOT log the actual secret key value
    metadata: {
      user_agent: metadata.user_agent,
      error: metadata.error
    }
  };

  // Store in Redis list
  await redis.lpush(REDIS_AUDIT_KEY, JSON.stringify(auditEntry));

  // Maintain max 1000 entries
  await redis.ltrim(REDIS_AUDIT_KEY, 0, 999);

  // 90-day retention for compliance
  await redis.expire(REDIS_AUDIT_KEY, 86400 * 90);
}

/**
 * Track failed reset attempts for security monitoring
 * @param {string} userId - User ID
 * @param {string} ipAddress - IP address
 */
async function trackFailedAttempt(userId, ipAddress) {
  const key = `${REDIS_FAILED_ATTEMPTS_KEY}:${userId}`;

  // Increment failure count
  await redis.incr(key);

  // Set 1-hour expiry
  await redis.expire(key, 3600);

  // Check if threshold exceeded
  const count = await redis.get(key);
  if (parseInt(count) >= 5) {
    console.warn(`⚠️ Security Alert: User ${userId} exceeded 5 failed admin reset attempts`);

    // Could trigger additional security measures:
    // - Send alert to admin channel
    // - Temporarily block user
    // - Require CAPTCHA
  }
}

/**
 * Read whitelist configuration
 * @returns {Promise<object>} Whitelist object
 */
async function readWhitelist() {
  try {
    const data = await fs.readFile(WHITELIST_PATH, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.warn('Whitelist not found or invalid:', error.message);
    return { admins: [], channels: [] };
  }
}

/**
 * Write whitelist configuration
 * @param {object} whitelist - Whitelist object
 */
async function writeWhitelist(whitelist) {
  const data = JSON.stringify(whitelist, null, 2);
  await fs.writeFile(WHITELIST_PATH, data, 'utf8');
}

/**
 * Get reset audit trail
 * @param {number} limit - Max number of entries to return (default: 100)
 * @returns {Promise<array>} Array of audit entries
 */
async function getResetAuditTrail(limit = 100) {
  try {
    const entries = await redis.lrange(REDIS_AUDIT_KEY, 0, limit - 1);
    return entries.map(e => JSON.parse(e));
  } catch (error) {
    console.error('Error retrieving audit trail:', error);
    return [];
  }
}

/**
 * Get failed attempts count for a user
 * @param {string} userId - User ID
 * @returns {Promise<number>} Number of failed attempts in last hour
 */
async function getFailedAttemptsCount(userId) {
  try {
    const key = `${REDIS_FAILED_ATTEMPTS_KEY}:${userId}`;
    const count = await redis.get(key);
    return parseInt(count) || 0;
  } catch (error) {
    return 0;
  }
}

/**
 * Generate a new admin reset secret
 * @returns {string} 64-character hex string
 */
function generateSecret() {
  return crypto.randomBytes(32).toString('hex');
}

/**
 * Close Redis connection
 */
async function close() {
  await redis.quit();
}

module.exports = {
  executeReset,
  getResetAuditTrail,
  getFailedAttemptsCount,
  generateSecret,
  close
};
