"""End-to-end integration test for the full auditor + dev tools stack.

Verifies that the unified system works on representative inputs:
1. unified_auditor.audit_unified() handles complex multi-finding text
2. CLI smoke (subprocess) for all 5 auditor entry points
3. All 3 coverage reports' build_report() functions return well-formed data
4. coverage-report-all + who-cites smoke
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_module(alias: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(alias, PROJECT_ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


# === Unified auditor: in-process ===


def test_unified_audit_handles_clean_ca_only_answer():
    from unified_auditor.run import audit_unified
    text = (
        "Under CCPA (Cal. Civ. Code § 1798.150), consumers have a private "
        "right of action for data breaches. The business must comply per "
        "ca-civ-1798.100."
    )
    result = audit_unified(text)
    assert result["status"] in {"pass", "warn"}, (
        f"unexpected status: {result['status']}, findings: {result['findings']}"
    )


def test_unified_audit_catches_invalid_id_and_cross_juris():
    """Multi-issue text: invalid CA citation + GDPR ref in CCPA-only context."""
    from unified_auditor.run import audit_unified
    text = (
        "Under CCPA, see Cal. Civ. Code § 1798.999 for the rule. "
        "GDPR Article 6 also applies (per gdpr-art6)."
    )
    result = audit_unified(text)
    assert result["status"] == "fail"
    ca_findings = [f for f in result["findings"] if f["auditor"] == "us-ca"]
    assert any("ca-civ-1798.999" in f.get("message", "") for f in ca_findings)
    cross_findings = [
        f for f in result["findings"] if f["auditor"] == "cross-jurisdiction"
    ]
    assert cross_findings


def test_unified_audit_per_auditor_keys_present():
    from unified_auditor.run import audit_unified
    result = audit_unified("generic text")
    for name in ("us-ca", "kr-pipa", "eu-gdpr", "cross-jurisdiction"):
        assert name in result["per_auditor"], f"missing auditor: {name}"


# === CLI smoke (subprocess) ===


def _run_cli(rel_path: str, stdin_text: str) -> int:
    proc = subprocess.run(
        ["python3", str(PROJECT_ROOT / rel_path)],
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    return proc.returncode


def test_ca_cli_exits_0_on_clean_input():
    rc = _run_cli(
        "sources/us-ca/scripts/audit-california-citations.py",
        "Cal. Civ. Code § 1798.150 grants a private right of action.",
    )
    assert rc == 0


def test_ca_cli_exits_1_on_invalid_citation():
    rc = _run_cli(
        "sources/us-ca/scripts/audit-california-citations.py",
        "Cal. Civ. Code § 1798.999 is the rule.",
    )
    assert rc == 1


def test_eu_cli_exits_0_on_clean_input():
    rc = _run_cli(
        "sources/eu-gdpr/scripts/audit-europe-citations.py",
        "GDPR Article 6 sets lawful bases.",
    )
    assert rc == 0


def test_kr_cli_exits_0_on_clean_input():
    rc = _run_cli(
        "sources/kr-pipa/scripts/audit-korea-citations.py",
        "개인정보 보호법 제15조에 따라 동의를 받는다.",
    )
    assert rc == 0


def test_unified_cli_exits_0_on_clean_input():
    rc = _run_cli(
        "scripts/audit-unified.py",
        "Cal. Civ. Code § 1798.150 grants a private right of action.",
    )
    assert rc == 0


def test_unified_cli_exits_1_on_fail():
    rc = _run_cli(
        "scripts/audit-unified.py",
        "Cal. Civ. Code § 1798.999 is the rule.",
    )
    assert rc == 1


# === Coverage reports + dev tools ===


def test_ca_coverage_report_builds():
    mod = _load_module("ca_cov_v14", "scripts/coverage-report.py")
    report = mod.build_report()
    assert report["total"]["indexed"] > 0


def test_kr_coverage_report_builds():
    mod = _load_module("kr_cov_v14", "scripts/coverage-report-kr.py")
    report = mod.build_report()
    assert report["total_indexed_articles"] > 0


def test_eu_coverage_report_builds():
    mod = _load_module("eu_cov_v14", "scripts/coverage-report-eu.py")
    report = mod.build_report()
    assert report["total_indexed_articles"] > 0


def test_coverage_all_dashboard_builds():
    mod = _load_module("cov_all_v14", "scripts/coverage-report-all.py")
    report = mod.build_unified_report()
    assert "summary" in report
    assert all(k in report["summary"] for k in ("ca", "kr", "eu"))


def test_who_cites_returns_eu_results():
    mod = _load_module("who_cites_v14b", "scripts/who-cites.py")
    result = mod.who_cites("gdpr-art6")
    assert result["total_citations"] > 0
