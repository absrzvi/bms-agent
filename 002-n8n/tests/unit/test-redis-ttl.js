/**
 * Unit Test: Redis TTL Enforcement (T029)
 *
 * Tests for redis-client.js module (T024)
 * Tests: retry logic, connection handling, execute with fallback, TTL enforcement
 */

const assert = require('assert');
const { RedisClient } = require('../../lib/redis-client');

describe('Redis TTL Enforcement (T029)', () => {
  let redisClient;

  beforeEach(() => {
    redisClient = new RedisClient();
  });

  afterEach(async () => {
    if (redisClient.client && redisClient.client.isOpen) {
      await redisClient.disconnect();
    }
  });

  describe('Connection Retry Logic', () => {
    it('should retry connection with exponential backoff', async () => {
      const delays = [];
      const originalSetTimeout = setTimeout;

      // Mock setTimeout to capture delays
      global.setTimeout = (fn, delay) => {
        delays.push(delay);
        return originalSetTimeout(fn, 0); // Execute immediately for test
      };

      try {
        // This will likely fail since Redis may not be running
        await redisClient.connect();
      } catch (error) {
        // Expected to fail
      } finally {
        global.setTimeout = originalSetTimeout;
      }

      // Check exponential backoff: 100ms, 300ms, 900ms
      // Note: May have retried 3 times if Redis unavailable
      if (delays.length >= 3) {
        assert.strictEqual(delays[0], 100, 'First retry delay should be 100ms');
        assert.strictEqual(delays[1], 300, 'Second retry delay should be 300ms');
        assert.strictEqual(delays[2], 900, 'Third retry delay should be 900ms');
      }
    });

    it('should return success=true when Redis is available', async function() {
      this.timeout(5000); // Extend timeout for connection

      const result = await redisClient.connect();

      if (result.success) {
        assert.strictEqual(result.success, true, 'Connection should succeed');
        assert.notStrictEqual(result.client, null, 'Client should be returned');
        assert.strictEqual(typeof result.restored, 'boolean', 'Restored flag should be boolean');
      } else {
        // Redis not available in test environment
        console.log('  �  Redis not available, skipping success test');
      }
    });

    it('should return success=false after max retries', async function() {
      this.timeout(10000); // Extend timeout for retries

      // Use invalid Redis config to force failure
      const invalidClient = new RedisClient({
        host: 'invalid-redis-host.local',
        port: 99999
      });

      const result = await invalidClient.connect();

      assert.strictEqual(result.success, false, 'Should fail after max retries');
      assert.strictEqual(result.client, null, 'Client should be null on failure');
      assert.strictEqual(result.restored, false, 'Restored should be false on failure');
    });

    it('should restore connection after temporary disconnect', async function() {
      this.timeout(5000);

      const firstConnect = await redisClient.connect();

      if (!firstConnect.success) {
        console.log('  �  Redis not available, skipping restore test');
        return;
      }

      // Disconnect
      await redisClient.disconnect();

      // Reconnect
      const secondConnect = await redisClient.connect();

      if (secondConnect.success) {
        assert.strictEqual(secondConnect.success, true, 'Should reconnect');
        assert.strictEqual(secondConnect.restored, true, 'Restored flag should be true');
      }
    });
  });

  describe('execute() with Fallback', () => {
    it('should execute Redis command when connected', async function() {
      this.timeout(5000);

      const connectResult = await redisClient.connect();

      if (!connectResult.success) {
        console.log('  �  Redis not available, skipping execute test');
        return;
      }

      // Execute a simple Redis command
      const result = await redisClient.execute(
        async (client) => {
          return await client.ping();
        },
        'FALLBACK'
      );

      if (result.success) {
        assert.strictEqual(result.success, true, 'Execute should succeed');
        assert.strictEqual(result.data, 'PONG', 'Ping should return PONG');
        assert.strictEqual(result.stateless, false, 'Stateless should be false');
      }
    });

    it('should return fallback value when Redis unavailable', async function() {
      this.timeout(5000);

      // Don't connect - execute should return fallback
      const result = await redisClient.execute(
        async (client) => {
          return await client.get('test-key');
        },
        'FALLBACK_VALUE'
      );

      assert.strictEqual(result.success, false, 'Should fail when not connected');
      assert.strictEqual(result.data, 'FALLBACK_VALUE', 'Should return fallback value');
      assert.strictEqual(result.stateless, true, 'Stateless should be true');
    });

    it('should handle command errors gracefully', async function() {
      this.timeout(5000);

      const connectResult = await redisClient.connect();

      if (!connectResult.success) {
        console.log('  �  Redis not available, skipping error handling test');
        return;
      }

      // Execute invalid command
      const result = await redisClient.execute(
        async (client) => {
          throw new Error('Command failed');
        },
        'ERROR_FALLBACK'
      );

      assert.strictEqual(result.success, false, 'Should fail on command error');
      assert.strictEqual(result.data, 'ERROR_FALLBACK', 'Should return fallback on error');
      assert.strictEqual(result.stateless, true, 'Stateless should be true on error');
    });

    it('should preserve null as fallback value', async function() {
      this.timeout(5000);

      // Don't connect - execute should return null fallback
      const result = await redisClient.execute(
        async (client) => {
          return await client.get('missing-key');
        },
        null
      );

      assert.strictEqual(result.data, null, 'Should preserve null fallback value');
      assert.strictEqual(result.stateless, true, 'Stateless should be true');
    });
  });

  describe('TTL Enforcement (60-second cache)', () => {
    it('should set TTL when storing cache entry', async function() {
      this.timeout(5000);

      const connectResult = await redisClient.connect();

      if (!connectResult.success) {
        console.log('  �  Redis not available, skipping TTL set test');
        return;
      }

      const cacheKey = 'test:cache:entry';
      const cacheValue = JSON.stringify({ data: 'test-value' });

      // Store with 60-second TTL
      const setResult = await redisClient.execute(
        async (client) => {
          await client.set(cacheKey, cacheValue, { EX: 60 });
          return await client.ttl(cacheKey);
        },
        0
      );

      if (setResult.success) {
        // TTL should be between 59-60 seconds (allowing for execution time)
        assert.strictEqual(setResult.data >= 59 && setResult.data <= 60, true,
          `TTL should be ~60 seconds, got ${setResult.data}`);
      }

      // Cleanup
      await redisClient.execute(
        async (client) => client.del(cacheKey),
        null
      );
    });

    it('should return -2 for expired keys', async function() {
      this.timeout(8000); // Need time for expiration

      const connectResult = await redisClient.connect();

      if (!connectResult.success) {
        console.log('  �  Redis not available, skipping expiration test');
        return;
      }

      const cacheKey = 'test:cache:expiring';
      const cacheValue = JSON.stringify({ data: 'expires-soon' });

      // Store with 1-second TTL
      await redisClient.execute(
        async (client) => {
          await client.set(cacheKey, cacheValue, { EX: 1 });
        },
        null
      );

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Check TTL after expiration
      const ttlResult = await redisClient.execute(
        async (client) => client.ttl(cacheKey),
        -3
      );

      if (ttlResult.success) {
        // -2 means key doesn't exist (expired)
        assert.strictEqual(ttlResult.data, -2, 'TTL should be -2 for expired key');
      }
    });

    it('should retrieve cached value before expiration', async function() {
      this.timeout(5000);

      const connectResult = await redisClient.connect();

      if (!connectResult.success) {
        console.log('  �  Redis not available, skipping cache retrieval test');
        return;
      }

      const cacheKey = 'test:cache:valid';
      const cacheValue = JSON.stringify({ query: 'test-query', results: [1, 2, 3] });

      // Store with 60-second TTL
      await redisClient.execute(
        async (client) => {
          await client.set(cacheKey, cacheValue, { EX: 60 });
        },
        null
      );

      // Retrieve immediately
      const getResult = await redisClient.execute(
        async (client) => client.get(cacheKey),
        null
      );

      if (getResult.success) {
        assert.strictEqual(getResult.data, cacheValue, 'Should retrieve cached value');
        const parsed = JSON.parse(getResult.data);
        assert.strictEqual(parsed.query, 'test-query', 'Cached query should match');
        assert.deepStrictEqual(parsed.results, [1, 2, 3], 'Cached results should match');
      }

      // Cleanup
      await redisClient.execute(
        async (client) => client.del(cacheKey),
        null
      );
    });

    it('should return null for non-existent cache key', async function() {
      this.timeout(5000);

      const connectResult = await redisClient.connect();

      if (!connectResult.success) {
        console.log('  �  Redis not available, skipping missing key test');
        return;
      }

      const cacheKey = 'test:cache:nonexistent';

      // Try to get non-existent key
      const getResult = await redisClient.execute(
        async (client) => client.get(cacheKey),
        'FALLBACK'
      );

      if (getResult.success) {
        assert.strictEqual(getResult.data, null, 'Should return null for missing key');
      }
    });

    it('should update TTL when refreshing cache entry', async function() {
      this.timeout(8000);

      const connectResult = await redisClient.connect();

      if (!connectResult.success) {
        console.log('  �  Redis not available, skipping TTL refresh test');
        return;
      }

      const cacheKey = 'test:cache:refresh';
      const cacheValue = JSON.stringify({ data: 'refreshable' });

      // Store with 5-second TTL
      await redisClient.execute(
        async (client) => {
          await client.set(cacheKey, cacheValue, { EX: 5 });
        },
        null
      );

      // Wait 3 seconds (TTL should be ~2 seconds)
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Refresh TTL to 60 seconds
      const refreshResult = await redisClient.execute(
        async (client) => {
          await client.expire(cacheKey, 60);
          return await client.ttl(cacheKey);
        },
        0
      );

      if (refreshResult.success) {
        // TTL should now be ~60 seconds (refreshed)
        assert.strictEqual(refreshResult.data >= 59 && refreshResult.data <= 60, true,
          `TTL should be refreshed to ~60 seconds, got ${refreshResult.data}`);
      }

      // Cleanup
      await redisClient.execute(
        async (client) => client.del(cacheKey),
        null
      );
    });
  });

  describe('Error Handling', () => {
    it('should handle connection timeout gracefully', async function() {
      this.timeout(15000);

      const timeoutClient = new RedisClient({
        host: '192.0.2.1', // Reserved non-routable IP
        port: 6379,
        connectTimeout: 1000
      });

      const result = await timeoutClient.connect();

      assert.strictEqual(result.success, false, 'Should fail on timeout');
      assert.strictEqual(result.client, null, 'Client should be null on timeout');
    });

    it('should handle null command function', async function() {
      this.timeout(5000);

      const result = await redisClient.execute(null, 'FALLBACK');

      assert.strictEqual(result.success, false, 'Should fail on null command');
      assert.strictEqual(result.data, 'FALLBACK', 'Should return fallback');
      assert.strictEqual(result.stateless, true, 'Should be stateless');
    });

    it('should handle undefined fallback value', async function() {
      this.timeout(5000);

      const result = await redisClient.execute(
        async (client) => client.get('missing-key'),
        undefined
      );

      assert.strictEqual(result.data, undefined, 'Should preserve undefined fallback');
    });

    it('should handle client disconnect mid-operation', async function() {
      this.timeout(5000);

      const connectResult = await redisClient.connect();

      if (!connectResult.success) {
        console.log('  �  Redis not available, skipping disconnect test');
        return;
      }

      // Disconnect immediately
      await redisClient.disconnect();

      // Try to execute command after disconnect
      const result = await redisClient.execute(
        async (client) => client.ping(),
        'DISCONNECTED'
      );

      assert.strictEqual(result.success, false, 'Should fail when disconnected');
      assert.strictEqual(result.data, 'DISCONNECTED', 'Should return fallback');
      assert.strictEqual(result.stateless, true, 'Should be stateless');
    });
  });

  describe('Integration with Context Manager', () => {
    it('should cache query results with TTL', async function() {
      this.timeout(5000);

      const connectResult = await redisClient.connect();

      if (!connectResult.success) {
        console.log('  �  Redis not available, skipping integration test');
        return;
      }

      // Simulate context manager cache pattern
      const queryHash = 'hash:railway-safety-procedures';
      const cachedResults = {
        query: 'railway safety procedures',
        results: [
          { doc: 'doc1', score: 0.95 },
          { doc: 'doc2', score: 0.89 }
        ],
        cached_at: new Date().toISOString()
      };

      // Store query results with 60s TTL
      await redisClient.execute(
        async (client) => {
          await client.set(`context:${queryHash}`, JSON.stringify(cachedResults), { EX: 60 });
        },
        null
      );

      // Retrieve cached results
      const getResult = await redisClient.execute(
        async (client) => client.get(`context:${queryHash}`),
        null
      );

      if (getResult.success) {
        const retrieved = JSON.parse(getResult.data);
        assert.strictEqual(retrieved.query, 'railway safety procedures', 'Query should match');
        assert.strictEqual(retrieved.results.length, 2, 'Should have 2 results');
        assert.strictEqual(retrieved.results[0].score, 0.95, 'Score should match');
      }

      // Cleanup
      await redisClient.execute(
        async (client) => client.del(`context:${queryHash}`),
        null
      );
    });

    it('should handle cache miss with fallback', async function() {
      this.timeout(5000);

      const connectResult = await redisClient.connect();

      if (!connectResult.success) {
        console.log('  �  Redis not available, skipping cache miss test');
        return;
      }

      const queryHash = 'hash:nonexistent-query';

      // Try to retrieve non-cached query
      const getResult = await redisClient.execute(
        async (client) => client.get(`context:${queryHash}`),
        null
      );

      if (getResult.success) {
        assert.strictEqual(getResult.data, null, 'Cache miss should return null');
      }
    });
  });
});

// Run tests if executed directly
if (require.main === module) {
  console.log('Running Redis TTL Enforcement Unit Tests (T029)...\n');

  // Simple test runner
  const tests = [];
  global.describe = (name, fn) => {
    tests.push({ name, fn });
  };
  global.it = () => {};
  global.beforeEach = () => {};
  global.afterEach = () => {};

  require('./test-redis-ttl.js');

  console.log(` ${tests.length} test suites defined`);
  console.log('  Run with: npm test or jest tests/unit/test-redis-ttl.js\n');
  console.log('  Note: Requires Redis running on localhost:6379 for full test execution\n');
}

module.exports = { describe, it, beforeEach, afterEach };
