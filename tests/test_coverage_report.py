"""Unit tests for the CA authority coverage report."""

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "coverage-report.py"

# coverage-report.py has a hyphen in its name so cannot be imported normally.
spec = importlib.util.spec_from_file_location("coverage_report", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_build_report_returns_expected_keys():
    report = mod.build_report()
    for key in ("total", "families", "most_cited", "uncited_samples"):
        assert key in report, f"missing key: {key}"


def test_per_family_breakdown_includes_5_families():
    report = mod.build_report()
    expected = {"statute", "adjacent_statute", "regulation", "case", "enforcement"}
    actual = set(report["families"].keys())
    assert expected.issubset(actual), f"missing families: {expected - actual}"


def test_total_coverage_pct_is_in_range():
    report = mod.build_report()
    pct = report["total"]["coverage_pct"]
    assert 0 <= pct <= 100, f"coverage_pct out of range: {pct}"


def test_most_cited_sorted_descending():
    report = mod.build_report()
    counts = [entry["count"] for entry in report["most_cited"]]
    assert counts == sorted(counts, reverse=True), "most_cited not sorted descending"


def test_each_family_has_consistent_counts():
    """uncited_count + cited_in_golden_or_topic should equal indexed."""
    report = mod.build_report()
    for family, info in report["families"].items():
        assert info["uncited_count"] + info["cited_in_golden_or_topic"] == info["indexed"], (
            f"{family}: counts inconsistent"
        )
