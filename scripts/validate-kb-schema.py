#!/usr/bin/env python3
"""Validate KB index files against expected schemas.

Fails fast when a sub-KB index drifts from expected structure (e.g.,
sibling PIPA-expert / GDPR-expert refactors a JSON schema). Each schema
declares the container key and required fields per item.

Usage:
    python3 scripts/validate-kb-schema.py
    python3 scripts/validate-kb-schema.py --json
    python3 scripts/validate-kb-schema.py --strict   # exit 1 on any error
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Schema per index file. container_key tells us where to find the item list;
# required_fields are checked on every item.
SCHEMAS: dict[str, dict[str, Any]] = {
    # CA sub-KB (sources/us-ca/index/)
    "sources/us-ca/index/ca-statute-index.json": {
        "container": "items",
        "required": ["id", "citation", "title", "path", "source_grade"],
    },
    "sources/us-ca/index/ca-adjacent-statute-index.json": {
        "container": "items",
        "required": ["id", "citation", "title", "path", "source_family"],
    },
    "sources/us-ca/index/ca-regulation-index.json": {
        "container": "items",
        "required": ["id", "citation", "title", "path"],
    },
    "sources/us-ca/index/ca-case-index.json": {
        "container": "cases",
        "required": ["id", "case_name", "court", "precedential_status",
                     "source_family", "source_grade", "path"],
    },
    "sources/us-ca/index/ca-enforcement-index.json": {
        "container": "items",
        "required": ["id", "agency", "matter_name"],
    },
    "sources/us-ca/index/ca-topic-index.json": {
        "container": "topics",
        "required": ["id", "title", "summary", "primary_authorities"],
    },
    "sources/us-ca/index/golden-questions.ca.json": {
        "container": "questions",
        "required": ["id", "topic_id", "question", "expected_authorities"],
    },

    # KR sub-KB (kb/kr-pipa/index/)
    "kb/kr-pipa/index/article-index.json": {
        "container": "articles",
        "required": ["id", "law", "article", "path", "source_grade"],
    },
    "kb/kr-pipa/index/guideline-index.json": {
        "container": "guidelines",
        "required": ["id", "slug", "source_grade"],
    },
    "kb/kr-pipa/index/external-law-candidates.json": {
        "container": "candidates",
        "required": ["law", "reference_count", "priority_tier"],
    },

    # EU sub-KB (kb/eu-gdpr/index/)
    "kb/eu-gdpr/index/article-index.json": {
        "container": "articles",
        "required": ["id", "law", "article", "path"],
    },
    "kb/eu-gdpr/index/recital-index.json": {
        "container": "recitals",
        "required": ["id"],
    },
    "kb/eu-gdpr/index/case-index.json": {
        "container": "cases",
        "required": ["id", "slug", "case_number", "ecli", "path", "gdpr_articles"],
    },
    "kb/eu-gdpr/index/edpb-document-index.json": {
        "container": "documents",
        "required": ["id", "slug", "document_number", "document_type", "path"],
    },
}


def validate_index(rel_path: str, schema: dict[str, Any]) -> tuple[int, int, list[str]]:
    """Returns (item_count, missing_field_count, sample_errors)."""
    full_path = PROJECT_ROOT / rel_path
    if not full_path.exists():
        return (0, 0, [f"{rel_path}: file does not exist"])
    data = json.loads(full_path.read_text(encoding="utf-8"))
    items = data.get(schema["container"], [])
    if not isinstance(items, list):
        return (0, 1, [f"{rel_path}: container '{schema['container']}' is not a list"])
    missing = 0
    errors: list[str] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            missing += 1
            if len(errors) < 10:
                errors.append(f"{rel_path}: item[{i}] is not a dict")
            continue
        for field in schema["required"]:
            if field not in item:
                missing += 1
                if len(errors) < 10:
                    errors.append(f"{rel_path}: item[{i}] missing '{field}'")
    return (len(items), missing, errors)


def build_report() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    total_items = 0
    total_missing = 0
    files_with_errors = 0
    for rel_path, schema in SCHEMAS.items():
        item_count, missing_count, errors = validate_index(rel_path, schema)
        results.append({
            "path": rel_path,
            "items": item_count,
            "missing_field_count": missing_count,
            "sample_errors": errors,
            "ok": missing_count == 0,
        })
        total_items += item_count
        total_missing += missing_count
        if missing_count > 0:
            files_with_errors += 1
    return {
        "total_files_validated": len(SCHEMAS),
        "total_items": total_items,
        "total_missing_fields": total_missing,
        "files_with_errors": files_with_errors,
        "results": results,
    }


def print_report(report: dict[str, Any]) -> None:
    print("=== KB schema validation ===")
    print()
    print(f"Files validated: {report['total_files_validated']}")
    print(f"Total items: {report['total_items']}")
    print(f"Total missing fields: {report['total_missing_fields']}")
    print(f"Files with errors: {report['files_with_errors']}")
    print()
    print("Per-file results:")
    print(f"  {'path':70s} {'items':>6s} {'missing':>8s} {'status':>6s}")
    for r in report["results"]:
        status = "ok" if r["ok"] else "FAIL"
        print(f"  {r['path']:70s} {r['items']:>6d} {r['missing_field_count']:>8d} {status:>6s}")
    if report["total_missing_fields"] > 0:
        print()
        print("Sample errors (up to 10 per file):")
        for r in report["results"]:
            if r["sample_errors"]:
                print(f"  {r['path']}:")
                for err in r["sample_errors"]:
                    print(f"    {err}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 on any schema violation")
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)
    if args.strict and report["files_with_errors"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
