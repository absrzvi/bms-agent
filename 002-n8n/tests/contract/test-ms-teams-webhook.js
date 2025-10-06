/**
 * Contract Test: MS Teams Webhook Schema
 *
 * T007: Validate incoming message structure per contracts/ms-teams-webhook.json
 * This test MUST FAIL initially (no workflow exists yet)
 */

const axios = require('axios');

describe('MS Teams Webhook Contract', () => {
  const WEBHOOK_URL = process.env.TEAMS_WEBHOOK_URL || 'http://localhost:5678/webhook/teams';

  describe('Incoming Message Schema Validation', () => {
    test('should accept valid MS Teams message with required fields', async () => {
      const validMessage = {
        type: 'message',
        id: '1234567890',
        timestamp: '2025-10-06T12:00:00.000Z',
        from: {
          id: '29:1abc-def-ghi',
          name: 'Test User'
        },
        conversation: {
          id: '19:abc@thread.tacv2',
          conversationType: 'personal'
        },
        text: 'What are emergency brake procedures?',
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      // This will fail until workflow is deployed
      await expect(
        axios.post(WEBHOOK_URL, validMessage, { timeout: 5000 })
      ).resolves.toMatchObject({
        status: 200
      });
    });

    test('should handle group chat message', async () => {
      const groupMessage = {
        type: 'message',
        id: '1234567891',
        timestamp: '2025-10-06T12:01:00.000Z',
        from: {
          id: '29:1xyz-abc-def',
          name: 'Group User'
        },
        conversation: {
          id: '19:meeting_xyz@thread.tacv2',
          conversationType: 'channel',
          name: '#operations-team'
        },
        text: '/help',
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      await expect(
        axios.post(WEBHOOK_URL, groupMessage, { timeout: 5000 })
      ).resolves.toMatchObject({
        status: 200
      });
    });

    test('should handle message with file attachment', async () => {
      const messageWithAttachment = {
        type: 'message',
        id: '1234567892',
        timestamp: '2025-10-06T12:02:00.000Z',
        from: {
          id: '29:1file-upload-user',
          name: 'Upload User'
        },
        conversation: {
          id: '19:personal@thread.tacv2',
          conversationType: 'personal'
        },
        text: 'Here is the document',
        attachments: [
          {
            contentType: 'application/pdf',
            contentUrl: 'https://example.com/files/doc.pdf',
            name: 'railway-procedures.pdf'
          }
        ],
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      await expect(
        axios.post(WEBHOOK_URL, messageWithAttachment, { timeout: 5000 })
      ).resolves.toMatchObject({
        status: 200
      });
    });

    test('should reject message missing required fields', async () => {
      const invalidMessage = {
        type: 'message',
        // Missing: id, from, conversation, text
        channelId: 'msteams'
      };

      await expect(
        axios.post(WEBHOOK_URL, invalidMessage, { timeout: 5000 })
      ).rejects.toMatchObject({
        response: {
          status: 400
        }
      });
    });

    test('should handle typing activity', async () => {
      const typingActivity = {
        type: 'typing',
        id: '1234567893',
        timestamp: '2025-10-06T12:03:00.000Z',
        from: {
          id: '29:1typing-user',
          name: 'Typing User'
        },
        conversation: {
          id: '19:personal@thread.tacv2',
          conversationType: 'personal'
        },
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      // Typing activities should be acknowledged but not processed
      await expect(
        axios.post(WEBHOOK_URL, typingActivity, { timeout: 5000 })
      ).resolves.toMatchObject({
        status: 200
      });
    });
  });

  describe('Response Format Validation', () => {
    test('should respond with typing indicator for questions', async () => {
      const questionMessage = {
        type: 'message',
        id: '1234567894',
        timestamp: '2025-10-06T12:04:00.000Z',
        from: {
          id: '29:1question-user',
          name: 'Question User'
        },
        conversation: {
          id: '19:personal@thread.tacv2',
          conversationType: 'personal'
        },
        text: 'What is VLAN configuration?',
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      const response = await axios.post(WEBHOOK_URL, questionMessage, { timeout: 5000 });

      expect(response.status).toBe(200);
      // Workflow should trigger typing indicator before processing
      expect(response.data).toBeDefined();
    });
  });
});
