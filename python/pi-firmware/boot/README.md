# Autopilot Pi Central Server — SD Card Setup Guide

## Overview

The Raspberry Pi 5 runs as a **standalone WiFi Access Point** and **central server** (no internet required). It hosts 4 services behind an Nginx reverse proxy, all managed by PM2:

| Service | Port | Description |
|---------|------|-------------|
| Nginx | 80 | Reverse proxy (entry point for all traffic) |
| iPad App | 4800 | Main CT scanner interface |
| Camera Server | 4801 | MJPEG camera streams + hardware control |
| Setup Portal | 4804 | First-time setup wizard + app download |

### Onboarding Flow

1. User powers on the Pi and connects to **AutoPilot-Setup** WiFi
2. Opens any browser → Nginx routes to **Setup Portal** (port 4804)
3. Setup portal configures CT scanner parameters, camera positions, etc.
4. On completion, setup portal writes `/opt/autopilot/config/setup-complete`
5. Nginx now routes to **iPad App** (port 4800) on all subsequent visits
6. Download page (`/download`) always remains available via setup portal

### Network Summary

| Setting          | Value                          |
|------------------|--------------------------------|
| SSID             | `AutoPilot-Setup`              |
| Password         | `autopilot`                    |
| Pi IP            | `192.168.4.1`                  |
| DHCP range       | `192.168.4.10` – `192.168.4.50` |
| Internet         | None (offline local network)   |
| mDNS hostname    | `autopilot-pi.local`           |
| Web interface    | `http://autopilot.local` (port 80) |
| Camera streams   | `http://autopilot.local/camera/` |
| Downloads        | `http://autopilot.local/releases/` |

## Prerequisites

- Raspberry Pi 5 (4GB+ RAM recommended)
- 2x Pi Camera Module 3 (IMX708) connected to CSI CAM0 + CAM1 ports
- MicroSD card (32GB+ recommended)
- Raspberry Pi Imager (https://www.raspberrypi.com/software/)
- A computer to flash the SD card

## Step 1: Flash Raspberry Pi OS

1. Open **Raspberry Pi Imager**
2. Choose device: **Raspberry Pi 5**
3. Choose OS: **Raspberry Pi OS Lite (64-bit)** (under "Raspberry Pi OS (other)")
   - Must be **Bookworm** or later (uses NetworkManager)
4. Choose storage: your microSD card
5. Click the **gear icon** (Advanced Options) and configure:
   - **Hostname**: `autopilot-pi`
   - **Enable SSH**: Yes (use password authentication)
   - **Username**: `pi`
   - **Password**: (set a secure password)
   - **Configure WiFi**: Skip — the Pi will be an AP, not a client
   - **Locale**: Europe/Berlin (or your timezone)
6. Click **Write** and wait for completion

## Step 2: Copy Boot Configuration

After flashing, the SD card has a `bootfs` partition. Append the camera/hardware config:

```bash
# macOS
cat boot/config.txt >> /Volumes/bootfs/config.txt

# Linux
cat boot/config.txt >> /media/$USER/bootfs/config.txt
```

## Step 3: First Boot (with Ethernet)

For the initial setup you need internet access to install packages. Connect the Pi via **Ethernet cable** to a router/switch.

1. Insert SD card into Pi 5
2. Connect both cameras to CSI CAM0 and CSI CAM1 ports
3. Connect Ethernet cable (for package downloads)
4. Power on and wait ~90 seconds for first boot

## Step 4: SSH In and Run Setup Scripts

```bash
# Connect via hostname (mDNS) or find the Pi's DHCP IP
ssh pi@autopilot-pi.local
# or
ssh pi@<IP-from-router>

# Clone the repo
sudo git clone https://github.com/Threedreamz/master-weaver-autopilot-starter.git /opt/autopilot

# Run firstboot — configures WiFi AP, DHCP, static IP, mDNS
sudo bash /opt/autopilot/python/pi-firmware/boot/firstboot.sh

# Run setup — installs Node.js, pnpm, Nginx, PM2, builds all apps
sudo bash /opt/autopilot/python/pi-firmware/boot/setup.sh

# Reboot to activate WiFi AP mode
sudo reboot
```

**What happens on reboot:**
- Ethernet is no longer needed (disconnect it)
- Pi starts broadcasting **AutoPilot-Setup** WiFi network
- NetworkManager creates AP via nmcli (hostapd as fallback)
- dnsmasq assigns IPs in 192.168.4.10–50 range
- PM2 starts all 3 app services automatically
- Nginx proxies port 80 to the appropriate app
- mDNS publishes `autopilot-pi.local`

## Step 5: Connect iPad / Windows PC

1. On iPad/PC, open WiFi settings
2. Connect to **AutoPilot-Setup** (password: `autopilot`)
3. Device gets an IP like 192.168.4.10
4. Open browser: `http://autopilot.local` (routes to setup portal on first visit)

## Step 6: Verify Everything Works

From a device connected to the AutoPilot-Setup WiFi:

```bash
# Main interface (routed by Nginx)
curl http://autopilot.local

# Camera streams
curl http://autopilot.local/camera/health

# Direct service access (bypass Nginx)
curl http://192.168.4.1:4800  # iPad app
curl http://192.168.4.1:4801/health  # Camera server
curl http://192.168.4.1:4804  # Setup portal
```

From the Pi itself (via SSH before disconnecting Ethernet, or via serial):

```bash
# PM2 service status
pm2 status
pm2 logs

# Nginx status
systemctl status nginx
nginx -t

# WiFi AP status (NetworkManager)
nmcli con show AutoPilot-AP
nmcli dev wifi

# System services
systemctl status autopilot-pi
systemctl status dnsmasq
systemctl status avahi-daemon

# Check DHCP leases
cat /var/lib/misc/dnsmasq.leases
```

## Architecture

```
iPad/PC Browser
      │
      ▼ (connects to AutoPilot-Setup WiFi)
   ┌──────────────────────────────────────┐
   │  Raspberry Pi 5 — 192.168.4.1       │
   │                                      │
   │  Nginx (:80)                         │
   │    ├── / → Setup Portal (:4804)      │  ← before setup-complete
   │    ├── / → iPad App (:4800)          │  ← after setup-complete
   │    ├── /camera/ → Camera (:4801)     │
   │    ├── /download → Setup (:4804)     │
   │    └── /releases/ → static files     │
   │                                      │
   │  PM2 manages:                        │
   │    ├── camera (Node.js :4801)        │
   │    ├── ipad-app (Next.js :4800)      │
   │    └── setup-portal (Next.js :4804)  │
   │                                      │
   │  NetworkManager AP (nmcli)           │
   │  dnsmasq (DHCP + DNS)               │
   │  Avahi (mDNS)                        │
   └──────────────────────────────────────┘
```

## Troubleshooting

### WiFi Network Not Visible

```bash
# Check NetworkManager AP (Bookworm)
nmcli con show AutoPilot-AP
nmcli con up AutoPilot-AP

# If using hostapd fallback
systemctl status hostapd
journalctl -u hostapd -n 30 --no-pager

# Check if wlan0 is up
ip addr show wlan0
```

### Services Not Starting

```bash
# Check PM2 status
pm2 status
pm2 logs --err

# Check individual service
pm2 logs camera --lines 50
pm2 logs ipad-app --lines 50
pm2 logs setup-portal --lines 50

# Restart everything
pm2 restart all
```

### Nginx Issues

```bash
# Test config
nginx -t

# Check status
systemctl status nginx
journalctl -u nginx -n 30 --no-pager

# Check which upstream is active
curl -I http://localhost
```

### No IP Assigned to Connected Device

```bash
# Check dnsmasq
systemctl status dnsmasq
journalctl -u dnsmasq -n 30 --no-pager

# Check DHCP leases
cat /var/lib/misc/dnsmasq.leases

# Verify wlan0 has static IP
ip addr show wlan0
# Should show 192.168.4.1/24
```

### Cameras Not Detected

```bash
# List cameras (Pi 5 libcamera stack)
libcamera-hello --list-cameras

# Check V4L2 devices
v4l2-ctl --list-devices

# Check kernel messages
dmesg | grep -i camera
dmesg | grep -i imx708
```

### Resetting Setup State

To go back to the setup portal (e.g., reconfigure):

```bash
# Remove the setup-complete flag
rm /opt/autopilot/config/setup-complete

# Nginx will now route to setup portal again
# No restart needed — Nginx checks the file on each request
```

### mDNS Not Working

```bash
# Check Avahi
systemctl status avahi-daemon
avahi-browse -art | grep autopilot

# From macOS/iOS — mDNS should work automatically
# From Windows — install Bonjour Print Services or use IP directly
```

### 5GHz WiFi Not Working (Fallback to 2.4GHz)

If using hostapd fallback and 5GHz doesn't work, edit `/etc/hostapd/hostapd.conf`:

```
# Change from 5GHz to 2.4GHz fallback:
hw_mode=g        # was: a
channel=6        # was: 36
# Remove ieee80211ac, vht_capab, vht_oper lines
```

Then restart: `sudo systemctl restart hostapd`

Note: The nmcli AP method uses 2.4GHz by default (`wifi.band bg`), which is more compatible.

### High CPU Temperature

```bash
cat /sys/class/thermal/thermal_zone0/temp
# Result in millidegrees — divide by 1000

# Health endpoint also reports this
curl -s http://192.168.4.1:4801/health | jq .system.cpuTemp
```

## Updating (Requires Temporary Internet)

Connect Ethernet, then:

```bash
cd /opt/autopilot
git pull --ff-only
pnpm install
pnpm build --filter=@autopilot/ipad --filter=@autopilot/setup
cd python/pi-firmware && pnpm build && cd ../..
pm2 restart all
```

## File Reference

| File | Purpose |
|------|---------|
| `boot/firstboot.sh` | WiFi AP + DHCP + static IP + mDNS configuration |
| `boot/setup.sh` | Node.js + pnpm + Nginx + PM2 + build all apps |
| `boot/config.txt` | Pi 5 hardware config (cameras, watchdog, GPIO) |
| `boot/nginx.conf` | Nginx reverse proxy config (setup-complete routing) |
| `boot/ecosystem.config.js` | PM2 process definitions (camera, iPad, setup) |
| `boot/hostapd.conf` | WiFi AP config — hostapd fallback (legacy Pi OS) |
| `boot/dnsmasq.conf` | DHCP + DNS config (ready to copy to `/etc/`) |
| `boot/autopilot-pi.service` | systemd unit — PM2 wrapper for auto-start |

## Key Directories on the Pi

| Path | Purpose |
|------|---------|
| `/opt/autopilot/` | Main installation directory |
| `/opt/autopilot/config/` | Runtime configuration (setup-complete flag, etc.) |
| `/opt/autopilot/releases/` | Downloadable files served at `/releases/` |
| `/opt/autopilot/ecosystem.config.js` | PM2 config (copied from boot/) |
| `/etc/nginx/sites-available/autopilot` | Nginx site config |
| `/home/pi/.pm2/` | PM2 state, logs, pid files |
