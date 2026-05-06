#!/usr/bin/env python3
"""Audit Korean privacy-law citations against the local KR PIPA KB indexes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# kb/kr-pipa/index/ : sources/kr-pipa/citation_auditor/ 기준 3단계 위 + kb/kr-pipa/index
BASE_DIR = Path(__file__).resolve().parents[3]
INDEX_DIR = BASE_DIR / "kb" / "kr-pipa" / "index"


@dataclass
class Finding:
    severity: str
    message: str
    citation: str = ""
    suggested_fix: str = ""


def load_json(name: str) -> dict[str, Any]:
    path = INDEX_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_valid_ids() -> dict[str, set[str]]:
    articles = {a["id"] for a in load_json("article-index.json").get("articles", [])
                if a.get("id")}
    guidelines = {g["id"] for g in load_json("guideline-index.json").get("guidelines", [])
                  if g.get("id")}
    return {"articles": articles, "guidelines": guidelines}


# 인용 패턴: (regex, id_template). 한국어 + 영문 혼용.
# 시행령은 별도 패턴 (한국어 인용에서 "시행령 제N조" 형태가 흔함).
ARTICLE_PATTERNS: tuple[tuple[str, str], ...] = (
    # 정보통신망법 시행규칙 → network-act-enforcement-rule-art{n}
    # (가장 긴 매치, 다른 정보통신망 패턴 위에 둘 것)
    (r"정보통신망(?:법|\s*이용촉진[^제]*법)\s*시행규칙\s*제\s*(\d+)\s*조(?:의\s*(\d+))?",
     "network-act-enforcement-rule-art{}"),
    # 개인정보 보호법 시행령 → pipa-enforcement-decree-art{n} (시행령이 먼저 — 더 긴 매치 우선)
    (r"개인정보\s*보호법\s*시행령\s*제\s*(\d+)\s*조(?:의\s*(\d+))?", "pipa-enforcement-decree-art{}"),
    # 개인정보 보호법 → pipa-art{n}
    (r"개인정보\s*보호법\s*제\s*(\d+)\s*조(?:의\s*(\d+))?", "pipa-art{}"),
    # 정보통신망법 시행령 → network-act-enforcement-decree-art{n}
    (r"정보통신망(?:법|\s*이용촉진[^제]*법)\s*시행령\s*제\s*(\d+)\s*조(?:의\s*(\d+))?", "network-act-enforcement-decree-art{}"),
    # 정보통신망법 → network-act-art{n}
    (r"정보통신망(?:법|\s*이용촉진[^제]*법)\s*제\s*(\d+)\s*조(?:의\s*(\d+))?", "network-act-art{}"),
    # 신용정보법 → credit-info-act-art{n}
    (r"신용정보(?:의\s*이용\s*및\s*보호에\s*관한\s*법률|법)\s*제\s*(\d+)\s*조(?:의\s*(\d+))?", "credit-info-act-art{}"),
    # 위치정보법 → location-info-act-art{n}
    (r"위치정보(?:의\s*보호\s*및\s*이용\s*등에\s*관한\s*법률|법)\s*제\s*(\d+)\s*조(?:의\s*(\d+))?", "location-info-act-art{}"),
    # 영문: PIPA Article N
    (r"PIPA\s+(?:Article|Art\.?)\s*(\d+)", "pipa-art{}"),
    # 영문: Network Act Article N
    (r"Network\s+Act\s+(?:Article|Art\.?)\s*(\d+)", "network-act-art{}"),
)

GUIDELINE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"PIPC\s*(?:가이드라인|guideline)\s*(\d+)", "pipc-guideline-{}"),
)


def _format_id(template: str, num: str, sub: str | None) -> str:
    if sub:
        return template.format(f"{num}-{sub}")
    return template.format(num)


def article_citations(text: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for pattern, template in ARTICLE_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.I):
            num = match.group(1)
            sub = match.group(2) if match.lastindex and match.lastindex >= 2 else None
            results.append((match.group(0), _format_id(template, num, sub)))
    return _dedupe(results)


def guideline_citations(text: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for pattern, template in GUIDELINE_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.I):
            results.append((match.group(0), template.format(match.group(1))))
    return _dedupe(results)


def local_id_citations(text: str) -> list[str]:
    candidates = []
    # NOTE: alternation order matters in Python re (leftmost match).
    # Longer prefixes (network-act-enforcement-rule) must come BEFORE
    # shorter prefixes (network-act) so the longer one wins.
    for match in re.finditer(
        r"\b(?:network-act-enforcement-rule|pipa|network-act|"
        r"credit-info-act|location-info-act|"
        r"e-government-act|pipc-guideline|kr-court)-[a-z0-9][a-z0-9.-]*\b",
        text, flags=re.I,
    ):
        candidates.append(match.group(0).lower().rstrip(".,;:)"))
    return sorted(set(candidates))


def _dedupe(values: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for citation, source_id in values:
        if source_id in seen:
            continue
        seen.add(source_id)
        out.append((citation, source_id))
    return out


PIPC_GUIDELINE_AS_BINDING_RE = re.compile(
    r"PIPC\s*(?:가이드라인|guideline)[^.]{0,80}?"
    r"(?:구속|binding|법적\s*효력|반드시|must|required|requires|mandates)",
    flags=re.I | re.S,
)


def check_pipc_guideline_as_binding(text: str) -> list[Finding]:
    """Warn when a PIPC guideline is cited as binding law.

    PIPC guidelines are official agency interpretation, not statute. Citing
    them as binding obligations confuses guidance with the underlying PIPA.
    """
    findings: list[Finding] = []
    for match in PIPC_GUIDELINE_AS_BINDING_RE.finditer(text):
        findings.append(Finding(
            severity="warn",
            citation="PIPC guideline",
            message="PIPC guideline cited as binding law.",
            suggested_fix=(
                "PIPC guidelines are administrative interpretation, not statute. "
                "Cite the underlying article of 개인정보 보호법 (PIPA) for binding rules."
            ),
        ))
        # Only emit once per audit even if multiple matches
        break
    return findings


def audit(text: str) -> dict[str, Any]:
    ids = load_valid_ids()
    findings: list[Finding] = []

    article_hits = article_citations(text)
    guideline_hits = guideline_citations(text)
    local_ids = local_id_citations(text)

    for citation, source_id in article_hits:
        if source_id not in ids["articles"]:
            findings.append(Finding(
                severity="error",
                citation=citation,
                message=f"Article citation does not exist in article-index.json: {source_id}",
                suggested_fix="Check the article number or refresh the KR article index.",
            ))

    for citation, source_id in guideline_hits:
        if source_id not in ids["guidelines"]:
            findings.append(Finding(
                severity="error",
                citation=citation,
                message=f"Guideline citation does not exist in guideline-index.json: {source_id}",
                suggested_fix="Check the guideline number or refresh the KR guideline index.",
            ))

    all_valid = ids["articles"] | ids["guidelines"]
    article_ids_from_text = {sid for _, sid in article_hits}
    for source_id in local_ids:
        if source_id in all_valid:
            continue
        if source_id in article_ids_from_text:
            # Already reported via article_citations error path
            continue
        findings.append(Finding(
            severity="warn",
            citation=source_id,
            message="Local KR KB id is not present in any KR index.",
            suggested_fix="Use an indexed KB id or rebuild KR indexes.",
        ))

    findings.extend(check_pipc_guideline_as_binding(text))

    status = "fail" if any(f.severity == "error" for f in findings) else "warn" if findings else "pass"
    return {
        "status": status,
        "findings": [asdict(f) for f in findings],
        "coverage": {
            "article_citations_checked": len(article_hits),
            "guideline_citations_checked": len(guideline_hits),
            "local_ids_checked": len(local_ids),
        },
    }


def main(argv: list[str] | None = None) -> int:
    sub_kb_root = Path(__file__).resolve().parent.parent
    if str(sub_kb_root) not in sys.path:
        sys.path.insert(0, str(sub_kb_root))

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Markdown file. Reads stdin if omitted.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    text = Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()
    result = audit(text)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"status: {result['status']}")
        for finding in result["findings"]:
            print(f"- {finding['severity']}: {finding['message']}")
            if finding.get("citation"):
                print(f"  citation: {finding['citation']}")
            if finding.get("suggested_fix"):
                print(f"  fix: {finding['suggested_fix']}")
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
