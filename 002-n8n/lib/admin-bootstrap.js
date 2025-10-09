/**
 * First-User-Admin Bootstrap Logic
 *
 * Automatically grants admin privileges to the first user who interacts with the bot
 * when no admins are configured.
 *
 * Security Features:
 * - Only works when admins array is completely empty
 * - Creates audit trail in Redis
 * - Sets permanent flag to prevent re-bootstrap
 * - Logs bootstrap event with user details
 *
 * Usage in n8n Function node:
 *   const bootstrap = require('./lib/admin-bootstrap');
 *   const result = await bootstrap.checkAndBootstrap(userId, displayName);
 *   if (result.bootstrapped) {
 *     // Send welcome message to new admin
 *   }
 */

const fs = require('fs').promises;
const path = require('path');
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

// Paths
const WHITELIST_PATH = path.join(__dirname, '../config/whitelist.json');
const REDIS_BOOTSTRAP_KEY = 'system:admin_bootstrapped';
const REDIS_AUDIT_KEY = 'audit:admin_bootstrap';

/**
 * Check if admin bootstrap is needed and execute if required
 * @param {string} userId - User ID (Slack user ID)
 * @param {string} displayName - User display name
 * @param {object} metadata - Additional metadata (team_id, channel_id, etc.)
 * @returns {Promise<object>} Result object
 */
async function checkAndBootstrap(userId, displayName, metadata = {}) {
  try {
    // Step 1: Check if bootstrap already occurred
    const bootstrapFlag = await redis.get(REDIS_BOOTSTRAP_KEY);
    if (bootstrapFlag === 'true') {
      return {
        bootstrapped: false,
        alreadyBootstrapped: true,
        message: 'Admin bootstrap already completed'
      };
    }

    // Step 2: Read current whitelist
    const whitelist = await readWhitelist();

    // Step 3: Check if admins array is empty
    if (!whitelist.admins || whitelist.admins.length === 0) {
      // Bootstrap: Grant admin to first user
      whitelist.admins = [userId];

      // Save updated whitelist
      await writeWhitelist(whitelist);

      // Set bootstrap flag in Redis (permanent, no TTL)
      await redis.set(REDIS_BOOTSTRAP_KEY, 'true');

      // Log bootstrap event
      await logBootstrapEvent(userId, displayName, metadata);

      return {
        bootstrapped: true,
        userId,
        displayName,
        message: `You are now the bot admin. Use /admin grant @user to add more admins.`,
        timestamp: new Date().toISOString()
      };
    }

    // Admins already exist
    return {
      bootstrapped: false,
      adminsExist: true,
      adminCount: whitelist.admins.length,
      message: 'Admin bootstrap not needed (admins already configured)'
    };

  } catch (error) {
    console.error('Bootstrap error:', error);
    return {
      bootstrapped: false,
      error: error.message
    };
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
    // If file doesn't exist or is invalid, return default
    console.warn('Whitelist not found or invalid, creating new:', error.message);
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
 * Log bootstrap event to Redis audit trail
 * @param {string} userId - User ID
 * @param {string} displayName - User display name
 * @param {object} metadata - Additional metadata
 */
async function logBootstrapEvent(userId, displayName, metadata = {}) {
  const event = {
    timestamp: new Date().toISOString(),
    event_type: 'admin_bootstrap',
    user_id: userId,
    display_name: displayName,
    team_id: metadata.team_id || 'unknown',
    channel_id: metadata.channel_id || 'unknown',
    message: 'First user automatically granted admin privileges'
  };

  // Store as JSON string in Redis list
  await redis.lpush(REDIS_AUDIT_KEY, JSON.stringify(event));

  // Keep only last 100 bootstrap events
  await redis.ltrim(REDIS_AUDIT_KEY, 0, 99);

  // Set 90-day retention (compliance)
  await redis.expire(REDIS_AUDIT_KEY, 86400 * 90);
}

/**
 * Check if user is admin
 * @param {string} userId - User ID to check
 * @returns {Promise<boolean>} True if user is admin
 */
async function isAdmin(userId) {
  try {
    const whitelist = await readWhitelist();
    return whitelist.admins && whitelist.admins.includes(userId);
  } catch (error) {
    console.error('Error checking admin status:', error);
    return false;
  }
}

/**
 * Get bootstrap status
 * @returns {Promise<object>} Bootstrap status
 */
async function getBootstrapStatus() {
  try {
    const bootstrapFlag = await redis.get(REDIS_BOOTSTRAP_KEY);
    const whitelist = await readWhitelist();

    return {
      bootstrapped: bootstrapFlag === 'true',
      adminCount: whitelist.admins?.length || 0,
      admins: whitelist.admins || []
    };
  } catch (error) {
    return {
      error: error.message
    };
  }
}

/**
 * Get bootstrap audit trail
 * @returns {Promise<array>} Array of bootstrap events
 */
async function getBootstrapAuditTrail() {
  try {
    const events = await redis.lrange(REDIS_AUDIT_KEY, 0, -1);
    return events.map(e => JSON.parse(e));
  } catch (error) {
    console.error('Error retrieving audit trail:', error);
    return [];
  }
}

/**
 * Close Redis connection
 */
async function close() {
  await redis.quit();
}

module.exports = {
  checkAndBootstrap,
  isAdmin,
  getBootstrapStatus,
  getBootstrapAuditTrail,
  close
};
