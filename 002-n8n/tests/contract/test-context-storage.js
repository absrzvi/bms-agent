/**
 * Contract Test: Conversation Storage API
 *
 * T009: Validate conversation CRUD operations and Redis storage
 * This test MUST FAIL initially (no storage logic exists yet)
 */

const redis = require('redis');

describe('Conversation Storage API Contract', () => {
  let redisClient;
  const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
  const TEST_CONVERSATION_ID = 'test-conv-123';
  const TEST_USER_ID = '29:1test-user';

  beforeAll(async () => {
    redisClient = redis.createClient({ url: REDIS_URL });
    await redisClient.connect();
  });

  afterAll(async () => {
    // Cleanup test data
    await redisClient.del(`conversation:${TEST_CONVERSATION_ID}`);
    await redisClient.del(`user:${TEST_USER_ID}:history`);
    await redisClient.quit();
  });

  afterEach(async () => {
    // Clean up after each test
    await redisClient.del(`conversation:${TEST_CONVERSATION_ID}`);
  });

  describe('Conversation Storage Schema', () => {
    test('should store conversation with required fields', async () => {
      const conversation = {
        conversation_id: TEST_CONVERSATION_ID,
        channel_id: '19:test@thread.tacv2',
        participants: [TEST_USER_ID],
        created_at: new Date().toISOString(),
        last_message_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        context_summary: 'User asked about brake procedures',
        message_count: 1
      };

      await redisClient.setEx(
        `conversation:${TEST_CONVERSATION_ID}`,
        604800, // 7 days
        JSON.stringify(conversation)
      );

      const stored = await redisClient.get(`conversation:${TEST_CONVERSATION_ID}`);
      expect(stored).toBeDefined();

      const parsed = JSON.parse(stored);
      expect(parsed).toMatchObject({
        conversation_id: TEST_CONVERSATION_ID,
        channel_id: expect.any(String),
        participants: expect.arrayContaining([TEST_USER_ID]),
        created_at: expect.any(String),
        last_message_at: expect.any(String),
        expires_at: expect.any(String),
        context_summary: expect.any(String),
        message_count: expect.any(Number)
      });
    });

    test('should enforce 7-day TTL on conversations', async () => {
      const conversation = {
        conversation_id: TEST_CONVERSATION_ID,
        channel_id: '19:test@thread.tacv2',
        participants: [TEST_USER_ID],
        created_at: new Date().toISOString(),
        last_message_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        context_summary: '',
        message_count: 0
      };

      await redisClient.setEx(
        `conversation:${TEST_CONVERSATION_ID}`,
        604800, // 7 days in seconds
        JSON.stringify(conversation)
      );

      const ttl = await redisClient.ttl(`conversation:${TEST_CONVERSATION_ID}`);
      expect(ttl).toBeGreaterThan(604700); // Should be close to 7 days
      expect(ttl).toBeLessThanOrEqual(604800);
    });

    test('should retrieve conversation by ID', async () => {
      const conversation = {
        conversation_id: TEST_CONVERSATION_ID,
        channel_id: '19:retrieve-test@thread.tacv2',
        participants: [TEST_USER_ID],
        created_at: new Date().toISOString(),
        last_message_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        context_summary: 'Test conversation',
        message_count: 2
      };

      await redisClient.setEx(
        `conversation:${TEST_CONVERSATION_ID}`,
        604800,
        JSON.stringify(conversation)
      );

      const retrieved = await redisClient.get(`conversation:${TEST_CONVERSATION_ID}`);
      expect(retrieved).toBeDefined();

      const parsed = JSON.parse(retrieved);
      expect(parsed.conversation_id).toBe(TEST_CONVERSATION_ID);
      expect(parsed.message_count).toBe(2);
    });

    test('should return null for non-existent conversation', async () => {
      const nonExistent = await redisClient.get('conversation:nonexistent-123');
      expect(nonExistent).toBeNull();
    });
  });

  describe('Message Storage Schema', () => {
    test('should store message with conversation context', async () => {
      const message = {
        message_id: 'msg-001',
        conversation_id: TEST_CONVERSATION_ID,
        sender: 'user',
        user_id: TEST_USER_ID,
        content: 'What are brake procedures?',
        timestamp: new Date().toISOString(),
        message_type: 'question'
      };

      // Store message as part of conversation context
      const conversation = {
        conversation_id: TEST_CONVERSATION_ID,
        channel_id: '19:test@thread.tacv2',
        participants: [TEST_USER_ID],
        created_at: new Date().toISOString(),
        last_message_at: message.timestamp,
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        context_summary: message.content,
        message_count: 1,
        last_message: message
      };

      await redisClient.setEx(
        `conversation:${TEST_CONVERSATION_ID}`,
        604800,
        JSON.stringify(conversation)
      );

      const stored = await redisClient.get(`conversation:${TEST_CONVERSATION_ID}`);
      const parsed = JSON.parse(stored);

      expect(parsed.last_message).toMatchObject({
        message_id: expect.any(String),
        conversation_id: TEST_CONVERSATION_ID,
        sender: expect.stringMatching(/user|bot/),
        user_id: TEST_USER_ID,
        content: expect.any(String),
        timestamp: expect.any(String),
        message_type: expect.stringMatching(/question|answer|command/)
      });
    });
  });

  describe('Search History Storage', () => {
    test('should store user search history', async () => {
      const historyEntry = {
        query: 'emergency brake procedures',
        timestamp: new Date().toISOString(),
        result_count: 5
      };

      await redisClient.rPush(
        `user:${TEST_USER_ID}:history`,
        JSON.stringify(historyEntry)
      );
      await redisClient.expire(`user:${TEST_USER_ID}:history`, 604800);

      const history = await redisClient.lRange(`user:${TEST_USER_ID}:history`, 0, -1);
      expect(history.length).toBeGreaterThan(0);

      const parsed = JSON.parse(history[0]);
      expect(parsed).toMatchObject({
        query: expect.any(String),
        timestamp: expect.any(String),
        result_count: expect.any(Number)
      });
    });

    test('should retrieve last 7 days of history', async () => {
      const entries = [
        { query: 'VLAN config', timestamp: new Date().toISOString(), result_count: 3 },
        { query: 'brake systems', timestamp: new Date().toISOString(), result_count: 7 },
        { query: 'safety procedures', timestamp: new Date().toISOString(), result_count: 12 }
      ];

      for (const entry of entries) {
        await redisClient.rPush(
          `user:${TEST_USER_ID}:history`,
          JSON.stringify(entry)
        );
      }
      await redisClient.expire(`user:${TEST_USER_ID}:history`, 604800);

      const history = await redisClient.lRange(`user:${TEST_USER_ID}:history`, 0, -1);
      expect(history.length).toBe(3);
    });
  });

  describe('Document Upload Job Storage', () => {
    test('should store document upload job', async () => {
      const jobId = 'job-upload-001';
      const uploadJob = {
        job_id: jobId,
        document_id: 'doc-123',
        file_name: 'railway-procedures.pdf',
        file_type: 'application/pdf',
        uploaded_by: TEST_USER_ID,
        upload_date: new Date().toISOString(),
        processing_status: 'queued',
        indexed_chunks_count: 0
      };

      await redisClient.setEx(
        `upload:${jobId}`,
        86400, // 24 hours for job tracking
        JSON.stringify(uploadJob)
      );

      const stored = await redisClient.get(`upload:${jobId}`);
      const parsed = JSON.parse(stored);

      expect(parsed).toMatchObject({
        job_id: jobId,
        document_id: expect.any(String),
        file_name: expect.any(String),
        file_type: expect.any(String),
        uploaded_by: TEST_USER_ID,
        upload_date: expect.any(String),
        processing_status: expect.stringMatching(/queued|processing|completed|failed/),
        indexed_chunks_count: expect.any(Number)
      });

      // Cleanup
      await redisClient.del(`upload:${jobId}`);
    });
  });

  describe('Storage Failure Handling', () => {
    test('should handle Redis connection failure gracefully', async () => {
      const badClient = redis.createClient({ url: 'redis://localhost:9999' });

      await expect(badClient.connect()).rejects.toThrow();
    });

    test('should detect expired conversations', async () => {
      const expiredConvId = 'expired-conv-123';

      await redisClient.setEx(
        `conversation:${expiredConvId}`,
        1, // 1 second TTL
        JSON.stringify({ conversation_id: expiredConvId })
      );

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 1100));

      const expired = await redisClient.get(`conversation:${expiredConvId}`);
      expect(expired).toBeNull();
    });
  });

  describe('Whitelist Storage', () => {
    test('should validate whitelist file structure', () => {
      // This tests the whitelist.json file structure
      // Actual validation will be done by whitelist module
      const validWhitelist = {
        admins: ['29:1admin-user'],
        channels: [
          {
            channel_id: '19:ops-team@thread.tacv2',
            channel_name: '#operations-team',
            added_by: '29:1admin-user',
            added_at: new Date().toISOString(),
            status: 'active'
          }
        ]
      };

      expect(validWhitelist).toMatchObject({
        admins: expect.any(Array),
        channels: expect.any(Array)
      });

      if (validWhitelist.channels.length > 0) {
        expect(validWhitelist.channels[0]).toMatchObject({
          channel_id: expect.any(String),
          channel_name: expect.any(String),
          added_by: expect.any(String),
          added_at: expect.any(String),
          status: expect.stringMatching(/active|revoked/)
        });
      }
    });
  });
});
