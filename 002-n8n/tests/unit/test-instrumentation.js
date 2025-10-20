/**
 * Unit Tests for Instrumentation Helper
 *
 * Tests workflow instrumentation, metrics tracking, and tool call logging
 */

const fs = require('fs');
const path = require('path');

// Mock prometheus-exporter before requiring instrumentation
jest.mock('../../lib/prometheus-exporter', () => ({
  incrementCounter: jest.fn().mockResolvedValue(undefined),
  setGauge: jest.fn().mockResolvedValue(undefined),
  recordLatency: jest.fn().mockResolvedValue(undefined)
}));

const metrics = require('../../lib/prometheus-exporter');
const instrument = require('../../lib/instrumentation');

// Mock fs for tool call logging tests
jest.mock('fs');

describe('Instrumentation Helper', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Reset console mocks
    jest.spyOn(console, 'error').mockImplementation(() => {});
    jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    console.error.mockRestore();
    console.log.mockRestore();
  });

  // =====================================================================
  // Track Request Tests
  // =====================================================================

  describe('trackRequest', () => {
    it('should increment request counter with command type', async () => {
      await instrument.trackRequest('ask', []);

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_requests_total',
        { command_type: 'ask' }
      );
    });

    it('should update active conversations gauge', async () => {
      const items = [
        { json: { conversation_id: 'C001' } },
        { json: { conversation_id: 'C002' } },
        { json: { conversation_id: 'C001' } } // duplicate
      ];

      await instrument.trackRequest('search', items);

      expect(metrics.setGauge).toHaveBeenCalledWith('slack_bot_active_conversations', 2);
    });

    it('should handle empty items array', async () => {
      await instrument.trackRequest('help', []);

      expect(metrics.incrementCounter).toHaveBeenCalledTimes(1);
      expect(metrics.setGauge).not.toHaveBeenCalled();
    });

    it('should catch and log errors', async () => {
      metrics.incrementCounter.mockRejectedValueOnce(new Error('Metrics error'));

      await instrument.trackRequest('ask', []);

      expect(console.error).toHaveBeenCalledWith(
        'Failed to track request:',
        'Metrics error'
      );
    });
  });

  // =====================================================================
  // Track Error Tests
  // =====================================================================

  describe('trackError', () => {
    it('should increment error counter with error type', async () => {
      await instrument.trackError('bms_api_timeout', new Error('Timeout'));

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_errors_total',
        { error_type: 'bms_api_timeout' }
      );
    });

    it('should include additional labels', async () => {
      await instrument.trackError('validation_error', {}, { field: 'query' });

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_errors_total',
        { error_type: 'validation_error', field: 'query' }
      );
    });

    it('should handle errors gracefully', async () => {
      metrics.incrementCounter.mockRejectedValueOnce(new Error('Counter error'));

      await instrument.trackError('redis_error', new Error('Connection failed'));

      expect(console.error).toHaveBeenCalledWith(
        'Failed to track error:',
        'Counter error'
      );
    });
  });

  // =====================================================================
  // Track Latency Tests
  // =====================================================================

  describe('trackLatency', () => {
    it('should record total response latency', async () => {
      await instrument.trackLatency('total_response', 1500);

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_response_latency_seconds',
        1500,
        {}
      );
    });

    it('should record operation-specific latency', async () => {
      await instrument.trackLatency('bms_api_call', 800, { endpoint: 'ask' });

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_bms_api_call_latency_seconds',
        800,
        { endpoint: 'ask' }
      );
    });

    it('should handle errors silently', async () => {
      metrics.recordLatency.mockRejectedValueOnce(new Error('Latency error'));

      await instrument.trackLatency('redis_query', 50);

      expect(console.error).toHaveBeenCalledWith(
        'Failed to track latency:',
        'Latency error'
      );
    });
  });

  // =====================================================================
  // Track Document Upload Tests
  // =====================================================================

  describe('trackDocumentUpload', () => {
    it('should track successful upload with file type', async () => {
      await instrument.trackDocumentUpload('success', { file_type: 'pdf' });

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_document_uploads_total',
        { status: 'success', file_type: 'pdf' }
      );
    });

    it('should track processing time if provided', async () => {
      await instrument.trackDocumentUpload('success', {
        file_type: 'xlsx',
        processing_time_ms: 3000
      });

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'document_processing_latency_seconds',
        3000
      );
    });

    it('should use unknown file type if not provided', async () => {
      await instrument.trackDocumentUpload('failed', {});

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_document_uploads_total',
        { status: 'failed', file_type: 'unknown' }
      );
    });
  });

  // =====================================================================
  // Track BMS API Call Tests
  // =====================================================================

  describe('trackBmsApiCall', () => {
    it('should record successful API call latency', async () => {
      await instrument.trackBmsApiCall('ask', 1200, 200);

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'bms_api_call_latency_seconds',
        1200,
        { endpoint: 'ask', status: '2xx' }
      );
    });

    it('should track errors for 4xx/5xx responses', async () => {
      await instrument.trackBmsApiCall('search', 5000, 503);

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'bms_api_call_latency_seconds',
        5000,
        { endpoint: 'search', status: '5xx' }
      );

      // Should also track error
      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_errors_total',
        { error_type: 'bms_api_error', endpoint: 'search', status_code: 503 }
      );
    });

    it('should not track errors for 2xx/3xx responses', async () => {
      await instrument.trackBmsApiCall('upload', 800, 201);

      expect(metrics.recordLatency).toHaveBeenCalledTimes(1);
      expect(metrics.incrementCounter).not.toHaveBeenCalled();
    });
  });

  // =====================================================================
  // Timer Tests
  // =====================================================================

  describe('startTimer', () => {
    it('should measure elapsed time', async () => {
      const stop = instrument.startTimer('test_operation');

      // Wait 100ms
      await new Promise(resolve => setTimeout(resolve, 100));

      const latencyMs = await stop();

      expect(latencyMs).toBeGreaterThanOrEqual(100);
      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_test_operation_latency_seconds',
        expect.any(Number),
        {}
      );
    });

    it('should include labels in metric', async () => {
      const stop = instrument.startTimer('db_query', { table: 'users' });
      const latencyMs = await stop();

      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_db_query_latency_seconds',
        latencyMs,
        { table: 'users' }
      );
    });
  });

  // =====================================================================
  // Instrument Workflow Tests
  // =====================================================================

  describe('instrumentWorkflow', () => {
    it('should track request and latency', async () => {
      const items = [{ json: { text: '/ask What is BMS?', conversation_id: 'C001' } }];
      const stop = await instrument.instrumentWorkflow('query-analyzer', items);

      await new Promise(resolve => setTimeout(resolve, 50));

      await stop();

      // Should track request
      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_requests_total',
        { command_type: 'ask' }
      );

      // Should record latency
      expect(metrics.recordLatency).toHaveBeenCalledWith(
        'slack_bot_response_latency_seconds',
        expect.any(Number),
        { workflow: 'query-analyzer' }
      );
    });

    it('should track errors when provided', async () => {
      const items = [{ json: { text: 'search documents' } }];
      const stop = await instrument.instrumentWorkflow('main-bot-handler', items);

      const error = new Error('Workflow failed');
      await stop(error);

      expect(metrics.incrementCounter).toHaveBeenCalledWith(
        'slack_bot_errors_total',
        { error_type: 'workflow_error', workflow: 'main-bot-handler' }
      );
    });

    it('should infer command type from text', async () => {
      const testCases = [
        { text: '/search query', expected: 'search' },
        { text: '/upload', expected: 'upload' },
        { text: '/admin list', expected: 'admin' },
        { text: '/help', expected: 'help' },
        { text: '/status doc123', expected: 'status' },
        { text: '/history', expected: 'history' },
        { text: 'How do brakes work?', expected: 'natural_language' }
      ];

      for (const testCase of testCases) {
        jest.clearAllMocks();
        const items = [{ json: { text: testCase.text } }];
        await instrument.instrumentWorkflow('test', items);

        expect(metrics.incrementCounter).toHaveBeenCalledWith(
          'slack_bot_requests_total',
          { command_type: testCase.expected }
        );
      }
    });
  });

  // =====================================================================
  // Tool Call Logging Tests
  // =====================================================================

  describe('logToolCall', () => {
    const MOCK_LOG_PATH = '/workspace/logs/tool-calls.jsonl';

    beforeEach(() => {
      fs.existsSync.mockReturnValue(true);
      fs.appendFileSync.mockImplementation(() => {});
      fs.mkdirSync.mockImplementation(() => {});
      fs.statSync.mockReturnValue({ size: 1024 * 1024 }); // 1MB
    });

    it('should log tool call with all required fields', () => {
      const toolCall = {
        tool_name: 'ask_bms',
        query: 'What are emergency brakes?',
        response_time_ms: 1200,
        result_count: 5,
        confidence_score: 0.92,
        success: true
      };

      instrument.logToolCall(toolCall);

      expect(fs.appendFileSync).toHaveBeenCalled();
      const loggedData = fs.appendFileSync.mock.calls[0][1];
      const parsedLog = JSON.parse(loggedData.trim());

      expect(parsedLog).toMatchObject({
        tool_name: 'ask_bms',
        query: 'What are emergency brakes?',
        response_time_ms: 1200,
        result_count: 5,
        confidence_score: 0.92,
        success: true,
        error_message: null
      });
      expect(parsedLog.timestamp).toBeDefined();
    });

    it('should sanitize PII from queries', () => {
      const toolCall = {
        tool_name: 'search_hybrid',
        query: 'Contact john.doe@example.com or call 555-123-4567 about U123456789',
        response_time_ms: 800,
        result_count: 3,
        success: true
      };

      instrument.logToolCall(toolCall);

      const loggedData = fs.appendFileSync.mock.calls[0][1];
      const parsedLog = JSON.parse(loggedData.trim());

      expect(parsedLog.query).toBe('Contact [EMAIL] or call [PHONE] about [USER_ID]');
    });

    it('should create logs directory if not exists', () => {
      fs.existsSync.mockReturnValue(false);

      instrument.logToolCall({
        tool_name: 'test_tool',
        query: 'test',
        response_time_ms: 100,
        result_count: 0,
        success: true
      });

      expect(fs.mkdirSync).toHaveBeenCalledWith(
        path.dirname(MOCK_LOG_PATH),
        { recursive: true }
      );
    });

    it('should handle logging errors gracefully', () => {
      fs.appendFileSync.mockImplementation(() => {
        throw new Error('Disk full');
      });

      instrument.logToolCall({
        tool_name: 'test',
        query: 'query',
        response_time_ms: 100,
        result_count: 0,
        success: true
      });

      expect(console.error).toHaveBeenCalledWith(
        'Failed to log tool call:',
        expect.any(Error)
      );
    });
  });

  // =====================================================================
  // Sanitize Query Tests
  // =====================================================================

  describe('sanitizeQuery', () => {
    it('should remove email addresses', () => {
      const result = instrument.sanitizeQuery('Contact admin@example.com');
      expect(result).toBe('Contact [EMAIL]');
    });

    it('should remove phone numbers', () => {
      const result = instrument.sanitizeQuery('Call 555-123-4567 or 5551234567');
      expect(result).toBe('Call [PHONE] or [PHONE]');
    });

    it('should remove Slack user IDs', () => {
      const result = instrument.sanitizeQuery('Ask U123456789 about it');
      expect(result).toBe('Ask [USER_ID] about it');
    });

    it('should truncate long queries to 500 chars', () => {
      const longQuery = 'a'.repeat(600);
      const result = instrument.sanitizeQuery(longQuery);
      expect(result).toHaveLength(500);
    });

    it('should handle empty query', () => {
      expect(instrument.sanitizeQuery('')).toBe('');
      expect(instrument.sanitizeQuery(null)).toBe('');
      expect(instrument.sanitizeQuery(undefined)).toBe('');
    });
  });

  // =====================================================================
  // Get Tool Stats Tests
  // =====================================================================

  describe('getToolStats', () => {
    beforeEach(() => {
      const mockLogData = [
        { timestamp: new Date().toISOString(), tool_name: 'ask_bms', response_time_ms: 1200, success: true },
        { timestamp: new Date().toISOString(), tool_name: 'search_hybrid', response_time_ms: 800, success: true },
        { timestamp: new Date().toISOString(), tool_name: 'ask_bms', response_time_ms: 1500, success: false },
        { timestamp: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(), tool_name: 'ask_bms', response_time_ms: 900, success: true }
      ].map(e => JSON.stringify(e)).join('\n');

      fs.existsSync.mockReturnValue(true);
      fs.readFileSync.mockReturnValue(mockLogData);
    });

    it('should return stats for last 24 hours by default', () => {
      const stats = instrument.getToolStats();

      expect(stats.total).toBe(3); // Excludes 48h old entry
      expect(stats.successful).toBe(2);
      expect(stats.failed).toBe(1);
      expect(stats.success_rate).toBe('66.67%');
    });

    it('should filter by tool name', () => {
      const stats = instrument.getToolStats({ tool_name: 'ask_bms' });

      expect(stats.total).toBe(2);
      expect(stats.by_tool['ask_bms']).toBeDefined();
      expect(stats.by_tool['search_hybrid']).toBeUndefined();
    });

    it('should calculate per-tool averages', () => {
      const stats = instrument.getToolStats();

      expect(stats.by_tool['ask_bms'].count).toBe(2);
      expect(stats.by_tool['ask_bms'].avg_response_time).toBe(1350); // (1200 + 1500) / 2
      expect(stats.by_tool['ask_bms'].success_rate).toBe('50.00%');
    });

    it('should return empty stats if log does not exist', () => {
      fs.existsSync.mockReturnValue(false);

      const stats = instrument.getToolStats();

      expect(stats).toEqual({
        total: 0,
        by_tool: {},
        avg_response_time: 0,
        success_rate: 0
      });
    });

    it('should handle malformed log lines gracefully', () => {
      fs.readFileSync.mockReturnValue('valid line\ninvalid{json\nvalid line');
      fs.existsSync.mockReturnValue(true);

      const stats = instrument.getToolStats();

      // Should not throw, just skip malformed lines
      expect(stats.error).toBeUndefined();
    });
  });
});

console.log('✓ Instrumentation unit tests defined');
console.log('  Coverage: trackRequest, trackError, trackLatency, trackDocumentUpload,');
console.log('           trackBmsApiCall, startTimer, instrumentWorkflow, logToolCall,');
console.log('           sanitizeQuery, getToolStats');
