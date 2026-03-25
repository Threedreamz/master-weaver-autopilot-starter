@echo off
echo ============================================================
echo   WerthAutopilot Build Script
echo ============================================================
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ and add to PATH.
    pause
    exit /b 1
)

REM Install/upgrade PyInstaller
echo [1/3] Installing PyInstaller...
pip install --upgrade pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller.
    pause
    exit /b 1
)

REM Install project dependencies
echo.
echo [2/3] Installing project dependencies...
pip install -e .
if errorlevel 1 (
    echo WARNING: pip install -e . failed. Trying pip install -r requirements...
    pip install fastapi "uvicorn[standard]" websockets pyautogui pywinauto opencv-python numpy mss pynput Pillow
)

REM Build the .exe
echo.
echo [3/3] Building WerthAutopilot.exe...
pyinstaller WerthAutopilot.spec --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Check the output above for details.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD SUCCESSFUL
echo   Find WerthAutopilot.exe in dist\WerthAutopilot.exe
echo ============================================================
echo.
pause
