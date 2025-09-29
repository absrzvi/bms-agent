#!/bin/bash
# Qdrant Service Management Script for BMS Agent

QDRANT_BINARY="$HOME/persistent/qdrant"
QDRANT_STORAGE="$HOME/persistent/qdrant_storage"
QDRANT_LOG="$HOME/persistent/logs/qdrant.log"
QDRANT_PID="$HOME/persistent/logs/qdrant.pid"

# Configuration
QDRANT_HOST="0.0.0.0"
QDRANT_PORT="6333"
QDRANT_GRPC_PORT="6334"

start_qdrant() {
    if [ -f "$QDRANT_PID" ] && kill -0 $(cat "$QDRANT_PID") 2>/dev/null; then
        echo "Qdrant is already running (PID: $(cat $QDRANT_PID))"
        return 0
    fi
    
    echo "Starting Qdrant..."
    mkdir -p "$(dirname "$QDRANT_LOG")"
    
    # Start Qdrant with configuration file
    cd "$(dirname "$0")/.."
    nohup "$QDRANT_BINARY" \
        --config-path "./config/config.yaml" \
        > "$QDRANT_LOG" 2>&1 &
    
    echo $! > "$QDRANT_PID"
    sleep 2
    
    if kill -0 $(cat "$QDRANT_PID") 2>/dev/null; then
        echo "✅ Qdrant started successfully (PID: $(cat $QDRANT_PID))"
        echo "   HTTP API: http://localhost:$QDRANT_PORT"
        echo "   gRPC API: http://localhost:$QDRANT_GRPC_PORT"
        echo "   Storage: $QDRANT_STORAGE"
        echo "   Logs: $QDRANT_LOG"
    else
        echo "❌ Failed to start Qdrant"
        return 1
    fi
}

stop_qdrant() {
    if [ ! -f "$QDRANT_PID" ]; then
        echo "Qdrant PID file not found"
        return 0
    fi
    
    PID=$(cat "$QDRANT_PID")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping Qdrant (PID: $PID)..."
        kill "$PID"
        sleep 2
        
        if kill -0 "$PID" 2>/dev/null; then
            echo "Force killing Qdrant..."
            kill -9 "$PID"
        fi
        
        rm -f "$QDRANT_PID"
        echo "✅ Qdrant stopped"
    else
        echo "Qdrant is not running"
        rm -f "$QDRANT_PID"
    fi
}

status_qdrant() {
    if [ -f "$QDRANT_PID" ] && kill -0 $(cat "$QDRANT_PID") 2>/dev/null; then
        PID=$(cat "$QDRANT_PID")
        echo "✅ Qdrant is running (PID: $PID)"
        
        # Check if API is responding
        if curl -s -f "http://localhost:$QDRANT_PORT/collections" > /dev/null; then
            echo "✅ Qdrant API is responding"
        else
            echo "⚠️  Qdrant process running but API not responding"
        fi
        
        return 0
    else
        echo "❌ Qdrant is not running"
        return 1
    fi
}

restart_qdrant() {
    echo "Restarting Qdrant..."
    stop_qdrant
    sleep 1
    start_qdrant
}

case "$1" in
    start)
        start_qdrant
        ;;
    stop)
        stop_qdrant
        ;;
    status)
        status_qdrant
        ;;
    restart)
        restart_qdrant
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo "  start   - Start Qdrant service"
        echo "  stop    - Stop Qdrant service"
        echo "  status  - Check Qdrant service status"
        echo "  restart - Restart Qdrant service"
        exit 1
        ;;
esac
