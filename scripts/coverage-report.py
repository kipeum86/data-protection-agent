#!/usr/bin/env python3
"""CA authority coverage report.

Shows which authorities are most/least cited by golden questions and the
topic index, and which indexed authorities have zero coverage. Useful
for spotting gaps in the test/seed corpus.

Usage:
    python3 scripts/coverage-report.py
    python3 scripts/coverage-report.py --json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = PROJECT_ROOT / "sources" / "us-ca" / "index"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((INDEX_DIR / name).read_text(encoding="utf-8"))


def collect_authority_counts() -> Counter:
    """Returns Counter of authority_id -> citation count from golden questions
    and from topic-index primary/supporting/cases."""
    counts: Counter = Counter()
    gq = load_json("golden-questions.ca.json")
    for q in gq.get("questions", []):
        for auth in q.get("expected_authorities", []) + q.get("supporting_authorities", []):
            aid = auth.get("id")
            if aid:
                counts[aid] += 1
    ti = load_json("ca-topic-index.json")
    for topic in ti.get("topics", []):
        for key in ("primary_authorities", "supporting_authorities", "cases"):
            for auth in topic.get(key, []):
                aid = auth.get("id")
                if aid:
                    counts[aid] += 1
    return counts


def collect_indexed_authorities() -> dict[str, set[str]]:
    """Returns {family_name: set_of_authority_ids} from each CA sub-index."""
    return {
        "statute": {s["id"] for s in load_json("ca-statute-index.json").get("items", [])},
        "adjacent_statute": {s["id"] for s in load_json("ca-adjacent-statute-index.json").get("items", [])},
        "regulation": {r["id"] for r in load_json("ca-regulation-index.json").get("items", [])},
        "case": {c["id"] for c in load_json("ca-case-index.json").get("cases", [])},
        "enforcement": {e["id"] for e in load_json("ca-enforcement-index.json").get("items", [])},
    }


def build_report() -> dict[str, Any]:
    counts = collect_authority_counts()
    indexed = collect_indexed_authorities()
    cited = set(counts.keys())

    families: dict[str, dict[str, Any]] = {}
    uncited_samples: dict[str, list[str]] = {}
    total_indexed = 0
    total_cited = 0
    for family, ids in indexed.items():
        family_cited = ids & cited
        families[family] = {
            "indexed": len(ids),
            "cited_in_golden_or_topic": len(family_cited),
            "coverage_pct": round(100 * len(family_cited) / len(ids), 1) if ids else 0,
            "uncited_count": len(ids - cited),
        }
        uncited_samples[family] = sorted(ids - cited)[:10]
        total_indexed += len(ids)
        total_cited += len(family_cited)

    return {
        "total": {
            "indexed": total_indexed,
            "cited": total_cited,
            "coverage_pct": round(100 * total_cited / total_indexed, 1) if total_indexed else 0,
        },
        "families": families,
        "most_cited": [
            {"id": aid, "count": n} for aid, n in counts.most_common(15)
        ],
        "uncited_samples": uncited_samples,
    }


def print_report(report: dict[str, Any]) -> None:
    print("=== CA authority coverage report ===")
    print()
    print(f"Total indexed authorities: {report['total']['indexed']}")
    print(f"Cited in golden questions or topic index: {report['total']['cited']}")
    print(f"Coverage: {report['total']['coverage_pct']}%")
    print()
    print("Per-family breakdown:")
    print(f"  {'family':25s} {'indexed':>8s}  {'cited':>6s}  {'coverage':>9s}  {'uncited':>8s}")
    for family, info in report["families"].items():
        print(
            f"  {family:25s} {info['indexed']:>8d}  {info['cited_in_golden_or_topic']:>6d}  "
            f"{info['coverage_pct']:>8.1f}%  {info['uncited_count']:>8d}"
        )
    print()
    print("Most-cited (top 15):")
    for entry in report["most_cited"]:
        print(f"  {entry['id']:35s} {entry['count']}")
    print()
    print("Uncited samples (per family, up to 10 each):")
    for family, samples in report["uncited_samples"].items():
        if not samples:
            continue
        print(f"  {family}:")
        for s in samples:
            print(f"    {s}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
