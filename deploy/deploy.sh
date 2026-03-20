#!/usr/bin/env bash
# deploy.sh — Set up / update the Teleprompter Streamlit app on the droplet.
# Run as root.
set -euo pipefail

INSTALL_DIR="/opt/teleprompter"
APP_USER="www-data"

echo "=== Deploying Teleprompter ==="

cd "$INSTALL_DIR"

# 1. Ensure venv exists
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    echo "Creating Python venv..."
    python3 -m venv "$INSTALL_DIR/.venv"
    chown -R "$APP_USER:$APP_USER" "$INSTALL_DIR/.venv"
fi

# 2. Install/update dependencies
echo "Updating Python dependencies..."
sudo -u "$APP_USER" "$INSTALL_DIR/.venv/bin/pip" install -r requirements.txt --quiet

# 3. Copy systemd service and reload
echo "Installing systemd service..."
cp "$INSTALL_DIR/deploy/teleprompter.service" /etc/systemd/system/
systemctl daemon-reload

# 4. Copy nginx config if not already included
NGINX_TOOLS_CONF="/etc/nginx/sites-enabled/tools.gregkiddfornevada.com"
if [ -f "$NGINX_TOOLS_CONF" ] && ! grep -q "teleprompter" "$NGINX_TOOLS_CONF"; then
    echo "NOTE: Add the teleprompter location block to $NGINX_TOOLS_CONF manually."
    echo "See $INSTALL_DIR/deploy/teleprompter.conf for the snippet."
fi

# 5. Enable and restart the service
echo "Restarting teleprompter service..."
systemctl enable teleprompter
systemctl restart teleprompter

echo ""
echo "=== Deploy Complete ==="
systemctl status teleprompter --no-pager
