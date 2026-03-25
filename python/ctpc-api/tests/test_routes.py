"""Tests for FastAPI REST API routes."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.api.routes import router, _scans


# ---------------------------------------------------------------------------
# Mock controller
# ---------------------------------------------------------------------------

class MockRouteController:
    """Mock controller satisfying the interface expected by routes.py."""

    def __init__(self, *, mock_mode: bool = True):
        self.mock_mode = mock_mode

    def get_system_status(self) -> dict:
        return {
            "winwerth_connected": not self.mock_mode,
            "tube_on": False,
            "scanning": False,
        }

    def get_available_profiles(self) -> list[dict]:
        return [
            {"id": "100L", "name": "100L Standard", "voltage": 100, "current": 50},
            {"id": "150H", "name": "150H High-Res", "voltage": 150, "current": 30},
        ]

    def complete_profile_selection_sequence(self, name: str) -> bool:
        if name == "INVALID":
            return False
        return True

    def activate_drehen(self) -> bool:
        return True

    def error_correction(self) -> bool:
        return True

    def complete_save_sequence(self) -> bool:
        return True


class FailingController(MockRouteController):
    """Controller that fails on error_correction."""

    def error_correction(self) -> bool:
        return False


class FailingSaveController(MockRouteController):
    """Controller that fails on save sequence."""

    def complete_save_sequence(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# App factory for tests
# ---------------------------------------------------------------------------

def _create_test_app(controller=None) -> FastAPI:
    """Create a FastAPI app with the controller attached to app.state."""
    app = FastAPI()
    app.include_router(router)
    app.state.controller = controller
    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_scan_store():
    """Clear the in-memory scan store before each test."""
    _scans.clear()
    yield
    _scans.clear()


@pytest.fixture
def mock_ctrl():
    return MockRouteController()


@pytest.fixture
def app(mock_ctrl):
    return _create_test_app(mock_ctrl)


@pytest.fixture
def client(app):
    """Synchronous test client for simple endpoint tests."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Async test client using httpx."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealth:

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["app"] == "ctpc-api"

    def test_health_has_timestamp(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "timestamp" in data
        assert "T" in data["timestamp"]  # ISO-ish format

    @pytest.mark.asyncio
    async def test_health_async(self, async_client):
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_works_without_controller(self):
        """Health endpoint works even if controller is None (not yet initialized)."""
        app = _create_test_app(controller=None)
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /status
# ---------------------------------------------------------------------------

class TestStatus:

    def test_status_returns_system_info(self, client):
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mock_mode"] is True
        assert "system" in data
        assert data["active_scans"] == 0
        assert data["total_scans"] == 0

    def test_status_reflects_scan_count(self, client):
        """After starting a scan, active_scans and total_scans update."""
        # Start a scan first
        client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        resp = client.get("/status")
        data = resp.json()
        assert data["total_scans"] == 1
        assert data["active_scans"] == 1  # status is "scanning"

    def test_status_503_without_controller(self):
        """Status returns 503 when controller is not set."""
        app = _create_test_app(controller=None)
        client = TestClient(app)
        resp = client.get("/status")
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_status_async(self, async_client):
        resp = await async_client.get("/status")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /profiles
# ---------------------------------------------------------------------------

class TestProfiles:

    def test_profiles_returns_list(self, client):
        resp = client.get("/profiles")
        assert resp.status_code == 200
        data = resp.json()
        assert "profiles" in data
        assert len(data["profiles"]) == 2
        assert data["profiles"][0]["id"] == "100L"

    def test_profiles_503_without_controller(self):
        app = _create_test_app(controller=None)
        client = TestClient(app)
        resp = client.get("/profiles")
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_profiles_async(self, async_client):
        resp = await async_client.get("/profiles")
        assert resp.status_code == 200
        assert len(resp.json()["profiles"]) == 2


# ---------------------------------------------------------------------------
# POST /profiles/{name}/select
# ---------------------------------------------------------------------------

class TestSelectProfile:

    def test_select_profile_success(self, client):
        resp = client.post("/profiles/100L/select")
        assert resp.status_code == 200
        data = resp.json()
        assert data["selected"] == "100L"
        assert data["success"] is True

    def test_select_profile_failure(self, client):
        resp = client.post("/profiles/INVALID/select")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /scan/start
# ---------------------------------------------------------------------------

class TestScanStart:

    def test_scan_start_success(self, client):
        resp = client.post("/scan/start", json={"profileId": "100L", "partId": "part-001"})
        assert resp.status_code == 200
        data = resp.json()
        scan = data["scan"]
        assert scan["profileId"] == "100L"
        assert scan["partId"] == "part-001"
        assert scan["status"] == "scanning"
        assert scan["startedAt"] is not None
        assert scan["id"] is not None

    def test_scan_start_profile_failure(self, client):
        """If profile selection fails, scan start returns 400."""
        resp = client.post("/scan/start", json={"profileId": "INVALID", "partId": "p1"})
        assert resp.status_code == 400

    def test_scan_start_error_correction_failure(self):
        """If error correction fails, scan start returns 400."""
        app = _create_test_app(FailingController())
        client = TestClient(app)
        resp = client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        assert resp.status_code == 400
        assert "Error correction" in resp.json()["detail"]

    def test_scan_start_assigns_unique_ids(self, client):
        """Each scan gets a unique ID."""
        r1 = client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        r2 = client.post("/scan/start", json={"profileId": "100L", "partId": "p2"})
        assert r1.json()["scan"]["id"] != r2.json()["scan"]["id"]

    def test_scan_start_503_without_controller(self):
        app = _create_test_app(controller=None)
        client = TestClient(app)
        resp = client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        assert resp.status_code == 503

    def test_scan_start_missing_body_fields(self, client):
        """Missing required fields returns 422 (validation error)."""
        resp = client.post("/scan/start", json={"profileId": "100L"})
        assert resp.status_code == 422

    def test_scan_start_empty_body(self, client):
        resp = client.post("/scan/start", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_scan_start_async(self, async_client):
        resp = await async_client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /scan/stop
# ---------------------------------------------------------------------------

class TestScanStop:

    def test_scan_stop_marks_active_as_stopped(self, client):
        """Active scans get marked as stopped."""
        client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        resp = client.post("/scan/stop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert len(data["stopped"]) == 1

    def test_scan_stop_no_active_scans(self, client):
        """Stopping with no active scans returns empty list."""
        resp = client.post("/scan/stop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["stopped"] == []

    def test_scan_stop_sets_completed_at(self, client):
        """Stopped scans get a completedAt timestamp."""
        r = client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        scan_id = r.json()["scan"]["id"]

        client.post("/scan/stop")

        # Verify via /scans/{id}
        r2 = client.get(f"/scans/{scan_id}")
        scan = r2.json()["scan"]
        assert scan["status"] == "stopped"
        assert scan["completedAt"] is not None

    def test_scan_stop_only_affects_scanning(self, client):
        """Scans not in 'scanning' status are not affected by stop."""
        # Start and stop a scan
        client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        client.post("/scan/stop")  # now it's "stopped"

        # Start another
        client.post("/scan/start", json={"profileId": "100L", "partId": "p2"})

        # Stop again -- should only stop the second one
        resp = client.post("/scan/stop")
        assert resp.json()["count"] == 1

    @pytest.mark.asyncio
    async def test_scan_stop_async(self, async_client):
        await async_client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        resp = await async_client.post("/scan/stop")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /scans
# ---------------------------------------------------------------------------

class TestListScans:

    def test_list_scans_empty(self, client):
        resp = client.get("/scans")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scans"] == []
        assert data["total"] == 0

    def test_list_scans_after_start(self, client):
        client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        client.post("/scan/start", json={"profileId": "150H", "partId": "p2"})

        resp = client.get("/scans")
        data = resp.json()
        assert data["total"] == 2
        assert len(data["scans"]) == 2

    @pytest.mark.asyncio
    async def test_list_scans_async(self, async_client):
        resp = await async_client.get("/scans")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /scans/{scan_id}
# ---------------------------------------------------------------------------

class TestGetScan:

    def test_get_scan_found(self, client):
        r = client.post("/scan/start", json={"profileId": "100L", "partId": "p1"})
        scan_id = r.json()["scan"]["id"]

        resp = client.get(f"/scans/{scan_id}")
        assert resp.status_code == 200
        assert resp.json()["scan"]["id"] == scan_id

    def test_get_scan_not_found(self, client):
        resp = client.get("/scans/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_scan_not_found_async(self, async_client):
        resp = await async_client.get("/scans/missing")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /stl/export
# ---------------------------------------------------------------------------

class TestStlExport:

    def test_stl_export_success(self, client):
        resp = client.post("/stl/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_stl_export_failure(self):
        app = _create_test_app(FailingSaveController())
        client = TestClient(app)
        resp = client.post("/stl/export")
        assert resp.status_code == 500

    def test_stl_export_503_without_controller(self):
        app = _create_test_app(controller=None)
        client = TestClient(app)
        resp = client.post("/stl/export")
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Integration: scan lifecycle
# ---------------------------------------------------------------------------

class TestScanLifecycle:
    """End-to-end lifecycle tests combining multiple endpoints."""

    def test_start_list_stop_verify(self, client):
        """Start a scan, verify it in the list, stop it, verify stopped."""
        # Start
        r1 = client.post("/scan/start", json={"profileId": "100L", "partId": "lifecycle-1"})
        assert r1.status_code == 200
        scan_id = r1.json()["scan"]["id"]

        # List
        r2 = client.get("/scans")
        assert any(s["id"] == scan_id for s in r2.json()["scans"])

        # Stop
        r3 = client.post("/scan/stop")
        assert scan_id in r3.json()["stopped"]

        # Verify stopped
        r4 = client.get(f"/scans/{scan_id}")
        assert r4.json()["scan"]["status"] == "stopped"

    def test_multiple_scans_independent(self, client):
        """Multiple scans can coexist in the store."""
        r1 = client.post("/scan/start", json={"profileId": "100L", "partId": "a"})
        r2 = client.post("/scan/start", json={"profileId": "150H", "partId": "b"})

        id1 = r1.json()["scan"]["id"]
        id2 = r2.json()["scan"]["id"]

        scans = client.get("/scans").json()["scans"]
        ids = [s["id"] for s in scans]
        assert id1 in ids
        assert id2 in ids
