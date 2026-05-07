#!/usr/bin/env python3
"""Reverse citation lookup: which corpora reference a given authority.

Given an authority id, search across:
  - CA golden-questions (expected_authorities + supporting_authorities)
  - CA topic-index (primary/supporting/cases per topic) + authority_to_topics
  - KR cross-reference-graph edges (article -> article)
  - EU case-index gdpr_articles
  - EU edpb-document-index gdpr_articles

Authority id prefix routes the search to the right sub-KB.

Usage:
    python3 scripts/who-cites.py ca-civ-1798.150
    python3 scripts/who-cites.py pipa-art15
    python3 scripts/who-cites.py gdpr-art6
    python3 scripts/who-cites.py ca-civ-1798.150 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CA_INDEX = PROJECT_ROOT / "sources" / "us-ca" / "index"
KR_INDEX = PROJECT_ROOT / "kb" / "kr-pipa" / "index"
EU_INDEX = PROJECT_ROOT / "kb" / "eu-gdpr" / "index"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


CA_PREFIXES = (
    "ca-civ-", "ca-bpc-", "ca-pen-", "ca-11-ccr-",
    "ca-supreme-", "ca-appeal-", "ca-oag-",
    "us-9th-", "us-fed-", "cppa-",
)
KR_PREFIXES = (
    "pipa", "network-act", "credit-info-act", "location-info-act",
    "e-government-act", "pipc-guideline", "kr-court",
)
EU_PREFIXES = (
    "gdpr", "eu-ai-act", "data-act", "data-governance-act",
    "eprivacy-directive", "a-precedent", "a-guideline", "a-opinion",
    "a-statement", "a-binding", "a-recommendation", "a-endorsement",
    "a-report",
)


def jurisdiction_for(aid: str) -> str:
    """Returns one of: us-ca, kr-pipa, eu-gdpr, unknown."""
    aid_l = aid.lower()
    if any(aid_l.startswith(p) for p in CA_PREFIXES):
        return "us-ca"
    if any(aid_l.startswith(p + "-") or aid_l == p for p in KR_PREFIXES):
        return "kr-pipa"
    if any(aid_l.startswith(p + "-") or aid_l == p for p in EU_PREFIXES):
        return "eu-gdpr"
    return "unknown"


def _ca_cites(aid: str) -> dict[str, Any]:
    citations: dict[str, Any] = {"golden_questions": [], "topics": []}
    gq = load_json(CA_INDEX / "golden-questions.ca.json")
    for q in gq.get("questions", []):
        for key in ("expected_authorities", "supporting_authorities"):
            for auth in q.get(key, []):
                if auth.get("id") == aid:
                    citations["golden_questions"].append({
                        "question_id": q.get("id"),
                        "question": q.get("question", "")[:80],
                        "role": key,
                    })

    ti = load_json(CA_INDEX / "ca-topic-index.json")
    for topic in ti.get("topics", []):
        for key in ("primary_authorities", "supporting_authorities", "cases"):
            for auth in topic.get(key, []):
                if auth.get("id") == aid:
                    citations["topics"].append({
                        "topic_id": topic.get("id"),
                        "role": key,
                    })
    a2t = ti.get("authority_to_topics", {})
    if aid in a2t:
        citations["authority_to_topics"] = a2t[aid]
    return citations


def _kr_cites(aid: str) -> dict[str, Any]:
    citations: dict[str, Any] = {"cross_reference_edges": []}
    graph = load_json(KR_INDEX / "cross-reference-graph.json")
    m = re.match(r"^(?P<family>.+?)-art(?P<num>.+)$", aid)
    if not m:
        return citations
    target_path = f"library/grade-a/{m.group('family')}/art{m.group('num')}.md"
    target_art_suffix = f"art{m.group('num')}.md"

    for edge in graph.get("edges", []):
        if edge.get("from_path") == target_path:
            citations["cross_reference_edges"].append({
                "direction": "outgoing",
                "to_law": edge.get("to_law"),
                "to_article": edge.get("to_article"),
            })
    for edge in graph.get("edges", []):
        # Best-effort incoming match: to_display ends with article suffix
        if edge.get("to_display", "").endswith(target_art_suffix):
            citations["cross_reference_edges"].append({
                "direction": "incoming",
                "from_law": edge.get("from_law"),
                "from_article": edge.get("from_article"),
            })
    return citations


def _eu_cites(aid: str) -> dict[str, Any]:
    citations: dict[str, Any] = {"cases": [], "edpb_docs": []}
    m = re.match(r"^gdpr-art(\d+)", aid)
    if not m:
        return citations
    art_num = m.group(1)
    art_pattern = re.compile(
        rf"\bArt(?:icle|\.)?\s*{art_num}\b|^{art_num}(?:\.|$|\()", re.I,
    )

    for case in load_json(EU_INDEX / "case-index.json").get("cases", []):
        for ref in case.get("gdpr_articles", []):
            if art_pattern.search(str(ref)):
                citations["cases"].append({
                    "case_id": case.get("id"),
                    "case_name": case.get("title", "")[:60],
                    "ref": ref,
                })
                break
    for doc in load_json(EU_INDEX / "edpb-document-index.json").get("documents", []):
        for ref in doc.get("gdpr_articles", []):
            if art_pattern.search(str(ref)):
                citations["edpb_docs"].append({
                    "doc_id": doc.get("id"),
                    "doc_number": doc.get("document_number"),
                    "ref": ref,
                })
                break
    return citations


def who_cites(aid: str) -> dict[str, Any]:
    juris = jurisdiction_for(aid)
    result: dict[str, Any] = {"authority_id": aid, "jurisdiction": juris}
    if juris == "us-ca":
        result["citations"] = _ca_cites(aid)
    elif juris == "kr-pipa":
        result["citations"] = _kr_cites(aid)
    elif juris == "eu-gdpr":
        result["citations"] = _eu_cites(aid)
    else:
        result["citations"] = {}
        result["error"] = f"Unknown jurisdiction for id: {aid}"
    total = 0
    for v in result.get("citations", {}).values():
        if isinstance(v, list):
            total += len(v)
    result["total_citations"] = total
    return result


def print_result(result: dict[str, Any]) -> None:
    print(f"=== who-cites: {result['authority_id']} ===")
    print(f"jurisdiction: {result['jurisdiction']}")
    print(f"total citations: {result['total_citations']}")
    if "error" in result:
        print(f"error: {result['error']}")
        return
    print()
    for category, items in result["citations"].items():
        if isinstance(items, list):
            print(f"{category} ({len(items)}):")
            for item in items[:20]:
                if isinstance(item, dict):
                    desc = ", ".join(f"{k}={v}" for k, v in item.items())
                else:
                    desc = str(item)
                print(f"  {desc}")
            if len(items) > 20:
                print(f"  ... ({len(items) - 20} more)")
        elif items:
            print(f"{category}: {items}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authority_id", help="e.g., ca-civ-1798.150 or gdpr-art6")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = who_cites(args.authority_id)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_result(result)
    return 0 if result["total_citations"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
