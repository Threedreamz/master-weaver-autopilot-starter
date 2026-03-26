# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for WerthAutopilot.exe

Build with:  pyinstaller WerthAutopilot.spec
Output:      dist/WerthAutopilot.exe  (single file, console mode)
"""

import os
import sys
from pathlib import Path

block_cipher = None

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SPEC_DIR = os.path.dirname(os.path.abspath(SPECPATH)) if 'SPECPATH' in dir() else os.path.dirname(os.path.abspath('WerthAutopilot.spec'))
SRC_DIR = os.path.join(SPEC_DIR, 'src')

# ---------------------------------------------------------------------------
# Collect all src/ subpackages
# ---------------------------------------------------------------------------
src_packages = []
for root, dirs, files in os.walk(SRC_DIR):
    # Skip __pycache__
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.py'):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, SPEC_DIR)
            src_packages.append(rel)

# ---------------------------------------------------------------------------
# Data files — JSON configs, YAML, etc.
# ---------------------------------------------------------------------------
datas = []

# Include any JSON config files in src/
for root, dirs, files in os.walk(SRC_DIR):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith(('.json', '.yaml', '.yml')):
            full = os.path.join(root, f)
            rel_dir = os.path.relpath(root, SPEC_DIR)
            datas.append((full, rel_dir))

# Include data/ directory if it exists (time tracking, etc.)
data_dir = os.path.join(SPEC_DIR, 'data')
if os.path.isdir(data_dir):
    for f in os.listdir(data_dir):
        full = os.path.join(data_dir, f)
        if os.path.isfile(full):
            datas.append((full, 'data'))

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    ['WerthAutopilot.py'],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # --- FastAPI / Uvicorn stack ---
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'starlette',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.routing',
        'starlette.responses',
        'starlette.websockets',
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        'httptools',
        'websockets',
        'watchfiles',
        # --- Windows automation ---
        'pyautogui',
        'pywinauto',
        'pywinauto.application',
        'pywinauto.controls',
        'pynput',
        'pynput.mouse',
        'pynput.keyboard',
        # --- Image / CV ---
        'cv2',
        'numpy',
        'mss',
        'PIL',
        'PIL.Image',
        # --- Our source packages ---
        'src',
        'src.main',
        'src.api',
        'src.api.routes',
        'src.api.ws',
        'src.winwerth',
        'src.winwerth.controller',
        'src.winwerth.config',
        'src.winwerth.mouse',
        'src.winwerth.pixel_check',
        'src.winwerth.tube',
        'src.winwerth.rotation',
        'src.winwerth.profile',
        'src.winwerth.menu_detection',
        'src.winwerth.pywinauto_controls',
        'src.winwerth.win_api',
        'src.winwerth.error_correction',
        'src.orchestrator',
        'src.orchestrator.states',
        'src.orchestrator.transitions',
        'src.orchestrator.folder_manager',
        'src.orchestrator.stl_export',
        'src.orchestrator.scan_machine',
        'src.discovery',
        'src.discovery.models',
        'src.discovery.network_scanner',
        'src.analysis',
        'src.analysis.soll_ist',
        'src.analysis.deviation_report',
        'src.optical',
        'src.optical.bg_whiten',
        'src.optical.border_detection',
        'src.queue',
        'src.queue.task_queue',
        'src.notifications',
        'src.notifications.email_notify',
        'src.timetracking',
        'src.timetracking.models',
        'src.timetracking.tracker',
        # --- Scipy / STL analysis ---
        'scipy',
        'scipy.spatial',
        'scipy.spatial._kdtree',
        'numpy_stl',
        'stl',
        'stl.mesh',
        # --- Network discovery ---
        'zeroconf',
        'zeroconf._utils',
        # --- HTTP client ---
        'httpx',
        'httpx._transports',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'pandas',
        'IPython',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ---------------------------------------------------------------------------
# Pack into single file
# ---------------------------------------------------------------------------
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WerthAutopilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,           # Console mode — operator needs to see logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/WerthAutopilot.ico',  # TODO: add icon file
)
