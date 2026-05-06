#!/usr/bin/env python3
"""Evaluate the local data-protection-agent runner on golden-set questions."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_data_protection_agent import META_FILENAME, RESULT_FILENAME, generate_outputs


DEFAULT_CONFIG = ROOT / "config" / "golden-set.json"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "golden-set"
REQUIRED_META_KEYS = {
    "summary",
    "research_mode",
    "jurisdictions",
    "domains",
    "issue_map",
    "key_findings",
    "sources",
    "coverage_gaps",
    "error",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in cleaned.split("-") if part)[:100] or "case"


def authority_ids(meta: dict[str, Any]) -> set[str]:
    return {source.get("authority_id", "") for source in meta.get("sources", [])}


def validate_case(case: dict[str, Any], meta: dict[str, Any], result_path: Path, meta_path: Path) -> list[str]:
    errors: list[str] = []
    missing_keys = sorted(REQUIRED_META_KEYS - set(meta))
    if missing_keys:
        errors.append(f"meta missing keys: {', '.join(missing_keys)}")
    if not result_path.exists():
        errors.append(f"missing {RESULT_FILENAME}")
    if not meta_path.exists():
        errors.append(f"missing {META_FILENAME}")
    if meta.get("error") is not None:
        errors.append(f"meta error is not null: {meta.get('error')}")
    if meta.get("research_mode") != case.get("expected_mode"):
        errors.append(f"mode {meta.get('research_mode')} != {case.get('expected_mode')}")
    if sorted(meta.get("jurisdictions", [])) != sorted(case.get("expected_jurisdictions", [])):
        errors.append(f"jurisdictions {meta.get('jurisdictions')} != {case.get('expected_jurisdictions')}")
    if len(meta.get("sources", [])) < int(case.get("min_sources", 1)):
        errors.append(f"sources {len(meta.get('sources', []))} < {case.get('min_sources')}")
    if not meta.get("issue_map"):
        errors.append("issue_map is empty")
    if not meta.get("key_findings"):
        errors.append("key_findings is empty")

    ids = authority_ids(meta)
    for expected in case.get("must_include", []):
        if expected not in ids:
            errors.append(f"missing expected authority {expected}")
    for group in case.get("must_include_any", []):
        if not any(expected in ids for expected in group):
            errors.append(f"missing one of expected authorities {group}")
    for forbidden in case.get("forbidden_authority_ids", []):
        if forbidden in ids:
            errors.append(f"forbidden authority present {forbidden}")

    for source in meta.get("sources", []):
        local_path = source.get("local_path")
        if local_path and not (ROOT / local_path).exists():
            errors.append(f"source local_path missing for {source.get('authority_id')}: {local_path}")
        if not source.get("grade"):
            errors.append(f"source grade missing for {source.get('authority_id')}")

    return errors


def evaluate(config_path: Path, output_dir: Path, *, top_k: int | None = None, clean: bool = False) -> dict[str, Any]:
    config = read_json(config_path)
    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    case_reports = []
    default_top_k = int(top_k or config.get("default_top_k", 14))
    for case in config.get("cases", []):
        case_dir = output_dir / slug(case["id"])
        generated = generate_outputs(case["question"], case_dir, top_k=int(case.get("top_k", default_top_k)))
        result_path = Path(generated["result_path"])
        meta_path = Path(generated["meta_path"])
        meta = read_json(meta_path)
        errors = validate_case(case, meta, result_path, meta_path)
        case_reports.append({
            "id": case["id"],
            "question": case["question"],
            "status": "pass" if not errors else "fail",
            "errors": errors,
            "research_mode": meta.get("research_mode"),
            "jurisdictions": meta.get("jurisdictions", []),
            "source_count": len(meta.get("sources", [])),
            "authority_ids": sorted(authority_ids(meta)),
            "result_path": str(result_path),
            "meta_path": str(meta_path),
        })

    passed = sum(1 for report in case_reports if report["status"] == "pass")
    failed = len(case_reports) - passed
    report = {
        "type": "golden_set_report",
        "config_path": str(config_path),
        "output_dir": str(output_dir),
        "count": len(case_reports),
        "passed": passed,
        "failed": failed,
        "status": "pass" if failed == 0 else "fail",
        "cases": case_reports,
    }
    (output_dir / "golden-set-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print full JSON report instead of one-line summary.")
    args = parser.parse_args()

    report = evaluate(args.config, args.output_dir, top_k=args.top_k, clean=args.clean)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"golden-set {report['status']}: {report['passed']}/{report['count']} passed; report={args.output_dir / 'golden-set-report.json'}")
        if report["failed"]:
            for case in report["cases"]:
                if case["status"] == "fail":
                    print(f"FAIL {case['id']}: {'; '.join(case['errors'])}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
