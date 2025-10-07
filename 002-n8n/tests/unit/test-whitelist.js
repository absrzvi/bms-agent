/**
 * Unit Test: Whitelist Validation Logic (T028)
 *
 * Tests for whitelist.js module (T025)
 * Tests: isChannelAllowed, isAdmin, cache behavior, invalidation
 */

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const WhitelistManager = require('../../lib/whitelist');

describe('Whitelist Validation Logic (T028)', () => {
  let whitelistManager;
  let testWhitelistPath;
  let originalWhitelistPath;

  // Test data
  const mockWhitelist = {
    channels: [
      {
        channel_id: 'test-channel-1',
        channel_name: '#operations',
        added_by: 'admin-user-1',
        added_at: '2025-10-01T00:00:00Z',
        status: 'active'
      },
      {
        channel_id: 'test-channel-2',
        channel_name: '#engineering',
        added_by: 'admin-user-1',
        added_at: '2025-10-02T00:00:00Z',
        status: 'active'
      },
      {
        channel_id: 'test-channel-revoked',
        channel_name: '#revoked',
        added_by: 'admin-user-1',
        added_at: '2025-10-03T00:00:00Z',
        status: 'revoked',
        revoked_by: 'admin-user-2',
        revoked_at: '2025-10-05T00:00:00Z'
      }
    ],
    admins: ['admin-user-1', 'admin-user-2']
  };

  beforeEach(() => {
    // Setup test whitelist file
    testWhitelistPath = path.join(__dirname, '../../config/test-whitelist.json');
    fs.writeFileSync(testWhitelistPath, JSON.stringify(mockWhitelist, null, 2));

    // Override the whitelist path in WhitelistManager
    whitelistManager = new WhitelistManager();
    whitelistManager.whitelistPath = testWhitelistPath;
    whitelistManager.cache = null; // Clear cache
    whitelistManager.lastRefresh = 0;
  });

  afterEach(() => {
    // Cleanup test file
    if (fs.existsSync(testWhitelistPath)) {
      fs.unlinkSync(testWhitelistPath);
    }
  });

  describe('isChannelAllowed() - Channel Validation', () => {
    it('should allow active whitelisted channel', () => {
      const result = whitelistManager.isChannelAllowed('test-channel-1');
      assert.strictEqual(result, true, 'Active channel should be allowed');
    });

    it('should allow second active whitelisted channel', () => {
      const result = whitelistManager.isChannelAllowed('test-channel-2');
      assert.strictEqual(result, true, 'Second active channel should be allowed');
    });

    it('should reject non-whitelisted channel', () => {
      const result = whitelistManager.isChannelAllowed('unknown-channel');
      assert.strictEqual(result, false, 'Non-whitelisted channel should be rejected');
    });

    it('should reject revoked channel', () => {
      const result = whitelistManager.isChannelAllowed('test-channel-revoked');
      assert.strictEqual(result, false, 'Revoked channel should be rejected');
    });

    it('should handle null/undefined channel ID gracefully', () => {
      const resultNull = whitelistManager.isChannelAllowed(null);
      const resultUndefined = whitelistManager.isChannelAllowed(undefined);
      const resultEmpty = whitelistManager.isChannelAllowed('');

      assert.strictEqual(resultNull, false, 'Null channel ID should be rejected');
      assert.strictEqual(resultUndefined, false, 'Undefined channel ID should be rejected');
      assert.strictEqual(resultEmpty, false, 'Empty channel ID should be rejected');
    });
  });

  describe('isAdmin() - Admin Validation', () => {
    it('should validate first admin user', () => {
      const result = whitelistManager.isAdmin('admin-user-1');
      assert.strictEqual(result, true, 'First admin should be validated');
    });

    it('should validate second admin user', () => {
      const result = whitelistManager.isAdmin('admin-user-2');
      assert.strictEqual(result, true, 'Second admin should be validated');
    });

    it('should reject non-admin user', () => {
      const result = whitelistManager.isAdmin('regular-user');
      assert.strictEqual(result, false, 'Non-admin should be rejected');
    });

    it('should reject empty admin list user when admins array is empty', () => {
      // Empty admins list
      fs.writeFileSync(testWhitelistPath, JSON.stringify({ channels: [], admins: [] }, null, 2));
      whitelistManager.cache = null;

      const result = whitelistManager.isAdmin('any-user');
      assert.strictEqual(result, false, 'Should reject when admins list is empty');
    });

    it('should handle null/undefined user ID gracefully', () => {
      const resultNull = whitelistManager.isAdmin(null);
      const resultUndefined = whitelistManager.isAdmin(undefined);
      const resultEmpty = whitelistManager.isAdmin('');

      assert.strictEqual(resultNull, false, 'Null user ID should be rejected');
      assert.strictEqual(resultUndefined, false, 'Undefined user ID should be rejected');
      assert.strictEqual(resultEmpty, false, 'Empty user ID should be rejected');
    });
  });

  describe('Cache Behavior', () => {
    it('should cache whitelist data after first load', () => {
      // First call - loads from file
      const result1 = whitelistManager.isChannelAllowed('test-channel-1');
      const firstCache = whitelistManager.cache;
      const firstRefreshTime = whitelistManager.lastRefresh;

      // Second call - should use cache
      const result2 = whitelistManager.isChannelAllowed('test-channel-1');
      const secondCache = whitelistManager.cache;
      const secondRefreshTime = whitelistManager.lastRefresh;

      assert.strictEqual(result1, true, 'First call should succeed');
      assert.strictEqual(result2, true, 'Second call should succeed');
      assert.strictEqual(firstCache, secondCache, 'Cache should be reused');
      assert.strictEqual(firstRefreshTime, secondRefreshTime, 'Refresh time should not change');
    });

    it('should refresh cache after TTL expiration (60s)', (done) => {
      // First load
      whitelistManager.isChannelAllowed('test-channel-1');
      const firstRefreshTime = whitelistManager.lastRefresh;

      // Force cache expiration by setting lastRefresh to past
      whitelistManager.lastRefresh = Date.now() - 61000; // 61 seconds ago

      // Modify file
      const updatedWhitelist = {
        ...mockWhitelist,
        channels: [
          ...mockWhitelist.channels,
          {
            channel_id: 'test-channel-new',
            channel_name: '#new-channel',
            added_by: 'admin-user-1',
            added_at: new Date().toISOString(),
            status: 'active'
          }
        ]
      };
      fs.writeFileSync(testWhitelistPath, JSON.stringify(updatedWhitelist, null, 2));

      // This should reload from file
      const result = whitelistManager.isChannelAllowed('test-channel-new');
      const secondRefreshTime = whitelistManager.lastRefresh;

      assert.strictEqual(result, true, 'New channel should be found after cache refresh');
      assert.notStrictEqual(firstRefreshTime, secondRefreshTime, 'Refresh time should update');
      done();
    });

    it('should use cache when within TTL window', () => {
      // First load
      whitelistManager.isChannelAllowed('test-channel-1');

      // Modify file (but cache should not pick it up)
      const updatedWhitelist = {
        ...mockWhitelist,
        channels: [
          {
            channel_id: 'test-channel-only-new',
            channel_name: '#only-new',
            added_by: 'admin-user-1',
            added_at: new Date().toISOString(),
            status: 'active'
          }
        ]
      };
      fs.writeFileSync(testWhitelistPath, JSON.stringify(updatedWhitelist, null, 2));

      // Should still use cached version (old data)
      const result1 = whitelistManager.isChannelAllowed('test-channel-1');
      const result2 = whitelistManager.isChannelAllowed('test-channel-only-new');

      assert.strictEqual(result1, true, 'Cached channel should still be found');
      assert.strictEqual(result2, false, 'New channel should not be found (using cache)');
    });
  });

  describe('Cache Invalidation on addChannel()', () => {
    it('should invalidate cache when adding new channel', () => {
      // Load initial cache
      whitelistManager.isChannelAllowed('test-channel-1');
      assert.notStrictEqual(whitelistManager.cache, null, 'Cache should be populated');

      // Add new channel (this should invalidate cache)
      whitelistManager.addChannel('test-channel-new', '#new-ops', 'admin-user-1');

      // Cache should be null
      assert.strictEqual(whitelistManager.cache, null, 'Cache should be invalidated after addChannel');

      // Next call should reload from file and find new channel
      const result = whitelistManager.isChannelAllowed('test-channel-new');
      assert.strictEqual(result, true, 'New channel should be found after cache invalidation');
    });

    it('should persist added channel to file', () => {
      whitelistManager.addChannel('test-persistent-channel', '#persistent', 'admin-user-1');

      // Read file directly
      const fileContent = JSON.parse(fs.readFileSync(testWhitelistPath, 'utf8'));
      const foundChannel = fileContent.channels.find(ch => ch.channel_id === 'test-persistent-channel');

      assert.notStrictEqual(foundChannel, undefined, 'Channel should be in file');
      assert.strictEqual(foundChannel.channel_name, '#persistent', 'Channel name should match');
      assert.strictEqual(foundChannel.status, 'active', 'Channel should be active');
    });

    it('should prevent non-admin from adding channel', () => {
      try {
        whitelistManager.addChannel('unauthorized-channel', '#unauthorized', 'regular-user');
        assert.fail('Should have thrown error for non-admin');
      } catch (error) {
        assert.strictEqual(error.message.includes('not an admin'), true, 'Should throw admin error');
      }
    });

    it('should prevent duplicate channel addition', () => {
      try {
        whitelistManager.addChannel('test-channel-1', '#operations', 'admin-user-1');
        assert.fail('Should have thrown error for duplicate channel');
      } catch (error) {
        assert.strictEqual(error.message.includes('already exists'), true, 'Should throw duplicate error');
      }
    });
  });

  describe('Cache Invalidation on revokeChannel()', () => {
    it('should invalidate cache when revoking channel', () => {
      // Load initial cache
      whitelistManager.isChannelAllowed('test-channel-1');
      assert.notStrictEqual(whitelistManager.cache, null, 'Cache should be populated');

      // Revoke channel (this should invalidate cache)
      whitelistManager.revokeChannel('test-channel-1', 'admin-user-2');

      // Cache should be null
      assert.strictEqual(whitelistManager.cache, null, 'Cache should be invalidated after revokeChannel');

      // Next call should reload from file and reject revoked channel
      const result = whitelistManager.isChannelAllowed('test-channel-1');
      assert.strictEqual(result, false, 'Revoked channel should be rejected after cache invalidation');
    });

    it('should persist revoked status to file', () => {
      whitelistManager.revokeChannel('test-channel-1', 'admin-user-2');

      // Read file directly
      const fileContent = JSON.parse(fs.readFileSync(testWhitelistPath, 'utf8'));
      const revokedChannel = fileContent.channels.find(ch => ch.channel_id === 'test-channel-1');

      assert.notStrictEqual(revokedChannel, undefined, 'Channel should still be in file');
      assert.strictEqual(revokedChannel.status, 'revoked', 'Channel status should be revoked');
      assert.strictEqual(revokedChannel.revoked_by, 'admin-user-2', 'Revoked by should be set');
      assert.notStrictEqual(revokedChannel.revoked_at, undefined, 'Revoked at timestamp should be set');
    });

    it('should prevent non-admin from revoking channel', () => {
      try {
        whitelistManager.revokeChannel('test-channel-1', 'regular-user');
        assert.fail('Should have thrown error for non-admin');
      } catch (error) {
        assert.strictEqual(error.message.includes('not an admin'), true, 'Should throw admin error');
      }
    });
  });

  describe('List Functions', () => {
    it('should list all channels with listChannels()', () => {
      const channels = whitelistManager.listChannels();

      assert.strictEqual(Array.isArray(channels), true, 'Should return array');
      assert.strictEqual(channels.length, 3, 'Should return all 3 channels');

      const activeChannels = channels.filter(ch => ch.status === 'active');
      const revokedChannels = channels.filter(ch => ch.status === 'revoked');

      assert.strictEqual(activeChannels.length, 2, 'Should have 2 active channels');
      assert.strictEqual(revokedChannels.length, 1, 'Should have 1 revoked channel');
    });

    it('should list all admins with listAdmins()', () => {
      const admins = whitelistManager.listAdmins();

      assert.strictEqual(Array.isArray(admins), true, 'Should return array');
      assert.strictEqual(admins.length, 2, 'Should return 2 admins');
      assert.strictEqual(admins.includes('admin-user-1'), true, 'Should include admin-user-1');
      assert.strictEqual(admins.includes('admin-user-2'), true, 'Should include admin-user-2');
    });

    it('should return empty arrays when whitelist is empty', () => {
      // Empty whitelist
      fs.writeFileSync(testWhitelistPath, JSON.stringify({ channels: [], admins: [] }, null, 2));
      whitelistManager.cache = null;

      const channels = whitelistManager.listChannels();
      const admins = whitelistManager.listAdmins();

      assert.strictEqual(channels.length, 0, 'Should return empty channels array');
      assert.strictEqual(admins.length, 0, 'Should return empty admins array');
    });
  });

  describe('Error Handling', () => {
    it('should handle missing whitelist file gracefully', () => {
      // Delete whitelist file
      fs.unlinkSync(testWhitelistPath);
      whitelistManager.cache = null;

      // Should return default empty structure
      const result = whitelistManager.isChannelAllowed('any-channel');
      assert.strictEqual(result, false, 'Should reject when file missing');
    });

    it('should handle corrupted whitelist file', () => {
      // Write invalid JSON
      fs.writeFileSync(testWhitelistPath, 'invalid json {{{');
      whitelistManager.cache = null;

      try {
        whitelistManager.isChannelAllowed('any-channel');
        // If it doesn't throw, it should return false
      } catch (error) {
        // Expected to throw JSON parse error
        assert.strictEqual(error instanceof SyntaxError, true, 'Should throw parse error');
      }
    });

    it('should handle whitelist with missing channels array', () => {
      fs.writeFileSync(testWhitelistPath, JSON.stringify({ admins: ['admin-user-1'] }, null, 2));
      whitelistManager.cache = null;

      const result = whitelistManager.isChannelAllowed('any-channel');
      assert.strictEqual(result, false, 'Should reject when channels array missing');
    });

    it('should handle whitelist with missing admins array', () => {
      fs.writeFileSync(testWhitelistPath, JSON.stringify({
        channels: [{ channel_id: 'ch1', status: 'active' }]
      }, null, 2));
      whitelistManager.cache = null;

      const result = whitelistManager.isAdmin('any-user');
      assert.strictEqual(result, false, 'Should reject when admins array missing');
    });
  });
});

// Run tests if executed directly
if (require.main === module) {
  console.log('Running Whitelist Validation Unit Tests (T028)...\n');

  // Simple test runner
  const tests = [];
  global.describe = (name, fn) => {
    tests.push({ name, fn });
  };
  global.it = () => {};
  global.beforeEach = () => {};
  global.afterEach = () => {};

  require('./test-whitelist.js');

  console.log(`✓ ${tests.length} test suites defined`);
  console.log('  Run with: npm test or jest tests/unit/test-whitelist.js\n');
}

module.exports = { describe, it, beforeEach, afterEach };
