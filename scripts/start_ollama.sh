#!/bin/bash
# Ollama Service Management Script for BMS Agent

OLLAMA_BINARY="/workspace/ollama/bin/ollama"
OLLAMA_HOME="/workspace/ollama"
OLLAMA_MODELS="/workspace/ollama/models"
OLLAMA_LOG="/workspace/logs/ollama.log"
OLLAMA_PID="/workspace/logs/ollama.pid"

# Configuration
OLLAMA_HOST="0.0.0.0"
OLLAMA_PORT="11434"

start_ollama() {
    if [ -f "$OLLAMA_PID" ] && kill -0 $(cat "$OLLAMA_PID") 2>/dev/null; then
        echo "Ollama is already running (PID: $(cat $OLLAMA_PID))"
        return 0
    fi
    
    echo "Starting Ollama..."
    mkdir -p "$(dirname "$OLLAMA_LOG")"
    
    # Set environment variables for Ollama
    export OLLAMA_HOME="$OLLAMA_HOME"
    export OLLAMA_MODELS="$OLLAMA_MODELS"
    export OLLAMA_HOST="$OLLAMA_HOST"
    export OLLAMA_PORT="$OLLAMA_PORT"
    export OLLAMA_KEEP_ALIVE="24h"
    export OLLAMA_MAX_LOADED_MODELS="3"
    
    # Start Ollama server
    nohup "$OLLAMA_BINARY" serve \
        > "$OLLAMA_LOG" 2>&1 &
    
    echo $! > "$OLLAMA_PID"
    sleep 3
    
    if kill -0 $(cat "$OLLAMA_PID") 2>/dev/null; then
        echo "✅ Ollama started successfully (PID: $(cat $OLLAMA_PID))"
        echo "   API: http://localhost:$OLLAMA_PORT"
        echo "   Models: $OLLAMA_MODELS"
        echo "   Logs: $OLLAMA_LOG"
        
        # Check if API is responding
        sleep 2
        if curl -s -f "http://localhost:$OLLAMA_PORT/api/version" > /dev/null; then
            echo "✅ Ollama API is responding"
        else
            echo "⚠️  Ollama process running but API not responding yet"
        fi
    else
        echo "❌ Failed to start Ollama"
        return 1
    fi
}

stop_ollama() {
    if [ ! -f "$OLLAMA_PID" ]; then
        echo "Ollama PID file not found"
        return 0
    fi
    
    PID=$(cat "$OLLAMA_PID")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping Ollama (PID: $PID)..."
        kill "$PID"
        sleep 3
        
        if kill -0 "$PID" 2>/dev/null; then
            echo "Force killing Ollama..."
            kill -9 "$PID"
        fi
        
        rm -f "$OLLAMA_PID"
        echo "✅ Ollama stopped"
    else
        echo "Ollama is not running"
        rm -f "$OLLAMA_PID"
    fi
}

status_ollama() {
    if [ -f "$OLLAMA_PID" ] && kill -0 $(cat "$OLLAMA_PID") 2>/dev/null; then
        PID=$(cat "$OLLAMA_PID")
        echo "✅ Ollama is running (PID: $PID)"
        
        # Check if API is responding
        if curl -s -f "http://localhost:$OLLAMA_PORT/api/version" > /dev/null; then
            echo "✅ Ollama API is responding"
            
            # Show available models
            echo "📋 Available models:"
            curl -s "http://localhost:$OLLAMA_PORT/api/tags" | jq -r '.models[]?.name // "No models found"' 2>/dev/null || echo "   (Unable to fetch model list)"
        else
            echo "⚠️  Ollama process running but API not responding"
        fi
        
        return 0
    else
        echo "❌ Ollama is not running"
        return 1
    fi
}

restart_ollama() {
    echo "Restarting Ollama..."
    stop_ollama
    sleep 2
    start_ollama
}

pull_model() {
    local model_name="$1"
    if [ -z "$model_name" ]; then
        echo "Usage: $0 pull <model_name>"
        echo "Example: $0 pull snowflake-arctic-embed2"
        return 1
    fi
    
    echo "Pulling model: $model_name"
    export OLLAMA_HOME="$OLLAMA_HOME"
    export OLLAMA_MODELS="$OLLAMA_MODELS"
    
    "$OLLAMA_BINARY" pull "$model_name"
}

list_models() {
    echo "📋 Available models:"
    export OLLAMA_HOME="$OLLAMA_HOME"
    export OLLAMA_MODELS="$OLLAMA_MODELS"
    
    "$OLLAMA_BINARY" list
}

case "$1" in
    start)
        start_ollama
        ;;
    stop)
        stop_ollama
        ;;
    status)
        status_ollama
        ;;
    restart)
        restart_ollama
        ;;
    pull)
        pull_model "$2"
        ;;
    list)
        list_models
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|pull <model>|list}"
        echo "  start   - Start Ollama service"
        echo "  stop    - Stop Ollama service"
        echo "  status  - Check Ollama service status"
        echo "  restart - Restart Ollama service"
        echo "  pull    - Pull a model (e.g., snowflake-arctic-embed2)"
        echo "  list    - List available models"
        exit 1
        ;;
esac
