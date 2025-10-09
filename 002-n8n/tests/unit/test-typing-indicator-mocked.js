/**
 * Mocked Typing Indicator Tests (Task 1.3 - Test Coverage Remediation)
 *
 * Purpose: Test typing-indicator.js with mocked MS Teams API
 * Coverage Goal: +5% (typing-indicator.js from 0% → 40%)
 * Strategy: Mock axios for Bot Framework API calls
 */

jest.mock('axios');
const axios = require('axios');
const handler = require('../../lib/typing-indicator');

describe('TypingIndicatorHandler (Mocked) - Task 1.3', () => {
  const mockServiceUrl = 'https://smba.trafficmanager.net/teams';
  const mockConversationId = 'conv-123';
  const mockBotId = 'bot-456';

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    handler.cleanup(); // Clean up any active indicators
  });

  afterEach(() => {
    jest.useRealTimers();
    handler.cleanup();
  });

  describe('Single Typing Indicator', () => {
    test('should send typing indicator successfully', async () => {
      axios.post.mockResolvedValue({ status: 200 });

      const result = await handler.sendTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      expect(result).toBe(true);
      expect(axios.post).toHaveBeenCalledWith(
        `${mockServiceUrl}/v3/conversations/${mockConversationId}/activities`,
        expect.objectContaining({
          type: 'typing',
          from: expect.objectContaining({
            id: mockBotId,
            name: 'BMS Teams Bot'
          })
        }),
        expect.objectContaining({
          headers: { 'Content-Type': 'application/json' },
          timeout: 5000
        })
      );
    });

    test('should handle API errors gracefully', async () => {
      axios.post.mockRejectedValue(new Error('Network timeout'));

      const result = await handler.sendTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      expect(result).toBe(false);
    });

    test('sendSingleIndicator should call sendTypingIndicator', async () => {
      axios.post.mockResolvedValue({ status: 200 });

      const result = await handler.sendSingleIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      expect(result).toBe(true);
      expect(axios.post).toHaveBeenCalledTimes(1);
    });
  });

  describe('Continuous Typing Indicator', () => {
    test('should start typing indicator', () => {
      axios.post.mockResolvedValue({ status: 200 });

      const indicatorId = handler.startTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      expect(indicatorId).toMatch(/^conv-123-\d+$/);
      expect(handler.getActiveCount()).toBe(1);
    });

    test('should send indicator immediately on start', () => {
      axios.post.mockResolvedValue({ status: 200 });

      handler.startTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      // Should have sent indicator immediately (before any timer fires)
      expect(axios.post).toHaveBeenCalledTimes(1);
    });

    test('should send indicator every 3 seconds', () => {
      axios.post.mockResolvedValue({ status: 200 });

      handler.startTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      // Initial call
      expect(axios.post).toHaveBeenCalledTimes(1);

      // Advance timer by 3 seconds
      jest.advanceTimersByTime(3000);
      expect(axios.post).toHaveBeenCalledTimes(2);

      // Advance another 3 seconds
      jest.advanceTimersByTime(3000);
      expect(axios.post).toHaveBeenCalledTimes(3);

      // Advance another 3 seconds
      jest.advanceTimersByTime(3000);
      expect(axios.post).toHaveBeenCalledTimes(4);
    });

    test('should stop typing indicator', () => {
      axios.post.mockResolvedValue({ status: 200 });

      const indicatorId = handler.startTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      expect(handler.getActiveCount()).toBe(1);

      handler.stopTypingIndicator(indicatorId);

      expect(handler.getActiveCount()).toBe(0);
    });

    test('should not send more indicators after stop', () => {
      axios.post.mockResolvedValue({ status: 200 });

      const indicatorId = handler.startTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      // Initial call
      expect(axios.post).toHaveBeenCalledTimes(1);

      // Stop indicator
      handler.stopTypingIndicator(indicatorId);

      // Advance timer - should NOT send more indicators
      jest.advanceTimersByTime(6000);
      expect(axios.post).toHaveBeenCalledTimes(1); // Still only 1
    });

    test('should handle multiple concurrent indicators', () => {
      axios.post.mockResolvedValue({ status: 200 });

      const id1 = handler.startTypingIndicator(mockServiceUrl, 'conv-1', mockBotId);
      const id2 = handler.startTypingIndicator(mockServiceUrl, 'conv-2', mockBotId);
      const id3 = handler.startTypingIndicator(mockServiceUrl, 'conv-3', mockBotId);

      expect(handler.getActiveCount()).toBe(3);

      handler.stopTypingIndicator(id2);
      expect(handler.getActiveCount()).toBe(2);

      handler.stopTypingIndicator(id1);
      handler.stopTypingIndicator(id3);
      expect(handler.getActiveCount()).toBe(0);
    });

    test('should handle stopping non-existent indicator gracefully', () => {
      handler.stopTypingIndicator('non-existent-id');
      // Should not throw error
      expect(handler.getActiveCount()).toBe(0);
    });
  });

  describe('Typing Indicator Wrapper', () => {
    test('should wrap async operation with typing indicator', async () => {
      axios.post.mockResolvedValue({ status: 200 });

      const mockOperation = jest.fn().mockResolvedValue('operation result');

      const result = await handler.withTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId,
        mockOperation
      );

      expect(result).toBe('operation result');
      expect(mockOperation).toHaveBeenCalled();
      expect(handler.getActiveCount()).toBe(0); // Should be stopped after operation
    });

    test('should stop indicator even if operation throws error', async () => {
      axios.post.mockResolvedValue({ status: 200 });

      const mockOperation = jest.fn().mockRejectedValue(new Error('Operation failed'));

      await expect(
        handler.withTypingIndicator(
          mockServiceUrl,
          mockConversationId,
          mockBotId,
          mockOperation
        )
      ).rejects.toThrow('Operation failed');

      // Indicator should still be stopped
      expect(handler.getActiveCount()).toBe(0);
    });

    test('should send indicators during long operation', async () => {
      axios.post.mockResolvedValue({ status: 200 });

      const mockOperation = jest.fn().mockImplementation(async () => {
        // Simulate 10-second operation
        await new Promise(resolve => setTimeout(resolve, 10000));
        return 'result';
      });

      const promise = handler.withTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId,
        mockOperation
      );

      // Should send initial indicator
      expect(axios.post).toHaveBeenCalledTimes(1);

      // Advance timer through the operation
      jest.advanceTimersByTime(10000);
      await promise;

      // Should have sent multiple indicators (initial + 3 intervals)
      expect(axios.post).toHaveBeenCalledTimes(4);
    });
  });

  describe('Cleanup', () => {
    test('should clean up all active indicators', () => {
      axios.post.mockResolvedValue({ status: 200 });

      handler.startTypingIndicator(mockServiceUrl, 'conv-1', mockBotId);
      handler.startTypingIndicator(mockServiceUrl, 'conv-2', mockBotId);
      handler.startTypingIndicator(mockServiceUrl, 'conv-3', mockBotId);

      expect(handler.getActiveCount()).toBe(3);

      handler.cleanup();

      expect(handler.getActiveCount()).toBe(0);
    });

    test('should handle cleanup with no active indicators', () => {
      handler.cleanup();
      // Should not throw error
      expect(handler.getActiveCount()).toBe(0);
    });
  });

  describe('Active Indicator Tracking', () => {
    test('should track active indicator count', () => {
      axios.post.mockResolvedValue({ status: 200 });

      expect(handler.getActiveCount()).toBe(0);

      const id1 = handler.startTypingIndicator(mockServiceUrl, 'conv-1', mockBotId);
      expect(handler.getActiveCount()).toBe(1);

      const id2 = handler.startTypingIndicator(mockServiceUrl, 'conv-2', mockBotId);
      expect(handler.getActiveCount()).toBe(2);

      handler.stopTypingIndicator(id1);
      expect(handler.getActiveCount()).toBe(1);

      handler.stopTypingIndicator(id2);
      expect(handler.getActiveCount()).toBe(0);
    });
  });

  describe('Error Resilience', () => {
    test('should continue sending indicators even if one fails', () => {
      axios.post
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValue({ status: 200 });

      handler.startTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      // First call fails
      expect(axios.post).toHaveBeenCalledTimes(1);

      // Subsequent calls should still work
      jest.advanceTimersByTime(3000);
      expect(axios.post).toHaveBeenCalledTimes(2);

      jest.advanceTimersByTime(3000);
      expect(axios.post).toHaveBeenCalledTimes(3);
    });

    test('should handle Bot Framework 401 errors', async () => {
      const error = new Error('Unauthorized');
      error.response = { status: 401, data: { error: 'Invalid credentials' } };
      axios.post.mockRejectedValue(error);

      const result = await handler.sendTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      expect(result).toBe(false);
    });

    test('should handle Bot Framework 429 rate limit', async () => {
      const error = new Error('Too Many Requests');
      error.response = { status: 429, data: { error: 'Rate limit exceeded' } };
      axios.post.mockRejectedValue(error);

      const result = await handler.sendTypingIndicator(
        mockServiceUrl,
        mockConversationId,
        mockBotId
      );

      expect(result).toBe(false);
    });
  });
});
