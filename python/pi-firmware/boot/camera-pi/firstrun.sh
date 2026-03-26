#!/usr/bin/env bash
# Erststart-Konfiguration fuer Kamera-Pi (Pi 5 im CT-Scanner)
# Verbindet sich als WiFi-CLIENT mit dem Haupt-Pi AP-Netzwerk "AutoPilot-CT"
# Ausfuehren als root: sudo bash firstrun.sh
#
# Nach diesem Skript und Neustart:
#   - Kamera-Pi verbindet sich automatisch mit "AutoPilot-CT" WiFi
#   - Kamera-Pi erhaelt IP via DHCP vom Haupt-Pi (192.168.4.x)
#   - Haupt-Pi erreichbar unter 192.168.4.1
#   - mDNS: autopilot-cam.local
#   - Kein eigener AP, kein Internet — reiner WiFi-Client

set -euo pipefail

# ─── Konfiguration ────────────────────────────────────────────────
AP_SSID="AutoPilot-CT"
AP_PASS="autopilot"
HAUPT_PI_IP="192.168.4.1"
HOSTNAME_CAM="autopilot-cam"
CONFIG_DIR="/opt/autopilot-cam/config"

echo "========================================="
echo "  Kamera-Pi — WiFi Client Setup"
echo "========================================="

# Root-Pruefung
if [ "$EUID" -ne 0 ]; then
  echo "FEHLER: Bitte als root ausfuehren (sudo bash firstrun.sh)"
  exit 1
fi

# ─── Schritt 1: Hostname setzen ──────────────────────────────────
echo ""
echo "[1/6] Hostname auf '${HOSTNAME_CAM}' setzen..."
hostnamectl set-hostname "${HOSTNAME_CAM}"
sed -i "s/127\.0\.1\.1.*/127.0.1.1\t${HOSTNAME_CAM}/" /etc/hosts
echo "Hostname: $(hostname)"

# ─── Schritt 2: SSH aktivieren ───────────────────────────────────
echo ""
echo "[2/6] SSH aktivieren..."
systemctl enable ssh
systemctl start ssh
echo "  SSH aktiv"

# ─── Schritt 3: WiFi-Verbindung zum Haupt-Pi ────────────────────
echo ""
echo "[3/6] Verbinde mit WiFi '${AP_SSID}'..."

if command -v nmcli &>/dev/null; then
  # Bestehende Verbindung entfernen falls vorhanden
  nmcli con delete "${AP_SSID}" 2>/dev/null || true

  # Als WiFi-Client verbinden (NICHT als AP!)
  nmcli dev wifi connect "${AP_SSID}" password "${AP_PASS}"

  # Autoconnect sicherstellen
  nmcli con modify "${AP_SSID}" connection.autoconnect yes
  nmcli con modify "${AP_SSID}" connection.autoconnect-priority 100

  echo "  WiFi-Client verbunden mit: ${AP_SSID}"
  echo "  Zugewiesene IP: $(nmcli -g IP4.ADDRESS dev show wlan0 2>/dev/null || echo 'wird per DHCP vergeben')"
else
  # Fallback: wpa_supplicant (aeltere Pi OS Versionen)
  echo "  NetworkManager nicht gefunden — wpa_supplicant Fallback..."

  cat > /etc/wpa_supplicant/wpa_supplicant.conf << EOF
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=DE

network={
    ssid="${AP_SSID}"
    psk="${AP_PASS}"
    key_mgmt=WPA-PSK
    priority=100
}
EOF

  # DHCP fuer wlan0 sicherstellen
  if [ -f /etc/dhcpcd.conf ]; then
    # Statische IP-Eintraege fuer wlan0 entfernen (wir wollen DHCP)
    sed -i '/# autopilot-cam wlan0/,/^$/d' /etc/dhcpcd.conf
  fi

  systemctl enable wpa_supplicant
  echo "  wpa_supplicant konfiguriert fuer: ${AP_SSID}"
fi

# ─── Schritt 4: Konfigurationsverzeichnis ────────────────────────
echo ""
echo "[4/6] Erstelle ${CONFIG_DIR}..."
mkdir -p "${CONFIG_DIR}"

# Kamera-Pi Identitaet speichern
cat > "${CONFIG_DIR}/identity.json" << EOF
{
  "type": "camera",
  "hostname": "${HOSTNAME_CAM}",
  "hauptPi": "${HAUPT_PI_IP}",
  "port": 4811,
  "createdAt": "$(date -Iseconds)"
}
EOF
echo "  Identitaet gespeichert: ${CONFIG_DIR}/identity.json"

# ─── Schritt 5: mDNS konfigurieren ──────────────────────────────
echo ""
echo "[5/6] mDNS konfigurieren (${HOSTNAME_CAM}.local)..."

# systemd-resolved fuer mDNS verwenden (leichtgewichtiger als avahi)
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/mdns.conf << EOF
[Resolve]
MulticastDNS=yes
EOF

# Hostname in resolved setzen
hostnamectl set-hostname "${HOSTNAME_CAM}"

systemctl enable systemd-resolved
systemctl restart systemd-resolved 2>/dev/null || true
echo "  mDNS aktiv: ${HOSTNAME_CAM}.local"

# ─── Schritt 6: Beim Haupt-Pi registrieren ──────────────────────
echo ""
echo "[6/6] Registrierung beim Haupt-Pi (${HAUPT_PI_IP})..."

# Registrierung im Hintergrund — Haupt-Pi ist moeglicherweise noch nicht bereit
# Wiederholungsversuch via systemd oneshot nach dem Netzwerk
cat > /etc/systemd/system/autopilot-cam-register.service << EOF
[Unit]
Description=Registriere Kamera-Pi beim Haupt-Pi
After=network-online.target
Wants=network-online.target
# Mehrere Versuche, da der Haupt-Pi evtl. noch startet
StartLimitIntervalSec=300
StartLimitBurst=10

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c '\
  for i in 1 2 3 4 5 6 7 8 9 10; do \
    echo "Registrierungsversuch \$i bei ${HAUPT_PI_IP}..."; \
    if curl -sf -X POST http://${HAUPT_PI_IP}/api/discovery \
      -H "Content-Type: application/json" \
      -d "{\"type\":\"camera\",\"hostname\":\"${HOSTNAME_CAM}\",\"port\":4811}" \
      --connect-timeout 5 --max-time 10; then \
      echo "Erfolgreich registriert!"; \
      exit 0; \
    fi; \
    sleep 10; \
  done; \
  echo "WARNUNG: Registrierung fehlgeschlagen — Haupt-Pi nicht erreichbar"; \
  exit 0'
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable autopilot-cam-register.service
echo "  Registrierungsdienst aktiviert (startet nach Netzwerk)"

# ─── Firewall (falls ufw installiert) ────────────────────────────
if command -v ufw &>/dev/null; then
  ufw allow 22/tcp comment "SSH"
  ufw allow 4811/tcp comment "Kamera-Server"
  ufw allow 5353/udp comment "mDNS"
fi

echo ""
echo "========================================="
echo "  Kamera-Pi Erststart abgeschlossen!"
echo "========================================="
echo ""
echo "  WiFi:          ${AP_SSID} (Client-Modus)"
echo "  Haupt-Pi:      ${HAUPT_PI_IP}"
echo "  Hostname:       ${HOSTNAME_CAM}"
echo "  mDNS:          ${HOSTNAME_CAM}.local"
echo "  Kamera-Port:   4811"
echo "  SSH:           aktiv"
echo ""
echo "  >>> setup.sh ausfuehren, dann: sudo reboot <<<"
echo ""
