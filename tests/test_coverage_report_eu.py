"""Unit tests for the EU GDPR authority coverage report."""

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "coverage-report-eu.py"

spec = importlib.util.spec_from_file_location("coverage_report_eu", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_build_report_returns_expected_keys():
    report = mod.build_report()
    for key in (
        "total_indexed_articles",
        "total_referenced",
        "coverage_pct",
        "families",
        "total_reference_edges",
        "case_refs",
        "edpb_refs",
        "most_cited",
        "uncited_samples",
    ):
        assert key in report, f"missing key: {key}"


def test_coverage_pct_in_range():
    report = mod.build_report()
    assert 0 <= report["coverage_pct"] <= 100


def test_each_family_referenced_uncited_sums_to_indexed():
    report = mod.build_report()
    for family, info in report["families"].items():
        assert info["referenced"] + info["uncited"] == info["indexed"], (
            f"{family}: counts inconsistent"
        )


def test_total_reference_edges_bounded_by_case_plus_edpb():
    """total_reference_edges may differ from case_refs + edpb_refs because
    normalize_ref() collapses paragraphs (e.g., '13.2' -> 'gdpr-art13'); but
    the sum of normalized refs must not exceed the raw case_refs + edpb_refs."""
    report = mod.build_report()
    assert report["total_reference_edges"] <= report["case_refs"] + report["edpb_refs"]


def test_most_cited_sorted_descending():
    report = mod.build_report()
    counts = [e["count"] for e in report["most_cited"]]
    assert counts == sorted(counts, reverse=True)


def test_normalize_ref_bare_number():
    assert mod.normalize_ref("6") == "gdpr-art6"
    assert mod.normalize_ref("13") == "gdpr-art13"


def test_normalize_ref_full_id_unchanged():
    assert mod.normalize_ref("gdpr-art6") == "gdpr-art6"
    assert mod.normalize_ref("eu-ai-act-art5") == "eu-ai-act-art5"


def test_normalize_ref_art_dot_form():
    """gdpr_articles often uses 'Art. 9' or 'Art. 6(1)(f)' forms."""
    assert mod.normalize_ref("Art. 9") == "gdpr-art9"
    assert mod.normalize_ref("Article 25") == "gdpr-art25"
    assert mod.normalize_ref("Art. 6(1)(f)") == "gdpr-art6"
    assert mod.normalize_ref("Art. 5(1)(a)") == "gdpr-art5"
