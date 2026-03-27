---
name: autopilot-pi
description: Flash and configure a Raspberry Pi 5 SD card for the dual-camera CT scanner server.
user_invocable: true
allowed-tools: [Bash, Read, Write]
---

# /autopilot-pi — Raspberry Pi SD Card Flash + Configuration

Flash a Raspberry Pi 5 SD card with the camera server image, configure WiFi access point mode, and install the dual 4K camera firmware. Runs `scripts/flash-pi.sh` for automated setup.

## When to Use

- Setting up a new Raspberry Pi 5 for the CT scanner
- Re-flashing after a corrupted SD card
- Updating the camera server firmware
- Changing WiFi AP configuration (SSID, password, channel)

## Steps

1. **Identify the SD card**
   - Insert the SD card and find the device:
     ```bash
     # macOS
     diskutil list

     # Linux
     lsblk
     ```
   - Confirm the correct device (e.g., `/dev/disk4` on macOS, `/dev/sdb` on Linux)
   - IMPORTANT: Double-check the device to avoid overwriting the wrong disk

2. **Run the flash script**
   ```bash
   bash scripts/flash-pi.sh --device /dev/diskN --hostname ct-pi
   ```
   - This script:
     - Downloads or uses cached Raspberry Pi OS Lite (64-bit) image
     - Flashes the image to the SD card
     - Mounts the boot partition for configuration
     - Enables SSH with key-based auth
     - Configures the Pi Camera Server to auto-start on boot

3. **Configure WiFi Access Point**
   - The Pi runs as a WiFi AP so the iPad can connect directly without external network:
     ```bash
     bash scripts/flash-pi.sh --configure-ap \
       --ssid "CT-Scanner" \
       --password "scanner-secure-pw" \
       --channel 36 \
       --ip 10.0.0.1
     ```
   - AP settings are written to the boot partition (no symlinks -- uses cp for FAT32 compatibility)
   - The Pi assigns IPs in the 10.0.0.0/24 range via dnsmasq

4. **Install camera firmware**
   - Configure dual IMX477 or IMX708 camera modules:
     ```bash
     bash scripts/flash-pi.sh --install-camera \
       --camera0 imx477 \
       --camera1 imx477
     ```
   - This writes the dtoverlay entries to config.txt on the boot partition
   - Camera server (Fastify, port 4801) streams both cameras over HTTP

5. **Set environment variables**
   - Write the camera server .env to the rootfs partition:
     ```
     PORT=4801
     HOSTNAME=0.0.0.0
     CAMERA_0=/dev/video0
     CAMERA_1=/dev/video2
     RESOLUTION=3840x2160
     FPS=30
     CT_PC_URL=http://10.0.0.2:4802
     ```

6. **Eject and boot**
   ```bash
   # macOS
   diskutil eject /dev/diskN

   # Linux
   sudo eject /dev/sdX
   ```
   - Insert SD card into Pi, power on, wait ~60 seconds for first boot

7. **Verify Pi is running**
   - Connect to the CT-Scanner WiFi AP from your machine
   - Check the camera server:
     ```bash
     curl -s http://10.0.0.1:4801/health
     ```
   - Verify both cameras:
     ```bash
     curl -s http://10.0.0.1:4801/cameras
     ```
   - Should report two cameras with resolution and status

## What's Next

- `/autopilot-health` — Verify all 4 nodes see each other on the network
- `/autopilot-scan` — Run a test scan using the newly configured Pi
- `/autopilot-deploy` — Deploy CT-PC API if not yet installed on the Windows PC
