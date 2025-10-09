# Optional Enhancements Implementation Guide

**Date**: 2025-10-09
**Status**: ✅ All enhancements implemented
**Slack Bot**: Production-ready with monitoring and security features

---

## Overview

This document describes 4 optional enhancement modules implemented to improve the Slack bot's production readiness, security, and user experience.

---

## Enhancement 1: Prometheus Metrics Instrumentation (T026b)

**Purpose**: Production monitoring and observability
**Status**: ✅ Complete
**Files**:
- `/workspace/002-n8n/lib/prometheus-exporter.js` - Core metrics collection
- `/workspace/002-n8n/lib/instrumentation.js` - Workflow instrumentation helpers
- `/workspace/002-n8n/scripts/metrics-server.js` - HTTP metrics endpoint
- `/workspace/002-n8n/tests/unit/test-prometheus-metrics.js` - Unit tests

### Features

**6 Core Metrics**:
1. `slack_bot_requests_total{command_type}` - Request counter
2. `slack_bot_response_latency_seconds` - Response latency histogram (p50/p95/p99)
3. `slack_bot_errors_total{error_type}` - Error counter
4. `slack_bot_active_conversations` - Active conversation gauge
5. `slack_bot_document_uploads_total{status}` - Document upload counter
6. `bms_api_call_latency_seconds{endpoint}` - BMS API latency histogram

### Quick Start

**1. Start metrics server**:
```bash
cd /workspace/002-n8n
node scripts/metrics-server.js
```

**2. Access metrics**:
```bash
curl http://localhost:9091/metrics
curl http://localhost:9091/health
```

**3. Configure Prometheus** (add to `prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'slack-bot'
    static_configs:
      - targets: ['localhost:9091']
    scrape_interval: 15s
```

### Usage in n8n Workflows

**Function Node Example**:
```javascript
const instrument = require('./lib/instrumentation');

// Track incoming request
await instrument.trackRequest('ask', $input.all());

// Track latency
const stopTimer = instrument.startTimer('bms_api_call', {endpoint: 'search'});
// ... make API call ...
await stopTimer();

// Track errors
try {
  // ... workflow logic ...
} catch (error) {
  await instrument.trackError('workflow_error', error);
}
```

**Workflow Instrumentation**:
```javascript
const instrument = require('./lib/instrumentation');

// At workflow start
const stop = await instrument.instrumentWorkflow('query-analyzer', $input.all());

// ... workflow logic ...

// At workflow end
await stop();
```

### Grafana Dashboard (Optional)

Create dashboard with panels:
- Request rate (requests/sec)
- p95/p99 latency
- Error rate by type
- Active conversations
- Document upload success rate

---

## Enhancement 2: First-User-Admin Bootstrap (T020-bootstrap)

**Purpose**: Automatic admin privilege grant for first user
**Status**: ✅ Complete
**File**: `/workspace/002-n8n/lib/admin-bootstrap.js`

### Features

- **Automatic Bootstrap**: First user to interact gets admin privileges
- **Security**: Only works when admins array is empty
- **Audit Trail**: All bootstrap events logged to Redis
- **Permanent Flag**: Prevents re-bootstrap attacks

### Quick Start

**Usage in n8n Function Node**:
```javascript
const bootstrap = require('./lib/admin-bootstrap');

// Check and bootstrap if needed
const result = await bootstrap.checkAndBootstrap(
  userId,        // Slack user ID (e.g., 'U01234567')
  displayName,   // Display name (e.g., 'John Doe')
  {
    team_id: teamId,
    channel_id: channelId
  }
);

if (result.bootstrapped) {
  // Send welcome message
  return {
    json: {
      message: "🎉 " + result.message,
      isAdmin: true
    }
  };
}
```

### API Methods

```javascript
// Check if user is admin
const isAdmin = await bootstrap.isAdmin(userId);

// Get bootstrap status
const status = await bootstrap.getBootstrapStatus();
// Returns: {bootstrapped: true, adminCount: 1, admins: ['U01234567']}

// Get audit trail
const events = await bootstrap.getBootstrapAuditTrail();
```

### Security

✅ **Bootstrap only works when**:
- `whitelist.json` admins array is empty
- Bootstrap flag not set in Redis

✅ **Audit logging**:
- All bootstrap events stored in Redis: `audit:admin_bootstrap`
- 90-day retention
- Includes: timestamp, user_id, display_name, team_id

---

## Enhancement 3: Admin Reset with Audit Logging (T020a)

**Purpose**: Secure admin privilege reset with compliance logging
**Status**: ✅ Complete
**File**: `/workspace/002-n8n/lib/admin-reset.js`

### Features

- **Secret Key Validation**: 64-character hex string
- **Mandatory Audit Logging**: All attempts logged (success + failure)
- **Rate Limiting**: Track failed attempts
- **Security Alerts**: Warn after 5 failed attempts
- **90-Day Retention**: Compliance audit trail

### Setup

**1. Generate secret key**:
```bash
openssl rand -hex 32
# Example output: a1b2c3d4e5f6...
```

**2. Add to environment**:
```bash
# /workspace/002-n8n/config/.env
ADMIN_RESET_SECRET=a1b2c3d4e5f6...  # Your generated key
```

**3. Store securely**:
- ⚠️ **Never commit to git**
- Add to `.gitignore`: `config/.env`
- Store backup in secure vault

### Usage in n8n Function Node

```javascript
const adminReset = require('./lib/admin-reset');

// Parse command: /admin reset <secret_key>
const secretKey = commandArgs[1]; // User-provided secret

// Execute reset
const result = await adminReset.executeReset(
  userId,
  displayName,
  secretKey,
  {
    ip_address: '192.168.1.100',
    team_id: teamId,
    channel_id: channelId
  }
);

if (result.success) {
  return {
    json: {
      message: "✅ " + result.message
    }
  };
} else {
  // Failed attempt is already logged
  return {
    json: {
      message: "❌ " + result.message
    }
  };
}
```

### API Methods

```javascript
// Get audit trail
const trail = await adminReset.getResetAuditTrail(100);
// Returns last 100 reset attempts with timestamps, success status

// Check failed attempts
const failureCount = await adminReset.getFailedAttemptsCount(userId);
// Returns count of failed attempts in last hour

// Generate new secret (for rotation)
const newSecret = adminReset.generateSecret();
```

### Security Features

✅ **Constant-time comparison**: Prevents timing attacks
✅ **No information disclosure**: Generic error messages
✅ **Rate limiting**: Track and alert on excessive failures
✅ **Comprehensive logging**: All attempts logged before validation
✅ **90-day retention**: Compliance with audit requirements

---

## Enhancement 4: Similar Query Dismiss Handler (T019b)

**Purpose**: Allow users to dismiss similar query suggestions
**Status**: ✅ Complete
**File**: `/workspace/002-n8n/lib/similar-query-dismiss.js`

### Features

- **Dismiss Individual Suggestions**: Store user preference per suggestion
- **Global Disable**: Turn off all suggestions for a user
- **7-Day TTL**: Matches conversation retention
- **Slack Integration**: Works with Slack interactive buttons

### Usage in Similar Query Workflow

**Check before showing suggestion**:
```javascript
const dismiss = require('./lib/similar-query-dismiss');

// Generate suggestion ID (hash of similar query)
const crypto = require('crypto');
const suggestionId = crypto.createHash('md5')
  .update(similarQuery)
  .digest('hex');

// Check if should show
const shouldShow = await dismiss.shouldShowSuggestion(userId, suggestionId);

if (!shouldShow) {
  // User dismissed this or disabled all suggestions
  return { json: { skip: true } };
}

// Show suggestion with dismiss button
return {
  json: {
    message: `💡 Similar query found: "${similarQuery}"`,
    blocks: [
      {
        type: 'actions',
        elements: [
          {
            type: 'button',
            text: { type: 'plain_text', text: 'Use This' },
            action_id: 'use_suggestion',
            value: similarQuery
          },
          {
            type: 'button',
            text: { type: 'plain_text', text: 'Dismiss' },
            action_id: 'dismiss_suggestion',
            value: suggestionId,
            style: 'danger'
          }
        ]
      }
    ]
  }
};
```

**Handle dismiss button click**:
```javascript
const dismiss = require('./lib/similar-query-dismiss');

// When user clicks "Dismiss" button
const result = await dismiss.recordDismissal(
  userId,
  suggestionId,
  {
    original_query: userQuery,
    suggested_query: similarQuery
  }
);

if (result.success) {
  return {
    json: {
      message: "✓ Suggestion dismissed. You won't see this again."
    }
  };
}
```

### API Methods

```javascript
// Check if dismissed
const dismissed = await dismiss.wasDismissed(userId, suggestionId);

// Get all dismissed suggestions
const dismissed = await dismiss.getDismissedSuggestions(userId);

// Clear specific dismissal
await dismiss.clearDismissal(userId, suggestionId);

// Clear all dismissals
await dismiss.clearAllDismissals(userId);

// Disable all suggestions globally
await dismiss.disableAllSuggestions(userId);

// Enable suggestions
await dismiss.enableAllSuggestions(userId);

// Get statistics
const stats = await dismiss.getStatistics(userId);
```

---

## Integration with Existing Workflows

### Admin Commands Workflow

Update `/workspace/002-n8n/workflows/admin-commands.json`:

**Add bootstrap check** (at workflow start):
```javascript
const bootstrap = require('./lib/admin-bootstrap');
const result = await bootstrap.checkAndBootstrap(userId, displayName, metadata);
if (result.bootstrapped) {
  // Return welcome message
}
```

**Add reset command handler**:
```javascript
if (command === '/admin reset') {
  const adminReset = require('./lib/admin-reset');
  const result = await adminReset.executeReset(userId, displayName, secretKey, metadata);
  return { json: { message: result.message } };
}
```

### Main Bot Handler Workflow

**Add metrics tracking**:
```javascript
const instrument = require('./lib/instrumentation');

// At workflow start
const stop = await instrument.instrumentWorkflow('main-bot-handler', $input.all());

try {
  // ... workflow logic ...
  await stop(); // Success
} catch (error) {
  await stop(error); // Error
}
```

### Similar Query Detector Workflow

**Add dismiss handling**:
```javascript
const dismiss = require('./lib/similar-query-dismiss');

// Before showing suggestion
if (!await dismiss.shouldShowSuggestion(userId, suggestionId)) {
  return { json: { skip: true } };
}

// Show with dismiss button (see example above)
```

---

## Testing

### Manual Testing

**1. Test Prometheus metrics**:
```bash
# Start server
node scripts/metrics-server.js

# Generate some traffic (in another terminal)
curl -X POST http://localhost:5678/webhook/teams -d '{"text":"test"}'

# Check metrics
curl http://localhost:9091/metrics | grep slack_bot
```

**2. Test first-user-admin bootstrap**:
```bash
# Clear whitelist
echo '{"admins":[],"channels":[]}' > config/whitelist.json

# Send message as any user
# Should receive: "You are now the bot admin..."

# Verify
cat config/whitelist.json
# Should show user in admins array
```

**3. Test admin reset**:
```bash
# Generate secret
SECRET=$(openssl rand -hex 32)
echo "ADMIN_RESET_SECRET=$SECRET" >> config/.env

# Send command: /admin reset <secret>
# Should receive: "Admin privileges granted. This action has been logged."
```

**4. Test dismiss handler**:
```bash
# Show similar query suggestion with dismiss button
# Click "Dismiss"
# Try showing same suggestion again
# Should be skipped
```

### Unit Tests

```bash
cd /workspace/002-n8n
npm test tests/unit/test-prometheus-metrics.js
```

---

## Production Deployment Checklist

### Prometheus Metrics
- [ ] Start metrics server: `node scripts/metrics-server.js`
- [ ] Configure Prometheus to scrape `localhost:9091`
- [ ] Create Grafana dashboard
- [ ] Set up alerts for high error rates

### Admin Security
- [ ] Generate admin reset secret: `openssl rand -hex 32`
- [ ] Add to `/workspace/002-n8n/config/.env`
- [ ] Secure `.env` file permissions: `chmod 600 config/.env`
- [ ] Backup secret to secure vault
- [ ] Document secret rotation procedure

### Bootstrap
- [ ] Clear `config/whitelist.json` admins array before first deployment
- [ ] Test first user receives admin privileges
- [ ] Verify bootstrap audit trail in Redis

### Dismiss Handler
- [ ] Update similar-query-detector workflow with dismiss buttons
- [ ] Test dismiss functionality in Slack
- [ ] Verify 7-day TTL on dismissed suggestions

---

## Monitoring & Maintenance

### Prometheus Metrics

**Dashboards**:
- Request rate: Track `slack_bot_requests_total`
- Error rate: Track `slack_bot_errors_total`
- Latency: Track `slack_bot_response_latency_seconds` p95/p99

**Alerts**:
- Error rate > 5% for 5 minutes
- p95 latency > 3 seconds
- Active conversations > 100

### Audit Logs

**Redis Keys**:
- `audit:admin_bootstrap` - Bootstrap events (90-day retention)
- `audit:admin_resets` - Reset attempts (90-day retention)
- `security:admin_reset_failures:{userId}` - Failed attempts (1-hour TTL)

**Review**:
```bash
# Get bootstrap events
redis-cli LRANGE audit:admin_bootstrap 0 -1

# Get reset attempts
redis-cli LRANGE audit:admin_resets 0 -1
```

### Dismissed Suggestions

**Redis Keys**:
- `bms:user:{userId}:dismissed_suggestions` - Hash of dismissed suggestions (7-day TTL)
- `bms:user:{userId}:disable_suggestions` - Global disable flag (permanent)

**Cleanup**:
- Automatic via 7-day TTL
- Manual: `redis-cli DEL "bms:user:{userId}:dismissed_suggestions"`

---

## Troubleshooting

### Metrics Server Won't Start

**Symptom**: `Error: listen EADDRINUSE`
**Cause**: Port 9091 already in use
**Solution**:
```bash
# Use different port
METRICS_PORT=9092 node scripts/metrics-server.js
```

### Admin Reset Fails

**Symptom**: Always returns "Invalid reset key"
**Cause**: Secret not configured or mismatch
**Solution**:
```bash
# Verify secret is set
echo $ADMIN_RESET_SECRET

# Check .env file loaded
source config/.env
echo $ADMIN_RESET_SECRET
```

### Bootstrap Not Working

**Symptom**: First user not getting admin privileges
**Cause**: Bootstrap flag already set or admins array not empty
**Solution**:
```bash
# Reset bootstrap
redis-cli DEL system:admin_bootstrapped

# Clear admins
echo '{"admins":[],"channels":[]}' > config/whitelist.json
```

### Dismiss Not Working

**Symptom**: Dismissed suggestions still showing
**Cause**: Suggestion ID mismatch
**Solution**:
```javascript
// Ensure consistent ID generation
const suggestionId = crypto.createHash('md5')
  .update(JSON.stringify({query: similarQuery, userId}))
  .digest('hex');
```

---

## Summary

✅ **T026b - Prometheus Metrics**: Production monitoring ready
✅ **T020-bootstrap - First-User-Admin**: UX improvement for initial setup
✅ **T020a - Admin Reset**: Secure admin privilege recovery
✅ **T019b - Dismiss Handler**: User control over suggestions

**Total Enhancement Value**:
- Production observability (metrics + dashboards)
- Security hardening (audit logging + rate limiting)
- User experience (bootstrap + dismiss)
- Compliance (90-day audit retention)

**Deployment Status**: Ready for production Slack bot deployment
