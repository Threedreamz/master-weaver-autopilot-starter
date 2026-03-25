"""Tests for the async scan state machine."""

from __future__ import annotations

import asyncio
import pytest
import time as time_mod
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.orchestrator.states import ScanState
from src.orchestrator.scan_machine import (
    InvalidTransitionError,
    ScanAlreadyRunningError,
    ScanMachine,
)
from src.orchestrator.transitions import (
    HAPPY_PATH,
    VALID_TRANSITIONS,
    ErrorSeverity,
    StatePolicy,
    get_policy,
    is_valid_transition,
    next_happy_state,
)


# ---------------------------------------------------------------------------
# Mock controller
# ---------------------------------------------------------------------------

class MockController:
    """Mock WinWerth controller that succeeds by default."""

    def __init__(self, *, fail_at: str | None = None, slow_tube: bool = False):
        self._fail_at = fail_at
        self._slow_tube = slow_tube
        self._scan_progress = 0.0
        self._scan_polls = 0

    def complete_profile_selection_sequence(self, profile_name: str) -> bool:
        if self._fail_at == "profile_select":
            return False
        return True

    def is_profile_selected(self, profile_name: str) -> bool:
        return self._fail_at != "profile_verify"

    def click_tube_power_on(self) -> bool:
        if self._fail_at == "tube_on":
            return False
        return True

    def is_tube_on(self) -> bool:
        if self._fail_at == "tube_status":
            return False
        return True

    def activate_rotation(self) -> bool:
        return self._fail_at != "rotation"

    def rotate_degrees(self, degrees: float) -> bool:
        return self._fail_at != "rotate"

    def get_min_distances(self) -> dict:
        if self._fail_at == "distances":
            return {}
        return {"top": 10.0, "bottom": 12.0, "left": 8.0, "right": 9.0}

    def set_green_box(self, boundaries: dict) -> bool:
        return self._fail_at != "green_box"

    def run_error_correction(self) -> bool:
        return self._fail_at != "error_correct"

    def get_pixel_status(self) -> dict:
        self._scan_polls += 1
        if self._scan_polls >= 3:
            return {"progress": 1.0, "complete": True}
        return {"progress": self._scan_polls / 3, "complete": False}

    def is_scan_complete(self) -> bool:
        return True

    def open_save_dialog(self) -> bool:
        return self._fail_at != "save_dialog"

    def set_save_path(self, path: str) -> bool:
        # Simulate file creation
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(b"solid test\nendsolid test\n")
        return True

    def confirm_save(self) -> bool:
        return True

    def close_save_dialog(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Transition tests
# ---------------------------------------------------------------------------

class TestTransitions:
    """Test the transition map."""

    def test_valid_happy_path_transitions(self):
        """Every consecutive pair in HAPPY_PATH is a valid transition."""
        for i in range(len(HAPPY_PATH) - 1):
            assert is_valid_transition(HAPPY_PATH[i], HAPPY_PATH[i + 1]), (
                f"{HAPPY_PATH[i]} -> {HAPPY_PATH[i + 1]} should be valid"
            )

    def test_any_state_can_go_to_error(self):
        """Every state except IDLE, DONE, ERROR can transition to ERROR."""
        for state in ScanState:
            if state in (ScanState.IDLE, ScanState.DONE, ScanState.ERROR):
                continue
            assert is_valid_transition(state, ScanState.ERROR), (
                f"{state} -> ERROR should be valid"
            )

    def test_error_and_done_go_to_idle(self):
        assert is_valid_transition(ScanState.ERROR, ScanState.IDLE)
        assert is_valid_transition(ScanState.DONE, ScanState.IDLE)

    def test_invalid_transition_backwards(self):
        """Cannot go backwards in the pipeline."""
        assert not is_valid_transition(ScanState.SCANNING, ScanState.TUBE_ON)
        assert not is_valid_transition(ScanState.DONE, ScanState.SCANNING)

    def test_invalid_transition_skip(self):
        """Cannot skip states."""
        assert not is_valid_transition(ScanState.IDLE, ScanState.SCANNING)
        assert not is_valid_transition(ScanState.PROFILE_SELECT, ScanState.GREEN_BOX)

    def test_next_happy_state_returns_successor(self):
        """next_happy_state returns the correct successor for each state."""
        assert next_happy_state(ScanState.IDLE) == ScanState.PROFILE_SELECT
        assert next_happy_state(ScanState.PROFILE_SELECT) == ScanState.TUBE_ON
        assert next_happy_state(ScanState.SCANNING) == ScanState.WAIT_COMPLETE
        assert next_happy_state(ScanState.ANALYSE) == ScanState.DONE

    def test_next_happy_state_none_at_end(self):
        """next_happy_state returns None for DONE (end of pipeline)."""
        assert next_happy_state(ScanState.DONE) is None

    def test_next_happy_state_none_for_error(self):
        """ERROR is not in the happy path so next_happy_state returns None."""
        assert next_happy_state(ScanState.ERROR) is None


# ---------------------------------------------------------------------------
# State policy tests
# ---------------------------------------------------------------------------

class TestStatePolicies:
    """Test per-state timeout and retry configuration."""

    def test_idle_has_no_timeout(self):
        policy = get_policy(ScanState.IDLE)
        assert policy.timeout_s == 0

    def test_profile_select_has_retries(self):
        policy = get_policy(ScanState.PROFILE_SELECT)
        assert policy.max_retries == 2
        assert policy.timeout_s == 30

    def test_scanning_has_long_timeout(self):
        policy = get_policy(ScanState.SCANNING)
        assert policy.timeout_s == 600
        assert policy.max_retries == 0

    def test_error_correct_has_many_retries(self):
        policy = get_policy(ScanState.ERROR_CORRECT)
        assert policy.max_retries == 10

    def test_default_policy_for_unknown(self):
        """get_policy returns a sensible default for states not explicitly configured."""
        # All states are configured, but the default fallback should still work
        default = StatePolicy()
        assert default.timeout_s == 30.0
        assert default.max_retries == 0

    def test_policy_is_frozen(self):
        """StatePolicy is a frozen dataclass — immutable after creation."""
        policy = get_policy(ScanState.SCANNING)
        with pytest.raises(AttributeError):
            policy.timeout_s = 999

    def test_backoff_factor_is_exponential(self):
        policy = get_policy(ScanState.PROFILE_SELECT)
        assert policy.backoff_factor == 2.0
        # backoff for attempt 0 = backoff_s * (factor ** 0) = backoff_s
        assert policy.backoff_s * (policy.backoff_factor ** 0) == policy.backoff_s
        # backoff for attempt 1 = backoff_s * (factor ** 1) = backoff_s * 2
        assert policy.backoff_s * (policy.backoff_factor ** 1) == policy.backoff_s * 2


# ---------------------------------------------------------------------------
# ErrorSeverity tests
# ---------------------------------------------------------------------------

class TestErrorSeverity:
    def test_values(self):
        assert ErrorSeverity.RECOVERABLE == "RECOVERABLE"
        assert ErrorSeverity.FATAL == "FATAL"

    def test_is_string_enum(self):
        assert isinstance(ErrorSeverity.RECOVERABLE, str)


# ---------------------------------------------------------------------------
# State machine tests
# ---------------------------------------------------------------------------

class TestScanMachine:
    """Test the ScanMachine class."""

    @pytest.fixture
    def tmp_dir(self, tmp_path):
        return tmp_path

    @pytest.fixture
    def machine(self, tmp_dir):
        ctrl = MockController()
        return ScanMachine(ctrl, base_path=tmp_dir)

    @pytest.fixture
    def failing_machine(self, tmp_dir):
        ctrl = MockController(fail_at="profile_select")
        return ScanMachine(ctrl, base_path=tmp_dir)

    @pytest.mark.asyncio
    async def test_initial_state_is_idle(self, machine):
        assert machine.state == ScanState.IDLE
        assert not machine.is_running

    @pytest.mark.asyncio
    async def test_happy_path_completes(self, machine):
        """Full scan pipeline completes successfully without reference STL."""
        states_visited: list[ScanState] = []

        def on_change(old, new, meta):
            states_visited.append(new)

        machine.on_state_change = on_change

        job = {"profileId": "100L", "partId": "test-part-001"}
        result = await machine.run_scan(job)

        assert result.state == ScanState.DONE
        assert result.error is None
        assert result.stl_path is not None
        assert Path(result.stl_path).exists()
        assert result.started_at is not None
        assert result.completed_at is not None

        # All pipeline states were visited
        assert ScanState.PROFILE_SELECT in states_visited
        assert ScanState.SCANNING in states_visited
        assert ScanState.EXPORT_STL in states_visited
        assert ScanState.DONE in states_visited

    @pytest.mark.asyncio
    async def test_all_happy_path_states_visited(self, machine):
        """Every state in the happy path is visited during a successful scan."""
        states_visited: list[ScanState] = []

        def on_change(old, new, meta):
            states_visited.append(new)

        machine.on_state_change = on_change

        job = {"profileId": "100L", "partId": "test-part-001"}
        result = await machine.run_scan(job)

        assert result.state == ScanState.DONE
        # All states from PROFILE_SELECT to DONE should be visited
        for state in HAPPY_PATH[1:]:  # skip IDLE (start state)
            assert state in states_visited, f"{state} was not visited"

    @pytest.mark.asyncio
    async def test_error_on_failure(self, failing_machine):
        """Machine transitions to ERROR when a state handler fails."""
        job = {"profileId": "100L", "partId": "test-part-001"}
        result = await failing_machine.run_scan(job)

        assert result.state == ScanState.ERROR
        assert result.error is not None
        assert "Profile selection failed" in result.error

    @pytest.mark.asyncio
    async def test_returns_to_idle_after_error(self, failing_machine):
        """Machine resets to IDLE after a failed scan."""
        job = {"profileId": "100L", "partId": "test-part-001"}
        await failing_machine.run_scan(job)

        assert failing_machine.state == ScanState.IDLE
        assert not failing_machine.is_running

    @pytest.mark.asyncio
    async def test_returns_to_idle_after_success(self, machine):
        """Machine resets to IDLE after a successful scan."""
        job = {"profileId": "100L", "partId": "test-part-001"}
        await machine.run_scan(job)

        assert machine.state == ScanState.IDLE
        assert not machine.is_running

    @pytest.mark.asyncio
    async def test_progress_callbacks_fire(self, machine):
        """Progress callbacks are invoked during the scan."""
        progress_events: list[tuple] = []

        def on_progress(state, progress, msg):
            progress_events.append((state, progress, msg))

        machine.on_progress = on_progress

        job = {"profileId": "100L", "partId": "test-part-001"}
        await machine.run_scan(job)

        assert len(progress_events) > 0
        # At least one progress event per state
        states_with_progress = {e[0] for e in progress_events}
        assert ScanState.PROFILE_SELECT in states_with_progress

    @pytest.mark.asyncio
    async def test_progress_values_are_floats(self, machine):
        """All progress values are between 0.0 and 1.0."""
        progress_events: list[tuple] = []

        def on_progress(state, progress, msg):
            progress_events.append((state, progress, msg))

        machine.on_progress = on_progress

        job = {"profileId": "100L", "partId": "test-part-001"}
        await machine.run_scan(job)

        for state, progress, msg in progress_events:
            assert 0.0 <= progress <= 1.0, (
                f"Progress {progress} out of range for state {state}"
            )

    @pytest.mark.asyncio
    async def test_error_callbacks_fire_on_failure(self, failing_machine):
        """Error callbacks are invoked when a state fails."""
        error_events: list[tuple] = []

        def on_error(state, exc, recoverable):
            error_events.append((state, str(exc), recoverable))

        failing_machine.on_error = on_error

        job = {"profileId": "100L", "partId": "test-part-001"}
        await failing_machine.run_scan(job)

        assert len(error_events) > 0

    @pytest.mark.asyncio
    async def test_error_callback_recoverable_flag(self, tmp_path):
        """Error callback has recoverable=True on retries, False on last attempt."""
        error_events: list[tuple] = []

        class FailingController(MockController):
            def complete_profile_selection_sequence(self, name: str) -> bool:
                raise RuntimeError("always fails")

        machine = ScanMachine(FailingController(), base_path=tmp_path)

        def on_error(state, exc, recoverable):
            error_events.append((state, str(exc), recoverable))

        machine.on_error = on_error

        job = {"profileId": "100L", "partId": "test-part-001"}
        await machine.run_scan(job)

        # PROFILE_SELECT has max_retries=2, so 3 total attempts
        profile_errors = [e for e in error_events if e[0] == ScanState.PROFILE_SELECT]
        assert len(profile_errors) == 3  # 1 initial + 2 retries

        # First two should be recoverable, last one not
        assert profile_errors[0][2] is True   # attempt 0, retries left
        assert profile_errors[1][2] is True   # attempt 1, retries left
        assert profile_errors[2][2] is False  # attempt 2, last attempt

    @pytest.mark.asyncio
    async def test_state_change_callback_receives_metadata(self, tmp_path):
        """on_state_change receives metadata dict."""
        metadata_received: list[dict] = []

        machine = ScanMachine(MockController(), base_path=tmp_path)

        def on_change(old, new, meta):
            metadata_received.append(meta)

        machine.on_state_change = on_change

        job = {"profileId": "100L", "partId": "test-part-001"}
        await machine.run_scan(job)

        # All metadata should be dicts
        for meta in metadata_received:
            assert isinstance(meta, dict)

    @pytest.mark.asyncio
    async def test_callback_exception_does_not_crash_machine(self, tmp_path):
        """If a callback raises, the machine continues."""
        machine = ScanMachine(MockController(), base_path=tmp_path)

        def bad_callback(old, new, meta):
            raise ValueError("callback bug")

        machine.on_state_change = bad_callback

        job = {"profileId": "100L", "partId": "test-part-001"}
        # Should not raise — callback errors are logged but swallowed
        result = await machine.run_scan(job)
        assert result.state == ScanState.DONE

    @pytest.mark.asyncio
    async def test_progress_callback_exception_does_not_crash(self, tmp_path):
        """If on_progress raises, the machine continues."""
        machine = ScanMachine(MockController(), base_path=tmp_path)

        def bad_progress(state, progress, msg):
            raise RuntimeError("progress bug")

        machine.on_progress = bad_progress

        job = {"profileId": "100L", "partId": "test-part-001"}
        result = await machine.run_scan(job)
        assert result.state == ScanState.DONE

    @pytest.mark.asyncio
    async def test_invalid_transition_raises(self):
        """InvalidTransitionError has correct attributes."""
        exc = InvalidTransitionError(ScanState.IDLE, ScanState.SCANNING)
        assert exc.from_state == ScanState.IDLE
        assert exc.to_state == ScanState.SCANNING
        assert "IDLE" in str(exc)
        assert "SCANNING" in str(exc)

    @pytest.mark.asyncio
    async def test_timeout_triggers_retry(self, tmp_path):
        """When a state times out, the machine retries per policy."""
        call_count = 0

        class SlowController(MockController):
            def complete_profile_selection_sequence(self, name: str) -> bool:
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    # Simulate blocking longer than timeout
                    time_mod.sleep(100)  # will be cancelled by asyncio timeout
                return True

            def is_profile_selected(self, name: str) -> bool:
                return True

        machine = ScanMachine(SlowController(), base_path=tmp_path)
        job = {"profileId": "100L", "partId": "test-part-001"}

        # The profile_select state has max_retries=2, timeout=30s
        # With our mock sleeping 100s, all 3 attempts will time out
        result = await machine.run_scan(job)

        # All 3 attempts (1 initial + 2 retries) should have been made
        assert call_count == 3
        assert result.state == ScanState.ERROR

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self, tmp_path):
        """If a state fails on first attempt but succeeds on retry, scan continues."""
        call_count = 0

        class RetryController(MockController):
            def complete_profile_selection_sequence(self, name: str) -> bool:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError("transient failure")
                return True

        machine = ScanMachine(RetryController(), base_path=tmp_path)
        job = {"profileId": "100L", "partId": "test-part-001"}
        result = await machine.run_scan(job)

        assert call_count >= 2  # at least two attempts
        assert result.state == ScanState.DONE

    @pytest.mark.asyncio
    async def test_scan_creates_output_folder(self, machine, tmp_dir):
        """Scan creates a date-based folder structure."""
        job = {"profileId": "100L", "partId": "test-part-001"}
        result = await machine.run_scan(job)

        scans_dir = tmp_dir / "scans"
        assert scans_dir.exists()
        # Should have at least one date directory
        date_dirs = list(scans_dir.iterdir())
        assert len(date_dirs) >= 1

    @pytest.mark.asyncio
    async def test_scan_result_contains_job_metadata(self, machine):
        """ScanResult carries job_id, scan_id, part_id, profile_id."""
        job = {"profileId": "100L", "partId": "test-part-001"}
        result = await machine.run_scan(job)

        assert result.job_id.startswith("job-")
        assert result.scan_id != ""
        assert result.part_id == "test-part-001"
        assert result.profile_id == "100L"

    @pytest.mark.asyncio
    async def test_failure_at_tube_on(self, tmp_path):
        """Failure at TUBE_ON stage produces ERROR result."""
        ctrl = MockController(fail_at="tube_on")
        machine = ScanMachine(ctrl, base_path=tmp_path)
        result = await machine.run_scan({"profileId": "X", "partId": "Y"})
        assert result.state == ScanState.ERROR
        assert "tube" in result.error.lower() or "power" in result.error.lower()

    @pytest.mark.asyncio
    async def test_failure_at_green_box(self, tmp_path):
        """Failure at GREEN_BOX stage produces ERROR result."""
        ctrl = MockController(fail_at="green_box")
        machine = ScanMachine(ctrl, base_path=tmp_path)
        result = await machine.run_scan({"profileId": "X", "partId": "Y"})
        assert result.state == ScanState.ERROR

    @pytest.mark.asyncio
    async def test_failure_at_rotation(self, tmp_path):
        """Failure at ROTATE_PREVIEW stage produces ERROR result."""
        ctrl = MockController(fail_at="rotation")
        machine = ScanMachine(ctrl, base_path=tmp_path)
        result = await machine.run_scan({"profileId": "X", "partId": "Y"})
        assert result.state == ScanState.ERROR

    @pytest.mark.asyncio
    async def test_failure_at_error_correct(self, tmp_path):
        """Failure at ERROR_CORRECT stage produces ERROR result."""
        ctrl = MockController(fail_at="error_correct")
        machine = ScanMachine(ctrl, base_path=tmp_path)
        result = await machine.run_scan({"profileId": "X", "partId": "Y"})
        assert result.state == ScanState.ERROR

    @pytest.mark.asyncio
    async def test_failure_at_save_dialog(self, tmp_path):
        """Failure at EXPORT_STL stage produces ERROR result."""
        ctrl = MockController(fail_at="save_dialog")
        machine = ScanMachine(ctrl, base_path=tmp_path)
        result = await machine.run_scan({"profileId": "X", "partId": "Y"})
        assert result.state == ScanState.ERROR

    @pytest.mark.asyncio
    async def test_concurrent_scan_rejected(self, tmp_path):
        """Running two scans concurrently raises ScanAlreadyRunningError."""
        # Use a controller that blocks long enough for the second scan to be rejected
        class SlowController(MockController):
            def complete_profile_selection_sequence(self, name: str) -> bool:
                time_mod.sleep(2)
                return True

        machine = ScanMachine(SlowController(), base_path=tmp_path)

        async def run_first():
            return await machine.run_scan({"profileId": "A", "partId": "1"})

        # Start first scan
        task1 = asyncio.create_task(run_first())
        # Give it a moment to acquire the lock
        await asyncio.sleep(0.1)

        # Second scan should be rejected
        with pytest.raises(ScanAlreadyRunningError):
            await machine.run_scan({"profileId": "B", "partId": "2"})

        # Let first scan finish
        await task1

    @pytest.mark.asyncio
    async def test_scan_already_running_error_message(self):
        exc = ScanAlreadyRunningError()
        assert "already in progress" in str(exc)

    @pytest.mark.asyncio
    async def test_disk_space_check_failure(self, tmp_path):
        """If disk space check fails, the scan errors."""
        machine = ScanMachine(MockController(), base_path=tmp_path)
        with patch("src.orchestrator.scan_machine.disk_space_ok", return_value=False):
            result = await machine.run_scan({"profileId": "X", "partId": "Y"})
        assert result.state == ScanState.ERROR
        assert "disk space" in result.error.lower()

    @pytest.mark.asyncio
    async def test_profile_verify_failure(self, tmp_path):
        """Profile verification failure (is_profile_selected returns False) causes error."""
        ctrl = MockController(fail_at="profile_verify")
        machine = ScanMachine(ctrl, base_path=tmp_path)
        result = await machine.run_scan({"profileId": "X", "partId": "Y"})
        assert result.state == ScanState.ERROR
        assert "not verified" in result.error.lower() or "Profile" in result.error

    @pytest.mark.asyncio
    async def test_error_result_has_completed_at(self, failing_machine):
        """Even on error, completed_at is set."""
        result = await failing_machine.run_scan({"profileId": "X", "partId": "Y"})
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_machine_reusable_after_error(self, tmp_path):
        """After an error, the machine can run another scan."""
        ctrl = MockController(fail_at="profile_select")
        machine = ScanMachine(ctrl, base_path=tmp_path)

        # First scan fails
        result1 = await machine.run_scan({"profileId": "X", "partId": "Y"})
        assert result1.state == ScanState.ERROR

        # Fix the controller
        ctrl._fail_at = None
        result2 = await machine.run_scan({"profileId": "X", "partId": "Y"})
        assert result2.state == ScanState.DONE

    @pytest.mark.asyncio
    async def test_machine_reusable_after_success(self, tmp_path):
        """After a success, the machine can run another scan."""
        machine = ScanMachine(MockController(), base_path=tmp_path)
        r1 = await machine.run_scan({"profileId": "A", "partId": "1"})
        assert r1.state == ScanState.DONE
        r2 = await machine.run_scan({"profileId": "B", "partId": "2"})
        assert r2.state == ScanState.DONE


# ---------------------------------------------------------------------------
# Transition edge cases
# ---------------------------------------------------------------------------

class TestTransitionEdgeCases:
    """Additional transition validation."""

    def test_idle_cannot_go_to_error(self):
        """IDLE has no error transition (nothing to fail at)."""
        assert not is_valid_transition(ScanState.IDLE, ScanState.ERROR)

    def test_done_cannot_go_to_error(self):
        assert not is_valid_transition(ScanState.DONE, ScanState.ERROR)

    def test_error_cannot_go_to_error(self):
        assert not is_valid_transition(ScanState.ERROR, ScanState.ERROR)

    def test_all_states_have_transition_entry(self):
        """Every ScanState appears as a key in VALID_TRANSITIONS."""
        for state in ScanState:
            assert state in VALID_TRANSITIONS, f"{state} missing from VALID_TRANSITIONS"

    def test_idle_can_only_go_to_profile_select(self):
        """IDLE has exactly one valid transition: PROFILE_SELECT."""
        valid = VALID_TRANSITIONS[ScanState.IDLE]
        assert valid == frozenset({ScanState.PROFILE_SELECT})

    def test_done_can_only_go_to_idle(self):
        valid = VALID_TRANSITIONS[ScanState.DONE]
        assert valid == frozenset({ScanState.IDLE})

    def test_error_can_only_go_to_idle(self):
        valid = VALID_TRANSITIONS[ScanState.ERROR]
        assert valid == frozenset({ScanState.IDLE})

    def test_self_transition_invalid_for_all_states(self):
        """No state can transition to itself."""
        for state in ScanState:
            assert not is_valid_transition(state, state), (
                f"{state} -> {state} should be invalid"
            )

    def test_happy_path_has_all_non_error_states(self):
        """HAPPY_PATH contains every state except ERROR."""
        non_error_states = {s for s in ScanState if s != ScanState.ERROR}
        assert set(HAPPY_PATH) == non_error_states

    def test_happy_path_starts_at_idle_ends_at_done(self):
        assert HAPPY_PATH[0] == ScanState.IDLE
        assert HAPPY_PATH[-1] == ScanState.DONE
