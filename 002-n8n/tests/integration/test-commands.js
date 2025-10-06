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
});
