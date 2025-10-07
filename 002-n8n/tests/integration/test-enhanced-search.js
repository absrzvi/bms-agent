/**
 * Integration Test: Enhanced Search Tools
 *
 * T027d: Test new enhanced search capabilities (batch, faceted, explained, latest)
 * Tests the 4 new tool webhook endpoints created in T027b/T027c
 */

const axios = require('axios');

describe('Enhanced Search Tools Integration', () => {
  const TOOL_BASE_URL = process.env.N8N_WEBHOOK_URL || 'http://localhost:5678/webhook';
  const BMS_API_URL = process.env.BMS_API_URL || 'http://localhost:8000';
  const REQUEST_TIMEOUT = 30000; // 30s for search operations

  // Helper to check if BMS API is available
  beforeAll(async () => {
    try {
      const response = await axios.get(`${BMS_API_URL}/health`, { timeout: 5000 });
      if (response.data.status !== 'healthy') {
        console.warn('⚠️  BMS API is not healthy, tests may fail');
      }
    } catch (error) {
      console.warn('⚠️  BMS API is not reachable, tests will fail:', error.message);
    }
  });

  describe('Batch Search Tool', () => {
    const BATCH_SEARCH_URL = `${TOOL_BASE_URL}/tool-batch-search`;

    test('should return union of results for multiple queries', async () => {
      const payload = {
        queries: ['safety procedures', 'emergency protocols', 'track maintenance'],
        mode: 'union',
        limit: 5
      };

      const response = await axios.post(BATCH_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true // Don't throw on non-2xx
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success');

      if (response.data.success) {
        expect(response.data).toHaveProperty('results');
        expect(Array.isArray(response.data.results)).toBe(true);
        expect(response.data).toHaveProperty('metadata');
        expect(response.data.metadata).toHaveProperty('mode', 'union');
        expect(response.data.metadata).toHaveProperty('queries_count', 3);
        expect(response.data.metadata).toHaveProperty('search_type', 'batch');

        // Each result should have matched_queries array
        if (response.data.results.length > 0) {
          const firstResult = response.data.results[0];
          expect(firstResult).toHaveProperty('matched_queries');
          expect(Array.isArray(firstResult.matched_queries)).toBe(true);
          expect(firstResult).toHaveProperty('match_count');
          expect(firstResult).toHaveProperty('relevance_score');
          expect(firstResult).toHaveProperty('document_name');
          expect(firstResult).toHaveProperty('content_preview');
        }
      }
    });

    test('should return intersection of results when mode=intersection', async () => {
      const payload = {
        queries: ['railway', 'safety'],
        mode: 'intersection',
        limit: 3
      };

      const response = await axios.post(BATCH_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success');

      if (response.data.success && response.data.results.length > 0) {
        expect(response.data.metadata.mode).toBe('intersection');
        // In intersection mode, results should match ALL queries
        response.data.results.forEach(result => {
          expect(result.match_count).toBeGreaterThanOrEqual(2);
        });
      }
    });

    test('should handle empty queries array gracefully', async () => {
      const payload = {
        queries: [],
        mode: 'union',
        limit: 5
      };

      const response = await axios.post(BATCH_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      // Should return error for empty queries
      expect(response.status).toBe(500);
      expect(response.data).toHaveProperty('error');
    });

    test('should respect min_score threshold', async () => {
      const payload = {
        queries: ['test query'],
        mode: 'union',
        limit: 10,
        min_score: 0.9 // High threshold
      };

      const response = await axios.post(BATCH_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      expect(response.status).toBe(200);
      if (response.data.success && response.data.results.length > 0) {
        // All results should have score >= 0.9
        response.data.results.forEach(result => {
          expect(result.relevance_score).toBeGreaterThanOrEqual(0.9);
        });
      }
    });
  });

  describe('Faceted Search Tool', () => {
    const FACETED_SEARCH_URL = `${TOOL_BASE_URL}/tool-faceted-search`;

    test('should return facet breakdown by metadata', async () => {
      const payload = {
        query: 'railway procedures',
        facet_fields: ['document_type', 'department'],
        limit: 10
      };

      const response = await axios.post(FACETED_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success');

      if (response.data.success) {
        expect(response.data).toHaveProperty('results');
        expect(response.data).toHaveProperty('facets');
        expect(response.data).toHaveProperty('metadata');

        // Facets should be an object with requested fields
        expect(typeof response.data.facets).toBe('object');
        expect(response.data.metadata).toHaveProperty('search_type', 'faceted');
        expect(response.data.metadata).toHaveProperty('facet_fields');

        // Each facet field should have counts
        const facets = response.data.facets;
        for (const field of payload.facet_fields) {
          if (facets[field]) {
            expect(typeof facets[field]).toBe('object');
            // Each value should have a count
            Object.values(facets[field]).forEach(count => {
              expect(typeof count).toBe('number');
              expect(count).toBeGreaterThan(0);
            });
          }
        }

        // Results should have facet metadata
        if (response.data.results.length > 0) {
          const firstResult = response.data.results[0];
          expect(firstResult).toHaveProperty('document_type');
          expect(firstResult).toHaveProperty('department');
          expect(firstResult).toHaveProperty('relevance_score');
        }
      }
    });

    test('should handle custom facet fields', async () => {
      const payload = {
        query: 'maintenance',
        facet_fields: ['fleet_type', 'standard_compliance'],
        limit: 5
      };

      const response = await axios.post(FACETED_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success');

      if (response.data.success) {
        expect(response.data.metadata.facet_fields).toEqual(payload.facet_fields);
      }
    });

    test('should require query parameter', async () => {
      const payload = {
        facet_fields: ['document_type'],
        limit: 5
      };

      const response = await axios.post(FACETED_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      // Should return error for missing query
      expect(response.status).toBe(500);
      expect(response.data).toHaveProperty('error');
    });
  });

  describe('Explained Search Tool', () => {
    const EXPLAINED_SEARCH_URL = `${TOOL_BASE_URL}/tool-explained-search`;

    test('should return detailed score explanations', async () => {
      const payload = {
        query: 'VLAN configuration',
        limit: 3
      };

      const response = await axios.post(EXPLAINED_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success');

      if (response.data.success && response.data.results.length > 0) {
        const firstResult = response.data.results[0];

        // Should have explanation breakdown
        expect(firstResult).toHaveProperty('explanation');
        const explanation = firstResult.explanation;

        expect(explanation).toHaveProperty('semantic_score');
        expect(explanation).toHaveProperty('quality_boost');
        expect(explanation).toHaveProperty('recency_factor');
        expect(explanation).toHaveProperty('tf_boost');
        expect(explanation).toHaveProperty('matching_terms');
        expect(explanation).toHaveProperty('formula');

        // Scores should be numbers
        expect(typeof explanation.semantic_score).toBe('number');
        expect(typeof explanation.quality_boost).toBe('number');
        expect(typeof explanation.recency_factor).toBe('number');
        expect(typeof explanation.tf_boost).toBe('number');

        // Matching terms should be an array
        expect(Array.isArray(explanation.matching_terms)).toBe(true);

        // Metadata should indicate explanation available
        expect(response.data.metadata).toHaveProperty('search_type', 'explained');
        expect(response.data.metadata).toHaveProperty('explanation_available', true);
      }
    });

    test('should show score components breakdown', async () => {
      const payload = {
        query: 'emergency brake',
        limit: 2
      };

      const response = await axios.post(EXPLAINED_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      expect(response.status).toBe(200);

      if (response.data.success && response.data.results.length > 0) {
        const explanation = response.data.results[0].explanation;

        // Should have components breakdown
        expect(explanation).toHaveProperty('components');
        const components = explanation.components;

        expect(components).toHaveProperty('base_semantic');
        expect(components).toHaveProperty('quality_multiplier');
        expect(components).toHaveProperty('recency_multiplier');
        expect(components).toHaveProperty('tf_multiplier');
      }
    });

    test('should handle queries with no matching terms', async () => {
      const payload = {
        query: 'xyzabc123nonexistent',
        limit: 5
      };

      const response = await axios.post(EXPLAINED_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success');

      // Should return empty results or low-score results
      if (response.data.success) {
        expect(Array.isArray(response.data.results)).toBe(true);
      }
    });
  });

  describe('Latest Versions Search Tool', () => {
    const LATEST_SEARCH_URL = `${TOOL_BASE_URL}/tool-latest-search`;

    test('should filter to latest document versions only', async () => {
      const payload = {
        query: 'fleet management',
        limit: 10
      };

      const response = await axios.post(LATEST_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success');

      if (response.data.success && response.data.results.length > 0) {
        // All results should be latest versions
        response.data.results.forEach(result => {
          expect(result).toHaveProperty('is_latest_version');
          expect(result.is_latest_version).toBe(true);
          expect(result).toHaveProperty('version');
          expect(result).toHaveProperty('document_date');
        });

        // Metadata should indicate version filter applied
        expect(response.data.metadata).toHaveProperty('search_type', 'latest_versions');
        expect(response.data.metadata).toHaveProperty('version_filter_applied', true);
        expect(response.data.metadata).toHaveProperty('note');
      }
    });

    test('should include version metadata in results', async () => {
      const payload = {
        query: 'procedure',
        limit: 5
      };

      const response = await axios.post(LATEST_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      expect(response.status).toBe(200);

      if (response.data.success && response.data.results.length > 0) {
        const firstResult = response.data.results[0];

        // Should have version information
        expect(firstResult).toHaveProperty('version');
        expect(firstResult).toHaveProperty('document_date');
        expect(firstResult).toHaveProperty('supersedes_version'); // May be null

        // Standard fields should also be present
        expect(firstResult).toHaveProperty('document_name');
        expect(firstResult).toHaveProperty('relevance_score');
        expect(firstResult).toHaveProperty('content_preview');
      }
    });

    test('should respect limit parameter', async () => {
      const payload = {
        query: 'document',
        limit: 3
      };

      const response = await axios.post(LATEST_SEARCH_URL, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      expect(response.status).toBe(200);

      if (response.data.success) {
        expect(response.data.results.length).toBeLessThanOrEqual(3);
      }
    });
  });

  describe('Error Handling', () => {
    test('Batch Search should handle BMS API errors gracefully', async () => {
      // Use invalid payload to trigger error
      const payload = {
        queries: null, // Invalid
        mode: 'union'
      };

      const response = await axios.post(`${TOOL_BASE_URL}/tool-batch-search`, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      // Should return error response
      expect([200, 500]).toContain(response.status);
      if (response.status === 200) {
        expect(response.data).toHaveProperty('success', false);
        expect(response.data).toHaveProperty('error');
      }
    });

    test('Faceted Search should validate facet_fields parameter', async () => {
      const payload = {
        query: 'test',
        facet_fields: 'not-an-array', // Invalid
        limit: 5
      };

      const response = await axios.post(`${TOOL_BASE_URL}/tool-faceted-search`, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });

      // Should return error
      expect(response.status).toBe(500);
      expect(response.data).toHaveProperty('error');
    });

    test('All tools should handle missing query parameter', async () => {
      const tools = [
        'tool-faceted-search',
        'tool-explained-search',
        'tool-latest-search'
      ];

      for (const tool of tools) {
        const response = await axios.post(`${TOOL_BASE_URL}/${tool}`, {}, {
          timeout: REQUEST_TIMEOUT,
          validateStatus: () => true
        });

        // Should return error for missing query
        expect(response.status).toBe(500);
        expect(response.data).toHaveProperty('error');
      }
    });
  });

  describe('Performance', () => {
    test('Batch Search should complete within 30 seconds', async () => {
      const payload = {
        queries: ['test1', 'test2'],
        mode: 'union',
        limit: 5
      };

      const startTime = Date.now();
      const response = await axios.post(`${TOOL_BASE_URL}/tool-batch-search`, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });
      const elapsed = Date.now() - startTime;

      expect(response.status).toBe(200);
      expect(elapsed).toBeLessThan(30000);
    });

    test('Faceted Search should complete within 15 seconds', async () => {
      const payload = {
        query: 'test',
        facet_fields: ['document_type'],
        limit: 10
      };

      const startTime = Date.now();
      const response = await axios.post(`${TOOL_BASE_URL}/tool-faceted-search`, payload, {
        timeout: REQUEST_TIMEOUT,
        validateStatus: () => true
      });
      const elapsed = Date.now() - startTime;

      expect(response.status).toBe(200);
      expect(elapsed).toBeLessThan(15000);
    });
  });
});
