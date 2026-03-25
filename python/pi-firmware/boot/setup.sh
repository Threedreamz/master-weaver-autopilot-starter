#!/usr/bin/env bash
# First-boot setup script for Raspberry Pi 5 Autopilot Camera Server
# Run as root: sudo bash setup.sh

set -euo pipefail

INSTALL_DIR="/opt/autopilot"
REPO_URL="https://github.com/Threedreamz/master-weaver-autopilot-starter.git"
SERVICE_NAME="autopilot-pi"
NODE_MAJOR=22

echo "========================================="
echo "  Autopilot Pi Camera Server Setup"
echo "========================================="

# Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root (sudo bash setup.sh)"
  exit 1
fi

echo ""
echo "[1/7] Updating system packages..."
apt-get update -y
apt-get upgrade -y

echo ""
echo "[2/7] Installing Node.js ${NODE_MAJOR}..."
if ! command -v node &>/dev/null || ! node -v | grep -q "v${NODE_MAJOR}"; then
  curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash -
  apt-get install -y nodejs
fi
echo "Node.js: $(node -v)"
echo "npm: $(npm -v)"

# Install pnpm
if ! command -v pnpm &>/dev/null; then
  npm install -g pnpm
fi

echo ""
echo "[3/7] Installing camera + WiFi AP dependencies..."
apt-get install -y \
  libcamera-apps \
  v4l-utils \
  libcamera-dev \
  python3-libcamera \
  ffmpeg \
  hostapd \
  dnsmasq \
  avahi-daemon \
  avahi-utils \
  libnss-mdns

echo ""
echo "[4/7] Cloning repository to ${INSTALL_DIR}..."
if [ -d "${INSTALL_DIR}" ]; then
  echo "Directory exists, pulling latest..."
  cd "${INSTALL_DIR}"
  git pull --ff-only
else
  git clone "${REPO_URL}" "${INSTALL_DIR}"
  cd "${INSTALL_DIR}"
fi

echo ""
echo "[5/7] Installing dependencies and building..."
cd "${INSTALL_DIR}/python/pi-firmware"
pnpm install --frozen-lockfile || pnpm install
pnpm build

echo ""
echo "[6/7] Installing systemd service..."
cp "${INSTALL_DIR}/python/pi-firmware/boot/autopilot-pi.service" \
   /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}

echo ""
echo "[7/7] Enabling supporting services..."

# Enable Avahi for mDNS
if ! systemctl is-enabled avahi-daemon &>/dev/null; then
  apt-get install -y avahi-daemon
  systemctl enable avahi-daemon
  systemctl start avahi-daemon
fi

# Enable hardware watchdog
if ! grep -q "bcm2835_wdt" /etc/modules 2>/dev/null; then
  echo "bcm2835_wdt" >> /etc/modules
fi

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Service status: systemctl status ${SERVICE_NAME}"
echo "View logs:      journalctl -u ${SERVICE_NAME} -f"
echo "Server URL:     http://$(hostname -I | awk '{print $1}'):4801"
echo "Health check:   curl http://localhost:4801/health"
echo ""
