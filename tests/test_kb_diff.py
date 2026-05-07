"""Unit tests for the KB snapshot diff CLI."""

import importlib.util
import json
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "kb-diff.py"

spec = importlib.util.spec_from_file_location("kb_diff", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _write_snapshot(dir_path: Path, authorities: list[dict]) -> Path:
    p = dir_path / "snap.json"
    p.write_text(json.dumps({"authorities": authorities}))
    return p


def test_diff_identical_snapshots_zero_changes():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        b_dir = td / "b"; b_dir.mkdir()
        c_dir = td / "c"; c_dir.mkdir()
        auths = [
            {"path": "a.md", "jurisdiction": "EU", "authority_group": "article"},
            {"path": "b.md", "jurisdiction": "EU", "authority_group": "article"},
        ]
        bp = _write_snapshot(b_dir, auths)
        cp = _write_snapshot(c_dir, auths)
        report = mod.diff_snapshots(bp, cp)
        assert report["added_count"] == 0
        assert report["removed_count"] == 0
        assert report["unchanged_count"] == 2


def test_diff_detects_added_and_removed():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        b_dir = td / "b"; b_dir.mkdir()
        c_dir = td / "c"; c_dir.mkdir()
        baseline = [
            {"path": "a.md", "jurisdiction": "EU", "authority_group": "article"},
            {"path": "b.md", "jurisdiction": "EU", "authority_group": "article"},
        ]
        current = [
            {"path": "a.md", "jurisdiction": "EU", "authority_group": "article"},
            {"path": "c.md", "jurisdiction": "EU", "authority_group": "article"},
        ]
        bp = _write_snapshot(b_dir, baseline)
        cp = _write_snapshot(c_dir, current)
        report = mod.diff_snapshots(bp, cp)
        assert report["added_count"] == 1
        assert report["removed_count"] == 1
        assert "c.md" in report["added_samples"]
        assert "b.md" in report["removed_samples"]


def test_diff_per_group_breakdown():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        b_dir = td / "b"; b_dir.mkdir()
        c_dir = td / "c"; c_dir.mkdir()
        baseline = [
            {"path": "eu1.md", "jurisdiction": "EU", "authority_group": "article"},
            {"path": "kr1.md", "jurisdiction": "KR", "authority_group": "article"},
        ]
        current = [
            {"path": "eu1.md", "jurisdiction": "EU", "authority_group": "article"},
            {"path": "kr1.md", "jurisdiction": "KR", "authority_group": "article"},
            {"path": "kr2.md", "jurisdiction": "KR", "authority_group": "article"},
        ]
        bp = _write_snapshot(b_dir, baseline)
        cp = _write_snapshot(c_dir, current)
        report = mod.diff_snapshots(bp, cp)
        kr = next(g for g in report["by_group"] if g["jurisdiction"] == "KR")
        assert kr["added"] == 1
        assert kr["removed"] == 0


def test_diff_real_snapshot_against_itself():
    """Diffing the live unified index against itself yields 0 changes."""
    real = PROJECT_ROOT / "index" / "unified-authority-index.json"
    if not real.exists():
        return
    report = mod.diff_snapshots(real, real)
    assert report["added_count"] == 0
    assert report["removed_count"] == 0
    assert report["unchanged_count"] > 0
