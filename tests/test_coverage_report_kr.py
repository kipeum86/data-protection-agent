"""Unit tests for the KR PIPA authority coverage report."""

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "coverage-report-kr.py"

spec = importlib.util.spec_from_file_location("coverage_report_kr", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_build_report_returns_expected_keys():
    report = mod.build_report()
    for key in (
        "total_indexed_articles",
        "families",
        "edges_total",
        "edges_unique_sources",
        "top_referencing_articles",
        "external_law_candidates",
    ):
        assert key in report, f"missing key: {key}"


def test_total_indexed_matches_family_sum():
    report = mod.build_report()
    family_sum = sum(info["indexed"] for info in report["families"].values())
    assert report["total_indexed_articles"] == family_sum


def test_external_law_priority_sums_to_total():
    report = mod.build_report()
    ext = report["external_law_candidates"]
    assert ext["high_priority"] + ext["medium_priority"] + ext["low_priority"] == ext["total"]


def test_top_referencing_articles_bounded_by_edges_total():
    report = mod.build_report()
    top_sum = sum(e["outgoing_refs"] for e in report["top_referencing_articles"])
    assert top_sum <= report["edges_total"]
