---
description: "Phase 0 research findings for BMS Agent MVP"
---

# Research Summary – BMS Agent MVP

## R0.1 RunPod Encryption & Key Rotation
- **Decision**: Use RunPod-managed encrypted NVMe volumes (Clarification Session 1).
- **Rationale**: Native platform encryption satisfies constitution §5 with minimal operational overhead and integrates with RunPod snapshots.
- **Alternatives Considered**:
  - LUKS full-disk encryption → Rejected due to added maintenance and snapshot complexity.
  - Application-layer AES encryption → Rejected because it complicates Qdrant search performance and duplicate storage of secrets.
- **Follow-ups**:
  - Document RunPod key rotation SOP in `DEPLOYMENT_CHECKLIST.md`.
  - Capture RunPod escalation contacts for key rollover and incident handling.

## R0.2 Qdrant Schema Sizing & Retention
- **Decision**: Multi-vector collection with 1024-d dense vectors (`snowflake-arctic-embed2`) plus sparse BM25 payload fields; estimate ~3 KB per chunk targeting 10k documents → ~15 GB footprint.
- **Rationale**: Supports hybrid retrieval while remaining within storage budget; aligns with R1.x chunking (1,500 tokens, 200 overlap).
- **Alternatives Considered**:
  - 512-d embeddings → Rejected due to lower retrieval accuracy in internal benchmarks.
  - External Elasticsearch for sparse vectors → Rejected to maintain single storage subsystem per constitution §2.
- **Follow-ups**:
  - Validate actual storage consumption after pilot corpus ingestion.
  - Define archival policy for obsolete document versions and chunk deletions.

## R0.3 Ollama Model Footprint & Fallbacks
- **Decision**: Primary embeddings via `snowflake-arctic-embed2`; generation via `mistral-nemo:12b-instruct`; fallback `qwen2.5:14b` if latency exceeds thresholds.
- **Rationale**: Balances quality and VRAM usage (~7 GB); fallback provides continuity without external dependencies (§11).
- **Alternatives Considered**:
  - `llama3.1:8b` generation → Slightly lower domain answer quality.
  - External APIs (OpenAI) → Rejected due to air-gapped mandate.
- **Follow-ups**:
  - Record GPU utilization during performance testing; ensure ≥20% headroom.
  - Version models and hashes in `docs/security-notes.md` for reproducibility.

## R0.4 Stream Ingestion Safeguards
- **Decision**: FastAPI streaming uploads with manual backpressure; enforce MIME whitelist and 1 GB size limit; reject unsupported formats with 400/413.
- **Rationale**: Protects memory footprint and security posture (§5); leverages EnhancedDocumentProcessor streaming pipeline.
- **Alternatives Considered**:
  - Temporary staging uploads → Rejected to avoid double-write I/O overhead.
  - Accept arbitrary MIME types → Rejected to prevent ingestion of unsupported data.
- **Follow-ups**:
  - Implement content-sniff validation before processing.
  - Add explicit 413 regression tests in `tests/test_basic.py`.

## Manual Alert Runbooks (MVP Scope)
- **Decision**: Produce manual escalation playbooks for latency breaches, ingestion failures, and dependency degradation; automation deferred post-MVP.
- **Follow-ups**:
  - Capture contact matrix and response timelines in `DEPLOYMENT_CHECKLIST.md`.
  - Reference runbooks from Grafana dashboards and operational docs.

## Outstanding Risks / Open Questions
- Define audit log retention beyond 90 days (coordinate with compliance).
- Monitor embedding/generation performance drift; schedule periodic benchmarks.
- Confirm RunPod support SLAs for encryption/key rotation procedures.

## Next Steps
- Proceed to Phase 1 deliverables: `data-model.md`, `/contracts/`, `quickstart.md` using decisions above.
- Update `specs/001-bms-agent/plan.md` progress checklist once Phase 1 completes.
