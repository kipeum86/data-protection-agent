"""Unit tests for the unified coverage dashboard."""

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "coverage-report-all.py"

spec = importlib.util.spec_from_file_location("coverage_report_all", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_build_unified_report_has_3_sub_kbs():
    report = mod.build_unified_report()
    for key in ("summary", "ca", "kr", "eu"):
        assert key in report, f"missing key: {key}"


def test_summary_per_sub_kb_keys():
    report = mod.build_unified_report()
    s = report["summary"]
    assert "coverage_pct" in s["ca"]
    assert "edges_total" in s["kr"]
    assert "coverage_pct" in s["eu"]


def test_ca_summary_consistent_with_full_report():
    report = mod.build_unified_report()
    assert report["summary"]["ca"]["total_indexed"] == report["ca"]["total"]["indexed"]
    assert report["summary"]["ca"]["coverage_pct"] == report["ca"]["total"]["coverage_pct"]


def test_eu_summary_consistent_with_full_report():
    report = mod.build_unified_report()
    assert report["summary"]["eu"]["coverage_pct"] == report["eu"]["coverage_pct"]
    assert report["summary"]["eu"]["case_refs"] == report["eu"]["case_refs"]
