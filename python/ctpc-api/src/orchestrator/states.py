"""Scan workflow states mirroring the TypeScript ScanState enum."""

from enum import Enum


class ScanState(str, Enum):
    """CT scan pipeline states.

    Each state represents a discrete phase of the automated scan workflow.
    The state machine progresses linearly from IDLE -> DONE, with any state
    able to transition to ERROR on failure.
    """

    IDLE = "IDLE"
    PROFILE_SELECT = "PROFILE_SELECT"
    TUBE_ON = "TUBE_ON"
    ROTATE_PREVIEW = "ROTATE_PREVIEW"
    GREEN_BOX = "GREEN_BOX"
    ERROR_CORRECT = "ERROR_CORRECT"
    SCANNING = "SCANNING"
    WAIT_COMPLETE = "WAIT_COMPLETE"
    EXPORT_STL = "EXPORT_STL"
    ANALYSE = "ANALYSE"
    DONE = "DONE"
    ERROR = "ERROR"
