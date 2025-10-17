# Migration Log

Record schema and data adjustments executed during the MVP. Use ISO8601 timestamps and reference related task IDs or PR numbers.

## Overview

This document tracks all schema changes, data migrations, and breaking changes for the BMS Agent project. For Qdrant (NoSQL vector database), migrations are manual and tracked here. Future SQL databases will use Alembic (see T053).

## Migration History

| Date (UTC) | Version | Change Description | Impacted Components | Reference | Status |
|------------|---------|-------------------|---------------------|-----------|--------|
| 2025-09-30 | v1.0.0 | Initial Qdrant collection setup with v4.0 schema | Qdrant collection `nomad_bms_documents` | T004, T005 | ✅ Complete |
| 2025-09-30 | v1.0.0 | Multi-vector schema: chunk_embedding, parent_embedding (768-d) | Qdrant vectors | T004 | ✅ Complete |
| 2025-09-30 | v1.0.0 | Sparse vector support for BM25 keyword search | Qdrant sparse vectors | T004 | ✅ Complete |
| 2025-10-02 | v1.1.0 | Enhanced Document Processor v4.0 integration | Document processing pipeline | T009 | ✅ Complete |
| 2025-10-02 | v1.1.0 | Quality score metadata added to chunks | Qdrant payload | T038 | ✅ Complete |
| 2025-10-02 | v1.1.0 | Document type metadata added | Qdrant payload | T030 | ✅ Complete |
| 2025-10-03 | v1.2.0 | Workspace persistence migration | All services, data storage | T028 | ✅ Complete |
| 2025-10-03 | v1.2.0 | Automated backup system | Backup infrastructure | T041 | ✅ Complete |

## Pending Migrations

| Planned Version | Change Description | Impacted Components | Reference | Priority |
|----------------|-------------------|---------------------|-----------|----------|
| v2.0.0 | JWT authentication schema | API endpoints, user model | T046 | Production |
| v2.0.0 | RBAC role definitions | User roles, permissions | T046 | Production |
| v2.0.0 | Audit log schema | Audit logging system | T045 | Production |
| v2.0.0 | Encryption at rest | Qdrant storage, BMS data | T043 | Production |
| v2.0.0 | Model versioning metadata | Qdrant collection metadata | T048 | Production |

## Migration Procedures

### Qdrant Collection Schema Changes

**Manual Migration Process:**
1. **Backup existing collection:**
   ```bash
   ./scripts/backup_system.sh
   ```

2. **Create new collection with updated schema:**
   ```bash
   python scripts/init_qdrant.py --collection nomad_bms_documents_v2
   ```

3. **Migrate data (if needed):**
   ```bash
   python scripts/migrate_qdrant_data.py \
     --source nomad_bms_documents \
     --target nomad_bms_documents_v2
   ```

4. **Verify migration:**
   ```bash
   curl http://localhost:6333/collections/nomad_bms_documents_v2
   ```

5. **Update application config:**
   ```bash
   # Update QDRANT_COLLECTION in .env or config/env.sh
   QDRANT_COLLECTION=nomad_bms_documents_v2
   ```

6. **Restart services:**
   ```bash
   ./scripts/start_all_services.sh restart
   ```

7. **Validate functionality:**
   ```bash
   ./scripts/health_check.sh
   python scripts/evaluate_retrieval.py
   ```

8. **Archive old collection (after validation):**
   ```bash
   curl -X DELETE http://localhost:6333/collections/nomad_bms_documents
   ```

### Rollback Procedures

**Qdrant Collection Rollback:**
1. **Stop services:**
   ```bash
   ./scripts/start_all_services.sh stop
   ```

2. **Restore from backup:**
   ```bash
   ./scripts/restore_backup.sh qdrant
   ```

3. **Revert application config:**
   ```bash
   # Restore previous QDRANT_COLLECTION value
   ```

4. **Restart services:**
   ```bash
   ./scripts/start_all_services.sh start
   ```

5. **Verify rollback:**
   ```bash
   ./scripts/health_check.sh
   ```

## Breaking Changes

### v1.0.0 → v1.1.0
- **Enhanced Document Processor v4.0:** Improved quality scoring (0.72-0.85 by format)
- **Impact:** Existing documents may have different quality scores if reprocessed
- **Action Required:** None (backward compatible)

### v1.1.0 → v1.2.0
- **Workspace Persistence:** All data moved to `/workspace/`
- **Impact:** Path changes for Qdrant storage, logs, data directories
- **Action Required:** Run `scripts/migrate_to_workspace.sh` (automated)

### v1.2.0 → v2.0.0 (Planned)
- **JWT Authentication:** All API endpoints will require authentication
- **Impact:** Breaking change - clients must provide valid JWT tokens
- **Action Required:** Update client applications to handle authentication
- **Migration Path:** Gradual rollout with grace period for legacy clients

## Future SQL Database Migrations

When SQL databases are added to the project (e.g., for user management, audit logs):

1. **Initialize Alembic:**
   ```bash
   alembic init alembic
   ```

2. **Create migration:**
   ```bash
   alembic revision --autogenerate -m "Add user table"
   ```

3. **Apply migration:**
   ```bash
   alembic upgrade head
   ```

4. **Rollback migration:**
   ```bash
   alembic downgrade -1
   ```

See T053 for Alembic setup and configuration.

## Notes

- **Qdrant Migrations:** Manual process, no automated migration tool
- **Backup First:** Always backup before schema changes
- **Test Migrations:** Test in staging environment before production
- **Document Changes:** Update this file for all schema changes
- **Version Tracking:** Use semantic versioning for all releases
- **Constitution Compliance:** All migrations must maintain constitution §9 requirements
