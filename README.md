# BMS Agent

Railway network documentation retrieval-augmented assistant with Enhanced Document Processor v4.0, deployed on RunPod with complete integration stack.

## Overview

The BMS Agent provides intelligent document search and retrieval for railway network documentation using:
- **Enhanced Document Processor v4.0**: Multi-format support (PDF, DOCX, PPTX, CSV, XLSX, TXT) with 0.718 quality score
- **Qdrant Vector Database**: Hybrid search with semantic and keyword capabilities
- **FastAPI**: RESTful API with OpenAPI 3.0 documentation
- **Complete Integrations**: Slack bot, OpenWebUI tool, n8n workflows

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
