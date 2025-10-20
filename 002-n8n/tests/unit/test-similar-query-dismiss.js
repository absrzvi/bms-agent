/**
 * Unit Tests for Similar Query Dismiss Handler
 *
 * Tests dismissal tracking, global preferences, and statistics
 */

// Mock ioredis with redis-mock
jest.mock('ioredis', () => require('redis-mock'));

const dismissHandler = require('../../lib/similar-query-dismiss');

describe('Similar Query Dismiss Handler', () => {
  const testUserId = 'U123456';
  const testSuggestionId = 'sugg_abc123';
  const testMetadata = {
    original_query: 'how to configure VLAN',
    suggested_query: 'how to configure VLAN settings'
  };

  beforeEach(async () => {
    // Clear all test data
    await dismissHandler.clearAllDismissals(testUserId);
    await dismissHandler.enableAllSuggestions(testUserId);
  });

  afterAll(async () => {
    await dismissHandler.close();
  });

  // =====================================================================
  // Record Dismissal Tests
  // =====================================================================

  describe('recordDismissal', () => {
    it('should record a dismissal with metadata', async () => {
      const result = await dismissHandler.recordDismissal(testUserId, testSuggestionId, testMetadata);

      expect(result.success).toBe(true);
      expect(result.key).toContain(testUserId);
    });

    it('should make suggestion retrievable', async () => {
      await dismissHandler.recordDismissal(testUserId, testSuggestionId, testMetadata);

      const wasDismissed = await dismissHandler.wasDismissed(testUserId, testSuggestionId);
      expect(wasDismissed).toBe(true);
    });

    it('should handle missing metadata gracefully', async () => {
      const result = await dismissHandler.recordDismissal(testUserId, testSuggestionId);

      expect(result.success).toBe(true);
    });

    it('should handle Redis errors', async () => {
      const result = await dismissHandler.recordDismissal('', '', {});

      // Should return error result, not throw
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  // =====================================================================
  // Was Dismissed Tests
  // =====================================================================

  describe('wasDismissed', () => {
    it('should return true for dismissed suggestion', async () => {
      await dismissHandler.recordDismissal(testUserId, testSuggestionId, testMetadata);

      const result = await dismissHandler.wasDismissed(testUserId, testSuggestionId);
      expect(result).toBe(true);
    });

    it('should return false for non-dismissed suggestion', async () => {
      const result = await dismissHandler.wasDismissed(testUserId, 'non_existent_id');
      expect(result).toBe(false);
    });

    it('should handle Redis errors gracefully', async () => {
      const result = await dismissHandler.wasDismissed('', '');
      expect(result).toBe(false);
    });
  });

  // =====================================================================
  // Get Dismissed Suggestions Tests
  // =====================================================================

  describe('getDismissedSuggestions', () => {
    it('should return all dismissed suggestions for user', async () => {
      await dismissHandler.recordDismissal(testUserId, 'sugg_1', { original_query: 'query 1' });
      await dismissHandler.recordDismissal(testUserId, 'sugg_2', { original_query: 'query 2' });

      const dismissed = await dismissHandler.getDismissedSuggestions(testUserId);

      expect(dismissed.length).toBe(2);
      expect(dismissed.map(d => d.suggestion_id)).toContain('sugg_1');
      expect(dismissed.map(d => d.suggestion_id)).toContain('sugg_2');
    });

    it('should return empty array if no dismissals', async () => {
      const dismissed = await dismissHandler.getDismissedSuggestions('U999999');

      expect(dismissed).toEqual([]);
    });

    it('should handle Redis errors', async () => {
      const dismissed = await dismissHandler.getDismissedSuggestions('');

      expect(Array.isArray(dismissed)).toBe(true);
      expect(dismissed.length).toBe(0);
    });
  });

  // =====================================================================
  // Clear Dismissal Tests
  // =====================================================================

  describe('clearDismissal', () => {
    it('should remove specific dismissal', async () => {
      await dismissHandler.recordDismissal(testUserId, testSuggestionId, testMetadata);

      const result = await dismissHandler.clearDismissal(testUserId, testSuggestionId);

      expect(result.success).toBe(true);

      const wasDismissed = await dismissHandler.wasDismissed(testUserId, testSuggestionId);
      expect(wasDismissed).toBe(false);
    });

    it('should not affect other dismissals', async () => {
      await dismissHandler.recordDismissal(testUserId, 'sugg_1', testMetadata);
      await dismissHandler.recordDismissal(testUserId, 'sugg_2', testMetadata);

      await dismissHandler.clearDismissal(testUserId, 'sugg_1');

      const wasDismissed1 = await dismissHandler.wasDismissed(testUserId, 'sugg_1');
      const wasDismissed2 = await dismissHandler.wasDismissed(testUserId, 'sugg_2');

      expect(wasDismissed1).toBe(false);
      expect(wasDismissed2).toBe(true);
    });
  });

  // =====================================================================
  // Clear All Dismissals Tests
  // =====================================================================

  describe('clearAllDismissals', () => {
    it('should remove all dismissals for user', async () => {
      await dismissHandler.recordDismissal(testUserId, 'sugg_1', testMetadata);
      await dismissHandler.recordDismissal(testUserId, 'sugg_2', testMetadata);

      const result = await dismissHandler.clearAllDismissals(testUserId);

      expect(result.success).toBe(true);

      const dismissed = await dismissHandler.getDismissedSuggestions(testUserId);
      expect(dismissed.length).toBe(0);
    });
  });

  // =====================================================================
  // Global Disable/Enable Tests
  // =====================================================================

  describe('disableAllSuggestions', () => {
    it('should disable suggestions globally for user', async () => {
      const result = await dismissHandler.disableAllSuggestions(testUserId);

      expect(result.success).toBe(true);

      const isDisabled = await dismissHandler.areSuggestionsDisabled(testUserId);
      expect(isDisabled).toBe(true);
    });

    it('should persist disable state', async () => {
      await dismissHandler.disableAllSuggestions(testUserId);

      // Check again
      const isDisabled = await dismissHandler.areSuggestionsDisabled(testUserId);
      expect(isDisabled).toBe(true);
    });
  });

  describe('enableAllSuggestions', () => {
    it('should enable suggestions after being disabled', async () => {
      await dismissHandler.disableAllSuggestions(testUserId);
      await dismissHandler.enableAllSuggestions(testUserId);

      const isDisabled = await dismissHandler.areSuggestionsDisabled(testUserId);
      expect(isDisabled).toBe(false);
    });
  });

  describe('areSuggestionsDisabled', () => {
    it('should return false by default', async () => {
      const isDisabled = await dismissHandler.areSuggestionsDisabled('U_NEW_USER');
      expect(isDisabled).toBe(false);
    });

    it('should return true after disabling', async () => {
      await dismissHandler.disableAllSuggestions(testUserId);

      const isDisabled = await dismissHandler.areSuggestionsDisabled(testUserId);
      expect(isDisabled).toBe(true);
    });
  });

  // =====================================================================
  // Should Show Suggestion Tests
  // =====================================================================

  describe('shouldShowSuggestion', () => {
    it('should return false if suggestion was dismissed', async () => {
      await dismissHandler.recordDismissal(testUserId, testSuggestionId, testMetadata);

      const shouldShow = await dismissHandler.shouldShowSuggestion(testUserId, testSuggestionId);
      expect(shouldShow).toBe(false);
    });

    it('should return false if all suggestions disabled', async () => {
      await dismissHandler.disableAllSuggestions(testUserId);

      const shouldShow = await dismissHandler.shouldShowSuggestion(testUserId, 'any_suggestion');
      expect(shouldShow).toBe(false);
    });

    it('should return true if not dismissed and not globally disabled', async () => {
      const shouldShow = await dismissHandler.shouldShowSuggestion(testUserId, 'new_suggestion');
      expect(shouldShow).toBe(true);
    });

    it('should handle Redis errors by defaulting to show', async () => {
      const shouldShow = await dismissHandler.shouldShowSuggestion('', '');
      expect(shouldShow).toBe(true); // Default to showing on error
    });
  });

  // =====================================================================
  // Statistics Tests
  // =====================================================================

  describe('getStatistics', () => {
    it('should return statistics for user', async () => {
      await dismissHandler.recordDismissal(testUserId, 'sugg_1', testMetadata);
      await dismissHandler.recordDismissal(testUserId, 'sugg_2', testMetadata);

      const stats = await dismissHandler.getStatistics(testUserId);

      expect(stats.total_dismissed).toBe(2);
      expect(stats.suggestions_disabled).toBe(false);
      expect(stats.recent_dismissals).toBeDefined();
    });

    it('should include global disable status', async () => {
      await dismissHandler.disableAllSuggestions(testUserId);

      const stats = await dismissHandler.getStatistics(testUserId);

      expect(stats.suggestions_disabled).toBe(true);
    });

    it('should return empty stats for new user', async () => {
      const stats = await dismissHandler.getStatistics('U_NEW_USER');

      expect(stats.total_dismissed).toBe(0);
      expect(stats.suggestions_disabled).toBe(false);
      expect(stats.recent_dismissals).toEqual([]);
    });

    it('should handle errors gracefully', async () => {
      const stats = await dismissHandler.getStatistics('');

      expect(stats.error).toBeDefined();
    });
  });

  // =====================================================================
  // Integration Tests
  // =====================================================================

  describe('Integration: Full Workflow', () => {
    it('should handle complete dismiss-clear-show workflow', async () => {
      // 1. New suggestion should show
      let shouldShow = await dismissHandler.shouldShowSuggestion(testUserId, testSuggestionId);
      expect(shouldShow).toBe(true);

      // 2. User dismisses
      await dismissHandler.recordDismissal(testUserId, testSuggestionId, testMetadata);

      // 3. Should not show dismissed suggestion
      shouldShow = await dismissHandler.shouldShowSuggestion(testUserId, testSuggestionId);
      expect(shouldShow).toBe(false);

      // 4. Clear dismissal
      await dismissHandler.clearDismissal(testUserId, testSuggestionId);

      // 5. Should show again
      shouldShow = await dismissHandler.shouldShowSuggestion(testUserId, testSuggestionId);
      expect(shouldShow).toBe(true);
    });

    it('should handle global disable workflow', async () => {
      // 1. Disable all suggestions
      await dismissHandler.disableAllSuggestions(testUserId);

      // 2. No suggestions should show
      let shouldShow = await dismissHandler.shouldShowSuggestion(testUserId, 'any_id');
      expect(shouldShow).toBe(false);

      // 3. Re-enable
      await dismissHandler.enableAllSuggestions(testUserId);

      // 4. Suggestions should show again
      shouldShow = await dismissHandler.shouldShowSuggestion(testUserId, 'any_id');
      expect(shouldShow).toBe(true);
    });

    it('should handle statistics across multiple operations', async () => {
      // Record multiple dismissals
      await dismissHandler.recordDismissal(testUserId, 'sugg_1', testMetadata);
      await dismissHandler.recordDismissal(testUserId, 'sugg_2', testMetadata);
      await dismissHandler.recordDismissal(testUserId, 'sugg_3', testMetadata);

      // Clear one
      await dismissHandler.clearDismissal(testUserId, 'sugg_2');

      // Get stats
      const stats = await dismissHandler.getStatistics(testUserId);

      expect(stats.total_dismissed).toBe(2); // 3 - 1 cleared
      expect(stats.recent_dismissals.length).toBe(2);
    });
  });
});

console.log('✓ Similar Query Dismiss unit tests defined');
console.log('  Coverage: recordDismissal, wasDismissed, getDismissedSuggestions,');
console.log('           clearDismissal, clearAllDismissals, disableAllSuggestions,');
console.log('           enableAllSuggestions, areSuggestionsDisabled, shouldShowSuggestion,');
console.log('           getStatistics + integration scenarios');
