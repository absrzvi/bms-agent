/**
 * Redis Client with Retry Logic and Stateless Fallback (T024)
 *
 * Purpose: Shared Redis connection module with exponential backoff retry
 * Used by: context-manager workflow, admin-commands workflow
 * NFR-002: Falls back to stateless mode if Redis unavailable
 */

const redis = require('redis');

class RedisClient {
  constructor() {
    this.client = null;
    this.isConnected = false;
    this.retryAttempts = 0;
    this.maxRetries = 3;
    this.wasDown = false; // Track if storage was previously unavailable (NFR-002a)
  }

  /**
   * Connect to Redis with retry strategy
   * @returns {Promise<Object>} { success: boolean, client: RedisClient|null, restored: boolean }
   */
  async connect() {
    const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';

    try {
      // Create client with retry strategy
      this.client = redis.createClient({
        url: redisUrl,
        socket: {
          reconnectStrategy: (retries) => {
            this.retryAttempts = retries;

            // Give up after max retries (NFR-002 fallback)
            if (retries >= this.maxRetries) {
              this.wasDown = true;
              console.error('[Redis] Max retries reached, switching to stateless mode');
              return new Error('Redis unavailable, using stateless mode');
            }

            // Exponential backoff: 100ms, 300ms, 900ms
            const delay = Math.min(retries * 100 * Math.pow(3, retries - 1), 3000);
            console.log(`[Redis] Retry attempt ${retries}/${this.maxRetries}, waiting ${delay}ms`);
            return delay;
          }
        }
      });

      // Handle connection events
      this.client.on('error', (err) => {
        console.error('[Redis] Connection error:', err.message);
        this.isConnected = false;
        this.wasDown = true;
      });

      this.client.on('connect', () => {
        console.log('[Redis] Connected successfully');
        this.isConnected = true;
        this.retryAttempts = 0;
      });

      this.client.on('ready', () => {
        console.log('[Redis] Client ready for commands');
      });

      // Attempt connection
      await this.client.connect();

      // Check if this is a restoration after downtime (NFR-002a)
      const wasDownBefore = this.wasDown;
      this.wasDown = false;

      return {
        success: true,
        client: this.client,
        restored: wasDownBefore && this.isConnected
      };

    } catch (error) {
      console.error('[Redis] Connection failed:', error.message);
      this.isConnected = false;
      this.wasDown = true;

      // Return stateless mode error for NFR-002
      return {
        success: false,
        client: null,
        restored: false,
        error: 'Redis unavailable, using stateless mode'
      };
    }
  }

  /**
   * Execute Redis command with fallback handling
   * @param {Function} commandFn - Async function that executes Redis command
   * @param {*} fallbackValue - Value to return if Redis unavailable
   * @returns {Promise<{success: boolean, data: any, stateless: boolean, restored: boolean}>}
   */
  async execute(commandFn, fallbackValue = null) {
    // Try to connect if not connected
    if (!this.isConnected) {
      const result = await this.connect();
      if (!result.success) {
        return {
          success: false,
          data: fallbackValue,
          stateless: true,
          restored: false,
          error: result.error
        };
      }

      // Return restoration flag if storage was restored
      if (result.restored) {
        const data = await commandFn(this.client);
        return {
          success: true,
          data,
          stateless: false,
          restored: true
        };
      }
    }

    try {
      const data = await commandFn(this.client);
      return {
        success: true,
        data,
        stateless: false,
        restored: false
      };
    } catch (error) {
      console.error('[Redis] Command execution failed:', error.message);
      this.isConnected = false;
      this.wasDown = true;

      // Fall back to stateless mode
      return {
        success: false,
        data: fallbackValue,
        stateless: true,
        restored: false,
        error: error.message
      };
    }
  }

  /**
   * Disconnect from Redis
   */
  async disconnect() {
    if (this.client) {
      await this.client.quit();
      this.isConnected = false;
      console.log('[Redis] Disconnected');
    }
  }

  /**
   * Get connection status
   * @returns {boolean}
   */
  getStatus() {
    return this.isConnected;
  }
}

// Singleton instance
let redisClientInstance = null;

/**
 * Get or create Redis client instance
 * @returns {RedisClient}
 */
function getRedisClient() {
  if (!redisClientInstance) {
    redisClientInstance = new RedisClient();
  }
  return redisClientInstance;
}

module.exports = {
  RedisClient,
  getRedisClient
};
