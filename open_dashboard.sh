#!/bin/bash

# Find the IP address (prefer Wi-Fi, fallback to ethernet)
IP_ADDRESS=""

# Try to get Wi-Fi IP first (usually starts with 192.168.1.x)
WIFI_IP=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K[0-9.]+' | head -1)
if [[ $WIFI_IP =~ ^192\.168\.1\. ]]; then
    IP_ADDRESS=$WIFI_IP
else
    # Fallback to any available IP
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
fi

# If no IP found, use localhost
if [ -z "$IP_ADDRESS" ]; then
    IP_ADDRESS="localhost"
fi

# Open dashboard in default browser
DASHBOARD_URL="http://$IP_ADDRESS:5050"
echo "Opening dashboard at: $DASHBOARD_URL"

# Try different browser commands (prefer Chromium)
if command -v chromium-browser >/dev/null 2>&1; then
    chromium-browser "$DASHBOARD_URL" &
elif command -v chromium >/dev/null 2>&1; then
    chromium "$DASHBOARD_URL" &
elif command -v google-chrome >/dev/null 2>&1; then
    google-chrome "$DASHBOARD_URL" &
elif command -v firefox >/dev/null 2>&1; then
    firefox "$DASHBOARD_URL" &
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$DASHBOARD_URL" &
else
    echo "No browser found. Please open: $DASHBOARD_URL"
fi