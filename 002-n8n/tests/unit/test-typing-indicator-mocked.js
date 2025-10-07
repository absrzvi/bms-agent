/**
 * Mocked Typing Indicator Tests (Task 1.3 - Coverage Remediation)
 *
 * Purpose: Test typing-indicator.js with mocked MS Teams Bot Framework API
 * Strategy: Mock axios for HTTP requests, use fake timers for intervals
 * Coverage Target: +5% (typing-indicator.js from 0% → 40%)
 */

const axios = require('axios');
const MockAdapter = require('axios-mock-adapter');

describe('TypingIndicatorHandler (Mocked) - Task 1.3', () => {
  let handler;
  let mockAxios;

  beforeEach(() => {
    // Clear module cache to get fresh instance
    jest.resetModules();
    handler = require('../../lib/typing-indicator');
    mockAxios = new MockAdapter(axios);
    jest.useFakeTimers();
  });

  afterEach(() => {
    mockAxios.restore();
    handler.cleanup();
    jest.useRealTimers();
  });

  // ===== Single Typing Indicator Tests =====

  test('should send typing activity to Bot Framework API', async () => {
    mockAxios.onPost('https://smba.trafficmanager.net/teams/v3/conversations/conv-123/activities')
      .reply(200, { id: 'activity-123' });

    const result = await handler.sendTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456'
    );

    expect(result).toBe(true);
    expect(mockAxios.history.post.length).toBe(1);

    const request = mockAxios.history.post[0];
    expect(request.url).toContain('conv-123/activities');
    expect(JSON.parse(request.data).type).toBe('typing');
    expect(JSON.parse(request.data).from.id).toBe('bot-456');
  });

  test('should handle Bot Framework API error gracefully', async () => {
    mockAxios.onPost().reply(401, { error: 'Unauthorized' });

    const result = await handler.sendTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456'
    );

    expect(result).toBe(false);
  });

  test('should handle network timeout gracefully', async () => {
    mockAxios.onPost().timeout();

    const result = await handler.sendTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456'
    );

    expect(result).toBe(false);
  });

  test('should send single indicator via sendSingleIndicator', async () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const result = await handler.sendSingleIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456'
    );

    expect(result).toBe(true);
    expect(mockAxios.history.post.length).toBe(1);
  });

  // ===== Continuous Typing Indicator Tests =====

  test('should start continuous typing indicator', () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const indicatorId = handler.startTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456'
    );

    expect(indicatorId).toBeTruthy();
    expect(indicatorId).toContain('conv-123');
    expect(handler.getActiveCount()).toBe(1);
  });

  test('should send typing indicator immediately on start', () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    handler.startTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456'
    );

    // Should have sent one indicator immediately
    expect(mockAxios.history.post.length).toBeGreaterThan(0);
  });

  test('should auto-refresh typing indicator every 3 seconds', () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    handler.startTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456'
    );

    const initialCount = mockAxios.history.post.length;

    // Advance time by 9 seconds (3 cycles)
    jest.advanceTimersByTime(9000);

    // Should have sent 3 additional indicators (plus the initial one)
    expect(mockAxios.history.post.length).toBeGreaterThanOrEqual(initialCount + 3);
  });

  test('should stop typing indicator', () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const indicatorId = handler.startTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456'
    );

    expect(handler.getActiveCount()).toBe(1);

    handler.stopTypingIndicator(indicatorId);

    expect(handler.getActiveCount()).toBe(0);
  });

  test('should not send more indicators after stop', () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const indicatorId = handler.startTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456'
    );

    const countBeforeStop = mockAxios.history.post.length;

    handler.stopTypingIndicator(indicatorId);

    // Advance time after stopping
    jest.advanceTimersByTime(9000);

    // Should not have sent any new indicators
    expect(mockAxios.history.post.length).toBe(countBeforeStop);
  });

  test('should handle stop on non-existent indicator gracefully', () => {
    expect(() => {
      handler.stopTypingIndicator('non-existent-id');
    }).not.toThrow();
  });

  // ===== Wrap Operation with Indicator Tests =====

  test('should wrap async operation with typing indicator', async () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const mockOperation = jest.fn().mockResolvedValue('operation result');

    const result = await handler.withTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456',
      mockOperation
    );

    expect(result).toBe('operation result');
    expect(mockOperation).toHaveBeenCalledTimes(1);
    expect(handler.getActiveCount()).toBe(0); // Indicator should be stopped
  });

  test('should stop indicator even if operation fails', async () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const mockOperation = jest.fn().mockRejectedValue(new Error('Operation failed'));

    await expect(
      handler.withTypingIndicator(
        'https://smba.trafficmanager.net/teams',
        'conv-123',
        'bot-456',
        mockOperation
      )
    ).rejects.toThrow('Operation failed');

    // Indicator should still be stopped
    expect(handler.getActiveCount()).toBe(0);
  });

  test('should handle long-running operation with continuous typing', async () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const longOperation = () => {
      return new Promise(resolve => {
        jest.advanceTimersByTime(10000); // Simulate 10 second operation
        resolve('done');
      });
    };

    const indicatorCountBefore = mockAxios.history.post.length;

    await handler.withTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456',
      longOperation
    );

    // Should have sent multiple indicators during operation
    expect(mockAxios.history.post.length).toBeGreaterThan(indicatorCountBefore + 2);
  });

  // ===== Multiple Indicators Tests =====

  test('should support multiple concurrent indicators', () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const id1 = handler.startTypingIndicator('https://teams.com', 'conv-1', 'bot-1');
    const id2 = handler.startTypingIndicator('https://teams.com', 'conv-2', 'bot-1');

    expect(handler.getActiveCount()).toBe(2);
    expect(id1).not.toBe(id2);
  });

  test('should stop specific indicator without affecting others', () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const id1 = handler.startTypingIndicator('https://teams.com', 'conv-1', 'bot-1');
    const id2 = handler.startTypingIndicator('https://teams.com', 'conv-2', 'bot-1');

    handler.stopTypingIndicator(id1);

    expect(handler.getActiveCount()).toBe(1);
  });

  // ===== Cleanup Tests =====

  test('should cleanup all active indicators', () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    handler.startTypingIndicator('https://teams.com', 'conv-1', 'bot-1');
    handler.startTypingIndicator('https://teams.com', 'conv-2', 'bot-1');
    handler.startTypingIndicator('https://teams.com', 'conv-3', 'bot-1');

    expect(handler.getActiveCount()).toBe(3);

    handler.cleanup();

    expect(handler.getActiveCount()).toBe(0);
  });

  test('should handle cleanup with no active indicators', () => {
    expect(() => {
      handler.cleanup();
    }).not.toThrow();
  });

  // ===== Edge Cases =====

  test('should handle empty conversation ID', async () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const result = await handler.sendTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      '',
      'bot-456'
    );

    // Should not throw, but may fail API call
    expect(typeof result).toBe('boolean');
  });

  test('should handle malformed service URL', async () => {
    mockAxios.onPost().networkError();

    const result = await handler.sendTypingIndicator(
      'invalid-url',
      'conv-123',
      'bot-456'
    );

    expect(result).toBe(false);
  });

  test('should handle Bot Framework 403 Forbidden', async () => {
    mockAxios.onPost().reply(403, { error: 'Forbidden' });

    const result = await handler.sendTypingIndicator(
      'https://smba.trafficmanager.net/teams',
      'conv-123',
      'bot-456'
    );

    expect(result).toBe(false);
  });

  test('should use 3 second indicator duration', () => {
    expect(handler.indicatorDuration).toBe(3000);
  });

  test('should generate unique indicator IDs for same conversation', () => {
    mockAxios.onPost().reply(200, { id: 'activity-123' });

    const id1 = handler.startTypingIndicator('https://teams.com', 'conv-1', 'bot-1');
    const id2 = handler.startTypingIndicator('https://teams.com', 'conv-1', 'bot-1');

    expect(id1).not.toBe(id2); // Different IDs even for same conversation
  });
});
