#!/bin/bash
set +e

# =============================================================================
# AutoPilot Pi — Complete First-Run Setup
# Runs ONCE on first boot via: systemd.run=/boot/firmware/firstrun.sh
# After this script exits 0, systemd reboots the Pi automatically.
#
# Monitor from Mac (Pi on hotspot):
#   ssh autopilot-main@<hotspot-ip> 'tail -f /boot/firmware/firstrun-log.txt'
# =============================================================================

LOG="/boot/firmware/firstrun-log.txt"
exec > >(tee -a "$LOG") 2>&1

echo "============================================="
echo "  AutoPilot Pi — First Boot Setup"
echo "  $(date)"
echo "============================================="

# ─── 1. User + SSH ────────────────────────────────────────────────────────────
echo ""
echo "[1/12] Creating user and enabling SSH..."
if ! id -u autopilot-main >/dev/null 2>&1; then
    useradd -m -s /bin/bash autopilot-main
    echo 'autopilot-main:autopilot2026' | chpasswd
    usermod -aG sudo,video,gpio,i2c,spi autopilot-main
    echo 'autopilot-main ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/autopilot-main
    chmod 440 /etc/sudoers.d/autopilot-main
fi
systemctl enable ssh
mkdir -p /etc/ssh/sshd_config.d
echo "PasswordAuthentication yes" > /etc/ssh/sshd_config.d/autopilot.conf
systemctl start ssh
echo "  user: autopilot-main / autopilot2026"

# ─── 2. Hostname + timezone ───────────────────────────────────────────────────
echo ""
echo "[2/12] Setting hostname and timezone..."
echo "autopilot-pi" > /etc/hostname
if grep -q "127.0.1.1" /etc/hosts 2>/dev/null; then
    sed -i 's/127\.0\.1\.1.*/127.0.1.1\tautopilot-pi/' /etc/hosts
else
    echo "127.0.1.1 autopilot-pi" >> /etc/hosts
fi
ln -sf /usr/share/zoneinfo/Europe/Berlin /etc/localtime
raspi-config nonint do_wifi_country DE 2>/dev/null || true
echo "  hostname: autopilot-pi, tz: Europe/Berlin"

# ─── 3. Connect to iPhone hotspot ────────────────────────────────────────────
echo ""
echo "[3/12] Connecting to iPhone hotspot 'iPhonevonNiklas'..."
nmcli radio wifi on
sleep 2

mkdir -p /etc/NetworkManager/system-connections
cat > /etc/NetworkManager/system-connections/iphone-hotspot.nmconnection << 'WIFI'
[connection]
id=iphone-hotspot
type=wifi
autoconnect=true

[wifi]
mode=infrastructure
ssid=iPhonevonNiklas

[wifi-security]
key-mgmt=wpa-psk
psk=1234567890

[ipv4]
method=auto

[ipv6]
method=auto
WIFI
chmod 600 /etc/NetworkManager/system-connections/iphone-hotspot.nmconnection
nmcli con reload
sleep 2
nmcli con up iphone-hotspot 2>/dev/null || \
    nmcli dev wifi connect "iPhonevonNiklas" password "1234567890" 2>/dev/null || true

# Flush firewall rules
nft flush ruleset 2>/dev/null || true

# ─── 4. Wait for internet ─────────────────────────────────────────────────────
echo ""
echo "[4/12] Waiting for internet (max 90s)..."
TIMEOUT=90
ELAPSED=0
while ! ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1; do
    sleep 3
    ELAPSED=$((ELAPSED + 3))
    echo "  ... ${ELAPSED}s — make sure iPhone hotspot is ON"
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "  WARNING: No internet after ${TIMEOUT}s. Continuing with cached packages if available."
        break
    fi
done
echo "  Internet: OK"

# ─── 5. System packages ───────────────────────────────────────────────────────
echo ""
echo "[5/12] Installing system packages..."
apt-get update -qq 2>&1 | tail -2
apt-get install -y \
    dnsmasq \
    nginx \
    avahi-daemon avahi-utils libnss-mdns \
    libcamera-apps \
    git curl \
    nftables 2>&1 | grep -E "^(Reading|Get:|Unpacking|Setting up)" | tail -10
echo "  Packages installed."

# ─── 6. Node.js 22 ───────────────────────────────────────────────────────────
echo ""
echo "[6/12] Installing Node.js 22..."
if [ -f "/boot/firmware/pkgs/node.tar.gz" ]; then
    echo "  Extracting bundled Node.js from SD card..."
    tar -xzf /boot/firmware/pkgs/node.tar.gz -C /usr/local --strip-components=1
elif command -v node >/dev/null 2>&1 && node -v 2>/dev/null | grep -q "^v22"; then
    echo "  Node.js 22 already present."
else
    echo "  Downloading via nodesource..."
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - 2>&1 | tail -2
    apt-get install -y nodejs 2>&1 | tail -5
fi
echo "  Node.js: $(node -v), npm: $(npm -v)"

# ─── 7. pnpm + PM2 ───────────────────────────────────────────────────────────
echo ""
echo "[7/12] Installing pnpm + PM2 globally..."
npm install -g pnpm@9 pm2 --quiet 2>&1 | tail -3
echo "  pnpm: $(pnpm -v), pm2: $(pm2 -v)"

# ─── 8. Autopilot source ─────────────────────────────────────────────────────
echo ""
echo "[8/12] Installing autopilot source to /opt/autopilot..."
mkdir -p /opt/autopilot

if [ -d "/opt/autopilot/.git" ]; then
    echo "  Already present, pulling..."
    cd /opt/autopilot && git pull --ff-only 2>/dev/null || true
elif [ -f "/boot/firmware/pkgs/autopilot.tar.gz" ]; then
    echo "  Extracting bundled source (~$(du -sh /boot/firmware/pkgs/autopilot.tar.gz 2>/dev/null | cut -f1))..."
    tar -xzf /boot/firmware/pkgs/autopilot.tar.gz -C /opt/autopilot
    echo "  Source extracted."
else
    echo "  Cloning from GitHub..."
    git clone --depth=1 --branch dev https://github.com/Threedreamz/master-weaver-autopilot-starter.git /opt/autopilot
    echo "  Cloned."
fi
mkdir -p /opt/autopilot/config /opt/autopilot/releases

# ─── 9. Build apps ───────────────────────────────────────────────────────────
echo ""
echo "[9/12] Building apps (takes ~10min on Pi 5)..."
cd /opt/autopilot
echo "  pnpm install..."
pnpm install --frozen-lockfile 2>/dev/null || pnpm install
echo "  Building iPad app (port 4800)..."
pnpm build --filter=@autopilot/ipad 2>&1 | tail -5 || echo "  WARNING: iPad build failed"
echo "  Building Setup portal (port 4804)..."
pnpm build --filter=@autopilot/setup 2>&1 | tail -5 || echo "  WARNING: Setup build failed"
echo "  Building camera server (port 4801)..."
cd /opt/autopilot/python/pi-firmware
pnpm install --frozen-lockfile 2>/dev/null || pnpm install
pnpm build 2>&1 | tail -3 || echo "  WARNING: Camera server build failed"
echo "  Build complete."

# ─── 10. WiFi Access Point ───────────────────────────────────────────────────
echo ""
echo "[10/12] Configuring WiFi AP 'AutoPilot-CT'..."

# Remove iPhone hotspot — Pi becomes its own AP
nmcli con delete iphone-hotspot 2>/dev/null || true

nmcli con delete AutoPilot-AP 2>/dev/null || true
nmcli con add \
    type wifi ifname wlan0 con-name AutoPilot-AP \
    ssid "AutoPilot-CT" autoconnect yes \
    wifi.mode ap wifi.band bg wifi.channel 6 \
    wifi-sec.key-mgmt wpa-psk wifi-sec.psk "autopilot2024" \
    ipv4.method shared ipv4.addresses 192.168.4.1/24

nmcli con delete PC-Direct 2>/dev/null || true
nmcli con add \
    type ethernet ifname eth0 con-name PC-Direct \
    ipv4.method manual ipv4.addresses 192.168.5.1/24 autoconnect yes

echo "  AP: AutoPilot-CT @ 192.168.4.1 (pw: autopilot2024)"
echo "  Ethernet: 192.168.5.1 (CT-PC on 192.168.5.2)"

# ─── 11. dnsmasq + Avahi ─────────────────────────────────────────────────────
echo ""
echo "[11/12] Configuring DHCP + mDNS..."

cp /etc/dnsmasq.conf /etc/dnsmasq.conf.orig 2>/dev/null || true
cat > /etc/dnsmasq.conf << 'DNSEOF'
interface=wlan0
bind-interfaces
dhcp-range=192.168.4.10,192.168.4.50,24h
dhcp-option=3,192.168.4.1
dhcp-option=6,192.168.4.1
address=/autopilot-pi.local/192.168.4.1
address=/autopilot.local/192.168.4.1
log-dhcp
log-facility=/var/log/dnsmasq.log
DNSEOF
systemctl enable dnsmasq

cat > /etc/avahi/avahi-daemon.conf << 'AVAHIEOF'
[server]
host-name=autopilot-pi
domain-name=local
use-ipv4=yes
use-ipv6=yes
allow-interfaces=wlan0,eth0

[wide-area]
enable-wide-area=no

[publish]
publish-addresses=yes
publish-hinfo=yes
publish-workstation=no
publish-domain=yes
AVAHIEOF
systemctl enable avahi-daemon

# ─── 12. Nginx + PM2 ─────────────────────────────────────────────────────────
echo ""
echo "[12/12] Configuring Nginx + PM2..."

NGINX_CONF=""
[ -f /boot/firmware/nginx.conf ] && NGINX_CONF=/boot/firmware/nginx.conf
[ -z "$NGINX_CONF" ] && [ -f /opt/autopilot/python/pi-firmware/boot/nginx.conf ] && \
    NGINX_CONF=/opt/autopilot/python/pi-firmware/boot/nginx.conf

if [ -n "$NGINX_CONF" ]; then
    cp "$NGINX_CONF" /etc/nginx/sites-available/autopilot
    ln -sf /etc/nginx/sites-available/autopilot /etc/nginx/sites-enabled/autopilot
    rm -f /etc/nginx/sites-enabled/default
    nginx -t 2>/dev/null && systemctl enable nginx || echo "  WARNING: nginx config failed"
fi

ECOSYSTEM=""
[ -f /boot/firmware/ecosystem.config.js ] && ECOSYSTEM=/boot/firmware/ecosystem.config.js
[ -z "$ECOSYSTEM" ] && [ -f /opt/autopilot/python/pi-firmware/boot/ecosystem.config.js ] && \
    ECOSYSTEM=/opt/autopilot/python/pi-firmware/boot/ecosystem.config.js
[ -n "$ECOSYSTEM" ] && cp "$ECOSYSTEM" /opt/autopilot/ecosystem.config.js

chown -R autopilot-main:autopilot-main /opt/autopilot

echo "  Starting PM2..."
su - autopilot-main -c "cd /opt/autopilot && pm2 start ecosystem.config.js" 2>&1 | tail -5 || true

# PM2 systemd startup
PM2_STARTUP=$(su - autopilot-main -c "pm2 startup systemd -u autopilot-main --hp /home/autopilot-main" 2>/dev/null | grep "sudo")
[ -n "$PM2_STARTUP" ] && eval "$PM2_STARTUP" || true
su - autopilot-main -c "pm2 save" || true

# ─── Finalize ────────────────────────────────────────────────────────────────
sed -i 's| systemd.run=/boot/firmware/firstrun.sh||g' /boot/firmware/cmdline.txt
sed -i 's| systemd.run_success_action=reboot||g' /boot/firmware/cmdline.txt
sed -i 's| systemd.unit=kernel-command-line.target||g' /boot/firmware/cmdline.txt

echo ""
echo "============================================="
echo "  SETUP COMPLETE at $(date)"
echo "============================================="
echo ""
echo "  WiFi:     AutoPilot-CT / autopilot2024"
echo "  Pi IP:    192.168.4.1"
echo "  mDNS:     autopilot-pi.local"
echo "  SSH:      ssh autopilot-main@192.168.4.1"
echo "  Portal:   http://192.168.4.1"
echo "  iPad:     http://192.168.4.1:4800"
echo ""
echo "  REBOOTING into AP mode..."
echo ""

echo "SETUP COMPLETE: $(date)" >> /boot/firmware/firstrun-log.txt
echo "ssid=AutoPilot-CT pw=autopilot2024 ip=192.168.4.1" >> /boot/firmware/firstrun-log.txt

exit 0
