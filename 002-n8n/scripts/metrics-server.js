#!/usr/bin/env node
/**
 * Prometheus Metrics HTTP Server
 *
 * Exposes GET /metrics endpoint for Prometheus scraping
 * Serves metrics collected by prometheus-exporter.js module
 *
 * Usage:
 *   node scripts/metrics-server.js
 *   # or with custom port:
 *   PORT=9090 node scripts/metrics-server.js
 *
 * Endpoint:
 *   GET http://localhost:9091/metrics
 */

const http = require('http');
const metricsExporter = require('../lib/prometheus-exporter');

const PORT = process.env.METRICS_PORT || 9091;
const HOST = process.env.METRICS_HOST || '0.0.0.0';

// Create HTTP server
const server = http.createServer(async (req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle OPTIONS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Health check endpoint
  if (req.url === '/health' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      service: 'prometheus-metrics-exporter',
      timestamp: new Date().toISOString()
    }));
    return;
  }

  // Metrics endpoint
  if (req.url === '/metrics' && req.method === 'GET') {
    try {
      const metrics = await metricsExporter.getMetrics();
      res.writeHead(200, { 'Content-Type': 'text/plain; version=0.0.4' });
      res.end(metrics);
    } catch (error) {
      console.error('Error generating metrics:', error);
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end(`# Error: ${error.message}\n`);
    }
    return;
  }

  // 404 for all other routes
  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not Found\n\nAvailable endpoints:\n  GET /metrics\n  GET /health\n');
});

// Start server
server.listen(PORT, HOST, () => {
  console.log(`📊 Prometheus Metrics Server running at http://${HOST}:${PORT}/`);
  console.log(`📈 Metrics endpoint: http://${HOST}:${PORT}/metrics`);
  console.log(`❤️  Health endpoint: http://${HOST}:${PORT}/health`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing server...');
  server.close(async () => {
    await metricsExporter.close();
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', async () => {
  console.log('\nSIGINT received, closing server...');
  server.close(async () => {
    await metricsExporter.close();
    console.log('Server closed');
    process.exit(0);
  });
});
