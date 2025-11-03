#!/bin/bash
# Wait for port 5000 to be available, then start system monitor

PORT=5000
TIMEOUT=60
START_TIME=$(date +%s)

echo "Waiting for port $PORT to be available..."

while true; do
    # Check if port is open using /dev/tcp
    if timeout 1 bash -c "echo >/dev/tcp/localhost/$PORT" 2>/dev/null; then
        echo "Port $PORT is now available! Starting system monitor..."
        # Use system python (PyQt5 is installed system-wide)
        python3 /home/kw/cyl_a/system_monitor_qt.py &
        echo "System monitor started!"
        exit 0
    fi

    # Check timeout
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    if [ $ELAPSED -gt $TIMEOUT ]; then
        echo "Timeout waiting for port $PORT"
        exit 1
    fi

    sleep 1
done