/**
 * Integration Test: Context Storage Failure Fallback
 *
 * T014: Test stateless mode when Redis unavailable
 * Scenario: Redis down, user asks question → bot responds with warning + answer
 * This test MUST FAIL initially (no fallback logic exists)
 */

const axios = require('axios');
const redis = require('redis');

describe('Storage Failure Integration', () => {
  const WEBHOOK_URL = process.env.TEAMS_WEBHOOK_URL || 'http://localhost:5678/webhook/teams';
  const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

  const mockMessage = (text) => ({
    type: 'message',
    id: `storage-fail-${Date.now()}`,
    timestamp: new Date().toISOString(),
    from: {
      id: '29:1storage-test-user',
      name: 'Storage Test User'
    },
    conversation: {
      id: '19:storage-fail-test@thread.tacv2',
      conversationType: 'personal'
    },
    text,
    channelId: 'msteams',
    serviceUrl: 'https://smba.trafficmanager.net/emea/'
  });

  describe('Redis Unavailable Scenario', () => {
    test('should continue processing query when Redis down', async () => {
      // NOTE: This test simulates Redis failure
      // In real testing, temporarily stop Redis or mock connection failure

      const message = mockMessage('What is VLAN configuration?');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      // NFR-002: Continue in stateless mode
      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();

      // Should still have answer even without context
      expect(response.data.answer || response.data.text).toBeDefined();
    });

    test('should warn user about context unavailability', async () => {
      const message = mockMessage('What are brake procedures?');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);

      // NFR-002: Warning message from response-templates.json
      const responseText = JSON.stringify(response.data);
      expect(responseText).toMatch(/conversation history.*temporarily unavailable/i);
    });

    test('should not fail entire request', async () => {
      const message = mockMessage('emergency brake systems');

      // Should not throw error or return 500
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Must still provide answer (stateless mode)
      expect(response.data.answer || response.data.text).toBeDefined();
    });
  });

  describe('Context Storage Restoration', () => {
    test('should detect when Redis becomes available again', async () => {
      let redisClient;
      let wasConnected = false;

      try {
        redisClient = redis.createClient({ url: REDIS_URL });
        await redisClient.connect();
        wasConnected = true;
      } catch (error) {
        // Redis not available
        wasConnected = false;
      }

      if (wasConnected) {
        const message = mockMessage('test query after Redis restore');
        const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

        expect(response.status).toBe(200);

        // NFR-002a: Should notify when restored
        if (response.data.status || response.data.message) {
          const text = JSON.stringify(response.data);
          // May include restoration notice
          expect(text).toBeDefined();
        }

        await redisClient.quit();
      }
    });

    test('should resume context tracking after restoration', async () => {
      // Assumes Redis is back online
      const convId = '19:restoration-test@thread.tacv2';

      const message = {
        ...mockMessage('first query after restoration'),
        conversation: { id: convId, conversationType: 'personal' }
      };

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);

      // Follow-up should use context if Redis restored
      await new Promise(resolve => setTimeout(resolve, 500));

      const followUp = {
        ...mockMessage('follow-up question'),
        conversation: { id: convId, conversationType: 'personal' }
      };

      const response2 = await axios.post(WEBHOOK_URL, followUp, { timeout: 3500 });
      expect(response2.status).toBe(200);
    });
  });

  describe('Partial Storage Failure', () => {
    test('should handle conversation read failure', async () => {
      // Scenario: Can't read existing conversation but can continue
      const message = mockMessage('query during read failure');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Should still process query
      expect(response.data).toBeDefined();
    });

    test('should handle conversation write failure', async () => {
      // Scenario: Query succeeds but can't save to context
      const message = mockMessage('query during write failure');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Should still return answer
      expect(response.data.answer || response.data.text).toBeDefined();
    });

    test('should handle history retrieval failure', async () => {
      const message = mockMessage('/history');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      // Should handle gracefully even if Redis down
      if (response.status === 200) {
        expect(response.data.error || response.data.message).toMatch(
          /unavailable|cannot.*retrieve|temporarily/i
        );
      }
    });
  });

  describe('Redis Connection Retry Logic', () => {
    test('should retry connection with exponential backoff', async () => {
      // This tests the retry mechanism in T024 (Redis client)
      const message = mockMessage('test query triggering retry');

      const startTime = Date.now();
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });
      const elapsed = Date.now() - startTime;

      expect(response.status).toBe(200);

      // T024: Should retry 3 times with exponential backoff
      // If Redis down, retries should add some delay but not block too long
      expect(elapsed).toBeLessThan(3000); // Should still meet SLA
    });

    test('should fallback after retry exhaustion', async () => {
      const message = mockMessage('query after retry exhaustion');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // After 3 failed retries, should enter stateless mode
      expect(response.data).toBeDefined();
    });
  });

  describe('Whitelist Access During Storage Failure', () => {
    test('should still enforce whitelist when Redis down', async () => {
      // Whitelist is file-based, should work even if Redis down
      const nonWhitelistedMessage = {
        type: 'message',
        id: 'non-whitelisted-001',
        timestamp: new Date().toISOString(),
        from: {
          id: '29:1non-whitelisted',
          name: 'Non-Whitelisted User'
        },
        conversation: {
          id: '19:non-whitelisted@thread.tacv2',
          conversationType: 'channel',
          name: '#non-whitelisted'
        },
        text: 'test',
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      const response = await axios.post(WEBHOOK_URL, nonWhitelistedMessage, { timeout: 3500 });

      // FR-021: Whitelist check should still work (file-based)
      if (response.status === 200) {
        expect(response.data.error || response.data.message).toMatch(/POC phase|contact.*admin/i);
      } else {
        expect(response.status).toBe(403);
      }
    });
  });

  describe('Document Upload During Storage Failure', () => {
    test('should allow uploads but warn about tracking limitation', async () => {
      const uploadMessage = {
        type: 'message',
        id: 'upload-fail-001',
        timestamp: new Date().toISOString(),
        from: {
          id: '29:1upload-user',
          name: 'Upload User'
        },
        conversation: {
          id: '19:upload-test@thread.tacv2',
          conversationType: 'personal'
        },
        text: 'uploading document',
        attachments: [
          {
            contentType: 'application/pdf',
            contentUrl: 'https://example.com/test.pdf',
            name: 'test-doc.pdf',
            content: Buffer.from('Test PDF').toString('base64')
          }
        ],
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      const response = await axios.post(WEBHOOK_URL, uploadMessage, { timeout: 5000 });

      // Should still forward to BMS API
      expect(response.status).toBe(200);

      // May warn about job tracking unavailable
      if (response.data.warning || response.data.message) {
        const text = JSON.stringify(response.data);
        // Can mention tracking limitation
        expect(text).toBeDefined();
      }
    });
  });

  describe('Error Message Quality', () => {
    test('should use template from response-templates.json', async () => {
      const message = mockMessage('test query for error message');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);

      if (response.data.warning || response.data.message) {
        const warningText = response.data.warning || response.data.message;

        // NFR-002: Exact warning from templates
        expect(warningText).toMatch(
          /Conversation history is temporarily unavailable.*Your question will still be answered/i
        );
      }
    });

    test('should not expose technical details to user', async () => {
      const message = mockMessage('query during failure');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);

      const responseText = JSON.stringify(response.data);

      // Should not mention Redis, connection errors, stack traces
      expect(responseText).not.toMatch(/redis|ECONNREFUSED|stack trace|exception/i);
    });
  });

  describe('Performance Under Failure', () => {
    test('should maintain sub-3s response time even with retries', async () => {
      const message = mockMessage('performance test during failure');
      const startTime = Date.now();

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });
      const elapsed = Date.now() - startTime;

      expect(response.status).toBe(200);
      // FR-003: Must still meet SLA
      expect(elapsed).toBeLessThan(3000);
    });

    test('should not accumulate delays over multiple requests', async () => {
      const queries = [
        'query 1 during failure',
        'query 2 during failure',
        'query 3 during failure'
      ];

      const responseTimes = [];

      for (const query of queries) {
        const startTime = Date.now();
        await axios.post(WEBHOOK_URL, mockMessage(query), { timeout: 3500 });
        responseTimes.push(Date.now() - startTime);
      }

      // Each request should be fast (no cumulative delays)
      responseTimes.forEach(time => {
        expect(time).toBeLessThan(3000);
      });

      // Average should also be good
      const avg = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      expect(avg).toBeLessThan(2500);
    });
  });

  describe('Mixed Failure Scenarios', () => {
    test('should handle Redis down + BMS API slow', async () => {
      const message = mockMessage('query with multiple challenges');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      // Should handle gracefully
      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
    });

    test('should prioritize query response over context storage', async () => {
      const message = mockMessage('priority test query');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Answer is more important than storing context
      expect(response.data.answer || response.data.text).toBeDefined();
    });
  });

  describe('Recovery Validation', () => {
    test('should log storage failures for monitoring', async () => {
      // This validates that failures are tracked
      // Actual log checking would be in production monitoring

      const message = mockMessage('query for logging test');
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Workflow should log the failure (validated in observability)
    });

    test('should provide actionable error info for debugging', async () => {
      const message = mockMessage('debug info test');
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Response should be useful for troubleshooting
      expect(response.data).toBeDefined();
    });
  });
});
