/**
 * Unit Test: Whitelist Validation Logic (T028)
 *
 * Tests for whitelist.js module (T025)
 * Tests: isChannelAllowed, isAdmin, cache behavior, invalidation
 */

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { WhitelistManager } = require('../../lib/whitelist');

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

  describe('Edge Cases - Concurrent Access', () => {
    it('should handle rapid successive calls without corruption', async () => {
      // Simulate multiple rapid calls
      const promises = [];
      for (let i = 0; i < 10; i++) {
        promises.push(Promise.resolve(whitelistManager.isChannelAllowed('test-channel-1')));
      }

      const results = await Promise.all(promises);

      // All calls should return true
      results.forEach((result, idx) => {
        assert.strictEqual(result, true, `Call ${idx} should succeed`);
      });
    });

    it('should handle concurrent admin checks without cache corruption', async () => {
      const adminPromises = [];
      const nonAdminPromises = [];

      for (let i = 0; i < 5; i++) {
        adminPromises.push(Promise.resolve(whitelistManager.isAdmin('admin-user-1')));
        nonAdminPromises.push(Promise.resolve(whitelistManager.isAdmin('regular-user')));
      }

      const adminResults = await Promise.all(adminPromises);
      const nonAdminResults = await Promise.all(nonAdminPromises);

      adminResults.forEach((result) => {
        assert.strictEqual(result, true, 'Admin check should succeed');
      });

      nonAdminResults.forEach((result) => {
        assert.strictEqual(result, false, 'Non-admin check should fail');
      });
    });

    it('should handle interleaved read and write operations', () => {
      // Read
      whitelistManager.isChannelAllowed('test-channel-1');

      // Write (add channel)
      whitelistManager.addChannel('test-rapid-add', '#rapid', 'admin-user-1');

      // Read again
      const result1 = whitelistManager.isChannelAllowed('test-rapid-add');

      // Write (revoke)
      whitelistManager.revokeChannel('test-rapid-add', 'admin-user-2');

      // Read revoked
      const result2 = whitelistManager.isChannelAllowed('test-rapid-add');

      assert.strictEqual(result1, true, 'Added channel should be found');
      assert.strictEqual(result2, false, 'Revoked channel should be rejected');
    });
  });

  describe('Edge Cases - Cache Expiration Boundaries', () => {
    it('should refresh cache exactly at 60s boundary', () => {
      // First load
      whitelistManager.isChannelAllowed('test-channel-1');

      // Set lastRefresh to exactly 60 seconds ago
      whitelistManager.lastRefresh = Date.now() - 60000; // Exactly 60s

      // Add new channel to file
      const updatedWhitelist = {
        ...mockWhitelist,
        channels: [
          ...mockWhitelist.channels,
          {
            channel_id: 'boundary-channel',
            channel_name: '#boundary',
            added_by: 'admin-user-1',
            added_at: new Date().toISOString(),
            status: 'active'
          }
        ]
      };
      fs.writeFileSync(testWhitelistPath, JSON.stringify(updatedWhitelist, null, 2));

      // Should refresh (60s >= TTL)
      const result = whitelistManager.isChannelAllowed('boundary-channel');

      assert.strictEqual(result, true, 'Should reload at 60s boundary');
    });

    it('should not refresh cache just before 60s boundary', () => {
      // First load
      whitelistManager.isChannelAllowed('test-channel-1');

      // Set lastRefresh to 59 seconds ago (within TTL)
      whitelistManager.lastRefresh = Date.now() - 59000;

      // Add new channel to file
      const updatedWhitelist = {
        ...mockWhitelist,
        channels: [
          {
            channel_id: 'not-yet-channel',
            channel_name: '#not-yet',
            added_by: 'admin-user-1',
            added_at: new Date().toISOString(),
            status: 'active'
          }
        ]
      };
      fs.writeFileSync(testWhitelistPath, JSON.stringify(updatedWhitelist, null, 2));

      // Should still use cache (old data)
      const result1 = whitelistManager.isChannelAllowed('test-channel-1');
      const result2 = whitelistManager.isChannelAllowed('not-yet-channel');

      assert.strictEqual(result1, true, 'Cached channel should still be found');
      assert.strictEqual(result2, false, 'New channel should not be found (using cache)');
    });
  });

  describe('Edge Cases - Large Whitelist Performance', () => {
    it('should handle whitelist with many channels efficiently', () => {
      // Create large whitelist (100 channels)
      const largeWhitelist = {
        channels: [],
        admins: ['admin-user-1']
      };

      for (let i = 0; i < 100; i++) {
        largeWhitelist.channels.push({
          channel_id: `channel-${i}`,
          channel_name: `#channel-${i}`,
          added_by: 'admin-user-1',
          added_at: new Date().toISOString(),
          status: i % 10 === 0 ? 'revoked' : 'active' // Every 10th is revoked
        });
      }

      fs.writeFileSync(testWhitelistPath, JSON.stringify(largeWhitelist, null, 2));
      whitelistManager.cache = null;

      const startTime = Date.now();

      // Check first channel
      const result1 = whitelistManager.isChannelAllowed('channel-0');

      // Check middle channel
      const result2 = whitelistManager.isChannelAllowed('channel-50');

      // Check last channel
      const result3 = whitelistManager.isChannelAllowed('channel-99');

      const elapsed = Date.now() - startTime;

      assert.strictEqual(result1, false, 'Revoked channel should be rejected');
      assert.strictEqual(result2, false, 'Revoked channel should be rejected');
      assert.strictEqual(result3, true, 'Active channel should be allowed');
      assert.strictEqual(elapsed < 100, true, 'Should complete in <100ms');
    });

    it('should handle whitelist with many admins efficiently', () => {
      const largeWhitelist = {
        channels: [],
        admins: Array.from({ length: 50 }, (_, i) => `admin-${i}`)
      };

      fs.writeFileSync(testWhitelistPath, JSON.stringify(largeWhitelist, null, 2));
      whitelistManager.cache = null;

      const startTime = Date.now();

      const result1 = whitelistManager.isAdmin('admin-0');
      const result2 = whitelistManager.isAdmin('admin-49');
      const result3 = whitelistManager.isAdmin('not-admin');

      const elapsed = Date.now() - startTime;

      assert.strictEqual(result1, true, 'First admin should be validated');
      assert.strictEqual(result2, true, 'Last admin should be validated');
      assert.strictEqual(result3, false, 'Non-admin should be rejected');
      assert.strictEqual(elapsed < 50, true, 'Should complete in <50ms');
    });
  });

  describe('Edge Cases - Special Characters', () => {
    it('should handle channel names with special characters', () => {
      const specialWhitelist = {
        channels: [
          {
            channel_id: 'special-channel-1',
            channel_name: '#ops-team_2025',
            added_by: 'admin-user-1',
            added_at: new Date().toISOString(),
            status: 'active'
          },
          {
            channel_id: 'special-channel-2',
            channel_name: '#engineering-&-ops',
            added_by: 'admin-user-1',
            added_at: new Date().toISOString(),
            status: 'active'
          }
        ],
        admins: ['admin-user-1']
      };

      fs.writeFileSync(testWhitelistPath, JSON.stringify(specialWhitelist, null, 2));
      whitelistManager.cache = null;

      const result1 = whitelistManager.isChannelAllowed('special-channel-1');
      const result2 = whitelistManager.isChannelAllowed('special-channel-2');

      assert.strictEqual(result1, true, 'Channel with underscore/numbers should work');
      assert.strictEqual(result2, true, 'Channel with ampersand should work');
    });

    it('should handle admin IDs with special formats', () => {
      const specialWhitelist = {
        channels: [],
        admins: ['29:admin-123', 'user@domain.com', 'admin_2025']
      };

      fs.writeFileSync(testWhitelistPath, JSON.stringify(specialWhitelist, null, 2));
      whitelistManager.cache = null;

      const result1 = whitelistManager.isAdmin('29:admin-123');
      const result2 = whitelistManager.isAdmin('user@domain.com');
      const result3 = whitelistManager.isAdmin('admin_2025');

      assert.strictEqual(result1, true, 'MS Teams format ID should work');
      assert.strictEqual(result2, true, 'Email format ID should work');
      assert.strictEqual(result3, true, 'Underscore ID should work');
    });
  });

  describe('Edge Cases - File System Errors', () => {
    it('should handle whitelist file with only whitespace', () => {
      fs.writeFileSync(testWhitelistPath, '   \n  \t  \n  ');
      whitelistManager.cache = null;

      try {
        whitelistManager.isChannelAllowed('any-channel');
        assert.fail('Should have thrown error for whitespace-only file');
      } catch (error) {
        assert.strictEqual(error instanceof SyntaxError, true, 'Should throw parse error');
      }
    });

    it('should handle empty whitelist file', () => {
      fs.writeFileSync(testWhitelistPath, '');
      whitelistManager.cache = null;

      try {
        whitelistManager.isChannelAllowed('any-channel');
      } catch (error) {
        // Expected - empty file cannot be parsed
        assert.strictEqual(error instanceof SyntaxError || error instanceof Error, true);
      }
    });

    it('should handle whitelist with empty channel objects', () => {
      const emptyChannelWhitelist = {
        channels: [
          {}, // Empty channel object
          { channel_id: 'valid-channel', status: 'active' }
        ],
        admins: ['admin-user-1']
      };

      fs.writeFileSync(testWhitelistPath, JSON.stringify(emptyChannelWhitelist, null, 2));
      whitelistManager.cache = null;

      const result1 = whitelistManager.isChannelAllowed('');
      const result2 = whitelistManager.isChannelAllowed('valid-channel');

      assert.strictEqual(result1, false, 'Empty channel should be rejected');
      assert.strictEqual(result2, true, 'Valid channel should be allowed');
    });
  });

  describe('Edge Cases - Data Consistency', () => {
    it('should maintain data consistency after multiple operations', () => {
      // Perform multiple operations
      whitelistManager.addChannel('consistency-1', '#cons1', 'admin-user-1');
      whitelistManager.addChannel('consistency-2', '#cons2', 'admin-user-1');
      whitelistManager.revokeChannel('consistency-1', 'admin-user-2');
      whitelistManager.addChannel('consistency-3', '#cons3', 'admin-user-1');

      // Read file directly to verify consistency
      const fileContent = JSON.parse(fs.readFileSync(testWhitelistPath, 'utf8'));

      const chan1 = fileContent.channels.find(ch => ch.channel_id === 'consistency-1');
      const chan2 = fileContent.channels.find(ch => ch.channel_id === 'consistency-2');
      const chan3 = fileContent.channels.find(ch => ch.channel_id === 'consistency-3');

      assert.strictEqual(chan1.status, 'revoked', 'Channel 1 should be revoked');
      assert.strictEqual(chan2.status, 'active', 'Channel 2 should be active');
      assert.strictEqual(chan3.status, 'active', 'Channel 3 should be active');

      // Total should be original 3 + 3 new = 6
      assert.strictEqual(fileContent.channels.length, 6, 'Should have 6 total channels');
    });

    it('should preserve existing channels when adding new ones', () => {
      const initialChannelCount = mockWhitelist.channels.length;

      whitelistManager.addChannel('preserve-test', '#preserve', 'admin-user-1');

      const fileContent = JSON.parse(fs.readFileSync(testWhitelistPath, 'utf8'));

      assert.strictEqual(
        fileContent.channels.length,
        initialChannelCount + 1,
        'Should preserve existing channels'
      );

      // Verify original channels still exist
      const originalChannel = fileContent.channels.find(ch => ch.channel_id === 'test-channel-1');
      assert.notStrictEqual(originalChannel, undefined, 'Original channel should still exist');
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
