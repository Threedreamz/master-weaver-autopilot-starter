#!/usr/bin/env bash
# Full setup script for Raspberry Pi 5 — AutoPilot Central Server
# Installs Node.js, pnpm, Nginx, PM2, builds all apps, configures services
# Run as root: sudo bash setup.sh

set -euo pipefail

INSTALL_DIR="/opt/autopilot"
REPO_URL="https://github.com/Threedreamz/master-weaver-autopilot-starter.git"
SERVICE_NAME="autopilot-pi"
NODE_MAJOR=22

echo "========================================="
echo "  Autopilot Pi — Central Server Setup"
echo "========================================="

# Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root (sudo bash setup.sh)"
  exit 1
fi

echo ""
echo "[1/10] Updating system packages..."
apt-get update -y
apt-get upgrade -y

echo ""
echo "[2/10] Installing Node.js ${NODE_MAJOR}..."
if ! command -v node &>/dev/null || ! node -v | grep -q "v${NODE_MAJOR}"; then
  curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash -
  apt-get install -y nodejs
fi
echo "Node.js: $(node -v)"
echo "npm: $(npm -v)"

echo ""
echo "[3/10] Installing pnpm + PM2..."
if ! command -v pnpm &>/dev/null; then
  npm install -g pnpm
fi
echo "pnpm: $(pnpm -v)"

if ! command -v pm2 &>/dev/null; then
  npm install -g pm2
fi
echo "pm2: $(pm2 -v)"

echo ""
echo "[4/10] Installing Nginx..."
apt-get install -y nginx
systemctl stop nginx  # Will configure before starting

echo ""
echo "[5/10] Installing camera + system dependencies..."
apt-get install -y \
  libcamera-apps \
  v4l-utils \
  libcamera-dev \
  python3-libcamera \
  ffmpeg \
  avahi-daemon \
  avahi-utils \
  libnss-mdns

echo ""
echo "[6/10] Cloning/updating repository to ${INSTALL_DIR}..."
if [ -d "${INSTALL_DIR}/.git" ]; then
  echo "  Repository exists, pulling latest..."
  cd "${INSTALL_DIR}"
  git pull --ff-only
else
  # Check if /opt/autopilot exists but isn't a git repo (e.g., config dir created by firstboot)
  if [ -d "${INSTALL_DIR}" ]; then
    # Preserve config directory
    if [ -d "${INSTALL_DIR}/config" ]; then
      cp -r "${INSTALL_DIR}/config" /tmp/autopilot-config-backup
    fi
    rm -rf "${INSTALL_DIR}"
  fi
  git clone --branch dev "${REPO_URL}" "${INSTALL_DIR}"
  # Restore config directory
  if [ -d /tmp/autopilot-config-backup ]; then
    cp -r /tmp/autopilot-config-backup "${INSTALL_DIR}/config"
    rm -rf /tmp/autopilot-config-backup
  fi
fi

# Ensure config and releases directories exist
mkdir -p "${INSTALL_DIR}/config"
mkdir -p "${INSTALL_DIR}/releases"

echo ""
echo "[7/10] Installing dependencies and building all apps..."
cd "${INSTALL_DIR}"
pnpm install --frozen-lockfile || pnpm install

# Build iPad app and Setup portal (Next.js standalone)
echo "  Building iPad app (@autopilot/ipad)..."
pnpm build --filter=@autopilot/ipad || echo "  WARNING: iPad app build failed (may not exist yet)"

echo "  Building Setup portal (@autopilot/setup)..."
pnpm build --filter=@autopilot/setup || echo "  WARNING: Setup portal build failed (may not exist yet)"

# Build camera server
echo "  Building camera server..."
cd "${INSTALL_DIR}/python/pi-firmware"
pnpm install --frozen-lockfile || pnpm install
pnpm build

echo ""
echo "[8/10] Configuring Nginx..."
cd "${INSTALL_DIR}"

# Copy nginx config
cp "${INSTALL_DIR}/python/pi-firmware/boot/nginx.conf" /etc/nginx/sites-available/autopilot

# Enable autopilot site, disable default
ln -sf /etc/nginx/sites-available/autopilot /etc/nginx/sites-enabled/autopilot
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t
systemctl enable nginx
systemctl start nginx
echo "  Nginx configured and started"

echo ""
echo "[9/10] Configuring PM2..."

# Copy ecosystem config
cp "${INSTALL_DIR}/python/pi-firmware/boot/ecosystem.config.js" "${INSTALL_DIR}/ecosystem.config.js"

# Set up PM2 startup (generates systemd unit)
pm2 startup systemd -u pi --hp /home/pi 2>/dev/null || pm2 startup systemd

# Start all services via PM2
cd "${INSTALL_DIR}"
pm2 start ecosystem.config.js
pm2 save

echo "  PM2 configured with ecosystem.config.js"

# Install systemd service as a PM2 wrapper
cp "${INSTALL_DIR}/python/pi-firmware/boot/autopilot-pi.service" \
   /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}

echo ""
echo "[10/10] Enabling supporting services..."

# Enable Avahi for mDNS
systemctl enable avahi-daemon
systemctl start avahi-daemon

# Enable hardware watchdog
if ! grep -q "bcm2835_wdt" /etc/modules 2>/dev/null; then
  echo "bcm2835_wdt" >> /etc/modules
fi

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "  Services managed by PM2:"
echo "    - camera        → :4801 (camera streams)"
echo "    - ipad-app      → :4800 (iPad interface)"
echo "    - setup-portal  → :4804 (setup + download)"
echo ""
echo "  Nginx reverse proxy on port 80:"
echo "    - http://autopilot.local → setup portal (until setup complete)"
echo "    - http://autopilot.local → iPad app (after setup complete)"
echo "    - http://autopilot.local/camera/ → camera streams"
echo "    - http://autopilot.local/releases/ → download files"
echo ""
echo "  PM2 commands:"
echo "    pm2 status                # Service status"
echo "    pm2 logs                  # View all logs"
echo "    pm2 restart all           # Restart everything"
echo ""
echo "  >>> Reboot to activate: sudo reboot <<<"
echo ""
