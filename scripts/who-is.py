#!/usr/bin/env python3
"""Authority detail CLI: show frontmatter + body excerpt + reverse citations.

Given an authority id, look up the markdown file via the appropriate
sub-KB index, parse the YAML frontmatter, show the first ~500 chars of
body text, and append a brief who-cites summary.

Reuses jurisdiction_for() and who_cites() from who-cites.py.

Usage:
    python3 scripts/who-is.py ca-civ-1798.150
    python3 scripts/who-is.py gdpr-art6
    python3 scripts/who-is.py pipa-art15 --json
    python3 scripts/who-is.py ca-civ-1798.150 --body-chars 1500
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CA_INDEX = PROJECT_ROOT / "sources" / "us-ca" / "index"
KR_INDEX = PROJECT_ROOT / "kb" / "kr-pipa" / "index"
EU_INDEX = PROJECT_ROOT / "kb" / "eu-gdpr" / "index"

CA_KB_ROOT = PROJECT_ROOT / "sources" / "us-ca"
KR_KB_ROOT = PROJECT_ROOT / "kb" / "kr-pipa"
EU_KB_ROOT = PROJECT_ROOT / "kb" / "eu-gdpr"

# Reuse who-cites.py routing + lookup
_spec = importlib.util.spec_from_file_location(
    "who_cites_inner", PROJECT_ROOT / "scripts" / "who-cites.py"
)
_who_cites_mod = importlib.util.module_from_spec(_spec)
sys.modules["who_cites_inner"] = _who_cites_mod
_spec.loader.exec_module(_who_cites_mod)
jurisdiction_for = _who_cites_mod.jurisdiction_for
who_cites = _who_cites_mod.who_cites


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _ca_path_for(aid: str) -> Path | None:
    for index_name, key in (
        ("ca-statute-index.json", "items"),
        ("ca-adjacent-statute-index.json", "items"),
        ("ca-regulation-index.json", "items"),
        ("ca-enforcement-index.json", "items"),
        ("ca-case-index.json", "cases"),
    ):
        for entry in load_json(CA_INDEX / index_name).get(key, []):
            if entry.get("id") == aid and entry.get("path"):
                return CA_KB_ROOT / entry["path"]
    return None


def _kr_path_for(aid: str) -> Path | None:
    for entry in load_json(KR_INDEX / "article-index.json").get("articles", []):
        if entry.get("id") == aid and entry.get("path"):
            return KR_KB_ROOT / entry["path"]
    for entry in load_json(KR_INDEX / "guideline-index.json").get("guidelines", []):
        if entry.get("id") == aid and entry.get("path"):
            return KR_KB_ROOT / entry["path"]
    return None


def _eu_path_for(aid: str) -> Path | None:
    for index_name, key in (
        ("article-index.json", "articles"),
        ("recital-index.json", "recitals"),
        ("case-index.json", "cases"),
        ("edpb-document-index.json", "documents"),
        ("enforcement-index.json", "decisions"),
    ):
        for entry in load_json(EU_INDEX / index_name).get(key, []):
            if entry.get("id") == aid and entry.get("path"):
                return EU_KB_ROOT / entry["path"]
    return None


def find_path(aid: str, juris: str) -> Path | None:
    if juris == "us-ca":
        return _ca_path_for(aid)
    if juris == "kr-pipa":
        return _kr_path_for(aid)
    if juris == "eu-gdpr":
        return _eu_path_for(aid)
    return None


def parse_frontmatter_and_body(text: str, body_chars: int = 500) -> tuple[dict[str, str], str]:
    """Minimal YAML frontmatter parser: scalar key:value lines between --- markers.
    No nesting, no lists. Returns (frontmatter_dict, body_excerpt).
    """
    if not text.startswith("---"):
        return {}, text[:body_chars]
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text[:body_chars]
    fm_text = text[3:end].strip()
    body = text[end + 4:].lstrip()[:body_chars]
    fm: dict[str, str] = {}
    for line in fm_text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or line.startswith(" ") or line.startswith("-"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm, body


def _summarize_citations(citations: dict[str, Any]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for category, items in citations.items():
        if isinstance(items, list):
            summary[category] = len(items)
    return summary


def who_is(aid: str, body_chars: int = 500) -> dict[str, Any]:
    juris = jurisdiction_for(aid)
    result: dict[str, Any] = {"authority_id": aid, "jurisdiction": juris}
    if juris == "unknown":
        result["error"] = f"Unknown jurisdiction for id: {aid}"
        return result
    path = find_path(aid, juris)
    if path is None:
        result["error"] = f"No path found for id {aid} in {juris} indexes"
        return result
    if not path.exists():
        result["error"] = f"Path resolved but file missing: {path}"
        result["path"] = str(path.relative_to(PROJECT_ROOT))
        return result
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter_and_body(text, body_chars=body_chars)
    citations = who_cites(aid)
    result.update({
        "path": str(path.relative_to(PROJECT_ROOT)),
        "frontmatter": fm,
        "body_excerpt": body,
        "total_citations": citations.get("total_citations", 0),
        "citation_summary": _summarize_citations(citations.get("citations", {})),
    })
    return result


def print_result(result: dict[str, Any]) -> None:
    print(f"=== who-is: {result['authority_id']} ===")
    print(f"jurisdiction: {result['jurisdiction']}")
    if "error" in result:
        print(f"error: {result['error']}")
        return
    print(f"path: {result['path']}")
    print()
    print("Frontmatter:")
    for key, value in result["frontmatter"].items():
        print(f"  {key}: {value}")
    print()
    print(f"Body excerpt ({len(result['body_excerpt'])} chars):")
    print("---")
    print(result["body_excerpt"])
    print("---")
    print()
    print(f"Cited in {result['total_citations']} place(s):")
    for category, count in result["citation_summary"].items():
        print(f"  {category}: {count}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authority_id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--body-chars", type=int, default=500)
    args = parser.parse_args(argv)
    result = who_is(args.authority_id, body_chars=args.body_chars)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_result(result)
    return 1 if "error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
