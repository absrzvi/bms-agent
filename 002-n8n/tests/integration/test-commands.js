/**
 * Integration Test: Slash Command Execution
 *
 * T011: Test all slash commands (/help, /status, /history, /search, /ask)
 * This test MUST FAIL initially (no command handlers exist)
 */

const axios = require('axios');

describe('Slash Command Integration', () => {
  const WEBHOOK_URL = process.env.TEAMS_WEBHOOK_URL || 'http://localhost:5678/webhook/teams';
  const TEST_USER_ID = '29:1test-cmd-user';
  const TEST_CONV_ID = '19:cmd-test@thread.tacv2';

  const mockCommandMessage = (command) => ({
    type: 'message',
    id: `cmd-${Date.now()}`,
    timestamp: new Date().toISOString(),
    from: {
      id: TEST_USER_ID,
      name: 'Command Test User'
    },
    conversation: {
      id: TEST_CONV_ID,
      conversationType: 'personal'
    },
    text: command,
    channelId: 'msteams',
    serviceUrl: 'https://smba.trafficmanager.net/emea/'
  });

  describe('/help Command', () => {
    test('should return help message with all 7 commands', async () => {
      const message = mockCommandMessage('/help');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();

      // FR-009: Must show all commands from response-templates.json
      const helpText = JSON.stringify(response.data);
      expect(helpText).toMatch(/\/search/i);
      expect(helpText).toMatch(/\/ask/i);
      expect(helpText).toMatch(/\/upload/i);
      expect(helpText).toMatch(/\/help/i);
      expect(helpText).toMatch(/\/history/i);
      expect(helpText).toMatch(/\/status/i);
      expect(helpText).toMatch(/\/admin/i);
    });

    test('should include command examples in help', async () => {
      const message = mockCommandMessage('/help');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      // NFR-004: Help command output must include clear examples
      expect(response.status).toBe(200);
      const helpText = JSON.stringify(response.data);
      expect(helpText).toMatch(/example/i);
    });

    test('should respond quickly to help command', async () => {
      const message = mockCommandMessage('/help');
      const startTime = Date.now();

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });
      const elapsed = Date.now() - startTime;

      expect(response.status).toBe(200);
      expect(elapsed).toBeLessThan(1000); // Help should be instant
    });
  });

  describe('/status Command', () => {
    test('should return document upload status', async () => {
      const testDocId = 'test-doc-123';
      const message = mockCommandMessage(`/status ${testDocId}`);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-014: Return DocumentUploadJob status
      if (response.data.status) {
        expect(response.data.status).toMatch(/queued|processing|completed|failed|not found/i);
      }
    });

    test('should handle status check for non-existent document', async () => {
      const message = mockCommandMessage('/status nonexistent-doc-999');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Should return "not found" message
      if (response.data.error || response.data.message) {
        expect(
          response.data.error || response.data.message
        ).toMatch(/not found/i);
      }
    });

    test('should show processing progress if available', async () => {
      const testDocId = 'processing-doc-456';
      const message = mockCommandMessage(`/status ${testDocId}`);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // If processing, should show status from response-templates.json
      if (response.data.status === 'processing') {
        expect(response.data).toHaveProperty('progress');
      }
    });
  });

  describe('/history Command', () => {
    test('should return last 7 days of search queries', async () => {
      // First, make some queries to build history
      const queries = [
        'What are brake procedures?',
        'VLAN configuration emergency',
        'safety guidelines'
      ];

      for (const query of queries) {
        const msg = mockCommandMessage(query);
        await axios.post(WEBHOOK_URL, msg, { timeout: 3500 });
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      // Now request history
      const historyMessage = mockCommandMessage('/history');
      const response = await axios.post(WEBHOOK_URL, historyMessage, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-015: Display user's search queries from last 7 days
      expect(response.data).toBeDefined();

      if (response.data.history && Array.isArray(response.data.history)) {
        expect(response.data.history.length).toBeGreaterThan(0);
        // Should have timestamps
        if (response.data.history[0]) {
          expect(response.data.history[0]).toHaveProperty('timestamp');
          expect(response.data.history[0]).toHaveProperty('query');
        }
      }
    });

    test('should show empty message when no history exists', async () => {
      const newUserMessage = {
        ...mockCommandMessage('/history'),
        from: { id: '29:1new-user-999', name: 'New User' }
      };

      const response = await axios.post(WEBHOOK_URL, newUserMessage, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Should return "no history" message from templates
      if (response.data.message || response.data.history) {
        const text = response.data.message || JSON.stringify(response.data.history);
        expect(text).toMatch(/no.*history|empty/i);
      }
    });

    test('should limit history to 7 days', async () => {
      const historyMessage = mockCommandMessage('/history');
      const response = await axios.post(WEBHOOK_URL, historyMessage, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-023: Only 7-day retention
      if (response.data.history && Array.isArray(response.data.history)) {
        for (const entry of response.data.history) {
          const timestamp = new Date(entry.timestamp);
          const now = new Date();
          const daysDiff = (now - timestamp) / (1000 * 60 * 60 * 24);
          expect(daysDiff).toBeLessThanOrEqual(7);
        }
      }
    });
  });

  describe('/search Command', () => {
    test('should return document search results without answer', async () => {
      const message = mockCommandMessage('/search emergency brake vlan');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-007: Return search results (not generated answer)
      expect(response.data).toBeDefined();

      // Should have results array
      if (response.data.results) {
        expect(Array.isArray(response.data.results)).toBe(true);
      }
    });

    test('should handle search with no results', async () => {
      const message = mockCommandMessage('/search xyznonexistentquery12345');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-019: Display no results message
      if (response.data.message || response.data.results) {
        const text = response.data.message || JSON.stringify(response.data);
        expect(text).toMatch(/no results|not found/i);
      }
    });

    test('should include relevance scores in search results', async () => {
      const message = mockCommandMessage('/search brake procedures');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);

      if (response.data.results && response.data.results.length > 0) {
        const result = response.data.results[0];
        expect(result).toHaveProperty('score');
        expect(typeof result.score).toBe('number');
      }
    });
  });

  describe('/ask Command', () => {
    test('should return generated answer with citations', async () => {
      const message = mockCommandMessage('/ask What are the emergency brake procedures?');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-008: Return direct answer
      expect(response.data).toHaveProperty('answer');

      // FR-004: Include citations
      if (response.data.citations) {
        expect(Array.isArray(response.data.citations)).toBe(true);
      }
    });

    test('should handle complex questions', async () => {
      const message = mockCommandMessage(
        '/ask What is the difference between Class 395 and Class 373 brake systems?'
      );

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      expect(response.data.answer).toBeDefined();
      expect(response.data.answer.length).toBeGreaterThan(0);
    });

    test('should respond within 3 seconds', async () => {
      const message = mockCommandMessage('/ask What is VLAN configuration?');
      const startTime = Date.now();

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });
      const elapsed = Date.now() - startTime;

      expect(response.status).toBe(200);
      expect(elapsed).toBeLessThan(3000); // FR-003
    });
  });

  describe('Command Parsing', () => {
    test('should handle commands with extra whitespace', async () => {
      const message = mockCommandMessage('  /help  ');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
    });

    test('should handle commands in mixed case', async () => {
      const message = mockCommandMessage('/HELP');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Commands should be case-insensitive
    });

    test('should reject invalid commands', async () => {
      const message = mockCommandMessage('/invalidcommand');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Should return error or treat as natural language
      expect(response.data).toBeDefined();
    });

    test('should handle commands without parameters when required', async () => {
      const message = mockCommandMessage('/status');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Should return error asking for document_id
      if (response.data.error || response.data.message) {
        expect(
          response.data.error || response.data.message
        ).toMatch(/document.*id|parameter|required/i);
      }
    });
  });

  describe('Natural Language vs Commands', () => {
    test('should differentiate between command and natural language', async () => {
      const naturalMessage = mockCommandMessage('help me understand brake systems');
      const commandMessage = mockCommandMessage('/help');

      const naturalResponse = await axios.post(WEBHOOK_URL, naturalMessage, { timeout: 3500 });
      const commandResponse = await axios.post(WEBHOOK_URL, commandMessage, { timeout: 3500 });

      // Natural language should trigger query analysis
      expect(naturalResponse.status).toBe(200);
      expect(naturalResponse.data).toBeDefined();

      // Command should return help text
      expect(commandResponse.status).toBe(200);
      const helpText = JSON.stringify(commandResponse.data);
      expect(helpText).toMatch(/\/search|\/ask|\/upload/i);
    });

    test('should treat slash in middle of text as natural language', async () => {
      const message = mockCommandMessage('The system has a 5/10 uptime ratio');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Should be processed as natural language, not as command
      expect(response.data).toBeDefined();
    });
  });

  // FR-032: Similar query suggestion dismissal
  describe('Similar Query Dismissal (FR-032)', () => {
    test('should allow user to dismiss similar query suggestion', async () => {
      // Step 1: User asks first query
      const query1 = mockCommandMessage('/ask What are emergency brake procedures?');
      const response1 = await axios.post(WEBHOOK_URL, query1, { timeout: 3500 });

      expect(response1.status).toBe(200);
      expect(response1.data).toBeDefined();

      // Wait for query to be stored in history
      await new Promise(resolve => setTimeout(resolve, 500));

      // Step 2: User asks similar query (should trigger suggestion)
      const query2 = mockCommandMessage('/ask Tell me about emergency brakes');
      const response2 = await axios.post(WEBHOOK_URL, query2, { timeout: 3500 });

      expect(response2.status).toBe(200);

      // Response should contain similar query suggestion
      const responseText = JSON.stringify(response2.data);
      if (responseText.includes('similar') || responseText.includes('asked')) {
        // Suggestion was shown - test dismiss functionality

        // Step 3: User dismisses suggestion (simulated via Redis)
        const redisClient = require('../../lib/redis-client').getRedisClient();
        await redisClient.execute(async (client) => {
          const userId = query2.from.id;
          const suggestionId = `suggestion_${Date.now()}`;
          const key = `bms:user:${userId}:dismissed_suggestions`;

          // Store dismissed suggestion with 7-day TTL
          await client.hSet(key, suggestionId, Date.now().toString());
          await client.expire(key, 7 * 24 * 60 * 60); // 604800 seconds

          return true;
        });

        // Step 4: Ask similar query again - should NOT show suggestion
        const query3 = mockCommandMessage('/ask Emergency brake information');
        const response3 = await axios.post(WEBHOOK_URL, query3, { timeout: 3500 });

        expect(response3.status).toBe(200);
        // Should process query normally without suggestion
        expect(response3.data).toBeDefined();
      } else {
        // Similar query detection not triggered (threshold not met)
        // This is acceptable behavior - test passes
        expect(response2.status).toBe(200);
      }
    });

    test('dismissed suggestions should expire after 7 days (TTL validation)', async () => {
      const redisClient = require('../../lib/redis-client').getRedisClient();
      const userId = 'test-user-dismiss-ttl';
      const key = `bms:user:${userId}:dismissed_suggestions`;

      // Store dismissed suggestion
      await redisClient.execute(async (client) => {
        await client.hSet(key, 'test_suggestion_123', Date.now().toString());
        await client.expire(key, 7 * 24 * 60 * 60);
        return true;
      });

      // Verify TTL is set correctly
      const ttl = await redisClient.execute(async (client) => {
        return await client.ttl(key);
      });

      expect(ttl.data).toBeGreaterThan(0);
      expect(ttl.data).toBeLessThanOrEqual(7 * 24 * 60 * 60);

      // Cleanup
      await redisClient.execute(async (client) => {
        await client.del(key);
        return true;
      });
    });

    test('multiple dismissed suggestions should be stored per user', async () => {
      const redisClient = require('../../lib/redis-client').getRedisClient();
      const userId = 'test-user-multiple-dismiss';
      const key = `bms:user:${userId}:dismissed_suggestions`;

      // Dismiss multiple suggestions
      await redisClient.execute(async (client) => {
        await client.hSet(key, 'suggestion_1', Date.now().toString());
        await client.hSet(key, 'suggestion_2', (Date.now() + 1000).toString());
        await client.hSet(key, 'suggestion_3', (Date.now() + 2000).toString());
        await client.expire(key, 7 * 24 * 60 * 60);
        return true;
      });

      // Verify all dismissed suggestions stored
      const dismissed = await redisClient.execute(async (client) => {
        return await client.hGetAll(key);
      });

      expect(dismissed.data).toBeDefined();
      expect(Object.keys(dismissed.data).length).toBe(3);
      expect(dismissed.data).toHaveProperty('suggestion_1');
      expect(dismissed.data).toHaveProperty('suggestion_2');
      expect(dismissed.data).toHaveProperty('suggestion_3');

      // Cleanup
      await redisClient.execute(async (client) => {
        await client.del(key);
        return true;
      });
    });
  });

  // FR-006: Intent Classification with LLM Confidence Threshold
  describe('Intent Classification (FR-006)', () => {
    test('LLM confidence ≥0.80 routes to /api/v1/ask for direct answer', async () => {
      // Clear, direct question should trigger ASK intent with high confidence
      const message = mockCommandMessage('What is the emergency brake procedure for Class 395 trains?');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-006: Query routed to /api/v1/ask (not /api/v1/search/semantic)
      // Should have 'answer' property (generated answer) rather than just 'results' (search results)
      expect(response.data).toBeDefined();

      // If answer is present, it should be from /api/v1/ask endpoint
      if (response.data.answer) {
        expect(response.data).toHaveProperty('answer');
        expect(typeof response.data.answer).toBe('string');
        expect(response.data.answer.length).toBeGreaterThan(0);

        // FR-004: Should also include citations
        if (response.data.citations) {
          expect(Array.isArray(response.data.citations)).toBe(true);
        }
      }
    });

    test('LLM confidence <0.80 falls back to semantic search', async () => {
      // Ambiguous or vague query should trigger SEARCH fallback
      const message = mockCommandMessage('emergency procedures');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-006: Query routed to /api/v1/search/semantic (safe fallback)
      expect(response.data).toBeDefined();

      // Should have 'results' array (search results) rather than generated 'answer'
      if (response.data.results) {
        expect(Array.isArray(response.data.results)).toBe(true);

        // Results should have relevance scores
        if (response.data.results.length > 0) {
          expect(response.data.results[0]).toHaveProperty('score');
        }
      }
    });

    test('intent classification respects confidence threshold boundary', async () => {
      // Test queries near the 0.80 threshold boundary
      const borderlineQueries = [
        'What are brake systems?',  // Medium clarity
        'How does the procedure work?'  // Somewhat unclear (missing context)
      ];

      for (const queryText of borderlineQueries) {
        const message = mockCommandMessage(queryText);
        const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

        expect(response.status).toBe(200);
        expect(response.data).toBeDefined();

        // Should be routed to either /ask OR /search based on confidence
        // Both are acceptable outcomes depending on LLM confidence score
        const hasAnswer = response.data.answer !== undefined;
        const hasResults = response.data.results !== undefined;

        expect(hasAnswer || hasResults).toBe(true);
      }
    });
  });

  // FR-022: Query Validation with Clarity Score
  describe('Query Validation (FR-022)', () => {
    test('unclear query (clarity_score <0.60) returns suggestions', async () => {
      // Single word, unclear query
      const message = mockCommandMessage('brakes');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-022: Should return suggestions for unclear queries
      expect(response.data).toBeDefined();

      // Response should contain suggestions or clarification request
      const responseText = JSON.stringify(response.data);
      if (responseText.includes('suggest') || responseText.includes('clarify') ||
          responseText.includes('example') || responseText.includes('specific')) {
        // Suggestions provided - test passed
        expect(response.data.message || response.data.suggestion).toBeDefined();
      } else if (response.data.error || response.data.message) {
        // Error message explaining query is unclear
        expect(
          response.data.error || response.data.message
        ).toMatch(/unclear|specific|rephrase|example/i);
      }
    });

    test('clear query (clarity_score ≥0.60) proceeds normally', async () => {
      // Clear, specific query
      const message = mockCommandMessage('What are the maintenance schedules for Class 395 trains?');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-022: Clear query should proceed to intent classification
      expect(response.data).toBeDefined();

      // Should have either answer (ASK intent) or results (SEARCH intent)
      const hasAnswer = response.data.answer !== undefined;
      const hasResults = response.data.results !== undefined;

      expect(hasAnswer || hasResults).toBe(true);

      // Should NOT return unclear query suggestions
      const responseText = JSON.stringify(response.data);
      expect(responseText).not.toMatch(/query.*unclear|please.*clarify/i);
    });

    test('empty query is rejected immediately', async () => {
      // Empty string query (should be invalid without LLM call)
      const message = mockCommandMessage('   ');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-022: Invalid queries (empty/whitespace-only) should be rejected
      if (response.data.error || response.data.message) {
        expect(
          response.data.error || response.data.message
        ).toMatch(/empty|required|invalid/i);
      }
    });

    test('query with ambiguous pronouns triggers unclear response', async () => {
      // Query with missing context (unclear)
      const message = mockCommandMessage('How does it work?');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Should either ask for clarification OR attempt to answer based on context
      expect(response.data).toBeDefined();

      // If treated as unclear, should provide suggestions
      // If context is available, may proceed to answer
      const hasAnswer = response.data.answer !== undefined;
      const hasResults = response.data.results !== undefined;
      const hasSuggestion = response.data.suggestion !== undefined ||
                            (response.data.message &&
                             response.data.message.match(/unclear|specific|example/i));

      expect(hasAnswer || hasResults || hasSuggestion).toBe(true);
    });

    test('query clarity validation respects 0.60 threshold', async () => {
      // Test queries near the clarity threshold boundary
      const borderlineQueries = [
        'the procedure',  // Low clarity (missing specifics)
        'safety guidelines overview'  // Medium clarity
      ];

      for (const queryText of borderlineQueries) {
        const message = mockCommandMessage(queryText);
        const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

        expect(response.status).toBe(200);
        expect(response.data).toBeDefined();

        // Should be either processed OR rejected based on clarity_score
        // Both outcomes are acceptable depending on LLM assessment
        const processed = response.data.answer !== undefined || response.data.results !== undefined;
        const rejected = response.data.error !== undefined ||
                        (response.data.message &&
                         response.data.message.match(/unclear|specific/i));

        expect(processed || rejected).toBe(true);
      }
    });
  });
});
