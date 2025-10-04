#!/bin/bash
# Environment variables for BMS Agent
# Source this file in scripts to ensure consistent configuration

# BMS Agent
export BMS_AGENT_ROOT=/workspace/001-bms-agent

# Ollama
export OLLAMA_MODELS=/workspace/data/ollama_models
export OLLAMA_HOST=http://localhost:11434

# Qdrant
export QDRANT_PATH=/workspace/apps/qdrant
export QDRANT_STORAGE=/workspace/data/qdrant_storage

# OpenWebUI
export OPENWEBUI_DATA_DIR=/workspace/data/openwebui

# Python virtual environments
export BMS_API_VENV=/workspace/bms-api-venv
export OPENWEBUI_VENV=/workspace/openwebui/venv

# Logs
export LOG_DIR=/workspace/logs
