#!/usr/bin/env bash
# WerthAutopilot Build Script (cross-platform reference)
#
# NOTE: The resulting .exe can only run on Windows. This script is provided
#       for reference and CI usage. For production builds, use build.bat on
#       a Windows machine where pywinauto and pyautogui are available.
set -euo pipefail

echo "============================================================"
echo "  WerthAutopilot Build Script"
echo "============================================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.11+."
    exit 1
fi

echo "[1/3] Installing PyInstaller..."
pip install --upgrade pyinstaller

echo ""
echo "[2/3] Installing project dependencies..."
pip install -e . || {
    echo "WARNING: pip install -e . failed, installing deps directly..."
    pip install fastapi "uvicorn[standard]" websockets pyautogui pywinauto \
        opencv-python numpy mss pynput Pillow
}

echo ""
echo "[3/3] Building WerthAutopilot..."
pyinstaller WerthAutopilot.spec --noconfirm

echo ""
echo "============================================================"
echo "  BUILD SUCCESSFUL"
echo "  Output: dist/WerthAutopilot"
if [[ "$(uname)" == MINGW* ]] || [[ "$(uname)" == MSYS* ]]; then
    echo "  (dist/WerthAutopilot.exe on Windows)"
fi
echo "============================================================"
