# Deployment Checklist

This checklist guides the rollout of the BMS Agent to a RunPod pod. Complete each
section before moving to the next. Record results in your change log for auditability.

## 1. Pre-Deployment Validation
- **Environment sync**: Confirm `main` is merged into the deployment branch.
- **Tests**: Run `./scripts/run_tests.sh` locally and ensure the GitHub Actions pipeline is green.
- **Secrets**: Double-check RunPod credentials and GitHub repository secrets: `BMS_API_KEY`, `DEPLOY_KEY`, `JWT_KEY_ROTATION_DAYS`, optional `CODECOV_TOKEN`, `SAFETY_API_KEY`.
- **Artifacts**: Verify Ollama models (`snowflake-arctic-embed2`, `mistral-nemo:12b-instruct`) are pre-pulled on the pod or listed in rollout plan.
- **Prerequisites**: Confirm RSA key pair exists (`private_key.pem`, `public_key.pem`), Python ≥3.11 is installed, and Qdrant v1.7.4 binary is downloaded to `/usr/local/bin/qdrant`.
- **Resources**: Document pod allocation (16 vCPUs, 64 GB RAM, 500 GB NVMe) in change log.
- **Backups**: Snapshot `~/persistent/qdrant_storage`, `~/persistent/bms_data`, and `~/persistent/backups`.

## 2. Deployment Steps
- **Sync code**:
  ```bash
  rsync -avz --delete ./bms-agent <user>@<runpod-ip>:~/bms-agent
  ```
- **Install requirements**:
  ```bash
  ssh <user>@<runpod-ip> 'cd ~/bms-agent && source venv/bin/activate && \
    pip install -r reqs/requirements.txt && pip install -r requirements-test.txt'
  ```
- **Apply configuration** (update `config/env.sh` or `.env` with latest variables):
  ```bash
  cat <<'EOF' > config/env.sh
  export BMS_API_KEY=<key>
  export BMS_JWT_PUBLIC_KEY="$(cat public_key.pem)"
  export BMS_JWT_ALGORITHM=RS256
  export RATE_LIMIT_PER_MIN=60
  export JWT_KEY_ROTATION_DAYS=30
  export QDRANT_HOST=localhost
  export QDRANT_PORT=6333
  export QDRANT_GRPC_PORT=6334
  export QDRANT_MAX_PAYLOAD_SIZE=1073741824
  export QDRANT_COLLECTION=nomad_bms_documents
  export OLLAMA_URL=http://localhost:11434
  export EMBEDDING_MODEL=snowflake-arctic-embed2
  export GENERATION_MODEL=mistral-nemo:12b-instruct
  export EMBEDDING_BATCH_SIZE=32
  export PROMETHEUS_PORT=9090
  export GRAFANA_PORT=3000
  EOF
  ```
- **Restart services**:
  ```bash
  ssh <user>@<runpod-ip> '~/bms-agent/scripts/manage_services.sh restart'
  ```
- **Run smoke tests**:
  ```bash
  ssh <user>@<runpod-ip> '~/bms-agent/scripts/run_tests.sh'
  ```
- **Validate health**:
  ```bash
  ssh <user>@<runpod-ip> '~/bms-agent/scripts/health_check.sh'
  ```

## 3. Post-Deployment Verification
- **Functional check**: Use `/api/v1/search/semantic` with a known query and confirm
  relevant results.
- **Monitoring**: Tail `~/persistent/logs/api.log` and `~/persistent/logs/qdrant.log` for at least 10 minutes, verifying alert thresholds:
  - Latency ≤100 ms p95 (`/metrics/uplink`)
  - CPU usage <85 %
  - Disk usage <80 %
  - Embedding latency <1 s
  - Ingestion failures <1 per 100 documents
- **n8n/OpenWebUI**: Trigger Slack workflow and OpenWebUI tool to ensure
  integrations are intact.
- **Backup automation**: Ensure cron job exists for daily archives:
  ```bash
  0 2 * * * tar -czf ~/persistent/backups/bms_$(date +\%Y\%m\%d).tar.gz ~/persistent/qdrant_storage ~/persistent/bms_data
  ```
- **Rollback plan**: If issues arise, restore backups and rerun `./scripts/manage_services.sh restart`.

## 4. Communication
- Notify stakeholders (engineering, product) with:
  - Deployment window and result
  - Version/commit SHA deployed
  - Known issues or follow-up tickets
- Update `tasks.md` and project tracker with deployment status and any new action
  items.

## 5. Continuous Improvement
- Capture lessons learned and feed them into `tasks.md` as new tasks.
- Consider automating manual steps in `.github/workflows/ci-cd.yml` deploy job.
- Review performance metrics (`reports/performance-baseline.md`) within 24 hours.
