# n8n Configuration Summary

**Date**: 2025-10-06
**Status**: ✅ Complete

## Overview

n8n is now properly configured across all RunPod initialization and service management scripts with OAuth support for MS Teams integration.

## Configuration Files Updated

### 1. `/workspace/scripts/env.sh`

Added n8n environment variables (lines 24-33):

```bash
# n8n Configuration
export N8N_USER_FOLDER=/workspace/n8n
export WEBHOOK_URL="https://nqz5l77nsrdkyt-5678.proxy.runpod.net/"
export N8N_EDITOR_BASE_URL="https://nqz5l77nsrdkyt-5678.proxy.runpod.net/"
export N8N_HOST="0.0.0.0"
export N8N_PORT="5678"
export N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS="false"
export DB_SQLITE_POOL_SIZE="3"
export N8N_DIAGNOSTICS_ENABLED="false"
export N8N_RUNNERS_ENABLED="true"
```

**Purpose**: Central environment variable definitions sourced by all scripts.

---

### 2. `/workspace/scripts/health_check.sh`

Added n8n health check (line 23):

```bash
check_service "n8n" "http://localhost:5678/healthz"
```

**Purpose**: Verify n8n is running and responding to health checks.

**Test result**:
```
✅ n8n: Running
```

---

### 3. `/workspace/scripts/start_all_services.sh`

**Issues Fixed**:
- ❌ Removed duplicate n8n startup block (lines 102-120)
- ❌ Missing OAuth environment variables
- ❌ Using global `n8n` command instead of local installation

**New configuration** (lines 81-110):

```bash
# Start n8n with OAuth configuration
if [ -f /workspace/n8n/node_modules/.bin/n8n ]; then
    if ! pgrep -f "n8n start" > /dev/null; then
        echo "Starting n8n with OAuth support..."
        cd /workspace/n8n
        export N8N_USER_FOLDER=/workspace/n8n
        export WEBHOOK_URL="https://nqz5l77nsrdkyt-5678.proxy.runpod.net/"
        export N8N_EDITOR_BASE_URL="https://nqz5l77nsrdkyt-5678.proxy.runpod.net/"
        export N8N_HOST="0.0.0.0"
        export N8N_PORT="5678"
        export N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS="false"
        export DB_SQLITE_POOL_SIZE="3"
        export N8N_DIAGNOSTICS_ENABLED="false"
        export N8N_RUNNERS_ENABLED="true"
        mkdir -p /workspace/n8n/.n8n /workspace/n8n/workflows
        nohup node node_modules/.bin/n8n start > /workspace/logs/n8n.log 2>&1 &
        sleep 5
        if pgrep -f "n8n start" > /dev/null; then
            echo "✅ n8n started (PID: $(pgrep -f 'n8n start'))"
            echo "   URL: $WEBHOOK_URL"
            echo "   OAuth Callback: ${WEBHOOK_URL}rest/oauth2-credential/callback"
        else
            echo "⚠️  n8n failed to start. Check /workspace/logs/n8n.log"
        fi
    else
        echo "n8n already running (PID: $(pgrep -f 'n8n start'))"
    fi
else
    echo "WARNING: n8n not found at /workspace/n8n/node_modules/.bin/n8n"
fi
```

**Purpose**: Start n8n with consistent OAuth configuration matching runpod_init.sh.

---

### 4. `/workspace/scripts/runpod_init.sh`

**Status**: ✅ Already correct (lines 157-178)

n8n auto-starts on pod boot with OAuth configuration:

```bash
export WEBHOOK_URL="https://nqz5l77nsrdkyt-5678.proxy.runpod.net/"
export N8N_EDITOR_BASE_URL="https://nqz5l77nsrdkyt-5678.proxy.runpod.net/"
export N8N_HOST="0.0.0.0"
export N8N_PORT="5678"
export N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS="false"
```

---

### 5. `/workspace/n8n/start.sh`

**Status**: ✅ Already correct

Manual startup script for n8n with OAuth:

```bash
#!/bin/bash
cd /workspace/n8n
export N8N_USER_FOLDER="/workspace/n8n"
export WEBHOOK_URL="https://nqz5l77nsrdkyt-5678.proxy.runpod.net/"
export N8N_EDITOR_BASE_URL="https://nqz5l77nsrdkyt-5678.proxy.runpod.net/"
export N8N_HOST="0.0.0.0"
export N8N_PORT="5678"
nohup node node_modules/.bin/n8n start > /workspace/logs/n8n.log 2>&1 &
```

**Usage**:
```bash
bash /workspace/n8n/start.sh
```

---

### 6. `/workspace/scripts/manage_services.sh`

**Status**: ✅ Created (previously missing)

Service management wrapper:

```bash
./manage_services.sh start    # Start all services
./manage_services.sh stop     # Stop all services
./manage_services.sh restart  # Restart all services
./manage_services.sh status   # Health check
```

---

### 7. `/workspace/scripts/start-n8n.sh`

**Status**: ✅ Removed (was empty 0-byte file)

Redundant with `/workspace/n8n/start.sh`.

---

## Environment Variables Reference

| Variable | Value | Purpose |
|----------|-------|---------|
| `N8N_USER_FOLDER` | `/workspace/n8n` | Data directory (workflows, credentials, database) |
| `WEBHOOK_URL` | `https://nqz5l77nsrdkyt-5678.proxy.runpod.net/` | Public webhook URL for OAuth callbacks |
| `N8N_EDITOR_BASE_URL` | `https://nqz5l77nsrdkyt-5678.proxy.runpod.net/` | Public editor URL |
| `N8N_HOST` | `0.0.0.0` | Listen on all interfaces |
| `N8N_PORT` | `5678` | HTTP port |
| `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS` | `false` | Disable strict permissions (RunPod compatibility) |
| `DB_SQLITE_POOL_SIZE` | `3` | SQLite connection pool size |
| `N8N_DIAGNOSTICS_ENABLED` | `false` | Disable telemetry |
| `N8N_RUNNERS_ENABLED` | `true` | Enable task runners (future-proof) |

---

## OAuth Configuration

**MS Teams OAuth Callback URL**:
```
https://nqz5l77nsrdkyt-5678.proxy.runpod.net/rest/oauth2-credential/callback
```

**Usage**:
1. Configure Azure App Registration with redirect URI above
2. Create "Microsoft Teams OAuth2 API" credential in n8n UI
3. Add Client ID and Client Secret from Azure
4. Authorize connection (redirects to MS Teams for consent)

---

## Persistence

All n8n data persists across RunPod pod restarts:

- **Workflows**: `/workspace/n8n/.n8n/workflows/`
- **Credentials**: `/workspace/n8n/.n8n/credentials/`
- **Database**: `/workspace/n8n/.n8n/database.sqlite`
- **Logs**: `/workspace/logs/n8n.log`

---

## Verification Commands

```bash
# Check if n8n is running
pgrep -f "n8n start"

# View logs
tail -50 /workspace/logs/n8n.log

# Health check
curl http://localhost:5678/healthz

# Public URL
curl https://nqz5l77nsrdkyt-5678.proxy.runpod.net/healthz

# Full health check (all services)
bash /workspace/scripts/health_check.sh
```

---

## Service Management

```bash
# Start all services (including n8n)
./scripts/manage_services.sh start

# Stop all services
./scripts/manage_services.sh stop

# Restart all services
./scripts/manage_services.sh restart

# Check status
./scripts/manage_services.sh status

# Start n8n only (manual)
bash /workspace/n8n/start.sh
```

---

## Troubleshooting

### n8n not starting

```bash
# Check logs
tail -100 /workspace/logs/n8n.log

# Verify installation
ls -la /workspace/n8n/node_modules/.bin/n8n

# Reinstall if needed
cd /workspace/n8n
npm install n8n
```

### Workflows not loading

```bash
# Verify N8N_USER_FOLDER
echo $N8N_USER_FOLDER  # Should be /workspace/n8n

# Check database
ls -la /workspace/n8n/.n8n/database.sqlite

# Check workflows directory
ls -la /workspace/n8n/.n8n/workflows/
```

### OAuth callback not working

```bash
# Verify public URL
curl https://nqz5l77nsrdkyt-5678.proxy.runpod.net/healthz

# Check environment
env | grep -E "(WEBHOOK_URL|N8N_EDITOR_BASE_URL)"

# Restart n8n
./scripts/manage_services.sh restart
```

---

## Next Steps

1. ✅ n8n configuration complete
2. ⏭️ Configure Azure App Registration with OAuth callback
3. ⏭️ Create MS Teams credential in n8n UI
4. ⏭️ Build MS Teams workflows (T016-T020)
5. ⏭️ Integration testing (T026-T027)

---

## Summary of Changes

| File | Change | Status |
|------|--------|--------|
| `/workspace/scripts/env.sh` | Added n8n environment variables | ✅ Complete |
| `/workspace/scripts/health_check.sh` | Added n8n health check | ✅ Complete |
| `/workspace/scripts/start_all_services.sh` | Fixed duplicate block, added OAuth | ✅ Complete |
| `/workspace/scripts/manage_services.sh` | Created service management wrapper | ✅ Complete |
| `/workspace/scripts/start-n8n.sh` | Removed empty file | ✅ Complete |
| `/workspace/scripts/runpod_init.sh` | Already correct | ✅ No change needed |
| `/workspace/n8n/start.sh` | Already correct | ✅ No change needed |

**All n8n configuration scripts now have consistent OAuth settings and proper health checks.**
