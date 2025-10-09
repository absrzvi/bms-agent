/**
 * Unit tests for Prometheus metrics system
 *
 * Tests prometheus-exporter.js and instrumentation.js modules
 */

const metrics = require('../../lib/prometheus-exporter');
const instrument = require('../../lib/instrumentation');

describe('Prometheus Metrics System', () => {
  beforeEach(async () => {
    // Clean up any existing test metrics
    // Note: In production, use a separate Redis database for tests
  });

  afterAll(async () => {
    await metrics.close();
  });

  describe('Counter Metrics', () => {
    test('should increment counter', async () => {
      await metrics.incrementCounter('test_counter', { label: 'value' });
      const output = await metrics.getMetrics();

      expect(output).toContain('test_counter');
      expect(output).toContain('label="value"');
    });

    test('should increment by custom value', async () => {
      await metrics.incrementCounter('test_counter_custom', {}, 5);
      const output = await metrics.getMetrics();

      expect(output).toContain('test_counter_custom 5');
    });
  });

  describe('Latency Metrics', () => {
    test('should record latency values', async () => {
      await metrics.recordLatency('test_latency', 150);
      await metrics.recordLatency('test_latency', 250);
      await metrics.recordLatency('test_latency', 350);

      const output = await metrics.getMetrics();

      expect(output).toContain('test_latency');
      expect(output).toContain('_bucket');
      expect(output).toContain('_sum');
      expect(output).toContain('_count');
    });
  });

  describe('Gauge Metrics', () => {
    test('should set gauge value', async () => {
      await metrics.setGauge('test_gauge', 42);
      const output = await metrics.getMetrics();

      expect(output).toContain('test_gauge 42');
    });

    test('should update gauge value', async () => {
      await metrics.setGauge('test_gauge_update', 10);
      await metrics.setGauge('test_gauge_update', 20);

      const output = await metrics.getMetrics();
      expect(output).toContain('test_gauge_update 20');
    });
  });

  describe('Instrumentation Helper', () => {
    test('should track request with command type', async () => {
      const items = [{ json: { conversation_id: 'test-123' } }];
      await instrument.trackRequest('ask', items);

      const output = await metrics.getMetrics();
      expect(output).toContain('slack_bot_requests_total');
      expect(output).toContain('command_type="ask"');
    });

    test('should track errors', async () => {
      await instrument.trackError('test_error', new Error('Test error'));

      const output = await metrics.getMetrics();
      expect(output).toContain('slack_bot_errors_total');
      expect(output).toContain('error_type="test_error"');
    });

    test('should track latency with timer', async () => {
      const stop = instrument.startTimer('test_operation');

      // Simulate some work
      await new Promise(resolve => setTimeout(resolve, 100));

      const latency = await stop();

      expect(latency).toBeGreaterThanOrEqual(100);

      const output = await metrics.getMetrics();
      expect(output).toContain('slack_bot_test_operation_latency_seconds');
    });

    test('should track BMS API calls', async () => {
      await instrument.trackBmsApiCall('ask', 250, 200);

      const output = await metrics.getMetrics();
      expect(output).toContain('bms_api_call_latency_seconds');
      expect(output).toContain('endpoint="ask"');
    });

    test('should track document uploads', async () => {
      await instrument.trackDocumentUpload('success', {
        file_type: 'pdf',
        processing_time_ms: 500
      });

      const output = await metrics.getMetrics();
      expect(output).toContain('slack_bot_document_uploads_total');
      expect(output).toContain('status="success"');
      expect(output).toContain('file_type="pdf"');
    });
  });

  describe('Prometheus Format', () => {
    test('should output valid Prometheus format', async () => {
      await metrics.incrementCounter('valid_format_test', { env: 'test' });

      const output = await metrics.getMetrics();

      // Check for valid Prometheus format
      expect(output).toMatch(/^# Slack Bot Metrics/);
      expect(output).toMatch(/# TYPE \w+ (counter|gauge|histogram)/);
      expect(output).toMatch(/\w+(\{[^}]+\})? \d+/);
    });

    test('should include metadata comments', async () => {
      const output = await metrics.getMetrics();

      expect(output).toContain('# Slack Bot Metrics');
      expect(output).toMatch(/# Generated at \d{4}-\d{2}-\d{2}/);
    });
  });
});
