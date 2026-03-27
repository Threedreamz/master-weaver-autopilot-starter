"""
PyWinAuto Bridge — bridges trello_era pywinauto modules into the MW FastAPI backend.

Wraps the legacy pywinauto library at ``source/libs/pywinauto/`` with a clean
interface that matches what :class:`WinWerthController` needs.  On non-Windows
platforms (or when pywinauto is unavailable), sets ``BRIDGE_AVAILABLE = False``
so the controller can fall back to mock mode.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ctpc-api.pywinauto_bridge")

# ---------------------------------------------------------------------------
# Inject source/ into sys.path so trello_era imports resolve
# ---------------------------------------------------------------------------

# Resolve: …/master-weaver-autopilot-starter/source
_REPO_ROOT = Path(__file__).resolve().parents[5]  # up from winwerth/ -> src/ -> ctpc-api/ -> python/ -> repo root
_SOURCE_DIR = _REPO_ROOT / "source"

if str(_SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(_SOURCE_DIR))
    logger.info("Added source directory to sys.path: %s", _SOURCE_DIR)

# ---------------------------------------------------------------------------
# Attempt to import trello_era modules
# ---------------------------------------------------------------------------

BRIDGE_AVAILABLE = False

try:
    from libs.pywinauto.process import winWerth_Process
    from libs.pywinauto.profile.profile import profile as ProfileModule
    from libs.pywinauto.rohr.rohr import rohr as RohrModule
    from libs.pywinauto.tabcontrol.tabcontrol import tabcontrol as TabControlModule
    from libs.pywinauto.button.button import ButtonPresser
    from libs.pywinauto.checkbox.checkbox import checkbox as CheckboxModule
    from libs.pywinauto.textbox.textBox import TextBox_method as TextBoxModule
    from libs.pywinauto.combobox.combobox import combobox as ComboboxModule
    from libs.pywinauto.topMenu.topMenu import topMenu as TopMenuModule
    from libs.pywinauto.voxel.voxel import voxel as VoxelModule
    from libs.pywinauto.sideButtons.sideButtons import sideButtons as SideButtonsModule
    from libs.pywinauto.error_correction.error_correction import error_correction as ErrorCorrectionModule
    from libs.pywinauto.childWindow.SaveFileDialog.SaveFileDialog import SaveFileDialog
    from libs.pywinauto.label.label_h import label_h as LabelModule
    from libs.pywinauto.punkte_Menu.punkte_Menu import punkte_Menu as PunkteMenuModule

    BRIDGE_AVAILABLE = True
    logger.info("trello_era pywinauto modules loaded successfully")

except ImportError as exc:
    logger.warning(
        "trello_era pywinauto modules unavailable (expected on non-Windows): %s", exc
    )
except Exception as exc:
    logger.error("Unexpected error loading trello_era modules: %s", exc)


class PyWinAutoBridge:
    """Clean bridge interface over the trello_era pywinauto library.

    Each public method maps to an operation that :class:`WinWerthController`
    needs.  All trello_era module instantiation happens lazily in
    :meth:`connect` so the bridge can be constructed even when the WinWerth
    application is not yet running.

    Args:
        force_mock: If *True*, skip real initialisation.  The bridge will
            report ``is_connected == False`` and every operation returns a
            failure value.
    """

    def __init__(self, force_mock: bool = False) -> None:
        self._connected = False
        self._force_mock = force_mock

        # trello_era instances (populated by connect())
        self._process: Optional[Any] = None
        self._dlg: Optional[Any] = None
        self._app: Optional[Any] = None

        # Module instances
        self._profile: Optional[Any] = None
        self._rohr: Optional[Any] = None
        self._tab: Optional[Any] = None
        self._button: Optional[Any] = None
        self._checkbox: Optional[Any] = None
        self._textbox: Optional[Any] = None
        self._combobox: Optional[Any] = None
        self._top_menu: Optional[Any] = None
        self._voxel: Optional[Any] = None
        self._side_buttons: Optional[Any] = None
        self._error_correction: Optional[Any] = None
        self._label: Optional[Any] = None
        self._punkte_menu: Optional[Any] = None

        if not force_mock and BRIDGE_AVAILABLE:
            self._init_modules()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _init_modules(self) -> None:
        """Instantiate all trello_era module classes (no connection yet)."""
        try:
            self._process = winWerth_Process()
            self._profile = ProfileModule()
            self._rohr = RohrModule()
            self._tab = TabControlModule()
            self._button = ButtonPresser()
            self._checkbox = CheckboxModule()
            self._textbox = TextBoxModule()
            self._combobox = ComboboxModule()
            self._top_menu = TopMenuModule()
            self._voxel = VoxelModule()
            self._side_buttons = SideButtonsModule()
            self._error_correction = ErrorCorrectionModule()
            self._label = LabelModule()
            self._punkte_menu = PunkteMenuModule()
            logger.info("All trello_era module instances created")
        except Exception as exc:
            logger.error("Failed to instantiate trello_era modules: %s", exc)

    def connect(self, backend: str = "uia") -> bool:
        """Connect to the running WinWerth application.

        Returns *True* on success, *False* on failure.
        """
        if self._force_mock or not BRIDGE_AVAILABLE:
            logger.info("Bridge connect skipped (mock=%s, available=%s)",
                        self._force_mock, BRIDGE_AVAILABLE)
            return False

        try:
            self._process.init(proc_type=backend)
            self._dlg = self._process.getDlg()
            self._app = self._process.getApp()
            self._connected = True
            logger.info("Connected to WinWerth via pywinauto (%s backend)", backend)
            return True
        except Exception as exc:
            logger.error("Failed to connect to WinWerth: %s", exc)
            self._connected = False
            return False

    def reconnect(self) -> bool:
        """Re-establish the connection (e.g. after WinWerth restart)."""
        if not BRIDGE_AVAILABLE or self._force_mock:
            return False
        try:
            self._process.connect()
            self._dlg = self._process.getDlg()
            self._app = self._process.getApp()
            self._connected = True
            logger.info("Reconnected to WinWerth")
            return True
        except Exception as exc:
            logger.error("Reconnection failed: %s", exc)
            self._connected = False
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def dlg(self) -> Optional[Any]:
        return self._dlg

    def _require_connection(self) -> bool:
        """Guard — logs a warning and returns False if not connected."""
        if not self._connected or self._dlg is None:
            logger.warning("Bridge operation called but not connected to WinWerth")
            return False
        return True

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------

    def complete_profile_selection_sequence(self, profile_name: str) -> bool:
        """Open the CT-Sensor profile window, select *profile_name*, close.

        Delegates to: profile.openProfileWindow, profile.getCTSensorDlg,
        profile.selectListBoxItemByText, profile.closeWindow.
        """
        if not self._require_connection():
            return False

        try:
            logger.info("Opening CT-Sensor profile window")
            ct_sensor = self._profile.find_ct_sensor(self._dlg)
            if ct_sensor is None:
                logger.error("Cannot find CT-Sensor profile window")
                return False

            logger.info("CT-Sensor window found, getting dialog")
            ct_dlg = self._profile.getCTSensorDlg(self._dlg)

            logger.info("Selecting profile: %s", profile_name)
            result = self._profile.selectListBoxItemByText(ct_dlg, profile_name)
            if not result:
                logger.error("Failed to select profile '%s' in listbox", profile_name)

            logger.info("Closing profile window")
            self._profile.closeWindow(ct_dlg, self._dlg)

            logger.info("Profile selection sequence complete: %s (result=%s)",
                        profile_name, result)
            return bool(result)

        except Exception as exc:
            logger.error("complete_profile_selection_sequence failed: %s", exc)
            return False

    def open_profile_window(self) -> bool:
        """Open the CT-Sensor profile window without selecting."""
        if not self._require_connection():
            return False
        try:
            result = self._profile.openProfileWindow(self._dlg)
            logger.info("open_profile_window: %s", result)
            return result is not None
        except Exception as exc:
            logger.error("open_profile_window failed: %s", exc)
            return False

    def is_profile_window_open(self) -> bool:
        """Check whether the CT-Sensor profile window is currently open."""
        if not self._require_connection():
            return False
        try:
            return bool(self._profile.isWindowOpen(self._dlg))
        except Exception as exc:
            logger.error("is_profile_window_open failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Tube (Rohr) control
    # ------------------------------------------------------------------

    def click_tube_power_on(self) -> bool:
        """Turn the X-ray tube on (Rohre An).

        Delegates to: rohr.rohrAn(dlg).
        """
        if not self._require_connection():
            return False

        try:
            logger.info("Clicking tube power on (rohrAn)")
            self._rohr.rohrAn(self._dlg)
            logger.info("Tube power on command sent")
            return True
        except Exception as exc:
            logger.error("click_tube_power_on failed: %s", exc)
            return False

    def is_tube_on(self) -> bool:
        """Check whether the X-ray tube is on via label detection.

        Delegates to: label_h.isLabelAvailable (index 15 is the tube-on label).
        """
        if not self._require_connection():
            return False

        try:
            result = self._label.isLabelAvailable(index=15, dlg=self._dlg)
            logger.debug("is_tube_on label check: %s", result)
            return bool(result)
        except Exception as exc:
            logger.error("is_tube_on failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Rotation (Drehen)
    # ------------------------------------------------------------------

    def activate_rotation(self) -> bool:
        """Activate the Drehen (rotation) tab.

        Delegates to: tabcontrol.selectTabDrehen(dlg).
        """
        if not self._require_connection():
            return False

        try:
            logger.info("Selecting Drehen tab")
            self._tab.selectTabDrehen(self._dlg)
            logger.info("Drehen tab selected")
            return True
        except Exception as exc:
            logger.error("activate_rotation failed: %s", exc)
            return False

    def rotate_degrees(self, degrees: float) -> bool:
        """Set the rotation angle via the A-value textbox.

        Delegates to: TextBox_method.setAValue(degrees, dlg).
        """
        if not self._require_connection():
            return False

        try:
            logger.info("Setting rotation angle to %.1f degrees", degrees)
            result = self._textbox.setAValue(val=degrees, dlg=self._dlg)
            logger.info("rotate_degrees result: %s", result)
            return bool(result)
        except Exception as exc:
            logger.error("rotate_degrees failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Scan control
    # ------------------------------------------------------------------

    def start_scan(self) -> bool:
        """Click the Messen (measure/scan) button.

        Delegates to: button.press_by_text(dlg, "Messen").
        """
        if not self._require_connection():
            return False

        try:
            logger.info("Pressing Messen button to start scan")
            result = self._button.press_by_text(self._dlg, "Messen")
            logger.info("start_scan result: %s", result)
            return bool(result)
        except Exception as exc:
            logger.error("start_scan failed: %s", exc)
            return False

    def is_scan_complete(self) -> bool:
        """Check if the scan has finished by detecting the current menu state.

        After a scan completes, WinWerth transitions to the Rechnen (calculation)
        menu.  Delegates to: punkte_Menu.detectMenu(dlg).
        """
        if not self._require_connection():
            return False

        try:
            current_menu = self._punkte_menu.detectMenu(self._dlg)
            complete = current_menu == "Rechnen"
            logger.debug("is_scan_complete: current_menu=%s, complete=%s",
                         current_menu, complete)
            return complete
        except Exception as exc:
            logger.error("is_scan_complete failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Error correction
    # ------------------------------------------------------------------

    def run_error_correction(self) -> bool:
        """Run the voltage/ampere auto-tune error correction.

        Delegates to: error_correction.correctErrors(dlg).
        """
        if not self._require_connection():
            return False

        try:
            logger.info("Running error correction (auto-tune voltage/ampere)")
            self._error_correction.correctErrors(self._dlg)
            logger.info("Error correction complete")
            return True
        except Exception as exc:
            logger.error("run_error_correction failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # STL save-dialog control
    # ------------------------------------------------------------------

    def open_save_dialog(self) -> bool:
        """Navigate Grafik3D -> Speichern unter to open the save dialog.

        Delegates to: topMenu.pressGrafik3D(dlg), topMenu.pressSpeichernUnter(dlg).
        """
        if not self._require_connection():
            return False

        try:
            logger.info("Opening save dialog: Grafik3D -> Speichern unter")
            self._top_menu.pressGrafik3D(self._dlg)
            time.sleep(0.5)  # wait for menu to expand
            self._top_menu.pressSpeichernUnter(self._dlg)
            time.sleep(1.0)  # wait for dialog to appear
            logger.info("Save dialog opened")
            return True
        except Exception as exc:
            logger.error("open_save_dialog failed: %s", exc)
            return False

    def is_save_dialog_open(self) -> bool:
        """Check if the Speichern-unter dialog is currently visible.

        Delegates to: SaveFileDialog.is_savefile_dialog_open().
        """
        if not self._require_connection():
            return False

        try:
            sfd = SaveFileDialog(dlg=self._dlg)
            return sfd.is_savefile_dialog_open()
        except Exception as exc:
            logger.error("is_save_dialog_open failed: %s", exc)
            return False

    def set_save_path(self, path: str) -> bool:
        """Type *path* into the save dialog's filename field.

        Finds the save dialog, then uses label_h.set_edit_text to fill
        the file-name edit box.
        """
        if not self._require_connection():
            return False

        try:
            logger.info("Setting save path: %s", path)
            sfd = SaveFileDialog(dlg=self._dlg)
            save_dlg = sfd.find_savefile_dialog()
            if save_dlg is None:
                logger.error("Save dialog not found - cannot set path")
                return False

            # Use label_h's set_edit_text to fill the filename field
            # The standard Windows save dialog has an Edit control for the filename
            result = self._label.set_edit_text(save_dlg, "Dateiname", path)
            if not result:
                # Fallback: try English name
                result = self._label.set_edit_text(save_dlg, "File name", path)
            logger.info("set_save_path result: %s", result)
            return bool(result)
        except Exception as exc:
            logger.error("set_save_path failed: %s", exc)
            return False

    def confirm_save(self) -> bool:
        """Click the save/confirm button in the save dialog.

        Delegates to: button.press_by_text on the save dialog.
        """
        if not self._require_connection():
            return False

        try:
            logger.info("Confirming save")
            sfd = SaveFileDialog(dlg=self._dlg)
            save_dlg = sfd.find_savefile_dialog()
            if save_dlg is None:
                logger.error("Save dialog not found - cannot confirm")
                return False

            # Click "Speichern" button in the dialog
            result = self._button.press_by_text(save_dlg, "Speichern")
            if not result:
                # Fallback: try English text
                result = self._button.press_by_text(save_dlg, "Save")
            logger.info("confirm_save result: %s", result)
            return bool(result)
        except Exception as exc:
            logger.error("confirm_save failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Tab / menu navigation helpers
    # ------------------------------------------------------------------

    def select_tab_ct(self) -> bool:
        """Switch to the CT tab. Delegates to tabcontrol.selectTabCT."""
        if not self._require_connection():
            return False
        try:
            self._tab.selectTabCT(self._dlg)
            logger.info("CT tab selected")
            return True
        except Exception as exc:
            logger.error("select_tab_ct failed: %s", exc)
            return False

    def select_tab_drehen(self) -> bool:
        """Switch to the Drehen tab. Delegates to tabcontrol.selectTabDrehen."""
        if not self._require_connection():
            return False
        try:
            self._tab.selectTabDrehen(self._dlg)
            logger.info("Drehen tab selected")
            return True
        except Exception as exc:
            logger.error("select_tab_drehen failed: %s", exc)
            return False

    def select_tab_xray(self) -> bool:
        """Switch to the X-ray tab. Delegates to tabcontrol.selectTabXray."""
        if not self._require_connection():
            return False
        try:
            self._tab.selectTabXray(self._dlg)
            logger.info("X-ray tab selected")
            return True
        except Exception as exc:
            logger.error("select_tab_xray failed: %s", exc)
            return False

    def check_live_bild(self) -> bool:
        """Ensure the 'Schnelles Live Bild' checkbox is checked.

        Delegates to: checkbox.checkLiveBild(dlg).
        """
        if not self._require_connection():
            return False
        try:
            self._checkbox.checkLiveBild(self._dlg)
            logger.info("Live Bild checkbox ensured checked")
            return True
        except Exception as exc:
            logger.error("check_live_bild failed: %s", exc)
            return False

    def select_file_type_stl(self) -> bool:
        """Select STL in the save dialog file type combobox.

        Delegates to: combobox.selectType(dlg, "stl").
        """
        if not self._require_connection():
            return False
        try:
            result = self._combobox.selectType(self._dlg, "stl")
            logger.info("File type set to STL")
            return bool(result)
        except Exception as exc:
            logger.error("select_file_type_stl failed: %s", exc)
            return False

    def select_voxel_endfil(self) -> bool:
        """Select ENDFIL voxel mode. Delegates to voxel.selectENDFIL."""
        if not self._require_connection():
            return False
        try:
            self._voxel.selectENDFIL(self._dlg)
            logger.info("Voxel ENDFIL selected")
            return True
        except Exception as exc:
            logger.error("select_voxel_endfil failed: %s", exc)
            return False

    def select_stl_voxel_v(self) -> bool:
        """Select STLVoxelV side button. Delegates to sideButtons.selectSTLVoxelV."""
        if not self._require_connection():
            return False
        try:
            self._side_buttons.selectSTLVoxelV(self._dlg)
            logger.info("STLVoxelV side button selected")
            return True
        except Exception as exc:
            logger.error("select_stl_voxel_v failed: %s", exc)
            return False

    def detect_current_menu(self) -> Optional[str]:
        """Detect which top-level menu/tab is currently active.

        Returns one of: 'Messfleck', 'CT', 'Hand', 'Rechnen', or None.
        Delegates to: punkte_Menu.detectMenu(dlg).
        """
        if not self._require_connection():
            return None
        try:
            result = self._punkte_menu.detectMenu(self._dlg)
            logger.debug("Detected current menu: %s", result)
            return result
        except Exception as exc:
            logger.error("detect_current_menu failed: %s", exc)
            return None

    def click_menu_tab(self, tab_name: str) -> bool:
        """Click a specific punkte-menu tab by name.

        Delegates to: punkte_Menu.clickTab(tab_name, dlg).
        """
        if not self._require_connection():
            return False
        try:
            result = self._punkte_menu.clickTab(tab_name, self._dlg)
            logger.info("Clicked menu tab '%s': %s", tab_name, result)
            return bool(result)
        except Exception as exc:
            logger.error("click_menu_tab '%s' failed: %s", tab_name, exc)
            return False

    def press_button_by_id(self, automation_id: str) -> bool:
        """Press a button by its automation ID.

        Delegates to: ButtonPresser.press_by_automation_id(dlg, automation_id).
        """
        if not self._require_connection():
            return False
        try:
            result = self._button.press_by_automation_id(self._dlg, automation_id)
            logger.debug("press_button_by_id('%s'): %s", automation_id, result)
            return bool(result)
        except Exception as exc:
            logger.error("press_button_by_id('%s') failed: %s", automation_id, exc)
            return False

    def press_button_by_text(self, text: str) -> bool:
        """Press a button by its visible text.

        Delegates to: ButtonPresser.press_by_text(dlg, text).
        """
        if not self._require_connection():
            return False
        try:
            result = self._button.press_by_text(self._dlg, text)
            logger.debug("press_button_by_text('%s'): %s", text, result)
            return bool(result)
        except Exception as exc:
            logger.error("press_button_by_text('%s') failed: %s", text, exc)
            return False

    def get_label_text(self, automation_id: str) -> Optional[str]:
        """Read the text of a label by automation ID.

        Delegates to: label_h.get_label_text_by_id(dlg, automation_id).
        """
        if not self._require_connection():
            return None
        try:
            text = self._label.get_label_text_by_id(self._dlg, automation_id)
            logger.debug("get_label_text('%s'): %s", automation_id, text)
            return text
        except Exception as exc:
            logger.error("get_label_text('%s') failed: %s", automation_id, exc)
            return None

    def is_label_available(self, automation_id: str) -> bool:
        """Check if a label with the given automation ID exists.

        Delegates to: label_h.is_label_available_by_id(dlg, automation_id).
        """
        if not self._require_connection():
            return False
        try:
            result = self._label.is_label_available_by_id(self._dlg, automation_id)
            return bool(result)
        except Exception as exc:
            logger.error("is_label_available('%s') failed: %s", automation_id, exc)
            return False

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Return bridge status for diagnostics."""
        return {
            "bridge_available": BRIDGE_AVAILABLE,
            "connected": self._connected,
            "force_mock": self._force_mock,
            "source_dir": str(_SOURCE_DIR),
            "source_dir_exists": _SOURCE_DIR.exists(),
            "has_process": self._process is not None,
            "has_dlg": self._dlg is not None,
        }

    def __repr__(self) -> str:
        state = "CONNECTED" if self._connected else "DISCONNECTED"
        if self._force_mock:
            state = "MOCK"
        elif not BRIDGE_AVAILABLE:
            state = "UNAVAILABLE"
        return f"<PyWinAutoBridge state={state}>"
