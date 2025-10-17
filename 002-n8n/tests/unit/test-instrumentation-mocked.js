/**
 * Mocked Instrumentation Tests (Priority 2 - Test Coverage Remediation)
 *
 * Purpose: Test instrumentation.js with mocked prometheus-exporter dependency
 * Coverage Goal: +12% (instrumentation.js from 0% → 70-80%)
 * Strategy: Mock prometheus metrics functions to avoid real metric collection
 */

// Mock prometheus-exporter before importing instrumentation
jest.mock('../../lib/prometheus-exporter', () => ({
  incrementCounter: jest.fn().mockResolvedValue(undefined),
  setGauge: jest.fn().mockResolvedValue(undefined),
  recordLatency: jest.fn().mockResolvedValue(undefined)
}));

// Mock fs for logToolCall tests
jest.mock('fs');

const instrumentation = require('../../lib/instrumentation');
const metrics = require('../../lib/prometheus-exporter');
const fs = require('fs');

describe('Instrumentation (Mocked) - Priority 2', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset environment variables
    delete process.env.TOOL_CALL_LOG_PATH;
    delete process.env.MAX_TOOL_LOG_SIZE_MB;
  });

  describe('trackRequest', () => {
    test('should track request with command type', async () => {
      await instrumentation.trackRequest('ask', [
        { json: { conversation_id: 'conv-123' } }
      ]);

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_requests_total',
        { command_type: 'ask' }
      );
    });

    test('should update active conversations gauge', async () => {
      const items = [
        { json: { conversation_id: 'conv-1' } },
        { json: { conversation_id: 'conv-2' } },
        { json: { conversation_id: 'conv-1' } } // duplicate
      ];

      await instrumentation.trackRequest('search', items);

      expect(metrics.setGauge).toHaveBeenCalledWith(
        'slack_bot_active_conversations',
        2 // unique conversations
      );
    });

    test('should handle empty items array', async () => {
      await instrumentation.trackRequest('help', []);

      expect(metrics.incrementCounter).toHaveBeenCalled();
      expect(metrics.setGauge).not.toHaveBeenCalled();
    });

    test('should handle items without conversation_id', async () => {
      await instrumentation.trackRequest('status', [
        { json: { text: '/status' } }
      ]);

      expect(metrics.incrementCounter).toHaveBeenCalled();
      expect(metrics.setGauge).not.toHaveBeenCalled();
    });

    test('should handle metrics errors gracefully', async () => {
      metrics.incrementCounter.mockRejectedValueOnce(new Error('Metrics unavailable'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await instrumentation.trackRequest('ask', []);

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to track request:',
        'Metrics unavailable'
      );

      consoleSpy.mockRestore();
    });
  });

  describe('trackError', () => {
    test('should track error with type and labels', async () => {
      await instrumentation.trackError('validation_error', new Error('Invalid input'), {
        endpoint: 'ask'
      });

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_errors_total',
        {
          error_type: 'validation_error',
          endpoint: 'ask'
        }
      );
    });

    test('should handle string error', async () => {
      await instrumentation.trackError('redis_error', 'Connection timeout');

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_errors_total',
        { error_type: 'redis_error' }
      );
    });

    test('should handle error without labels', async () => {
      await instrumentation.trackError('bms_api_timeout');

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_errors_total',
        { error_type: 'bms_api_timeout' }
      );
    });

    test('should handle metrics errors gracefully', async () => {
      metrics.incrementCounter.mockRejectedValueOnce(new Error('Metrics down'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await instrumentation.trackError('test_error');

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to track error:',
        'Metrics down'
      );

      consoleSpy.mockRestore();
    });
  });

  describe('trackLatency', () => {
    test('should track operation latency', async () => {
      await instrumentation.trackLatency('bms_api_call', 1500, {
        endpoint: 'ask',
        status: '2xx'
      });

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_bms_api_call_latency_seconds',
        1500,
        { endpoint: 'ask', status: '2xx' }
      );
    });

    test('should use special metric name for total_response', async () => {
      await instrumentation.trackLatency('total_response', 2500, {
        workflow: 'query-analyzer'
      });

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_response_latency_seconds',
        2500,
        { workflow: 'query-analyzer' }
      );
    });

    test('should handle latency without labels', async () => {
      await instrumentation.trackLatency('redis_query', 50);

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_redis_query_latency_seconds',
        50,
        {}
      );
    });

    test('should handle metrics errors gracefully', async () => {
      metrics.recordLatency.mockRejectedValueOnce(new Error('Metrics error'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await instrumentation.trackLatency('test_op', 100);

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to track latency:',
        'Metrics error'
      );

      consoleSpy.mockRestore();
    });
  });

  describe('trackDocumentUpload', () => {
    test('should track successful upload with metadata', async () => {
      await instrumentation.trackDocumentUpload('success', {
        file_type: 'pdf',
        size_kb: 1024,
        processing_time_ms: 5000
      });

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_document_uploads_total',
        { status: 'success', file_type: 'pdf' }
      );

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'document_processing_latency_seconds',
        5000
      );
    });

    test('should handle upload without processing time', async () => {
      await instrumentation.trackDocumentUpload('failed', {
        file_type: 'xlsx'
      });

      expect(metrics.incrementCounter).toHaveBeenCalled();
      expect(metrics.recordLatency).not.toHaveBeenCalled();
    });

    test('should default file_type to unknown', async () => {
      await instrumentation.trackDocumentUpload('success', {});

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_document_uploads_total',
        { status: 'success', file_type: 'unknown' }
      );
    });

    test('should handle metrics errors gracefully', async () => {
      metrics.incrementCounter.mockRejectedValueOnce(new Error('Metrics fail'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await instrumentation.trackDocumentUpload('success', { file_type: 'pdf' });

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to track document upload:',
        'Metrics fail'
      );

      consoleSpy.mockRestore();
    });
  });

  describe('trackBmsApiCall', () => {
    test('should track successful API call', async () => {
      await instrumentation.trackBmsApiCall('ask', 1200, 200);

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'bms_api_call_latency_seconds',
        1200,
        { endpoint: 'ask', status: '2xx' }
      );
    });

    test('should track error for 4xx status codes', async () => {
      await instrumentation.trackBmsApiCall('search', 800, 404);

      expect(metrics.recordLatency).toHaveBeenCalled();
      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_errors_total',
        { error_type: 'bms_api_error', endpoint: 'search', status_code: 404 }
      );
    });

    test('should track error for 5xx status codes', async () => {
      await instrumentation.trackBmsApiCall('upload', 3000, 503);

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_errors_total',
        { error_type: 'bms_api_error', endpoint: 'upload', status_code: 503 }
      );
    });

    test('should not track error for 3xx status codes', async () => {
      await instrumentation.trackBmsApiCall('redirect', 100, 302);

      expect(metrics.recordLatency).toHaveBeenCalled();
      expect(metrics.incrementCounter).not.toHaveBeenCalled();
    });

    test('should handle metrics errors gracefully', async () => {
      metrics.recordLatency.mockRejectedValueOnce(new Error('Metrics down'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await instrumentation.trackBmsApiCall('ask', 1000, 200);

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to track BMS API call:',
        'Metrics down'
      );

      consoleSpy.mockRestore();
    });
  });

  describe('startTimer', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    test('should create timer and record latency on stop', async () => {
      const stop = instrumentation.startTimer('test_operation', { test: 'label' });

      // Advance time by 500ms
      jest.advanceTimersByTime(500);

      const latencyMs = await stop();

      expect(latencyMs).toBeGreaterThanOrEqual(500);
      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_test_operation_latency_seconds',
        expect.any(Number),
        { test: 'label' }
      );
    });

    test('should handle timer without labels', async () => {
      const stop = instrumentation.startTimer('simple_op');

      jest.advanceTimersByTime(100);

      await stop();

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_simple_op_latency_seconds',
        expect.any(Number),
        {}
      );
    });
  });

  describe('instrumentWorkflow', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    test('should track workflow execution without error', async () => {
      const items = [{ json: { text: '/ask test question' } }];
      const stop = await instrumentation.instrumentWorkflow('query-analyzer', items);

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_requests_total',
        { command_type: 'ask' }
      );

      jest.advanceTimersByTime(1000);

      await stop();

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_response_latency_seconds',
        expect.any(Number),
        { workflow: 'query-analyzer' }
      );
    });

    test('should track workflow execution with error', async () => {
      const items = [{ json: { text: '/search query' } }];
      const stop = await instrumentation.instrumentWorkflow('bms-api-caller', items);

      jest.advanceTimersByTime(500);

      const error = new Error('BMS API timeout');
      await stop(error);

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_errors_total',
        expect.objectContaining({
          error_type: 'workflow_error',
          workflow: 'bms-api-caller'
        })
      );
    });

    test('should return latency from stop function', async () => {
      const stop = await instrumentation.instrumentWorkflow('test-workflow', []);

      jest.advanceTimersByTime(750);

      const latencyMs = await stop();

      expect(latencyMs).toBeGreaterThanOrEqual(750);
    });
  });

  // inferCommandType is an internal helper function, not exported
  // It's tested indirectly through instrumentWorkflow tests

  describe('logToolCall', () => {
    beforeEach(() => {
      fs.existsSync = jest.fn().mockReturnValue(true);
      fs.mkdirSync = jest.fn();
      fs.appendFileSync = jest.fn();
      fs.statSync = jest.fn().mockReturnValue({ size: 1024 * 1024 }); // 1MB
    });

    test('should log tool call with all fields', () => {
      const toolCall = {
        tool_name: 'ask_bms',
        query: 'What are the safety procedures?',
        response_time_ms: 1500,
        result_count: 5,
        confidence_score: 0.95,
        success: true,
        metadata: { endpoint: 'ask' }
      };

      instrumentation.logToolCall(toolCall);

      expect(fs.appendFileSync).toHaveBeenCalled();
      const loggedData = fs.appendFileSync.mock.calls[0][1];
      const parsedLog = JSON.parse(loggedData.trim());

      expect(parsedLog.tool_name).toBe('ask_bms');
      expect(parsedLog.response_time_ms).toBe(1500);
      expect(parsedLog.result_count).toBe(5);
      expect(parsedLog.confidence_score).toBe(0.95);
      expect(parsedLog.success).toBe(true);
      expect(parsedLog.timestamp).toBeDefined();
    });

    test('should create log directory if it does not exist', () => {
      fs.existsSync.mockReturnValueOnce(false);

      instrumentation.logToolCall({
        tool_name: 'test_tool',
        query: 'test',
        response_time_ms: 100,
        result_count: 0,
        success: true
      });

      expect(fs.mkdirSync).toHaveBeenCalledWith(
        expect.stringContaining('logs'),
        { recursive: true }
      );
    });

    test('should handle failed tool call', () => {
      const toolCall = {
        tool_name: 'search_hybrid',
        query: 'test query',
        response_time_ms: 500,
        result_count: 0,
        success: false,
        error_message: 'BMS API timeout'
      };

      instrumentation.logToolCall(toolCall);

      const loggedData = fs.appendFileSync.mock.calls[0][1];
      const parsedLog = JSON.parse(loggedData.trim());

      expect(parsedLog.success).toBe(false);
      expect(parsedLog.error_message).toBe('BMS API timeout');
    });

    test('should sanitize query for PII', () => {
      const toolCall = {
        tool_name: 'ask_bms',
        query: 'Contact john.doe@example.com for details',
        response_time_ms: 100,
        result_count: 1,
        success: true
      };

      instrumentation.logToolCall(toolCall);

      const loggedData = fs.appendFileSync.mock.calls[0][1];
      const parsedLog = JSON.parse(loggedData.trim());

      expect(parsedLog.query).not.toContain('john.doe@example.com');
      expect(parsedLog.query).toContain('[EMAIL]');
    });

    test('should handle logging errors gracefully', () => {
      fs.appendFileSync.mockImplementationOnce(() => {
        throw new Error('Disk full');
      });

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      instrumentation.logToolCall({
        tool_name: 'test',
        query: 'test',
        response_time_ms: 100,
        result_count: 0,
        success: true
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to log tool call:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });

    test.skip('should use custom log path from environment', () => {
      // Skipped: Environment variable is read at module load time,
      // setting it in test doesn't affect already-loaded module
      // This behavior is correct; log path is set at startup
    });
  });

  describe('sanitizeQuery', () => {
    test('should remove email addresses', () => {
      const query = 'Contact support@example.com or admin@test.org';
      const sanitized = instrumentation.sanitizeQuery(query);

      expect(sanitized).not.toContain('support@example.com');
      expect(sanitized).not.toContain('admin@test.org');
      expect(sanitized).toContain('[EMAIL]');
    });

    test('should handle empty query', () => {
      const sanitized = instrumentation.sanitizeQuery('');
      expect(sanitized).toBe('');
    });

    test('should handle null query', () => {
      const sanitized = instrumentation.sanitizeQuery(null);
      expect(sanitized).toBe('');
    });

    test('should handle query without PII', () => {
      const query = 'What are the emergency procedures?';
      const sanitized = instrumentation.sanitizeQuery(query);
      expect(sanitized).toBe(query);
    });
  });
});
