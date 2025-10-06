/**
 * Performance Test: Load Testing with 20 Concurrent Users
 *
 * T015: Simulate 20 concurrent users, 100 queries total
 * Target: p95 < 3000ms, error rate < 5%
 * This test MUST FAIL initially (no workflows deployed)
 */

const axios = require('axios');

// Simple load test implementation (alternative to Locust)
class LoadTester {
  constructor(config) {
    this.webhookUrl = config.webhookUrl;
    this.concurrentUsers = config.concurrentUsers || 20;
    this.queriesPerUser = config.queriesPerUser || 5;
    this.rampUpTime = config.rampUpTime || 5000; // 5 seconds
    this.results = [];
  }

  mockMessage(userId, queryText) {
    return {
      type: 'message',
      id: `load-test-${Date.now()}-${Math.random()}`,
      timestamp: new Date().toISOString(),
      from: {
        id: `29:1load-test-user-${userId}`,
        name: `Load Test User ${userId}`
      },
      conversation: {
        id: `19:load-test-conv-${userId}@thread.tacv2`,
        conversationType: 'personal'
      },
      text: queryText,
      channelId: 'msteams',
      serviceUrl: 'https://smba.trafficmanager.net/emea/'
    };
  }

  async sendQuery(userId, queryIndex) {
    const queries = [
      'What are emergency brake procedures?',
      'VLAN configuration for emergency systems',
      'What are safety guidelines?',
      'Class 395 brake systems',
      'Railway network documentation'
    ];

    const query = queries[queryIndex % queries.length];
    const message = this.mockMessage(userId, query);

    const startTime = Date.now();
    let success = false;
    let statusCode = 0;
    let error = null;

    try {
      const response = await axios.post(this.webhookUrl, message, {
        timeout: 3500
      });

      statusCode = response.status;
      success = response.status === 200;
    } catch (err) {
      error = err.message;
      statusCode = err.response?.status || 0;
    }

    const elapsed = Date.now() - startTime;

    this.results.push({
      userId,
      queryIndex,
      responseTime: elapsed,
      success,
      statusCode,
      error,
      timestamp: new Date().toISOString()
    });

    return { success, elapsed };
  }

  async simulateUser(userId) {
    const results = [];

    for (let i = 0; i < this.queriesPerUser; i++) {
      const result = await this.sendQuery(userId, i);
      results.push(result);

      // Small delay between queries from same user (100-500ms)
      const delay = 100 + Math.random() * 400;
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    return results;
  }

  async run() {
    console.log(`\n=== Load Test Configuration ===`);
    console.log(`Concurrent Users: ${this.concurrentUsers}`);
    console.log(`Queries per User: ${this.queriesPerUser}`);
    console.log(`Total Queries: ${this.concurrentUsers * this.queriesPerUser}`);
    console.log(`Ramp-up Time: ${this.rampUpTime}ms`);
    console.log(`Target: p95 < 3000ms, Error Rate < 5%\n`);

    const startTime = Date.now();

    // Ramp up: Start users gradually
    const userPromises = [];
    const delayBetweenUsers = this.rampUpTime / this.concurrentUsers;

    for (let userId = 0; userId < this.concurrentUsers; userId++) {
      await new Promise(resolve => setTimeout(resolve, delayBetweenUsers));
      userPromises.push(this.simulateUser(userId));
    }

    // Wait for all users to complete
    await Promise.all(userPromises);

    const totalTime = Date.now() - startTime;

    return this.analyzeResults(totalTime);
  }

  analyzeResults(totalTime) {
    const successfulRequests = this.results.filter(r => r.success);
    const failedRequests = this.results.filter(r => !r.success);

    const responseTimes = successfulRequests.map(r => r.responseTime).sort((a, b) => a - b);

    const p50 = responseTimes[Math.floor(responseTimes.length * 0.5)] || 0;
    const p95 = responseTimes[Math.floor(responseTimes.length * 0.95)] || 0;
    const p99 = responseTimes[Math.floor(responseTimes.length * 0.99)] || 0;
    const avg = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length || 0;
    const min = responseTimes[0] || 0;
    const max = responseTimes[responseTimes.length - 1] || 0;

    const errorRate = (failedRequests.length / this.results.length) * 100;
    const throughput = (this.results.length / (totalTime / 1000)).toFixed(2);

    const analysis = {
      totalRequests: this.results.length,
      successfulRequests: successfulRequests.length,
      failedRequests: failedRequests.length,
      errorRate: errorRate.toFixed(2) + '%',
      responseTimes: {
        min: Math.round(min),
        max: Math.round(max),
        avg: Math.round(avg),
        p50: Math.round(p50),
        p95: Math.round(p95),
        p99: Math.round(p99)
      },
      throughput: throughput + ' req/s',
      totalTime: Math.round(totalTime),
      passedSLA: p95 < 3000,
      passedErrorRate: errorRate < 5
    };

    this.printReport(analysis);

    return analysis;
  }

  printReport(analysis) {
    console.log(`\n=== Load Test Results ===`);
    console.log(`Total Requests: ${analysis.totalRequests}`);
    console.log(`Successful: ${analysis.successfulRequests}`);
    console.log(`Failed: ${analysis.failedRequests}`);
    console.log(`Error Rate: ${analysis.errorRate} ${analysis.passedErrorRate ? '✓' : '✗ FAILED'}`);
    console.log(`\nResponse Times (ms):`);
    console.log(`  Min: ${analysis.responseTimes.min}ms`);
    console.log(`  Avg: ${analysis.responseTimes.avg}ms`);
    console.log(`  p50: ${analysis.responseTimes.p50}ms`);
    console.log(`  p95: ${analysis.responseTimes.p95}ms ${analysis.passedSLA ? '✓' : '✗ FAILED (>3000ms)'}`);
    console.log(`  p99: ${analysis.responseTimes.p99}ms`);
    console.log(`  Max: ${analysis.responseTimes.max}ms`);
    console.log(`\nThroughput: ${analysis.throughput}`);
    console.log(`Total Duration: ${analysis.totalTime}ms`);
    console.log(`\n${analysis.passedSLA && analysis.passedErrorRate ? '✓ PASSED' : '✗ FAILED'}`);
  }
}

describe('Load Testing', () => {
  const WEBHOOK_URL = process.env.TEAMS_WEBHOOK_URL || 'http://localhost:5678/webhook/teams';

  describe('20 Concurrent Users - 100 Queries', () => {
    test('should handle 20 concurrent users with p95 < 3000ms', async () => {
      const loadTester = new LoadTester({
        webhookUrl: WEBHOOK_URL,
        concurrentUsers: 20,
        queriesPerUser: 5,
        rampUpTime: 5000
      });

      const results = await loadTester.run();

      // FR-022: Support 20 concurrent users without degradation
      expect(results.successfulRequests).toBeGreaterThan(0);

      // FR-026: Maintain sub-3s response time under load
      expect(results.responseTimes.p95).toBeLessThan(3000);

      // Error rate should be < 5%
      const errorRate = parseFloat(results.errorRate);
      expect(errorRate).toBeLessThan(5);

      // Overall pass criteria
      expect(results.passedSLA).toBe(true);
      expect(results.passedErrorRate).toBe(true);
    }, 120000); // 2 minute timeout for load test
  });

  describe('Sustained Load - 50-100 Queries/Day POC', () => {
    test('should handle burst of 50 queries', async () => {
      const loadTester = new LoadTester({
        webhookUrl: WEBHOOK_URL,
        concurrentUsers: 10,
        queriesPerUser: 5,
        rampUpTime: 3000
      });

      const results = await loadTester.run();

      // FR-025: Handle 50-100 queries/day
      expect(results.totalRequests).toBe(50);
      expect(results.responseTimes.p95).toBeLessThan(3000);

      const errorRate = parseFloat(results.errorRate);
      expect(errorRate).toBeLessThan(5);
    }, 90000);
  });

  describe('Performance Degradation Check', () => {
    test('should not degrade over sequential requests', async () => {
      const iterations = 20;
      const responseTimes = [];

      const message = {
        type: 'message',
        id: `perf-test-${Date.now()}`,
        timestamp: new Date().toISOString(),
        from: {
          id: '29:1perf-test-user',
          name: 'Performance Test User'
        },
        conversation: {
          id: '19:perf-test@thread.tacv2',
          conversationType: 'personal'
        },
        text: 'What are brake procedures?',
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      };

      for (let i = 0; i < iterations; i++) {
        message.id = `perf-test-${Date.now()}-${i}`;
        const startTime = Date.now();

        try {
          await axios.post(WEBHOOK_URL, message, { timeout: 3500 });
          responseTimes.push(Date.now() - startTime);
        } catch (error) {
          // Count timeout as max time
          responseTimes.push(3500);
        }

        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Compare first 5 vs last 5 requests
      const first5 = responseTimes.slice(0, 5);
      const last5 = responseTimes.slice(-5);

      const avgFirst = first5.reduce((a, b) => a + b, 0) / first5.length;
      const avgLast = last5.reduce((a, b) => a + b, 0) / last5.length;

      // Last 5 should not be significantly slower (allow 20% degradation)
      expect(avgLast).toBeLessThan(avgFirst * 1.2);
    }, 90000);
  });

  describe('Mixed Query Types Under Load', () => {
    test('should handle mixed natural language and commands', async () => {
      const queries = [
        'What are emergency brake procedures?',
        '/search VLAN configuration',
        '/ask What is Class 395?',
        'safety guidelines',
        '/help',
        '/history'
      ];

      const results = [];

      const mockMessage = (query, userId) => ({
        type: 'message',
        id: `mixed-${Date.now()}-${userId}`,
        timestamp: new Date().toISOString(),
        from: {
          id: `29:1mixed-user-${userId}`,
          name: `Mixed User ${userId}`
        },
        conversation: {
          id: `19:mixed-test-${userId}@thread.tacv2`,
          conversationType: 'personal'
        },
        text: query,
        channelId: 'msteams',
        serviceUrl: 'https://smba.trafficmanager.net/emea/'
      });

      // Send 10 concurrent requests with mixed query types
      const promises = [];
      for (let i = 0; i < 10; i++) {
        const query = queries[i % queries.length];
        const message = mockMessage(query, i);

        promises.push(
          axios.post(WEBHOOK_URL, message, { timeout: 3500 })
            .then(res => ({ success: true, status: res.status }))
            .catch(err => ({ success: false, error: err.message }))
        );
      }

      const responses = await Promise.all(promises);
      const successCount = responses.filter(r => r.success).length;

      expect(successCount).toBeGreaterThan(8); // At least 80% success
    }, 60000);
  });

  describe('Concurrent Uploads Under Load', () => {
    test('should handle multiple simultaneous file uploads', async () => {
      const uploadMessages = [];

      for (let i = 0; i < 5; i++) {
        uploadMessages.push({
          type: 'message',
          id: `upload-load-${Date.now()}-${i}`,
          timestamp: new Date().toISOString(),
          from: {
            id: `29:1upload-user-${i}`,
            name: `Upload User ${i}`
          },
          conversation: {
            id: `19:upload-conv-${i}@thread.tacv2`,
            conversationType: 'personal'
          },
          text: 'document upload',
          attachments: [
            {
              contentType: 'application/pdf',
              contentUrl: `https://example.com/doc-${i}.pdf`,
              name: `test-doc-${i}.pdf`,
              content: Buffer.from(`PDF content ${i}`).toString('base64')
            }
          ],
          channelId: 'msteams',
          serviceUrl: 'https://smba.trafficmanager.net/emea/'
        });
      }

      const promises = uploadMessages.map(msg =>
        axios.post(WEBHOOK_URL, msg, { timeout: 5000 })
          .then(res => ({ success: true, data: res.data }))
          .catch(err => ({ success: false, error: err.message }))
      );

      const responses = await Promise.all(promises);
      const successCount = responses.filter(r => r.success).length;

      expect(successCount).toBeGreaterThanOrEqual(4); // At least 4/5 should succeed
    }, 60000);
  });

  describe('Post-POC Scale Preparation (50-100 Users)', () => {
    test('should estimate performance for 50 users', async () => {
      // Smaller scale test to estimate 50-user performance
      const loadTester = new LoadTester({
        webhookUrl: WEBHOOK_URL,
        concurrentUsers: 15,
        queriesPerUser: 3,
        rampUpTime: 3000
      });

      const results = await loadTester.run();

      // NFR-005: Should scale to 50-100 users post-POC
      expect(results.responseTimes.p95).toBeLessThan(3000);

      const errorRate = parseFloat(results.errorRate);
      expect(errorRate).toBeLessThan(5);

      // If this passes, 50-user scale is feasible
      console.log(`\n📊 Estimated 50-user capacity: ${results.passedSLA && results.passedErrorRate ? '✓ READY' : '✗ NEEDS OPTIMIZATION'}`);
    }, 90000);

    test('should handle 250-500 queries per day (post-POC)', async () => {
      // Simulate 250 queries over compressed timeframe
      const loadTester = new LoadTester({
        webhookUrl: WEBHOOK_URL,
        concurrentUsers: 25,
        queriesPerUser: 10,
        rampUpTime: 10000
      });

      const results = await loadTester.run();

      // NFR-005a: 5x increase in query volume post-POC
      expect(results.totalRequests).toBe(250);
      expect(results.responseTimes.p95).toBeLessThan(3000);

      const errorRate = parseFloat(results.errorRate);
      expect(errorRate).toBeLessThan(5);

      console.log(`\n📊 Post-POC scale test (250 queries): ${results.passedSLA && results.passedErrorRate ? '✓ PASSED' : '✗ FAILED'}`);
    }, 180000); // 3 minute timeout
  });
});

// CLI execution (if run directly)
if (require.main === module) {
  const WEBHOOK_URL = process.env.TEAMS_WEBHOOK_URL || 'http://localhost:5678/webhook/teams';

  console.log('Starting Load Test...');
  console.log(`Target: ${WEBHOOK_URL}\n`);

  const loadTester = new LoadTester({
    webhookUrl: WEBHOOK_URL,
    concurrentUsers: parseInt(process.env.CONCURRENT_USERS) || 20,
    queriesPerUser: parseInt(process.env.QUERIES_PER_USER) || 5,
    rampUpTime: parseInt(process.env.RAMP_UP_TIME) || 5000
  });

  loadTester.run()
    .then(results => {
      process.exit(results.passedSLA && results.passedErrorRate ? 0 : 1);
    })
    .catch(error => {
      console.error('Load test failed:', error);
      process.exit(1);
    });
}

module.exports = { LoadTester };
