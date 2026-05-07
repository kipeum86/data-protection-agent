#!/usr/bin/env python3
"""Compare two unified-authority-index.json snapshots.

Reports per-(jurisdiction, authority_group) counts of authorities added
and removed between baseline and current. Useful when sibling
PIPA-expert / GDPR-expert KB updates land via import_namespaced_kbs.

Identifier: uses 'path' field as the stable key (id is None for KR/EU
in unified index). Falls back to id, then label.

Usage:
    python3 scripts/kb-diff.py baseline.json current.json
    python3 scripts/kb-diff.py baseline.json current.json --json

Tip: snapshot before update with
    cp index/unified-authority-index.json /tmp/before.json
    python3 scripts/import_namespaced_kbs.py --clean
    python3 scripts/kb-diff.py /tmp/before.json index/unified-authority-index.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_authorities(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("authorities", [])


def authority_key(a: dict[str, Any]) -> str:
    """Returns a stable key for diffing. Falls back through path → id → label."""
    return a.get("path") or a.get("id") or a.get("label") or ""


def group_label(a: dict[str, Any]) -> tuple[str, str]:
    return (a.get("jurisdiction", "?"), a.get("authority_group", "?"))


def diff_snapshots(baseline_path: Path, current_path: Path) -> dict[str, Any]:
    base = load_authorities(baseline_path)
    curr = load_authorities(current_path)

    base_keys: set[str] = set()
    base_groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    for a in base:
        k = authority_key(a)
        if not k:
            continue
        base_keys.add(k)
        base_groups[group_label(a)].add(k)

    curr_keys: set[str] = set()
    curr_groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    for a in curr:
        k = authority_key(a)
        if not k:
            continue
        curr_keys.add(k)
        curr_groups[group_label(a)].add(k)

    added = curr_keys - base_keys
    removed = base_keys - curr_keys
    unchanged = base_keys & curr_keys

    by_group: list[dict[str, Any]] = []
    all_groups = set(base_groups.keys()) | set(curr_groups.keys())
    for g in sorted(all_groups):
        b = base_groups.get(g, set())
        c = curr_groups.get(g, set())
        by_group.append({
            "jurisdiction": g[0],
            "authority_group": g[1],
            "baseline_count": len(b),
            "current_count": len(c),
            "added": len(c - b),
            "removed": len(b - c),
        })

    return {
        "baseline_total": len(base),
        "current_total": len(curr),
        "added_count": len(added),
        "removed_count": len(removed),
        "unchanged_count": len(unchanged),
        "added_samples": sorted(added)[:10],
        "removed_samples": sorted(removed)[:10],
        "by_group": by_group,
    }


def print_report(report: dict[str, Any]) -> None:
    print("=== KB diff report ===")
    print()
    print(f"Baseline total: {report['baseline_total']}")
    print(f"Current total:  {report['current_total']}")
    print(f"Added:     {report['added_count']}")
    print(f"Removed:   {report['removed_count']}")
    print(f"Unchanged: {report['unchanged_count']}")
    print()
    print("Per-group breakdown:")
    print(
        f"  {'jurisdiction':12s} {'group':25s} "
        f"{'base':>6s} {'curr':>6s} {'+added':>7s} {'-removed':>9s}"
    )
    for g in report["by_group"]:
        print(
            f"  {g['jurisdiction']:12s} {g['authority_group']:25s} "
            f"{g['baseline_count']:>6d} {g['current_count']:>6d} "
            f"{g['added']:>7d} {g['removed']:>9d}"
        )
    if report["added_samples"]:
        print()
        print("Added samples (up to 10):")
        for s in report["added_samples"]:
            print(f"  + {s}")
    if report["removed_samples"]:
        print()
        print("Removed samples (up to 10):")
        for s in report["removed_samples"]:
            print(f"  - {s}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", help="Path to baseline unified-authority-index.json")
    parser.add_argument("current", help="Path to current unified-authority-index.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = diff_snapshots(Path(args.baseline), Path(args.current))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
