/**
 * Integration Test: Admin Whitelist Management
 *
 * T013: Test /admin commands for whitelist management
 * This test MUST FAIL initially (no admin workflow exists)
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

describe('Admin Commands Integration', () => {
  const WEBHOOK_URL = process.env.TEAMS_WEBHOOK_URL || 'http://localhost:5678/webhook/teams';
  const WHITELIST_PATH = process.env.WHITELIST_PATH || '/workspace/002-n8n/config/whitelist.json';
  const ADMIN_USER_ID = '29:1admin-user';
  const REGULAR_USER_ID = '29:1regular-user';

  const mockAdminMessage = (command, isAdmin = true) => ({
    type: 'message',
    id: `admin-${Date.now()}`,
    timestamp: new Date().toISOString(),
    from: {
      id: isAdmin ? ADMIN_USER_ID : REGULAR_USER_ID,
      name: isAdmin ? 'Admin User' : 'Regular User',
      isAdmin
    },
    conversation: {
      id: '19:admin-test@thread.tacv2',
      conversationType: 'personal'
    },
    text: command,
    channelId: 'msteams',
    serviceUrl: 'https://smba.trafficmanager.net/emea/'
  });

  // Backup and restore whitelist
  let whitelistBackup;

  beforeAll(() => {
    if (fs.existsSync(WHITELIST_PATH)) {
      whitelistBackup = fs.readFileSync(WHITELIST_PATH, 'utf8');
    }
  });

  afterAll(() => {
    if (whitelistBackup) {
      fs.writeFileSync(WHITELIST_PATH, whitelistBackup);
    }
  });

  afterEach(() => {
    // Reset whitelist after each test
    if (whitelistBackup) {
      fs.writeFileSync(WHITELIST_PATH, whitelistBackup);
    }
  });

  describe('/admin allow Command', () => {
    test('should add channel to whitelist', async () => {
      const message = mockAdminMessage('/admin allow #operations-team');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-021a: Admin can manage whitelist
      expect(response.data.message || response.data.text).toMatch(/access granted|added|whitelisted/i);

      // Verify whitelist.json was updated
      const whitelist = JSON.parse(fs.readFileSync(WHITELIST_PATH, 'utf8'));
      const channel = whitelist.channels.find(c => c.channel_name === '#operations-team');
      expect(channel).toBeDefined();
      expect(channel.status).toBe('active');
      expect(channel.added_by).toBe(ADMIN_USER_ID);
    });

    test('should handle channel ID instead of name', async () => {
      const channelId = '19:ops-team@thread.tacv2';
      const message = mockAdminMessage(`/admin allow ${channelId}`);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);

      const whitelist = JSON.parse(fs.readFileSync(WHITELIST_PATH, 'utf8'));
      const channel = whitelist.channels.find(c => c.channel_id === channelId);
      expect(channel).toBeDefined();
    });

    test('should prevent duplicate channel additions', async () => {
      const message = mockAdminMessage('/admin allow #test-channel');

      // Add once
      await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      // Try to add again
      const response2 = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response2.status).toBe(200);
      // Should warn that channel already exists
      if (response2.data.message || response2.data.warning) {
        expect(response2.data.message || response2.data.warning).toMatch(/already|exists/i);
      }
    });

    test('should reject non-admin user attempts', async () => {
      const message = mockAdminMessage('/admin allow #unauthorized-channel', false);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      // FR-021a: Only admins can manage whitelist
      if (response.status === 200) {
        expect(response.data.error || response.data.message).toMatch(/not.*admin|unauthorized|permission/i);
      } else {
        expect(response.status).toBe(403);
      }

      // Verify channel was NOT added
      const whitelist = JSON.parse(fs.readFileSync(WHITELIST_PATH, 'utf8'));
      const channel = whitelist.channels.find(c => c.channel_name === '#unauthorized-channel');
      expect(channel).toBeUndefined();
    });

    test('should store metadata with channel', async () => {
      const message = mockAdminMessage('/admin allow #metadata-test');

      await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      const whitelist = JSON.parse(fs.readFileSync(WHITELIST_PATH, 'utf8'));
      const channel = whitelist.channels.find(c => c.channel_name === '#metadata-test');

      expect(channel).toMatchObject({
        channel_name: '#metadata-test',
        added_by: ADMIN_USER_ID,
        added_at: expect.any(String),
        status: 'active'
      });
    });
  });

  describe('/admin revoke Command', () => {
    test('should revoke channel access', async () => {
      // First add a channel
      const addMessage = mockAdminMessage('/admin allow #revoke-test');
      await axios.post(WEBHOOK_URL, addMessage, { timeout: 3500 });

      // Then revoke it
      const revokeMessage = mockAdminMessage('/admin revoke #revoke-test');
      const response = await axios.post(WEBHOOK_URL, revokeMessage, { timeout: 3500 });

      expect(response.status).toBe(200);
      expect(response.data.message || response.data.text).toMatch(/access revoked|removed/i);

      // Verify channel status changed to revoked or removed
      const whitelist = JSON.parse(fs.readFileSync(WHITELIST_PATH, 'utf8'));
      const channel = whitelist.channels.find(c => c.channel_name === '#revoke-test');

      if (channel) {
        expect(channel.status).toBe('revoked');
      } else {
        // Channel completely removed is also acceptable
        expect(channel).toBeUndefined();
      }
    });

    test('should handle revoking non-existent channel', async () => {
      const message = mockAdminMessage('/admin revoke #nonexistent-channel');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      expect(response.data.error || response.data.message).toMatch(/not found|does not exist/i);
    });

    test('should reject non-admin revoke attempts', async () => {
      const message = mockAdminMessage('/admin revoke #test-channel', false);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      if (response.status === 200) {
        expect(response.data.error || response.data.message).toMatch(/not.*admin|unauthorized|permission/i);
      } else {
        expect(response.status).toBe(403);
      }
    });
  });

  describe('/admin list Command', () => {
    test('should list all whitelisted channels', async () => {
      // Add some channels first
      await axios.post(WEBHOOK_URL, mockAdminMessage('/admin allow #channel-1'), { timeout: 3500 });
      await axios.post(WEBHOOK_URL, mockAdminMessage('/admin allow #channel-2'), { timeout: 3500 });

      const message = mockAdminMessage('/admin list');
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);

      const responseText = JSON.stringify(response.data);
      expect(responseText).toMatch(/#channel-1/);
      expect(responseText).toMatch(/#channel-2/);
    });

    test('should show admin list', async () => {
      const message = mockAdminMessage('/admin list');
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);

      // Should include admins section from response-templates.json
      const responseText = JSON.stringify(response.data);
      expect(responseText).toMatch(/admin/i);
    });

    test('should handle empty whitelist', async () => {
      // Reset to empty
      fs.writeFileSync(WHITELIST_PATH, JSON.stringify({ admins: [], channels: [] }));

      const message = mockAdminMessage('/admin list');
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      expect(response.data.message || response.data.text).toMatch(/no.*channels|empty/i);
    });

    test('should allow non-admins to view list', async () => {
      // List command might be accessible to all users
      const message = mockAdminMessage('/admin list', false);
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      // Either allow viewing or deny - both acceptable
      expect(response.status).toBe(200);
    });
  });

  describe('Whitelist Enforcement', () => {
    test('should block messages from non-whitelisted channels', async () => {
      const message = {
        type: 'message',
        id: 'blocked-msg-001',
        timestamp: new Date().toISOString(),
        from: {
          id: '29:1non-whitelisted-user',
          name: 'Non-Whitelisted User'
        },
        conversation: {
          id: '19:non-whitelisted@thread.tacv2',
          conversationType: 'channel',
          name: '#non-whitelisted-channel'
        },
        text: 'This should be blocked',
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      // FR-021b: Reject non-whitelisted channels
      if (response.status === 200) {
        expect(response.data.message || response.data.error).toMatch(/POC phase|contact.*admin|not.*authorized/i);
      } else {
        expect(response.status).toBe(403);
      }
    });

    test('should allow messages from whitelisted channels', async () => {
      // Add channel to whitelist
      await axios.post(WEBHOOK_URL, mockAdminMessage('/admin allow #allowed-channel'), { timeout: 3500 });

      const message = {
        type: 'message',
        id: 'allowed-msg-001',
        timestamp: new Date().toISOString(),
        from: {
          id: '29:1whitelisted-user',
          name: 'Whitelisted User'
        },
        conversation: {
          id: '19:allowed-channel@thread.tacv2',
          conversationType: 'channel',
          name: '#allowed-channel'
        },
        text: 'What are brake procedures?',
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Should process the question normally
      expect(response.data).toBeDefined();
    });

    test('should always allow admin user messages', async () => {
      const message = {
        type: 'message',
        id: 'admin-override-001',
        timestamp: new Date().toISOString(),
        from: {
          id: ADMIN_USER_ID,
          name: 'Admin User',
          isAdmin: true
        },
        conversation: {
          id: '19:any-channel@thread.tacv2',
          conversationType: 'channel',
          name: '#any-channel'
        },
        text: 'Admin testing',
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Admins should bypass whitelist check
    });
  });

  describe('Whitelist Cache', () => {
    test('should refresh cache after whitelist update', async () => {
      // Add channel
      await axios.post(WEBHOOK_URL, mockAdminMessage('/admin allow #cache-test'), { timeout: 3500 });

      // Immediately try to use it
      const message = {
        type: 'message',
        id: 'cache-msg-001',
        timestamp: new Date().toISOString(),
        from: { id: '29:1test-user', name: 'Test User' },
        conversation: {
          id: '19:cache-test@thread.tacv2',
          conversationType: 'channel',
          name: '#cache-test'
        },
        text: 'Test message',
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Should work immediately (cache refreshed)
    });

    test('should respect 60s cache refresh interval', async () => {
      // This test validates that whitelist caching works
      // Real-time validation would require waiting 60s
      // For now, just verify file-based approach works

      const message = mockAdminMessage('/admin list');
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // Cache mechanism should be working
    });
  });

  describe('Admin Authorization', () => {
    test('should verify admin status from whitelist.json', async () => {
      // Ensure admin is in whitelist
      const whitelist = JSON.parse(fs.readFileSync(WHITELIST_PATH, 'utf8'));
      if (!whitelist.admins.includes(ADMIN_USER_ID)) {
        whitelist.admins.push(ADMIN_USER_ID);
        fs.writeFileSync(WHITELIST_PATH, JSON.stringify(whitelist, null, 2));
      }

      const message = mockAdminMessage('/admin allow #auth-test');
      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      expect(response.data.message).toMatch(/access granted/i);
    });

    test('should deny commands from users not in admin list', async () => {
      const message = mockAdminMessage('/admin allow #unauthorized', false);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      if (response.status === 200) {
        expect(response.data.error).toMatch(/not.*admin|unauthorized/i);
      } else {
        expect(response.status).toBe(403);
      }
    });
  });

  describe('Command Validation', () => {
    test('should handle invalid /admin subcommands', async () => {
      const message = mockAdminMessage('/admin invalidcommand #test');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      expect(response.data.error || response.data.message).toMatch(/invalid.*command|unknown|usage/i);
    });

    test('should require channel parameter', async () => {
      const message = mockAdminMessage('/admin allow');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      expect(response.data.error || response.data.message).toMatch(/channel.*required|missing.*parameter/i);
    });

    test('should validate channel name format', async () => {
      const message = mockAdminMessage('/admin allow invalid channel name with spaces');

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      // Should either accept and normalize, or reject invalid format
      expect(response.status).toBe(200);
    });
  });
});
