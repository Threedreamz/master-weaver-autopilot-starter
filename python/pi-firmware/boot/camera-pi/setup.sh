#!/usr/bin/env bash
# Minimales Setup fuer Kamera-Pi — nur Node.js + Kamera-Server
# Kein Nginx, kein PM2, kein Setup-Portal — nur das Noetigste
# Ausfuehren als root: sudo bash setup.sh

set -euo pipefail

INSTALL_DIR="/opt/autopilot-cam"
REPO_URL="https://github.com/Threedreamz/master-weaver-autopilot-starter.git"
SERVICE_NAME="autopilot-cam"
NODE_MAJOR=22

echo "========================================="
echo "  Kamera-Pi — Minimales Setup"
echo "========================================="

# Root-Pruefung
if [ "$EUID" -ne 0 ]; then
  echo "FEHLER: Bitte als root ausfuehren (sudo bash setup.sh)"
  exit 1
fi

# ─── Schritt 1: System aktualisieren ─────────────────────────────
echo ""
echo "[1/7] System-Pakete aktualisieren..."
apt-get update -y
apt-get upgrade -y

# ─── Schritt 2: Node.js installieren ─────────────────────────────
echo ""
echo "[2/7] Node.js ${NODE_MAJOR} installieren..."
if ! command -v node &>/dev/null || ! node -v | grep -q "v${NODE_MAJOR}"; then
  curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash -
  apt-get install -y nodejs
fi
echo "Node.js: $(node -v)"
echo "npm: $(npm -v)"

# ─── Schritt 3: pnpm installieren ────────────────────────────────
echo ""
echo "[3/7] pnpm installieren..."
if ! command -v pnpm &>/dev/null; then
  npm install -g pnpm
fi
echo "pnpm: $(pnpm -v)"

# ─── Schritt 4: Kamera-Abhaengigkeiten installieren ─────────────
echo ""
echo "[4/7] Kamera-System-Pakete installieren..."
apt-get install -y \
  libcamera-apps \
  v4l-utils \
  libcamera-dev \
  python3-libcamera \
  ffmpeg \
  curl

# ─── Schritt 5: Nur Kamera-Server klonen/kopieren ───────────────
echo ""
echo "[5/7] Kamera-Server nach ${INSTALL_DIR} installieren..."

# Bestehende Config sichern
if [ -d "${INSTALL_DIR}/config" ]; then
  cp -r "${INSTALL_DIR}/config" /tmp/autopilot-cam-config-backup
fi

if [ -d "${INSTALL_DIR}/python/pi-firmware/.git" ] || [ -d "${INSTALL_DIR}/.git" ]; then
  echo "  Repository existiert, aktualisiere..."
  cd "${INSTALL_DIR}"
  git pull --ff-only 2>/dev/null || true
else
  # Sparse Checkout — nur pi-firmware Verzeichnis klonen
  echo "  Sparse Checkout: nur python/pi-firmware/..."
  rm -rf "${INSTALL_DIR}/repo" 2>/dev/null || true
  mkdir -p "${INSTALL_DIR}/repo"
  cd "${INSTALL_DIR}/repo"
  git init
  git remote add origin "${REPO_URL}"
  git config core.sparseCheckout true
  echo "python/pi-firmware/" > .git/info/sparse-checkout
  echo "pnpm-workspace.yaml" >> .git/info/sparse-checkout
  git pull origin dev --depth 1
fi

# Config wiederherstellen
if [ -d /tmp/autopilot-cam-config-backup ]; then
  mkdir -p "${INSTALL_DIR}/config"
  cp -r /tmp/autopilot-cam-config-backup/* "${INSTALL_DIR}/config/" 2>/dev/null || true
  rm -rf /tmp/autopilot-cam-config-backup
fi

# Config-Verzeichnis sicherstellen
mkdir -p "${INSTALL_DIR}/config"

# ─── Schritt 6: Dependencies installieren + bauen ────────────────
echo ""
echo "[6/7] Abhaengigkeiten installieren und bauen..."
cd "${INSTALL_DIR}/repo/python/pi-firmware"
pnpm install --frozen-lockfile || pnpm install

echo "  Kamera-Server bauen..."
pnpm build

# ─── Schritt 7: Systemd-Service einrichten ───────────────────────
echo ""
echo "[7/7] Systemd-Service '${SERVICE_NAME}' einrichten..."

# Service-Datei kopieren
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/autopilot-cam.service" ]; then
  cp "${SCRIPT_DIR}/autopilot-cam.service" /etc/systemd/system/${SERVICE_NAME}.service
else
  # Fallback: Service inline erstellen
  cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=AutoPilot Kamera-Server (Kamera-Pi)
Documentation=https://github.com/Threedreamz/master-weaver-autopilot-starter
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=${INSTALL_DIR}/repo/python/pi-firmware
ExecStart=/usr/bin/node dist/server.js
Restart=always
RestartSec=5

Environment=NODE_ENV=production
Environment=PORT=4811
Environment=HOST=0.0.0.0
Environment=LOG_LEVEL=info

MemoryMax=512M
CPUQuota=80%

StandardOutput=journal
StandardError=journal
SyslogIdentifier=autopilot-cam

[Install]
WantedBy=multi-user.target
EOF
fi

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME} || echo "  WARNUNG: Service konnte nicht gestartet werden (evtl. fehlende Kamera)"

echo ""
echo "========================================="
echo "  Kamera-Pi Setup abgeschlossen!"
echo "========================================="
echo ""
echo "  Kamera-Server:  http://$(hostname).local:4811"
echo "  Service:        systemctl status ${SERVICE_NAME}"
echo "  Logs:           journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "  Naechster Schritt (optional):"
echo "    sudo bash power-save.sh    # Stromsparmodus aktivieren"
echo ""
echo "  >>> Neustart empfohlen: sudo reboot <<<"
echo ""
