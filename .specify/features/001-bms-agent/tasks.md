# 001-bms-agent Production Compliance Tasks

**Objective**: Deliver full constitution compliance and production readiness for BMS Agent by **2025-12-04**.

## Parallel Execution Guidance
- **[P] Tests Batch 1**: `task run T003 & task run T004`
- **[P] Tests Batch 2**: `task run T005 & task run T006`
- **[P] Documentation Polish**: `task run T019 & task run T020`

## Setup

- **T001  Compliance Baseline Review**  
  - Summary: Review constitution (§5, §7, §8, §9, §11), production requirements in spec and plan, and produce master checklist `docs/compliance/production_requirements.md`.  
  - Dependencies: None  
  - Files/Paths: `.specify/features/001-bms-agent/spec.md`, `.specify/features/001-bms-agent/plan.md`, `docs/compliance/production_requirements.md`  
  - Parallel: No

- **T002  Compliance Branch & Tooling Setup**  
  - Summary: Create `feature/production-compliance` branch, configure task agent defaults, scaffold compliance helpers (`scripts/compliance/README.md`, `.env.production.sample`).  
  - Dependencies: T001  
  - Files/Paths: `scripts/compliance/README.md`, `.env.production.sample`, `.taskagent/config.yml`  
  - Parallel: No

## Tests First (TDD)

- **T003  Encryption at Rest Tests [P]**  
  - Summary: Add failing tests ensuring `/workspace/qdrant_storage` and `/workspace/bms_data` are encrypted and backups remain recoverable.  
  - Dependencies: T002  
  - Files/Paths: `tests/security/test_encryption_at_rest.py`, `scripts/backup_system.sh`  
  - Parallel: Yes ([P])

- **T004  GDPR Compliance Tests [P]**  
  - Summary: Add failing tests for retention windows (90-day data, 30-day logs) and right-to-erasure workflow.  
  - Dependencies: T002  
  - Files/Paths: `tests/compliance/test_gdpr.py`, `api/main.py`  
  - Parallel: Yes ([P])

- **T005  JWT & RBAC Tests [P]**  
  - Summary: Add failing authN/authZ tests enforcing JWT verification and role policies on protected endpoints.  
  - Dependencies: T002  
  - Files/Paths: `tests/security/test_authentication.py`, `api/security.py`  
  - Parallel: Yes ([P])

- **T006  Automated Alerting Tests [P]**  
  - Summary: Add failing monitoring tests validating Prometheus alerts trigger notifications and reference runbooks.  
  - Dependencies: T002  
  - Files/Paths: `tests/monitoring/test_alerting.py`, `prometheus/alerts.yml`  
  - Parallel: Yes ([P])

- **T007  CI Retrieval Guardrails**  
  - Summary: Update `.github/workflows/ci-cd.yml` to fail when top-5 accuracy <95% or quality <0.80 and add retrieval smoke job.  
  - Dependencies: T002  
  - Files/Paths: `.github/workflows/ci-cd.yml`, `scripts/evaluate_retrieval.py`  
  - Parallel: No

## Core Implementation

- **T008  Implement Storage Encryption**  
  - Summary: Encrypt Qdrant and data directories, manage keys, and update backup/restore scripts for encrypted volumes.  
  - Dependencies: T003  
  - Files/Paths: `scripts/setup_encryption.sh`, `scripts/restore_backup.sh`, `docs/security-notes.md`  
  - Parallel: No

- **T009  GDPR Enforcement & Data Retention**  
  - Summary: Implement retention jobs, right-to-erasure workflow, and update compliance documentation.  
  - Dependencies: T004  
  - Files/Paths: `api/main.py`, `scripts/cleanup_retention.sh`, `docs/security-notes.md`  
  - Parallel: No

- **T010  Audit Logging Framework**  
  - Summary: Add structured audit logging for admin operations and document audit procedures.  
  - Dependencies: T003, T004  
  - Files/Paths: `api/audit_log.py`, `api/main.py`, `docs/audit-log.md`  
  - Parallel: No

- **T011  JWT Authentication & RBAC**  
  - Summary: Integrate JWT verification, role-based access control, and production secrets management.  
  - Dependencies: T005  
  - Files/Paths: `api/security.py`, `api/main.py`, `.env.production`  
  - Parallel: No

- **T012  Automated Alerting Pipeline**  
  - Summary: Implement alert routing (PagerDuty/Slack), finalize Prometheus rules, and document escalation in runbooks.  
  - Dependencies: T006  
  - Files/Paths: `prometheus/alerts.yml`, `grafana/dashboards/bms-agent.json`, `DEPLOYMENT_CHECKLIST.md`  
  - Parallel: No

- **T013  Expand Retrieval Evaluation Dataset**  
  - Summary: Grow ground-truth dataset to ≥50 queries, refresh metrics, and record evidence.  
  - Dependencies: T007  
  - Files/Paths: `data/evaluation/ground_truth.jsonl`, `data/evaluation/EVALUATION_STATUS.md`  
  - Parallel: No

- **T014  Spec & Plan Alignment for Retrieval Enhancements**  
  - Summary: Update spec.md with requirements R2.5-R2.20 and align plan.md for retrieval enhancements.  
  - Dependencies: T013  
  - Files/Paths: `.specify/features/001-bms-agent/spec.md`, `.specify/features/001-bms-agent/plan.md`  
  - Parallel: No

## Integration & Architecture

- **T015  Alembic Migration Framework**  
  - Summary: Scaffold Alembic, add initial migration placeholder, and document dual strategy with Qdrant manual logs.  
  - Dependencies: T008  
  - Files/Paths: `alembic.ini`, `migrations/versions/`, `docs/migrations.md`  
  - Parallel: No

- **T016  Multi-Backend LLM Enablement**  
  - Summary: Add vLLM integration option, update service scripts, and document LLM fallback strategy.  
  - Dependencies: T011  
  - Files/Paths: `scripts/manage_services.sh`, `scripts/start_all_services.sh`, `docs/llm-architecture.md`  
  - Parallel: No

- **T017  Model Versioning & Hashing**  
  - Summary: Implement model artifact hashing, cataloging, and verification prior to deployment.  
  - Dependencies: T016  
  - Files/Paths: `scripts/model_versioning.py`, `docs/llm-architecture.md`, `DEPLOYMENT_CHECKLIST.md`  
  - Parallel: No

- **T018  Air-Gap Validation & Network Controls**  
  - Summary: Build air-gap verification script, tighten firewall rules, and document audit steps.  
  - Dependencies: T017  
  - Files/Paths: `scripts/airgap_validate.py`, `docs/security-notes.md`, `config/firewall.rules`  
  - Parallel: No

## Polish & Readiness

- **T019  Documentation Refresh [P]**  
  - Summary: Update README, quickstart, security notes, and deployment checklist with production compliance changes.  
  - Dependencies: T008, T009, T010, T011, T012, T013, T014, T015, T016, T017, T018  
  - Files/Paths: `README.md`, `specs/001-bms-agent/quickstart.md`, `docs/security-notes.md`, `DEPLOYMENT_CHECKLIST.md`  
  - Parallel: Yes ([P])

- **T020  Production Readiness Verification [P]**  
  - Summary: Execute final compliance checklist, gather evidence (logs, screenshots), and sign off in `docs/compliance/production_readiness.md`.  
  - Dependencies: T019  
  - Files/Paths: `docs/compliance/production_readiness.md`, `logs/`, `reports/performance-baseline.md`  
  - Parallel: Yes ([P])
