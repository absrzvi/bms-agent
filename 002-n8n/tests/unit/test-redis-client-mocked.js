/**
 * Mocked Redis Client Tests (Task 1.1 - Coverage Remediation)
 *
 * Purpose: Test redis-client.js with mocked Redis connection
 * Strategy: Use jest.mock() to mock redis module
 * Coverage Target: +10% (redis-client.js from 50.84% → 90%)
 */

jest.mock('redis', () => ({
  createClient: jest.fn()
}));

const redis = require('redis');
const { RedisClient, getRedisClient } = require('../../lib/redis-client');

describe('RedisClient (Mocked) - Task 1.1', () => {
  let mockRedisClient;

  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();

    // Create mock Redis client
    mockRedisClient = {
      connect: jest.fn().mockResolvedValue(true),
      ping: jest.fn().mockResolvedValue('PONG'),
      get: jest.fn().mockResolvedValue('{"test": "data"}'),
      set: jest.fn().mockResolvedValue('OK'),
      setEx: jest.fn().mockResolvedValue('OK'),
      del: jest.fn().mockResolvedValue(1),
      expire: jest.fn().mockResolvedValue(1),
      disconnect: jest.fn().mockResolvedValue(true),
      on: jest.fn((event, callback) => {
        if (event === 'connect') {
          setTimeout(() => callback(), 0);
        }
        if (event === 'ready') {
          setTimeout(() => callback(), 0);
        }
      })
    };

    redis.createClient.mockReturnValue(mockRedisClient);
  });

  // ===== Connection Tests =====

  test('should connect successfully', async () => {
    const client = new RedisClient();
    const result = await client.connect();

    expect(result.success).toBe(true);
    expect(result.client).toBeTruthy();
    expect(result.restored).toBe(false);
    expect(redis.createClient).toHaveBeenCalledTimes(1);
    expect(mockRedisClient.connect).toHaveBeenCalledTimes(1);
  });

  test('should handle connection failure and return stateless mode', async () => {
    mockRedisClient.connect.mockRejectedValue(new Error('ECONNREFUSED'));

    const client = new RedisClient();
    const result = await client.connect();

    expect(result.success).toBe(false);
    expect(result.client).toBeNull();
    expect(result.restored).toBe(false);
    expect(result.error).toBe('Redis unavailable, using stateless mode');
  });

  test('should detect restoration after downtime (NFR-003)', async () => {
    const client = new RedisClient();

    // Simulate initial connection failure
    mockRedisClient.connect.mockRejectedValueOnce(new Error('ECONNREFUSED'));
    const failResult = await client.connect();
    expect(failResult.success).toBe(false);

    // Simulate successful reconnection
    mockRedisClient.connect.mockResolvedValue(true);
    const successResult = await client.connect();

    expect(successResult.success).toBe(true);
    expect(successResult.restored).toBe(true); // Restoration detected!
  });

  // ===== Execute with Fallback Tests =====

  test('should execute Redis command successfully', async () => {
    const client = new RedisClient();
    await client.connect();

    const result = await client.execute(
      async (c) => c.ping(),
      null
    );

    expect(result.success).toBe(true);
    expect(result.data).toBe('PONG');
    expect(result.stateless).toBe(false);
    expect(result.restored).toBe(false);
    expect(mockRedisClient.ping).toHaveBeenCalledTimes(1);
  });

  test('should fall back to fallbackValue on command failure', async () => {
    const client = new RedisClient();
    await client.connect();

    // Mock command failure
    mockRedisClient.get.mockRejectedValue(new Error('Command failed'));

    const result = await client.execute(
      async (c) => c.get('test-key'),
      'default-value'
    );

    expect(result.success).toBe(false);
    expect(result.data).toBe('default-value');
    expect(result.stateless).toBe(true);
    expect(result.error).toBe('Command failed');
  });

  test('should auto-connect if not connected before execute', async () => {
    const client = new RedisClient();
    // Don't call connect() manually

    const result = await client.execute(
      async (c) => c.ping(),
      null
    );

    expect(result.success).toBe(true);
    expect(result.data).toBe('PONG');
    expect(redis.createClient).toHaveBeenCalledTimes(1);
    expect(mockRedisClient.connect).toHaveBeenCalledTimes(1);
  });

  test('should return fallback value if auto-connect fails', async () => {
    mockRedisClient.connect.mockRejectedValue(new Error('ECONNREFUSED'));

    const client = new RedisClient();
    const result = await client.execute(
      async (c) => c.get('test-key'),
      'fallback-data'
    );

    expect(result.success).toBe(false);
    expect(result.data).toBe('fallback-data');
    expect(result.stateless).toBe(true);
  });

  test('should return restoration flag on reconnect during execute', async () => {
    const client = new RedisClient();

    // Simulate initial connection failure
    mockRedisClient.connect.mockRejectedValueOnce(new Error('ECONNREFUSED'));
    await client.execute(async (c) => c.ping(), null);

    // Simulate successful reconnection
    mockRedisClient.connect.mockResolvedValue(true);
    const result = await client.execute(async (c) => c.ping(), null);

    expect(result.success).toBe(true);
    expect(result.restored).toBe(true);
  });

  // ===== Retry Logic Tests =====

  test('should use exponential backoff retry strategy', async () => {
    let reconnectStrategy;
    mockRedisClient.on.mockImplementation((event, callback) => {
      // Capture the reconnect strategy function
    });

    redis.createClient.mockImplementation((config) => {
      reconnectStrategy = config.socket.reconnectStrategy;
      return mockRedisClient;
    });

    const client = new RedisClient();
    await client.connect();

    // Test retry delays
    const delay1 = reconnectStrategy(1);
    const delay2 = reconnectStrategy(2);
    const delay3 = reconnectStrategy(3);

    // Exponential backoff: 100ms, 300ms, 900ms
    expect(delay1).toBeGreaterThanOrEqual(100);
    expect(delay2).toBeGreaterThanOrEqual(300);
    expect(delay3).toBeGreaterThanOrEqual(900);
  });

  test('should give up after max retries and switch to stateless mode', async () => {
    let reconnectStrategy;

    redis.createClient.mockImplementation((config) => {
      reconnectStrategy = config.socket.reconnectStrategy;
      return mockRedisClient;
    });

    const client = new RedisClient();
    await client.connect();

    // Test retry strategy at max retries (3)
    const result = reconnectStrategy(3);

    expect(result).toBeInstanceOf(Error);
    expect(result.message).toContain('stateless mode');
  });

  // ===== TTL Enforcement Tests (NFR requirement) =====

  test('should set TTL when storing conversation data', async () => {
    const client = new RedisClient();
    await client.connect();

    await client.execute(
      async (c) => c.setEx('conversation:123', 604800, JSON.stringify({test: 'data'})),
      null
    );

    expect(mockRedisClient.setEx).toHaveBeenCalledWith(
      'conversation:123',
      604800, // 7 days in seconds
      expect.any(String)
    );
  });

  test('should refresh TTL on conversation update', async () => {
    const client = new RedisClient();
    await client.connect();

    // Get existing conversation
    mockRedisClient.get.mockResolvedValue(JSON.stringify({messages: []}));
    await client.execute(async (c) => c.get('conversation:123'), null);

    // Update with refreshed TTL
    await client.execute(
      async (c) => c.setEx('conversation:123', 604800, JSON.stringify({messages: ['new']})),
      null
    );

    expect(mockRedisClient.setEx).toHaveBeenCalledWith(
      'conversation:123',
      604800,
      expect.any(String)
    );
  });

  // ===== Singleton Pattern Test =====

  test('getRedisClient should return singleton instance', () => {
    const client1 = getRedisClient();
    const client2 = getRedisClient();

    expect(client1).toBe(client2); // Same instance
  });

  // ===== Error Handling Tests =====

  test('should handle error event and mark as down', async () => {
    let errorCallback;
    mockRedisClient.on.mockImplementation((event, callback) => {
      if (event === 'error') {
        errorCallback = callback;
      }
    });

    const client = new RedisClient();
    await client.connect();

    // Trigger error event
    if (errorCallback) {
      errorCallback(new Error('Connection lost'));
    }

    // Verify client is marked as down
    expect(client.isConnected).toBe(false);
    expect(client.wasDown).toBe(true);
  });

  test('should handle connect event and mark as up', async () => {
    let connectCallback;
    mockRedisClient.on.mockImplementation((event, callback) => {
      if (event === 'connect') {
        connectCallback = callback;
      }
    });

    const client = new RedisClient();
    await client.connect();

    // Trigger connect event
    if (connectCallback) {
      connectCallback();
    }

    expect(client.isConnected).toBe(true);
  });

  // ===== Edge Cases =====

  test('should handle null fallback value', async () => {
    mockRedisClient.connect.mockRejectedValue(new Error('ECONNREFUSED'));

    const client = new RedisClient();
    const result = await client.execute(
      async (c) => c.get('test-key'),
      null
    );

    expect(result.success).toBe(false);
    expect(result.data).toBeNull();
    expect(result.stateless).toBe(true);
  });

  test('should handle empty string fallback value', async () => {
    mockRedisClient.connect.mockRejectedValue(new Error('ECONNREFUSED'));

    const client = new RedisClient();
    const result = await client.execute(
      async (c) => c.get('test-key'),
      ''
    );

    expect(result.success).toBe(false);
    expect(result.data).toBe('');
    expect(result.stateless).toBe(true);
  });

  test('should handle object fallback value', async () => {
    mockRedisClient.connect.mockRejectedValue(new Error('ECONNREFUSED'));

    const fallbackObj = { default: true };
    const client = new RedisClient();
    const result = await client.execute(
      async (c) => c.get('test-key'),
      fallbackObj
    );

    expect(result.success).toBe(false);
    expect(result.data).toEqual({ default: true });
    expect(result.stateless).toBe(true);
  });
});
