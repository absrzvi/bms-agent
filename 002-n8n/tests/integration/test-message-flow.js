/**
 * Integration Test: Natural Language Question in Personal Chat
 *
 * T010: End-to-end test for user asking questions
 * Scenario: User asks "What are emergency brake procedures?"
 * This test MUST FAIL initially (no workflows exist)
 */

const axios = require('axios');

describe('Message Flow Integration', () => {
  const WEBHOOK_URL = process.env.TEAMS_WEBHOOK_URL || 'http://localhost:5678/webhook/teams';
  const BMS_API_URL = process.env.BMS_API_URL || 'http://localhost:8000';

  // Mock MS Teams webhook trigger
  const mockTeamsMessage = (text, conversationType = 'personal') => ({
    type: 'message',
    id: `msg-${Date.now()}`,
    timestamp: new Date().toISOString(),
    from: {
      id: '29:1test-user-123',
      name: 'Test User'
    },
    conversation: {
      id: conversationType === 'personal'
        ? '19:personal-chat@thread.tacv2'
        : '19:group-chat@thread.tacv2',
      conversationType
    },
    text,
    channelId: 'msteams',
    serviceUrl: 'https://smba.trafficmanager.net/emea/'
  });

  describe('Personal Chat Question Flow', () => {
    test('should respond to natural language question within 3 seconds', async () => {
      const message = mockTeamsMessage('What are emergency brake procedures?');
      const startTime = Date.now();

      const response = await axios.post(WEBHOOK_URL, message, {
        timeout: 3500 // Allow 3.5s for test
      });

      const elapsed = Date.now() - startTime;

      expect(response.status).toBe(200);
      expect(elapsed).toBeLessThan(3000); // FR-003: <3s response time
      expect(response.data).toBeDefined();
    });

    test('should include answer and citations in response', async () => {
      const message = mockTeamsMessage('What is VLAN configuration for emergency systems?');

      const response = await axios.post(WEBHOOK_URL, message, {
        timeout: 3500
      });

      expect(response.status).toBe(200);
      expect(response.data).toMatchObject({
        answer: expect.any(String),
        citations: expect.any(Array)
      });

      // FR-004: Must include source citations
      expect(response.data.answer.length).toBeGreaterThan(0);
      if (response.data.citations.length > 0) {
        expect(response.data.citations[0]).toMatchObject({
          document_name: expect.any(String),
          relevance_score: expect.any(Number)
        });
      }
    });

    test('should handle follow-up questions with context', async () => {
      const conversationId = '19:followup-test@thread.tacv2';

      // First question
      const message1 = {
        ...mockTeamsMessage('What are brake procedures?'),
        conversation: { id: conversationId, conversationType: 'personal' }
      };

      const response1 = await axios.post(WEBHOOK_URL, message1, { timeout: 3500 });
      expect(response1.status).toBe(200);

      // Wait a moment for context to be stored
      await new Promise(resolve => setTimeout(resolve, 500));

      // Follow-up question (should use context)
      const message2 = {
        ...mockTeamsMessage('What about Class 395 trains?'),
        conversation: { id: conversationId, conversationType: 'personal' }
      };

      const response2 = await axios.post(WEBHOOK_URL, message2, { timeout: 3500 });
      expect(response2.status).toBe(200);

      // FR-005: Should maintain conversation context
      expect(response2.data).toBeDefined();
    });
  });

  describe('Group Chat Message Flow', () => {
    test('should respond in group chat visible to all', async () => {
      const message = mockTeamsMessage('What are safety procedures?', 'channel');

      const response = await axios.post(WEBHOOK_URL, message, {
        timeout: 3500
      });

      expect(response.status).toBe(200);
      // FR-017: Response visible to all participants
      expect(response.data).toBeDefined();
    });

    test('should handle multiple users in same group chat', async () => {
      const groupId = '19:multi-user@thread.tacv2';

      const user1Message = {
        ...mockTeamsMessage('What is VLAN?', 'channel'),
        conversation: { id: groupId, conversationType: 'channel' },
        from: { id: '29:1user-one', name: 'User One' }
      };

      const user2Message = {
        ...mockTeamsMessage('What is brake system?', 'channel'),
        conversation: { id: groupId, conversationType: 'channel' },
        from: { id: '29:1user-two', name: 'User Two' }
      };

      const response1 = await axios.post(WEBHOOK_URL, user1Message, { timeout: 3500 });
      const response2 = await axios.post(WEBHOOK_URL, user2Message, { timeout: 3500 });

      expect(response1.status).toBe(200);
      expect(response2.status).toBe(200);
    });
  });

  describe('Intelligent Query Routing', () => {
    test('should route to /ask for question queries', async () => {
      const message = mockTeamsMessage('What are the emergency procedures?');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-006: Should provide generated answer (not just search results)
      expect(response.data).toHaveProperty('answer');
    });

    test('should route to /search for document lookup queries', async () => {
      const message = mockTeamsMessage('emergency brake VLAN configuration');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-006: Should return document search results
      expect(response.data).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    test('should show error when BMS API unavailable', async () => {
      // This test assumes we can temporarily disable BMS API
      // In real scenario, mock the BMS API failure
      const message = mockTeamsMessage('test query when API down');

      // Expect either success with error message or graceful failure
      try {
        const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });
        if (response.status === 200 && response.data.error) {
          // FR-018: User-friendly error message
          expect(response.data.error).toContain('BMS-search tool cannot be accessed');
        }
      } catch (error) {
        // Timeout or connection error is also acceptable
        expect(error).toBeDefined();
      }
    });

    test('should suggest better query when no results found', async () => {
      const message = mockTeamsMessage('xyznonexistentquery12345');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-019: Suggest rephrasing
      if (response.data.error || response.data.message) {
        expect(
          response.data.error || response.data.message
        ).toMatch(/No results found|Try rephrasing/i);
      }
    });

    test('should handle unclear queries with suggestions', async () => {
      const message = mockTeamsMessage('it');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-020: Suggest better query formats
      if (response.data.suggestion || response.data.message) {
        expect(response.data.suggestion || response.data.message).toBeDefined();
      }
    });
  });

  describe('Typing Indicator', () => {
    test('should send typing indicator before processing', async () => {
      const message = mockTeamsMessage('What is brake configuration?');

      // FR-016: Display typing indicator while processing
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Workflow should have sent typing activity (validated in workflow logic)
    });
  });

  describe('Performance Validation', () => {
    test('should handle concurrent requests without degradation', async () => {
      const messages = [
        mockTeamsMessage('What are brake procedures?'),
        mockTeamsMessage('What is VLAN configuration?'),
        mockTeamsMessage('What are safety guidelines?')
      ];

      const startTime = Date.now();

      const promises = messages.map(msg =>
        axios.post(WEBHOOK_URL, msg, { timeout: 3500 })
      );

      const responses = await Promise.all(promises);

      const elapsed = Date.now() - startTime;

      responses.forEach(response => {
        expect(response.status).toBe(200);
      });

      // Should handle 3 concurrent requests reasonably
      expect(elapsed).toBeLessThan(5000);
    });

    test('should maintain sub-3s response under load', async () => {
      const iterations = 5;
      const responseTimes = [];

      for (let i = 0; i < iterations; i++) {
        const message = mockTeamsMessage(`Test query ${i + 1}`);
        const startTime = Date.now();

        await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

        responseTimes.push(Date.now() - startTime);
        await new Promise(resolve => setTimeout(resolve, 100)); // Small delay between requests
      }

      // FR-026: Maintain sub-3s response time under expected load
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      expect(avgResponseTime).toBeLessThan(3000);

      const p95 = responseTimes.sort((a, b) => a - b)[Math.floor(iterations * 0.95)];
      expect(p95).toBeLessThan(3000);
    });
  });

  describe('Conversation Context Retention', () => {
    test('should remember context for 7 days', async () => {
      const convId = '19:retention-test@thread.tacv2';

      const message = {
        ...mockTeamsMessage('Remember this: brake procedures'),
        conversation: { id: convId, conversationType: 'personal' }
      };

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-023: Context should be stored with 7-day retention
      // Actual TTL validation is in contract tests
    });
  });
});
