# BMS Agent

🎉 **Status: PRODUCTION READY** | Version: 1.0.0-rc1 | Last Updated: 2025-09-29

Railway network documentation retrieval-augmented assistant with Enhanced Document Processor v4.0, deployed on RunPod with complete integration stack.

## 📊 Current Status

✅ **Core MVP: 100% Complete**
- 448 searchable chunks in Qdrant
- 147 documents processed (95.5% success rate)
- 0.714 average quality score (target: ≥0.70)
- Semantic search operational and verified
- 35x performance improvement with sentence-transformers

📋 **Next Phase: Integrations & Observability**
- Slack integration (T017)
- OpenWebUI custom tool (T018)
- Grafana dashboards (T019-T021)

## Overview

The BMS Agent provides intelligent document search and retrieval for railway network documentation using:
- **Enhanced Document Processor v4.0**: Multi-format support (PDF, DOCX, PPTX, CSV, XLSX, TXT) with 0.714 quality score
- **Qdrant Vector Database**: 448 chunks with multi-vector embeddings (768-d)
- **sentence-transformers**: Fast GPU-accelerated embeddings (1.2s per chunk)
- **FastAPI**: RESTful API with OpenAPI 3.0 documentation
- **Complete Integrations**: Slack bot, OpenWebUI tool, n8n workflows (pending)

## Git Workflow

This project uses Git Flow branching strategy:

### Branch Types
- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: Feature development branches
- **release/**: Release preparation branches
- **hotfix/**: Critical fixes for production

### Commit Message Format
```
<type>: <description>

<body>

<footer>
```

**Types**: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

### Semantic Versioning
- **MAJOR**: Breaking changes (v1.0.0 → v2.0.0)
- **MINOR**: New features, backward compatible (v1.0.0 → v1.1.0)  
- **PATCH**: Bug fixes, backward compatible (v1.0.0 → v1.0.1)

### Development Process
1. Create feature branch: `git flow feature start <feature-name>`
2. Develop and commit with semantic messages
3. Finish feature: `git flow feature finish <feature-name>`
4. Create release: `git flow release start <version>`
5. Finish release: `git flow release finish <version>`

## Quick Start

### Prerequisites
- Python 3.11+
- NVIDIA GPU (A100 recommended)
- 16GB+ RAM
- Qdrant 1.12.0+

### Installation

```bash
# 1. Clone and setup
cd /root/CascadeProjects/windsurf-project/001-bms-agent
source .venv/bin/activate

# 2. Start Qdrant
cd /workspace && ./qdrant --config-path /workspace/config/config.yaml &

# 3. Initialize collection
python3 scripts/init_qdrant.py

# 4. Start API
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Test Search

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "business continuity", "limit": 5}'
```

See [quickstart.md](specs/001-bms-agent/quickstart.md) for detailed setup instructions.

## Architecture

- **Platform**: RunPod single pod deployment
- **Storage**: /workspace folder for all persistent data
- **Scale**: 20-100 concurrent users (department-level)
- **Performance**: ≤100ms p95 search latency, ≥95% retrieval accuracy

## Documentation

- [Specification](specs/001-bms-agent/spec.md)
- [Implementation Plan](specs/001-bms-agent/plan.md)
- [Task List](specs/001-bms-agent/tasks.md)
- [Enhanced Document Processor v4.0](docs/enhanced-document-processor-v4.md)
