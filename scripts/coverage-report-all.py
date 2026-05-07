#!/usr/bin/env python3
"""Unified coverage report for CA + KR + EU sub-KBs.

Imports build_report() from each per-jurisdiction coverage script and
renders a combined summary plus optional per-sub-KB sections.

Usage:
    python3 scripts/coverage-report-all.py            # summary
    python3 scripts/coverage-report-all.py --verbose  # full per-sub-KB sections
    python3 scripts/coverage-report-all.py --json     # JSON output
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_module(alias: str, path: Path):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


def build_unified_report() -> dict[str, Any]:
    ca_mod = _load_module("ca_cov_v13", PROJECT_ROOT / "scripts" / "coverage-report.py")
    kr_mod = _load_module("kr_cov_v13", PROJECT_ROOT / "scripts" / "coverage-report-kr.py")
    eu_mod = _load_module("eu_cov_v13", PROJECT_ROOT / "scripts" / "coverage-report-eu.py")

    ca = ca_mod.build_report()
    kr = kr_mod.build_report()
    eu = eu_mod.build_report()

    summary = {
        "ca": {
            "total_indexed": ca["total"]["indexed"],
            "cited": ca["total"]["cited"],
            "coverage_pct": ca["total"]["coverage_pct"],
        },
        "kr": {
            "total_articles": kr["total_indexed_articles"],
            "edges_total": kr["edges_total"],
            "edges_unique_sources": kr["edges_unique_sources"],
            "external_law_total": kr["external_law_candidates"]["total"],
        },
        "eu": {
            "total_articles": eu["total_indexed_articles"],
            "referenced": eu["total_referenced"],
            "coverage_pct": eu["coverage_pct"],
            "case_refs": eu["case_refs"],
            "edpb_refs": eu["edpb_refs"],
        },
    }
    return {"summary": summary, "ca": ca, "kr": kr, "eu": eu}


def print_summary(report: dict[str, Any], verbose: bool = False) -> None:
    s = report["summary"]
    print("=== Unified KB coverage dashboard ===")
    print()
    print(
        f"CA  : {s['ca']['cited']}/{s['ca']['total_indexed']} authorities cited "
        f"({s['ca']['coverage_pct']}%)"
    )
    print(
        f"KR  : {s['kr']['total_articles']} articles, "
        f"{s['kr']['edges_total']} cross-ref edges from "
        f"{s['kr']['edges_unique_sources']} sources, "
        f"{s['kr']['external_law_total']} external-law candidates"
    )
    print(
        f"EU  : {s['eu']['referenced']}/{s['eu']['total_articles']} articles "
        f"referenced ({s['eu']['coverage_pct']}%); "
        f"{s['eu']['case_refs']} case refs + {s['eu']['edpb_refs']} EDPB refs"
    )
    if not verbose:
        return
    print()
    print("--- CA detail ---")
    for family, info in report["ca"]["families"].items():
        print(
            f"  {family:25s} indexed={info['indexed']:4d} "
            f"cited={info['cited_in_golden_or_topic']:4d} "
            f"({info['coverage_pct']}%)"
        )
    print()
    print("--- KR detail ---")
    for family, info in report["kr"]["families"].items():
        print(f"  {family:45s} indexed={info['indexed']:4d}")
    print()
    print("--- EU detail ---")
    for family, info in report["eu"]["families"].items():
        print(
            f"  {family:25s} indexed={info['indexed']:4d} "
            f"cited={info['referenced']:4d} uncited={info['uncited']:4d}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_unified_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_summary(report, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
