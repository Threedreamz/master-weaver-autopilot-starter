# Autopilot Pi Camera Server — SD Card Setup Guide

## Overview

The Raspberry Pi 5 runs as a **standalone WiFi Access Point** (no internet required). Connected devices (iPad, Windows PC) join the "AutoPilot-CT" WiFi network and access the camera server at `192.168.4.1:4801`.

### Network Summary

| Setting          | Value                          |
|------------------|--------------------------------|
| SSID             | `AutoPilot-CT`                 |
| Password         | `autopilot2026`                |
| Band             | 5GHz (channel 36, 802.11ac)   |
| Pi IP            | `192.168.4.1`                  |
| DHCP range       | `192.168.4.10` – `192.168.4.50` |
| Internet         | None (offline local network)   |
| mDNS hostname    | `autopilot-pi.local`           |
| Camera server    | `http://192.168.4.1:4801`      |

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

# Run setup — installs Node.js, camera deps, builds server, installs systemd service
sudo bash /opt/autopilot/python/pi-firmware/boot/setup.sh

# Reboot to activate WiFi AP mode
sudo reboot
```

**What happens on reboot:**
- Ethernet is no longer needed (disconnect it)
- Pi starts broadcasting **AutoPilot-CT** WiFi network
- hostapd serves WPA2 on 5GHz channel 36
- dnsmasq assigns IPs in 192.168.4.10–50 range
- Camera server auto-starts on 192.168.4.1:4801
- mDNS publishes `autopilot-pi.local`

## Step 5: Connect iPad / Windows PC

1. On iPad/PC, open WiFi settings
2. Connect to **AutoPilot-CT** (password: `autopilot2026`)
3. Device gets an IP like 192.168.4.10
4. Open browser: `http://192.168.4.1:4801/health`

## Step 6: Verify Everything Works

From a device connected to the AutoPilot-CT WiFi:

```bash
# Health check
curl http://192.168.4.1:4801/health

# List cameras
curl http://192.168.4.1:4801/cameras

# Open MJPEG stream in browser
open http://192.168.4.1:4801/camera/0/stream

# mDNS also works
curl http://autopilot-pi.local:4801/health
```

From the Pi itself (via SSH before disconnecting Ethernet, or via serial):

```bash
# Service status
systemctl status autopilot-pi
systemctl status hostapd
systemctl status dnsmasq

# View camera server logs
journalctl -u autopilot-pi -f

# Check WiFi AP status
hostapd_cli status

# Check DHCP leases
cat /var/lib/misc/dnsmasq.leases
```

## Troubleshooting

### WiFi Network Not Visible

```bash
# Check hostapd status
systemctl status hostapd
journalctl -u hostapd -n 30 --no-pager

# Common fix: hostapd is masked by default on Pi OS
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd

# Check if wlan0 is up
ip addr show wlan0

# Check if wpa_supplicant is interfering
systemctl status wpa_supplicant
# If running, disable it:
sudo systemctl stop wpa_supplicant
sudo systemctl disable wpa_supplicant
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

### Service Won't Start

```bash
journalctl -u autopilot-pi -n 50 --no-pager
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

Some Pi 5 WiFi chips may have issues with certain 5GHz channels. Edit `/etc/hostapd/hostapd.conf`:

```
# Change from 5GHz to 2.4GHz fallback:
hw_mode=g        # was: a
channel=6        # was: 36
# Remove ieee80211ac, vht_capab, vht_oper lines
```

Then restart: `sudo systemctl restart hostapd`

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
cd python/pi-firmware
pnpm install
pnpm build
sudo systemctl restart autopilot-pi
```

## File Reference

| File | Purpose |
|------|---------|
| `boot/firstboot.sh` | WiFi AP + DHCP + static IP + mDNS configuration |
| `boot/setup.sh` | Node.js + camera deps + systemd service installation |
| `boot/config.txt` | Pi 5 hardware config (cameras, watchdog, GPIO) |
| `boot/hostapd.conf` | WiFi AP config (ready to copy to `/etc/hostapd/`) |
| `boot/dnsmasq.conf` | DHCP + DNS config (ready to copy to `/etc/`) |
| `boot/autopilot-pi.service` | systemd unit for auto-starting camera server |
