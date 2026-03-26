#!/usr/bin/env bash
# Stromsparmodus fuer Kamera-Pi — maximiert Powerbank-Laufzeit
# Deaktiviert alles was nicht fuer den Kamera-Server gebraucht wird
# Ausfuehren als root: sudo bash power-save.sh

set -euo pipefail

CONFIG_TXT="/boot/firmware/config.txt"
# Aeltere Pi OS Versionen nutzen /boot/config.txt
if [ ! -f "${CONFIG_TXT}" ]; then
  CONFIG_TXT="/boot/config.txt"
fi

echo "========================================="
echo "  Kamera-Pi — Stromsparmodus"
echo "========================================="

# Root-Pruefung
if [ "$EUID" -ne 0 ]; then
  echo "FEHLER: Bitte als root ausfuehren (sudo bash power-save.sh)"
  exit 1
fi

# ─── 1. Bluetooth deaktivieren ───────────────────────────────────
echo ""
echo "[1/7] Bluetooth deaktivieren..."
if ! grep -q "dtoverlay=disable-bt" "${CONFIG_TXT}" 2>/dev/null; then
  echo "" >> "${CONFIG_TXT}"
  echo "# Kamera-Pi Stromsparmodus — Bluetooth aus" >> "${CONFIG_TXT}"
  echo "dtoverlay=disable-bt" >> "${CONFIG_TXT}"
  echo "  Bluetooth-Overlay hinzugefuegt (aktiv nach Neustart)"
else
  echo "  Bereits deaktiviert"
fi

# Bluetooth-Dienste sofort stoppen
systemctl disable bluetooth 2>/dev/null || true
systemctl stop bluetooth 2>/dev/null || true
systemctl disable hciuart 2>/dev/null || true
systemctl stop hciuart 2>/dev/null || true
echo "  Bluetooth-Dienste gestoppt"

# ─── 2. HDMI deaktivieren ───────────────────────────────────────
echo ""
echo "[2/7] HDMI-Ausgang deaktivieren..."
# Sofort deaktivieren
if command -v vcgencmd &>/dev/null; then
  vcgencmd display_power 0 2>/dev/null || true
  echo "  HDMI sofort deaktiviert (vcgencmd)"
elif command -v tvservice &>/dev/null; then
  tvservice -o 2>/dev/null || true
  echo "  HDMI sofort deaktiviert (tvservice)"
fi

# Beim Booten deaktivieren via systemd
cat > /etc/systemd/system/hdmi-off.service << 'EOF'
[Unit]
Description=HDMI beim Start deaktivieren
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'vcgencmd display_power 0 2>/dev/null || tvservice -o 2>/dev/null || true'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable hdmi-off.service
echo "  HDMI wird bei jedem Start deaktiviert"

# ─── 3. GPU-Speicher reduzieren ──────────────────────────────────
echo ""
echo "[3/7] GPU-Speicher auf 16 MB reduzieren..."
# Kamera nutzt libcamera (laeuft auf CPU/ISP, nicht GPU)
if grep -q "^gpu_mem=" "${CONFIG_TXT}" 2>/dev/null; then
  sed -i 's/^gpu_mem=.*/gpu_mem=16/' "${CONFIG_TXT}"
else
  echo "" >> "${CONFIG_TXT}"
  echo "# Kamera-Pi Stromsparmodus — minimaler GPU-Speicher" >> "${CONFIG_TXT}"
  echo "gpu_mem=16" >> "${CONFIG_TXT}"
fi
echo "  gpu_mem=16 gesetzt (aktiv nach Neustart)"

# ─── 4. WiFi Power-Save aktivieren ──────────────────────────────
echo ""
echo "[4/7] WiFi Power-Save aktivieren..."
iw dev wlan0 set power_save on 2>/dev/null || true

# Permanent via NetworkManager (falls vorhanden)
if command -v nmcli &>/dev/null; then
  # WiFi-Powersave: 2 = aktiviert
  nmcli con modify "AutoPilot-CT" wifi.powersave 2 2>/dev/null || true
  echo "  WiFi Power-Save aktiviert (NetworkManager)"
else
  # Fallback: via systemd
  cat > /etc/systemd/system/wifi-powersave.service << 'EOF'
[Unit]
Description=WiFi Power-Save aktivieren
After=network-online.target

[Service]
Type=oneshot
ExecStart=/sbin/iw dev wlan0 set power_save on
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable wifi-powersave.service
  echo "  WiFi Power-Save aktiviert (systemd)"
fi

# ─── 5. Unnoetige Dienste deaktivieren ───────────────────────────
echo ""
echo "[5/7] Unnoetige Dienste deaktivieren..."

SERVICES_TO_DISABLE=(
  "avahi-daemon"          # mDNS via systemd-resolved stattdessen
  "triggerhappy"          # Tastenkuerzel-Daemon — brauchen wir nicht
  "ModemManager"          # Modem-Manager — kein Mobilfunk
  "wpa_supplicant"        # NetworkManager uebernimmt WiFi
  "cups"                  # Druckdienst
  "cups-browsed"          # Drucker-Erkennung
)

for svc in "${SERVICES_TO_DISABLE[@]}"; do
  if systemctl is-enabled "${svc}" &>/dev/null; then
    systemctl disable "${svc}" 2>/dev/null || true
    systemctl stop "${svc}" 2>/dev/null || true
    echo "  ${svc} deaktiviert"
  else
    echo "  ${svc} bereits inaktiv oder nicht vorhanden"
  fi
done

# ─── 6. CPU-Governor auf ondemand setzen ─────────────────────────
echo ""
echo "[6/7] CPU-Governor auf 'ondemand' setzen..."
# Sofort setzen fuer alle CPU-Kerne
for cpu in /sys/devices/system/cpu/cpu[0-3]/cpufreq/scaling_governor; do
  if [ -f "$cpu" ]; then
    echo "ondemand" > "$cpu" 2>/dev/null || true
  fi
done

# Permanent via systemd
cat > /etc/systemd/system/cpu-governor.service << 'EOF'
[Unit]
Description=CPU-Governor auf ondemand setzen
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'for cpu in /sys/devices/system/cpu/cpu[0-3]/cpufreq/scaling_governor; do echo ondemand > $cpu 2>/dev/null || true; done'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable cpu-governor.service
echo "  CPU-Governor: ondemand (aktiv)"

# ─── 7. LEDs deaktivieren (optional, spart minimal) ─────────────
echo ""
echo "[7/7] Status-LEDs deaktivieren..."
if ! grep -q "dtparam=act_led_trigger=none" "${CONFIG_TXT}" 2>/dev/null; then
  echo "" >> "${CONFIG_TXT}"
  echo "# Kamera-Pi Stromsparmodus — LEDs aus" >> "${CONFIG_TXT}"
  echo "dtparam=act_led_trigger=none" >> "${CONFIG_TXT}"
  echo "dtparam=act_led_activelow=on" >> "${CONFIG_TXT}"
  echo "dtparam=pwr_led_trigger=default-on" >> "${CONFIG_TXT}"
  echo "dtparam=pwr_led_activelow=on" >> "${CONFIG_TXT}"
  echo "  LEDs deaktiviert (aktiv nach Neustart)"
else
  echo "  Bereits deaktiviert"
fi

# ─── Zusammenfassung ─────────────────────────────────────────────
echo ""
echo "========================================="
echo "  Stromsparmodus aktiviert!"
echo "========================================="
echo ""
echo "  Sofort wirksam:"
echo "    - HDMI aus"
echo "    - WiFi Power-Save an"
echo "    - CPU ondemand"
echo "    - Unnoetige Dienste gestoppt"
echo ""
echo "  Nach Neustart zusaetzlich:"
echo "    - Bluetooth deaktiviert (dtoverlay)"
echo "    - GPU-Speicher auf 16 MB"
echo "    - Status-LEDs aus"
echo ""
echo "  Geschaetzte Einsparung: ~1-2W"
echo "  Erwartete Powerbank-Laufzeit:"
echo "    - 10.000 mAh: ~6-8 Stunden"
echo "    - 20.000 mAh: ~12-16 Stunden"
echo "    - 26.800 mAh: ~16-20 Stunden"
echo ""
echo "  >>> sudo reboot fuer volle Wirkung <<<"
echo ""
