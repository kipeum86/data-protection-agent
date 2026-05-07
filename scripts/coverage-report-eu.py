#!/usr/bin/env python3
"""EU GDPR authority coverage report.

EU sub-KB has no golden_questions. Instead, case-index and edpb-document-index
both carry a `gdpr_articles` field listing articles each case/document
references. This report shows:
  - article inventory by act (GDPR / EU AI Act / Data Act / etc.)
  - articles referenced by case law (CJEU + General Court)
  - articles referenced by EDPB documents (guideline / opinion / etc.)
  - top-cited articles across cases + EDPB combined
  - articles never referenced (gaps)

Usage:
    python3 scripts/coverage-report-eu.py
    python3 scripts/coverage-report-eu.py --json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = PROJECT_ROOT / "kb" / "eu-gdpr" / "index"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((INDEX_DIR / name).read_text(encoding="utf-8"))


def collect_inventory() -> dict[str, set[str]]:
    """Returns {act_family: set_of_article_ids}."""
    article_idx = load_json("article-index.json")
    by_family: dict[str, set[str]] = {}
    for art in article_idx.get("articles", []):
        aid = art.get("id", "")
        if not aid or "-art" not in aid:
            continue
        family = aid.rsplit("-art", 1)[0]
        by_family.setdefault(family, set()).add(aid)
    return by_family


_ART_NUMBER_RE = re.compile(r"^(?:Art(?:icle|\.)?\s*)?(\d+)", re.I)


def normalize_ref(ref: str) -> str:
    """Normalize a gdpr_articles entry to a canonical id form.

    The gdpr_articles field uses several forms:
      'gdpr-art6'         → unchanged
      'eu-ai-act-art5'    → unchanged
      '6'                 → 'gdpr-art6'
      '13.2'              → 'gdpr-art13' (paragraph dropped)
      'Art. 9'            → 'gdpr-art9'
      'Article 25'        → 'gdpr-art25'
      'Art. 6(1)(f)'      → 'gdpr-art6' (subpoint dropped)
    """
    s = str(ref).strip()
    if "-art" in s:
        return s
    m = _ART_NUMBER_RE.match(s)
    if m:
        return f"gdpr-art{m.group(1)}"
    return s


def collect_article_references() -> Counter:
    """Returns Counter of normalized_article_id -> reference count from cases + EDPB."""
    counts: Counter = Counter()
    for case in load_json("case-index.json").get("cases", []):
        for art in case.get("gdpr_articles", []):
            counts[normalize_ref(art)] += 1
    for doc in load_json("edpb-document-index.json").get("documents", []):
        for art in doc.get("gdpr_articles", []):
            counts[normalize_ref(art)] += 1
    return counts


def build_report() -> dict[str, Any]:
    inventory = collect_inventory()
    refs = collect_article_references()

    all_indexed: set[str] = set()
    for ids in inventory.values():
        all_indexed.update(ids)
    referenced_in_index = set(refs.keys()) & all_indexed
    uncited = sorted(all_indexed - set(refs.keys()))

    case_refs = sum(
        len(c.get("gdpr_articles", []))
        for c in load_json("case-index.json").get("cases", [])
    )
    edpb_refs = sum(
        len(d.get("gdpr_articles", []))
        for d in load_json("edpb-document-index.json").get("documents", [])
    )

    return {
        "total_indexed_articles": len(all_indexed),
        "total_referenced": len(referenced_in_index),
        "coverage_pct": round(100 * len(referenced_in_index) / len(all_indexed), 1)
        if all_indexed
        else 0,
        "families": {
            family: {
                "indexed": len(ids),
                "referenced": len(ids & set(refs.keys())),
                "uncited": len(ids - set(refs.keys())),
            }
            for family, ids in sorted(inventory.items())
        },
        "total_reference_edges": sum(refs.values()),
        "case_refs": case_refs,
        "edpb_refs": edpb_refs,
        "most_cited": [
            {"id": aid, "count": n} for aid, n in refs.most_common(15)
        ],
        "uncited_samples": uncited[:15],
    }


def print_report(report: dict[str, Any]) -> None:
    print("=== EU GDPR authority coverage report ===")
    print()
    print(f"Total indexed articles: {report['total_indexed_articles']}")
    print(f"Referenced by cases + EDPB: {report['total_referenced']}")
    print(f"Coverage: {report['coverage_pct']}%")
    print(
        f"Reference edges: {report['total_reference_edges']} "
        f"(cases: {report['case_refs']}, EDPB: {report['edpb_refs']})"
    )
    print()
    print("Per-act breakdown:")
    print(f"  {'act':30s} {'indexed':>8s}  {'cited':>6s}  {'uncited':>8s}")
    for family, info in report["families"].items():
        print(
            f"  {family:30s} {info['indexed']:>8d}  {info['referenced']:>6d}  "
            f"{info['uncited']:>8d}"
        )
    print()
    print("Most-cited articles (top 15):")
    for entry in report["most_cited"]:
        print(f"  {entry['id']:30s} {entry['count']}")
    print()
    print("Uncited samples (up to 15):")
    for aid in report["uncited_samples"]:
        print(f"  {aid}")


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
