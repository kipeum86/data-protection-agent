"""Unit tests for KB schema validation."""

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate-kb-schema.py"

spec = importlib.util.spec_from_file_location("validate_kb_schema", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_build_report_returns_expected_keys():
    report = mod.build_report()
    for key in ("total_files_validated", "total_items",
                "total_missing_fields", "files_with_errors", "results"):
        assert key in report


def test_all_known_indexes_validated():
    """SCHEMAS covers CA 7 + KR 3 + EU 4 = 14 index files."""
    assert len(mod.SCHEMAS) >= 14


def test_each_result_has_required_fields():
    report = mod.build_report()
    for r in report["results"]:
        for key in ("path", "items", "missing_field_count", "sample_errors", "ok"):
            assert key in r


def test_ca_statute_index_validates_clean():
    rel_path = "sources/us-ca/index/ca-statute-index.json"
    item_count, missing_count, errors = mod.validate_index(
        rel_path, mod.SCHEMAS[rel_path]
    )
    assert item_count > 0
    assert missing_count == 0, f"unexpected missing fields: {errors}"


def test_overall_baseline_clean():
    """v15 baseline: every defined schema must validate cleanly against the
    current KB. Failures here indicate either real schema drift or a stale
    SCHEMA definition that needs updating."""
    report = mod.build_report()
    failing = [r["path"] for r in report["results"] if not r["ok"]]
    assert not failing, f"schema drift detected: {failing}"
