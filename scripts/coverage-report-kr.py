#!/usr/bin/env python3
"""KR PIPA authority coverage report.

KR sub-KB has no golden_questions / topic-index (unlike CA). Instead the
cross-reference-graph.json captures article-to-article references. This
report shows:
  - article inventory by law family
  - cross-reference density (which articles reference others)
  - external-law candidates (laws referenced but not in local KB)
  - top-cited articles (by being referenced from elsewhere)

Usage:
    python3 scripts/coverage-report-kr.py
    python3 scripts/coverage-report-kr.py --json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = PROJECT_ROOT / "kb" / "kr-pipa" / "index"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((INDEX_DIR / name).read_text(encoding="utf-8"))


def collect_inventory() -> dict[str, set[str]]:
    """Returns {family: set_of_article_ids} per KR law family."""
    article_idx = load_json("article-index.json")
    by_family: dict[str, set[str]] = {}
    for art in article_idx.get("articles", []):
        aid = art.get("id", "")
        if not aid or "-art" not in aid:
            continue
        family = aid.rsplit("-art", 1)[0]
        by_family.setdefault(family, set()).add(aid)
    return by_family


def collect_outgoing_references() -> Counter:
    """Returns Counter of from_path -> outgoing reference count.

    Each cross-reference-graph edge records one article->article reference.
    """
    graph = load_json("cross-reference-graph.json")
    counts: Counter = Counter()
    for edge in graph.get("edges", []):
        path = edge.get("from_path", "")
        if path:
            counts[path] += 1
    return counts


def collect_external_law_summary() -> dict[str, Any]:
    cands = load_json("external-law-candidates.json")
    items = cands.get("candidates", [])
    return {
        "total": len(items),
        "high_priority": cands.get("high_priority_count", 0),
        "medium_priority": cands.get("medium_priority_count", 0),
        "low_priority": cands.get("low_priority_count", 0),
        "top": [
            {"law": c["law"], "reference_count": c.get("reference_count", 0)}
            for c in sorted(
                items, key=lambda c: c.get("reference_count", 0), reverse=True
            )[:10]
        ],
    }


def build_report() -> dict[str, Any]:
    by_family = collect_inventory()
    out_refs = collect_outgoing_references()
    external = collect_external_law_summary()
    total_indexed = sum(len(ids) for ids in by_family.values())

    return {
        "total_indexed_articles": total_indexed,
        "families": {
            family: {"indexed": len(ids)}
            for family, ids in sorted(by_family.items())
        },
        "edges_total": sum(out_refs.values()),
        "edges_unique_sources": len(out_refs),
        "top_referencing_articles": [
            {"path": p, "outgoing_refs": n}
            for p, n in out_refs.most_common(10)
        ],
        "external_law_candidates": external,
    }


def print_report(report: dict[str, Any]) -> None:
    print("=== KR PIPA authority coverage report ===")
    print()
    print(f"Total indexed articles: {report['total_indexed_articles']}")
    print(
        f"Cross-reference edges: {report['edges_total']} from "
        f"{report['edges_unique_sources']} unique articles"
    )
    print()
    print("Per-family breakdown:")
    print(f"  {'family':45s} {'indexed':>8s}")
    for family, info in report["families"].items():
        print(f"  {family:45s} {info['indexed']:>8d}")
    print()
    print("Top referencing articles (most outgoing cross-refs):")
    for entry in report["top_referencing_articles"]:
        print(f"  {entry['path']:55s} -> {entry['outgoing_refs']} refs")
    print()
    ext = report["external_law_candidates"]
    print(f"External law candidates: {ext['total']}")
    print(f"  high  : {ext['high_priority']}")
    print(f"  medium: {ext['medium_priority']}")
    print(f"  low   : {ext['low_priority']}")
    print()
    print("Top external laws (by reference count):")
    for entry in ext["top"]:
        print(f"  {entry['law']:50s} {entry['reference_count']}")


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
