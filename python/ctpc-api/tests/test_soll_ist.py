"""Tests for STL Soll-Ist comparison and deviation reporting."""

from __future__ import annotations

import json
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from stl import mesh as stl_mesh

from src.analysis.soll_ist import compare_stl, _extract_vertices
from src.analysis.deviation_report import DeviationReport, write_report


# ---------------------------------------------------------------------------
# Helpers -- create simple STL meshes programmatically
# ---------------------------------------------------------------------------

def _make_cube_stl(path: Path, size: float = 10.0, offset: tuple[float, float, float] = (0, 0, 0)) -> Path:
    """Create a simple cube STL file at *path*.

    The cube has side length *size* and is offset by *offset*.
    """
    ox, oy, oz = offset
    # 12 triangles for a cube (2 per face)
    vertices = np.array([
        # Bottom face
        [ox, oy, oz], [ox + size, oy, oz], [ox + size, oy + size, oz],
        [ox, oy, oz], [ox + size, oy + size, oz], [ox, oy + size, oz],
        # Top face
        [ox, oy, oz + size], [ox + size, oy + size, oz + size], [ox + size, oy, oz + size],
        [ox, oy, oz + size], [ox, oy + size, oz + size], [ox + size, oy + size, oz + size],
        # Front face
        [ox, oy, oz], [ox + size, oy, oz], [ox + size, oy, oz + size],
        [ox, oy, oz], [ox + size, oy, oz + size], [ox, oy, oz + size],
        # Back face
        [ox, oy + size, oz], [ox + size, oy + size, oz + size], [ox + size, oy + size, oz],
        [ox, oy + size, oz], [ox, oy + size, oz + size], [ox + size, oy + size, oz + size],
        # Left face
        [ox, oy, oz], [ox, oy, oz + size], [ox, oy + size, oz + size],
        [ox, oy, oz], [ox, oy + size, oz + size], [ox, oy + size, oz],
        # Right face
        [ox + size, oy, oz], [ox + size, oy + size, oz + size], [ox + size, oy, oz + size],
        [ox + size, oy, oz], [ox + size, oy + size, oz], [ox + size, oy + size, oz + size],
    ])

    # Reshape to (12 triangles, 3 vertices, 3 coords)
    faces = vertices.reshape(12, 3, 3)

    cube = stl_mesh.Mesh(np.zeros(12, dtype=stl_mesh.Mesh.dtype))
    for i, face in enumerate(faces):
        for j in range(3):
            cube.vectors[i][j] = face[j]

    cube.save(str(path))
    return path


def _make_single_triangle_stl(path: Path, v0=(0, 0, 0), v1=(1, 0, 0), v2=(0, 1, 0)) -> Path:
    """Create a minimal STL with a single triangle."""
    tri = stl_mesh.Mesh(np.zeros(1, dtype=stl_mesh.Mesh.dtype))
    tri.vectors[0][0] = v0
    tri.vectors[0][1] = v1
    tri.vectors[0][2] = v2
    tri.save(str(path))
    return path


# ---------------------------------------------------------------------------
# Tests -- compare_stl
# ---------------------------------------------------------------------------

class TestCompareStl:
    """Test STL comparison logic."""

    @pytest.fixture
    def reference_cube(self, tmp_path) -> Path:
        return _make_cube_stl(tmp_path / "reference.stl", size=10.0)

    @pytest.fixture
    def identical_cube(self, tmp_path) -> Path:
        return _make_cube_stl(tmp_path / "scan_identical.stl", size=10.0)

    @pytest.fixture
    def offset_cube(self, tmp_path) -> Path:
        return _make_cube_stl(tmp_path / "scan_offset.stl", size=10.0, offset=(1.0, 0, 0))

    @pytest.fixture
    def small_offset_cube(self, tmp_path) -> Path:
        return _make_cube_stl(tmp_path / "scan_small_offset.stl", size=10.0, offset=(0.05, 0, 0))

    def test_identical_stls_zero_deviation(self, reference_cube, identical_cube):
        """Comparing identical STLs should yield zero deviation."""
        report = compare_stl(reference_cube, identical_cube)

        assert report["minDeviation"] == pytest.approx(0.0, abs=1e-6)
        assert report["maxDeviation"] == pytest.approx(0.0, abs=1e-6)
        assert report["avgDeviation"] == pytest.approx(0.0, abs=1e-6)
        assert report["stdDeviation"] == pytest.approx(0.0, abs=1e-6)
        assert report["withinTolerance"] is True

    def test_offset_produces_expected_deviation(self, reference_cube, offset_cube):
        """A 1mm X-offset should produce measurable deviation."""
        report = compare_stl(reference_cube, offset_cube, tolerance_mm=0.1)

        # The offset is 1.0mm in X -- vertices on the shifted face are 1mm away,
        # but shared edges remain close. Average should be > 0.
        assert report["maxDeviation"] >= 0.99  # at least ~1mm
        assert report["avgDeviation"] > 0.0
        assert report["withinTolerance"] is False  # 0.1mm tolerance, 1mm offset

    def test_small_offset_within_tolerance(self, reference_cube, small_offset_cube):
        """A 0.05mm offset should be within 0.1mm tolerance."""
        report = compare_stl(reference_cube, small_offset_cube, tolerance_mm=0.1)

        assert report["avgDeviation"] < 0.1
        assert report["withinTolerance"] is True

    def test_report_has_all_fields(self, reference_cube, identical_cube):
        """Report dict has all required fields."""
        report = compare_stl(reference_cube, identical_cube)

        required_keys = [
            "referenceStlPath",
            "scanStlPath",
            "minDeviation",
            "maxDeviation",
            "avgDeviation",
            "stdDeviation",
            "withinTolerance",
            "toleranceMm",
            "heatmapData",
        ]
        for key in required_keys:
            assert key in report, f"Missing key: {key}"

    def test_heatmap_data_is_list(self, reference_cube, identical_cube):
        """Heatmap data should be a list of floats."""
        report = compare_stl(reference_cube, identical_cube)

        assert isinstance(report["heatmapData"], list)
        assert len(report["heatmapData"]) > 0
        assert all(isinstance(v, float) for v in report["heatmapData"])

    def test_custom_tolerance(self, reference_cube, offset_cube):
        """Custom tolerance value is reflected in report."""
        report = compare_stl(reference_cube, offset_cube, tolerance_mm=5.0)
        assert report["toleranceMm"] == 5.0
        # With 5mm tolerance, a 1mm offset should pass
        assert report["withinTolerance"] is True

    def test_file_not_found_reference(self, tmp_path, identical_cube):
        """Missing reference file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compare_stl(tmp_path / "nonexistent.stl", identical_cube)

    def test_file_not_found_scan(self, reference_cube, tmp_path):
        """Missing scan file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compare_stl(reference_cube, tmp_path / "nonexistent.stl")

    def test_both_files_missing(self, tmp_path):
        """Both files missing raises FileNotFoundError for the reference (checked first)."""
        with pytest.raises(FileNotFoundError, match="Reference"):
            compare_stl(tmp_path / "ref.stl", tmp_path / "scan.stl")

    def test_paths_stored_in_report(self, reference_cube, identical_cube):
        """Report stores the file paths as strings."""
        report = compare_stl(reference_cube, identical_cube)
        assert report["referenceStlPath"] == str(reference_cube)
        assert report["scanStlPath"] == str(identical_cube)

    def test_deviation_values_non_negative(self, reference_cube, offset_cube):
        """All deviation values should be non-negative."""
        report = compare_stl(reference_cube, offset_cube)
        assert report["minDeviation"] >= 0.0
        assert report["maxDeviation"] >= 0.0
        assert report["avgDeviation"] >= 0.0
        assert report["stdDeviation"] >= 0.0

    def test_min_less_equal_avg_less_equal_max(self, reference_cube, offset_cube):
        """min <= avg <= max should always hold."""
        report = compare_stl(reference_cube, offset_cube)
        assert report["minDeviation"] <= report["avgDeviation"]
        assert report["avgDeviation"] <= report["maxDeviation"]

    def test_single_triangle_comparison(self, tmp_path):
        """Minimal STL files (single triangle) can be compared."""
        ref = _make_single_triangle_stl(tmp_path / "ref.stl")
        scan = _make_single_triangle_stl(tmp_path / "scan.stl")
        report = compare_stl(ref, scan)
        assert report["minDeviation"] == pytest.approx(0.0, abs=1e-6)
        assert report["withinTolerance"] is True

    def test_single_triangle_with_offset(self, tmp_path):
        """Offset single triangle produces measurable deviation."""
        ref = _make_single_triangle_stl(tmp_path / "ref.stl")
        scan = _make_single_triangle_stl(
            tmp_path / "scan.stl", v0=(5, 0, 0), v1=(6, 0, 0), v2=(5, 1, 0)
        )
        report = compare_stl(ref, scan)
        assert report["maxDeviation"] > 0.0
        assert report["avgDeviation"] > 0.0

    def test_heatmap_length_matches_scan_vertices(self, reference_cube, identical_cube):
        """Heatmap should have one entry per unique scan vertex."""
        report = compare_stl(reference_cube, identical_cube)
        scan_verts = _extract_vertices(identical_cube)
        assert len(report["heatmapData"]) == len(scan_verts)

    def test_scaled_cube_deviation(self, tmp_path):
        """A slightly larger cube should have predictable max deviation."""
        ref = _make_cube_stl(tmp_path / "ref.stl", size=10.0)
        # A cube of size 12 has vertices at 0-12 instead of 0-10
        scan = _make_cube_stl(tmp_path / "scan.stl", size=12.0)
        report = compare_stl(ref, scan)
        # The farthest vertex is (12,12,12) vs closest ref vertex (10,10,10)
        # distance = sqrt(4+4+4) ~ 3.46
        assert report["maxDeviation"] > 2.0
        assert report["withinTolerance"] is False

    def test_empty_stl_file(self, tmp_path):
        """An empty/corrupt STL file should raise an exception."""
        empty_file = tmp_path / "empty.stl"
        empty_file.write_bytes(b"")
        ref = _make_cube_stl(tmp_path / "ref.stl")
        with pytest.raises(Exception):
            compare_stl(ref, empty_file)

    def test_corrupt_stl_file(self, tmp_path):
        """A file with random bytes should raise an exception."""
        corrupt = tmp_path / "corrupt.stl"
        corrupt.write_bytes(b"this is not a valid STL file at all")
        ref = _make_cube_stl(tmp_path / "ref.stl")
        with pytest.raises(Exception):
            compare_stl(ref, corrupt)


# ---------------------------------------------------------------------------
# Tests -- _extract_vertices
# ---------------------------------------------------------------------------

class TestExtractVertices:
    """Test the vertex extraction helper."""

    def test_returns_numpy_array(self, tmp_path):
        stl = _make_cube_stl(tmp_path / "cube.stl")
        verts = _extract_vertices(stl)
        assert isinstance(verts, np.ndarray)
        assert verts.ndim == 2
        assert verts.shape[1] == 3

    def test_deduplicates_vertices(self, tmp_path):
        """Cube has 8 unique vertices, but 36 raw (12 triangles * 3)."""
        stl = _make_cube_stl(tmp_path / "cube.stl")
        verts = _extract_vertices(stl)
        assert len(verts) == 8  # unique cube vertices

    def test_single_triangle_three_vertices(self, tmp_path):
        stl = _make_single_triangle_stl(tmp_path / "tri.stl")
        verts = _extract_vertices(stl)
        assert len(verts) == 3


# ---------------------------------------------------------------------------
# Tests -- DeviationReport dataclass
# ---------------------------------------------------------------------------

class TestDeviationReport:
    """Test report dataclass and file writing."""

    @pytest.fixture
    def sample_data(self) -> dict:
        return {
            "referenceStlPath": "/data/reference.stl",
            "scanStlPath": "/data/scan.stl",
            "minDeviation": 0.001,
            "maxDeviation": 0.152,
            "avgDeviation": 0.045,
            "stdDeviation": 0.023,
            "withinTolerance": True,
            "toleranceMm": 0.1,
            "heatmapData": [0.01, 0.02, 0.05, 0.15],
        }

    def test_from_dict(self, sample_data):
        report = DeviationReport.from_dict(sample_data)
        assert report.min_deviation == 0.001
        assert report.within_tolerance is True

    def test_from_dict_all_fields(self, sample_data):
        report = DeviationReport.from_dict(sample_data)
        assert report.reference_stl_path == "/data/reference.stl"
        assert report.scan_stl_path == "/data/scan.stl"
        assert report.max_deviation == 0.152
        assert report.avg_deviation == 0.045
        assert report.std_deviation == 0.023
        assert report.tolerance_mm == 0.1
        assert report.heatmap_data == [0.01, 0.02, 0.05, 0.15]

    def test_to_dict_roundtrip(self, sample_data):
        report = DeviationReport.from_dict(sample_data)
        d = report.to_dict()
        assert d["minDeviation"] == sample_data["minDeviation"]
        assert d["maxDeviation"] == sample_data["maxDeviation"]

    def test_to_dict_includes_heatmap_when_present(self, sample_data):
        report = DeviationReport.from_dict(sample_data)
        d = report.to_dict()
        assert "heatmapData" in d
        assert d["heatmapData"] == [0.01, 0.02, 0.05, 0.15]

    def test_to_dict_excludes_heatmap_when_none(self, sample_data):
        sample_data.pop("heatmapData")
        report = DeviationReport.from_dict(sample_data)
        d = report.to_dict()
        assert "heatmapData" not in d

    def test_write_report_creates_files(self, sample_data, tmp_path):
        json_path, txt_path = write_report(sample_data, tmp_path / "output")

        assert json_path.exists()
        assert txt_path.exists()
        assert json_path.name == "deviation-report.json"
        assert txt_path.name == "deviation-report.txt"

    def test_write_report_creates_output_dir(self, sample_data, tmp_path):
        """write_report creates the output directory if it doesn't exist."""
        output = tmp_path / "nested" / "deep" / "output"
        json_path, txt_path = write_report(sample_data, output)
        assert output.exists()
        assert json_path.exists()

    def test_text_report_contains_verdict(self, sample_data, tmp_path):
        _, txt_path = write_report(sample_data, tmp_path / "output")
        text = txt_path.read_text()
        assert "PASS" in text

    def test_fail_verdict(self, sample_data, tmp_path):
        sample_data["withinTolerance"] = False
        _, txt_path = write_report(sample_data, tmp_path / "output")
        text = txt_path.read_text()
        assert "FAIL" in text

    def test_text_report_contains_deviation_values(self, sample_data, tmp_path):
        _, txt_path = write_report(sample_data, tmp_path / "output")
        text = txt_path.read_text()
        assert "0.0010" in text  # min
        assert "0.1520" in text  # max
        assert "0.0450" in text  # avg
        assert "0.0230" in text  # std

    def test_text_report_contains_paths(self, sample_data, tmp_path):
        _, txt_path = write_report(sample_data, tmp_path / "output")
        text = txt_path.read_text()
        assert "/data/reference.stl" in text
        assert "/data/scan.stl" in text

    def test_heatmap_stored_separately(self, sample_data, tmp_path):
        output = tmp_path / "output"
        write_report(sample_data, output)
        heatmap_path = output / "heatmap-data.json"
        assert heatmap_path.exists()

    def test_heatmap_file_contents(self, sample_data, tmp_path):
        output = tmp_path / "output"
        write_report(sample_data, output)
        heatmap_path = output / "heatmap-data.json"
        data = json.loads(heatmap_path.read_text())
        assert data == [0.01, 0.02, 0.05, 0.15]

    def test_json_report_excludes_heatmap(self, sample_data, tmp_path):
        """JSON report should not contain heatmap (stored separately)."""
        output = tmp_path / "output"
        json_path, _ = write_report(sample_data, output)
        data = json.loads(json_path.read_text())
        assert "heatmapData" not in data

    def test_json_report_has_generated_at(self, sample_data, tmp_path):
        output = tmp_path / "output"
        json_path, _ = write_report(sample_data, output)
        data = json.loads(json_path.read_text())
        assert "generatedAt" in data

    def test_no_heatmap_skips_heatmap_file(self, sample_data, tmp_path):
        """If heatmapData is not in the input, no heatmap file is written."""
        sample_data.pop("heatmapData")
        output = tmp_path / "output"
        write_report(sample_data, output)
        assert not (output / "heatmap-data.json").exists()

    def test_report_with_zero_deviations(self, tmp_path):
        """Edge case: all deviations are zero."""
        data = {
            "referenceStlPath": "/a.stl",
            "scanStlPath": "/b.stl",
            "minDeviation": 0.0,
            "maxDeviation": 0.0,
            "avgDeviation": 0.0,
            "stdDeviation": 0.0,
            "withinTolerance": True,
            "toleranceMm": 0.1,
        }
        json_path, txt_path = write_report(data, tmp_path / "output")
        assert json_path.exists()
        text = txt_path.read_text()
        assert "PASS" in text
