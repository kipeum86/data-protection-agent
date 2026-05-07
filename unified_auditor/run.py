#!/usr/bin/env python3
"""Unified citation auditor — runs all 4 auditors and aggregates findings.

Loads each sub-auditor module via importlib (avoids package-name collision
between sources/{us-ca,kr-pipa,eu-gdpr}/citation_auditor/*) and the
cross-jurisdiction auditor via normal import.

Replaces the SKILL.md 4-step dispatch with a single invocation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_auditors() -> list[tuple[str, Callable[[str], dict[str, Any]]]]:
    """Returns [(name, audit_fn), ...] for all 4 auditors."""
    auditors: list[tuple[str, Callable]] = []

    sub_kbs = [
        ("us-ca",
         "sources/us-ca/citation_auditor/california_citation.py",
         "ca_citation_v9"),
        ("kr-pipa",
         "sources/kr-pipa/citation_auditor/korea_citation.py",
         "kr_citation_v9"),
        ("eu-gdpr",
         "sources/eu-gdpr/citation_auditor/europe_citation.py",
         "eu_citation_v9"),
    ]
    for name, rel_path, mod_alias in sub_kbs:
        mod = _load_module(mod_alias, PROJECT_ROOT / rel_path)
        auditors.append((name, mod.audit))

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from cross_jurisdiction_auditor.audit import audit as cross_audit
    auditors.append(("cross-jurisdiction", cross_audit))

    return auditors


def audit_unified(text: str) -> dict[str, Any]:
    """Run all 4 auditors and aggregate findings.

    Returns:
      {
        "status": "fail" | "warn" | "pass",
        "per_auditor": {name: {"status": ..., "finding_count": N}},
        "findings": [{"auditor": ..., "severity": ..., ...}, ...],
        "finding_count": N,
      }
    """
    auditors = load_auditors()
    per_auditor: dict[str, dict[str, Any]] = {}
    all_findings: list[dict[str, Any]] = []

    for name, audit_fn in auditors:
        try:
            result = audit_fn(text)
        except Exception as exc:
            per_auditor[name] = {
                "status": "error",
                "finding_count": 0,
                "error": str(exc),
            }
            continue
        per_auditor[name] = {
            "status": result.get("status", "?"),
            "finding_count": len(result.get("findings", [])),
        }
        for finding in result.get("findings", []):
            all_findings.append({**finding, "auditor": name})

    if any(f.get("severity") == "error" for f in all_findings):
        status = "fail"
    elif all_findings:
        status = "warn"
    else:
        status = "pass"

    return {
        "status": status,
        "per_auditor": per_auditor,
        "findings": all_findings,
        "finding_count": len(all_findings),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Markdown file. Reads stdin if omitted.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    text = Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()
    result = audit_unified(text)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"=== Aggregate status: {result['status']} ({result['finding_count']} finding(s)) ===")
        print()
        print("Per-auditor:")
        for name, info in result["per_auditor"].items():
            extra = f"  error={info['error']}" if "error" in info else ""
            print(f"  {name:22s} status={info['status']:5s}  findings={info['finding_count']}{extra}")
        if result["findings"]:
            print()
            print("Findings:")
            for f in result["findings"]:
                print(f"  [{f['auditor']}] [{f['severity']}] {f['message']}")
                if f.get("citation"):
                    print(f"    citation: {f['citation']}")
                if f.get("suggested_fix"):
                    print(f"    fix: {f['suggested_fix']}")

    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
