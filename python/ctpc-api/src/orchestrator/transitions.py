"""Valid state transitions, retry policies, and timeout configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet

from .states import ScanState


# ---------------------------------------------------------------------------
# Transition map
# ---------------------------------------------------------------------------

#: For each state, the set of states it is allowed to transition to.
VALID_TRANSITIONS: Dict[ScanState, FrozenSet[ScanState]] = {
    ScanState.IDLE: frozenset({ScanState.PROFILE_SELECT}),
    ScanState.PROFILE_SELECT: frozenset({ScanState.TUBE_ON, ScanState.ERROR}),
    ScanState.TUBE_ON: frozenset({ScanState.ROTATE_PREVIEW, ScanState.ERROR}),
    ScanState.ROTATE_PREVIEW: frozenset({ScanState.GREEN_BOX, ScanState.ERROR}),
    ScanState.GREEN_BOX: frozenset({ScanState.ERROR_CORRECT, ScanState.ERROR}),
    ScanState.ERROR_CORRECT: frozenset({ScanState.SCANNING, ScanState.ERROR}),
    ScanState.SCANNING: frozenset({ScanState.WAIT_COMPLETE, ScanState.ERROR}),
    ScanState.WAIT_COMPLETE: frozenset({ScanState.EXPORT_STL, ScanState.ERROR}),
    ScanState.EXPORT_STL: frozenset({ScanState.ANALYSE, ScanState.ERROR}),
    ScanState.ANALYSE: frozenset({ScanState.DONE, ScanState.ERROR}),
    ScanState.DONE: frozenset({ScanState.IDLE}),
    ScanState.ERROR: frozenset({ScanState.IDLE}),
}

#: The linear happy-path order (excludes ERROR).
HAPPY_PATH: list[ScanState] = [
    ScanState.IDLE,
    ScanState.PROFILE_SELECT,
    ScanState.TUBE_ON,
    ScanState.ROTATE_PREVIEW,
    ScanState.GREEN_BOX,
    ScanState.ERROR_CORRECT,
    ScanState.SCANNING,
    ScanState.WAIT_COMPLETE,
    ScanState.EXPORT_STL,
    ScanState.ANALYSE,
    ScanState.DONE,
]


def is_valid_transition(from_state: ScanState, to_state: ScanState) -> bool:
    """Return True if *from_state* -> *to_state* is allowed."""
    return to_state in VALID_TRANSITIONS.get(from_state, frozenset())


def next_happy_state(current: ScanState) -> ScanState | None:
    """Return the next state in the happy path, or None if at the end."""
    try:
        idx = HAPPY_PATH.index(current)
        if idx + 1 < len(HAPPY_PATH):
            return HAPPY_PATH[idx + 1]
    except ValueError:
        pass
    return None


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

class ErrorSeverity(str, Enum):
    """Classifies errors to decide retry vs abort."""

    RECOVERABLE = "RECOVERABLE"  # retry the current state
    FATAL = "FATAL"              # abort to ERROR -> IDLE


# ---------------------------------------------------------------------------
# Retry & timeout configuration per state
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StatePolicy:
    """Retry + timeout policy for a single state."""

    timeout_s: float = 30.0
    max_retries: int = 0
    backoff_s: float = 1.0
    backoff_factor: float = 2.0  # exponential backoff multiplier


#: Per-state policies.  States not listed use the default (30 s, 0 retries).
STATE_POLICIES: Dict[ScanState, StatePolicy] = {
    ScanState.IDLE: StatePolicy(timeout_s=0),  # no timeout while idle
    ScanState.PROFILE_SELECT: StatePolicy(timeout_s=30, max_retries=2, backoff_s=2),
    ScanState.TUBE_ON: StatePolicy(timeout_s=60, max_retries=1, backoff_s=5),
    ScanState.ROTATE_PREVIEW: StatePolicy(timeout_s=120, max_retries=1, backoff_s=5),
    ScanState.GREEN_BOX: StatePolicy(timeout_s=30, max_retries=2, backoff_s=2),
    ScanState.ERROR_CORRECT: StatePolicy(timeout_s=60, max_retries=10, backoff_s=1),
    ScanState.SCANNING: StatePolicy(timeout_s=600, max_retries=0),
    ScanState.WAIT_COMPLETE: StatePolicy(timeout_s=60, max_retries=0),
    ScanState.EXPORT_STL: StatePolicy(timeout_s=60, max_retries=2, backoff_s=3),
    ScanState.ANALYSE: StatePolicy(timeout_s=120, max_retries=1, backoff_s=2),
    ScanState.DONE: StatePolicy(timeout_s=0),
    ScanState.ERROR: StatePolicy(timeout_s=0),
}


def get_policy(state: ScanState) -> StatePolicy:
    """Return the retry/timeout policy for *state*."""
    return STATE_POLICIES.get(state, StatePolicy())
