/**
 * Contract Test: BMS API /ask Endpoint
 *
 * T008: Validate BMS API request/response schemas
 * This test MUST FAIL initially (no BMS integration exists yet)
 */

const axios = require('axios');

describe('BMS API /ask Endpoint Contract', () => {
  const BMS_API_URL = process.env.BMS_API_URL || 'http://localhost:8000';
  const ASK_ENDPOINT = `${BMS_API_URL}/api/v1/ask`;
  const SEARCH_ENDPOINT = `${BMS_API_URL}/api/v1/search/semantic`;

  describe('/api/v1/ask Request Schema', () => {
    test('should accept valid ask request', async () => {
      const validRequest = {
        query: 'What are the emergency brake procedures for Class 395 trains?',
        max_chunks: 5,
        include_citations: true
      };

      const response = await axios.post(ASK_ENDPOINT, validRequest, {
        timeout: 3000,
        headers: { 'Content-Type': 'application/json' }
      });

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
    });

    test('should handle minimal ask request', async () => {
      const minimalRequest = {
        query: 'VLAN configuration'
      };

      const response = await axios.post(ASK_ENDPOINT, minimalRequest, {
        timeout: 3000,
        headers: { 'Content-Type': 'application/json' }
      });

      expect(response.status).toBe(200);
    });

    test('should reject empty query', async () => {
      const invalidRequest = {
        query: ''
      };

      await expect(
        axios.post(ASK_ENDPOINT, invalidRequest, { timeout: 3000 })
      ).rejects.toMatchObject({
        response: {
          status: 422
        }
      });
    });
  });

  describe('/api/v1/ask Response Schema', () => {
    test('should return answer with required fields', async () => {
      const request = {
        query: 'What are brake procedures?',
        max_chunks: 3,
        include_citations: true
      };

      const response = await axios.post(ASK_ENDPOINT, request, { timeout: 3000 });

      expect(response.status).toBe(200);
      expect(response.data).toMatchObject({
        status: expect.stringMatching(/success|partial/),
        answer: expect.any(String),
        citations: expect.any(Array),
        confidence: expect.any(Number)
      });

      expect(response.data.answer.length).toBeGreaterThan(0);
      expect(response.data.confidence).toBeGreaterThanOrEqual(0);
      expect(response.data.confidence).toBeLessThanOrEqual(1);
    });

    test('should include citation metadata', async () => {
      const request = {
        query: 'emergency systems VLAN',
        include_citations: true
      };

      const response = await axios.post(ASK_ENDPOINT, request, { timeout: 3000 });

      if (response.data.citations && response.data.citations.length > 0) {
        const citation = response.data.citations[0];
        expect(citation).toMatchObject({
          document_name: expect.any(String),
          relevance_score: expect.any(Number),
          text: expect.any(String)
        });
      }
    });

    test('should handle no results scenario', async () => {
      const request = {
        query: 'xyznonexistentquery12345'
      };

      const response = await axios.post(ASK_ENDPOINT, request, { timeout: 3000 });

      expect(response.status).toBe(200);
      expect(response.data.status).toMatch(/no_results|partial/);
    });
  });

  describe('/api/v1/search/semantic Request Schema', () => {
    test('should accept valid search request', async () => {
      const validRequest = {
        query: 'brake procedures',
        limit: 5,
        min_score: 0.7
      };

      const response = await axios.post(SEARCH_ENDPOINT, validRequest, {
        timeout: 3000,
        headers: { 'Content-Type': 'application/json' }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('results');
    });

    test('should handle search without filters', async () => {
      const minimalRequest = {
        query: 'VLAN configuration'
      };

      const response = await axios.post(SEARCH_ENDPOINT, minimalRequest, {
        timeout: 3000
      });

      expect(response.status).toBe(200);
      expect(Array.isArray(response.data.results)).toBe(true);
    });
  });

  describe('/api/v1/search/semantic Response Schema', () => {
    test('should return results with required fields', async () => {
      const request = {
        query: 'emergency brake',
        limit: 3
      };

      const response = await axios.post(SEARCH_ENDPOINT, request, { timeout: 3000 });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('results');
      expect(Array.isArray(response.data.results)).toBe(true);

      if (response.data.results.length > 0) {
        const result = response.data.results[0];
        expect(result).toMatchObject({
          text: expect.any(String),
          score: expect.any(Number),
          metadata: expect.any(Object)
        });
      }
    });
  });

  describe('Error Handling', () => {
    test('should handle BMS API unavailable', async () => {
      const INVALID_URL = 'http://localhost:9999/api/v1/ask';
      const request = { query: 'test' };

      await expect(
        axios.post(INVALID_URL, request, { timeout: 1000 })
      ).rejects.toThrow();
    });

    test('should respect timeout (2.5s max)', async () => {
      const request = {
        query: 'complex query requiring long processing'
      };

      const startTime = Date.now();

      try {
        await axios.post(ASK_ENDPOINT, request, { timeout: 2500 });
      } catch (error) {
        const elapsed = Date.now() - startTime;
        if (error.code === 'ECONNABORTED') {
          expect(elapsed).toBeLessThanOrEqual(2600); // 100ms buffer
        }
      }
    });
  });
});
