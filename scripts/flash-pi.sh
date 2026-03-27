#!/usr/bin/env bash
# =============================================================================
# AutoPilot Pi — SD Card Flash Tool
# Usage: bash scripts/flash-pi.sh
#
# Prerequisites:
#   1. Flash Raspberry Pi OS Lite (64-bit) with Raspberry Pi Imager
#      Settings: hostname=autopilot-pi, enable SSH, NO WiFi config
#   2. SD card inserted in Mac — /Volumes/bootfs should be mounted
#   3. Run this script from the autopilot-starter repo root
#
# What this does:
#   - Writes the complete firstrun.sh (autopilot setup) to bootfs
#   - Downloads Node.js 22 ARM64 tarball to bootfs/pkgs/ (offline install)
#   - Creates a git archive of the autopilot source to bootfs/pkgs/ (offline clone)
#   - Copies nginx.conf, ecosystem.config.js to bootfs
#
# After running: Eject SD, insert in Pi 5, connect ethernet (internet required)
# Boot sequence: firstrun.sh runs → installs everything → reboots as WiFi AP
# =============================================================================
set -euo pipefail

BOOTFS="/Volumes/bootfs"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOOT_SCRIPTS="${REPO_ROOT}/python/pi-firmware/boot"
NODE_VERSION="22.14.0"
NODE_TARBALL="node-v${NODE_VERSION}-linux-arm64.tar.gz"
NODE_URL="https://nodejs.org/dist/v${NODE_VERSION}/${NODE_TARBALL}"

echo "========================================"
echo "  AutoPilot Pi — Flash Tool"
echo "  Repo: ${REPO_ROOT}"
echo "========================================"
echo ""

# ─── Check bootfs ────────────────────────────────────────────────────────────
if [ ! -d "$BOOTFS" ]; then
    echo "ERROR: /Volumes/bootfs not found."
    echo "  Flash SD card with Raspberry Pi Imager first:"
    echo "  OS: Raspberry Pi OS Lite (64-bit)"
    echo "  Settings: hostname=autopilot-pi, SSH enabled, NO WiFi"
    exit 1
fi
if [ ! -f "$BOOTFS/cmdline.txt" ]; then
    echo "ERROR: $BOOTFS doesn't look like Pi OS boot partition (no cmdline.txt)"
    exit 1
fi
echo "✓ bootfs found: $BOOTFS"
echo "  cmdline: $(cat $BOOTFS/cmdline.txt | head -c 80)..."
echo ""

# ─── config.txt ──────────────────────────────────────────────────────────────
echo "[1/5] config.txt..."
if ! grep -q "dtoverlay=imx708" "$BOOTFS/config.txt" 2>/dev/null; then
    cat >> "$BOOTFS/config.txt" << 'CONFIGEOF'

# ─── AutoPilot Camera Configuration ─────────────────────────────────────────
# Dual Pi Camera Module 3 (IMX708) on CAM0 + CAM1
dtoverlay=imx708
dtoverlay=imx708,cam1

# Hardware watchdog for auto-recovery
dtparam=watchdog=on

# GPU memory for dual 4K camera processing
gpu_mem=256
CONFIGEOF
    echo "  ✓ Camera overlays added to config.txt"
else
    echo "  ✓ config.txt already has camera overlays"
fi

# ─── Copy boot scripts ────────────────────────────────────────────────────────
echo ""
echo "[2/5] Copying boot scripts..."
for f in nginx.conf ecosystem.config.js; do
    if [ -f "${BOOT_SCRIPTS}/${f}" ]; then
        cp "${BOOT_SCRIPTS}/${f}" "$BOOTFS/${f}"
        echo "  ✓ ${f}"
    fi
done

# ─── Node.js tarball ─────────────────────────────────────────────────────────
echo ""
echo "[3/5] Node.js ${NODE_VERSION} ARM64 Linux tarball..."
mkdir -p "$BOOTFS/pkgs"
DEST="$BOOTFS/pkgs/${NODE_TARBALL}"
if [ -f "$DEST" ]; then
    echo "  ✓ Already cached: $(du -sh "$DEST" | cut -f1)"
else
    echo "  Downloading from nodejs.org (~50MB)..."
    curl -fL --progress-bar -o "$DEST" "$NODE_URL"
    echo "  ✓ Downloaded: $(du -sh "$DEST" | cut -f1)"
fi
# Generic symlink for firstrun.sh
ln -sf "${NODE_TARBALL}" "$BOOTFS/pkgs/node.tar.gz" 2>/dev/null || \
    cp "$DEST" "$BOOTFS/pkgs/node.tar.gz"
echo "  ✓ /boot/firmware/pkgs/node.tar.gz ready"

# ─── Source tarball ──────────────────────────────────────────────────────────
echo ""
echo "[4/5] Autopilot source tarball..."
if [ -d "$REPO_ROOT/.git" ]; then
    git -C "$REPO_ROOT" archive --format=tar.gz HEAD -o "$BOOTFS/pkgs/autopilot.tar.gz"
    echo "  ✓ Source bundled: $(du -sh "$BOOTFS/pkgs/autopilot.tar.gz" | cut -f1)"
else
    echo "  WARNING: Not a git repo. Pi will clone from GitHub instead."
fi

# ─── firstrun.sh ─────────────────────────────────────────────────────────────
echo ""
echo "[5/5] Writing firstrun.sh..."
cp "${REPO_ROOT}/python/pi-firmware/boot/firstrun-autopilot.sh" "$BOOTFS/firstrun.sh"
echo "  ✓ firstrun.sh written: $(wc -l < "$BOOTFS/firstrun.sh") lines"

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  Done! SD card contents:"
echo "========================================"
echo ""
ls -lh "$BOOTFS/pkgs/" 2>/dev/null
echo ""
echo "Next steps:"
echo "  1. Eject SD card:  diskutil eject /Volumes/bootfs"
echo "  2. Insert into Raspberry Pi 5"
echo "  3. Connect ethernet cable (internet for first-boot setup)"
echo "  4. Connect power — wait 15-20 minutes"
echo "  5. WiFi 'AutoPilot-CT' appears when done"
echo "  6. Connect: password 'autopilot2024'"
echo "  7. SSH:     ssh autopilot-main@192.168.4.1"
echo "  8. Portal:  http://192.168.4.1"
echo ""
echo "  Monitor setup: watch /Volumes/bootfs/firstrun-log.txt"
echo "  (while Pi is on iPhone hotspot, before AP mode)"
echo ""
