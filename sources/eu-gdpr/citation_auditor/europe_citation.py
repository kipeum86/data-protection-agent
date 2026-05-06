#!/usr/bin/env python3
"""Audit EU GDPR-family citations against the local EU GDPR KB indexes.

ID conventions in kb/eu-gdpr/index/ (verified 2026-05-06):
  Articles  : gdpr-art{n}, eu-ai-act-art{n}, data-act-art{n},
              data-governance-act-art{n}, eprivacy-directive-art{n}
  Recitals  : gdpr-recitals-recital{n}      (NB: plural 'recitals' in id)
  Cases     : a-precedent-{slug}            (e.g., a-precedent-c-131-12-google-spain)
  EDPB docs : a-guideline-{slug}, a-endorsement-{slug}, ...
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[3]
INDEX_DIR = BASE_DIR / "kb" / "eu-gdpr" / "index"


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
    recitals = {r["id"] for r in load_json("recital-index.json").get("recitals", [])
                if r.get("id")}
    cases = {c["id"] for c in load_json("case-index.json").get("cases", [])
             if c.get("id")}
    edpb = {d["id"] for d in load_json("edpb-document-index.json").get("documents", [])
            if d.get("id")}
    enforcement = {d["id"] for d in load_json("enforcement-index.json").get("decisions", [])
                   if d.get("id")}
    return {
        "articles": articles,
        "recitals": recitals,
        "cases": cases,
        "edpb": edpb,
        "enforcement": enforcement,
    }


# Article patterns. Longer / more specific patterns first so they win the match.
ARTICLE_PATTERNS: tuple[tuple[str, str], ...] = (
    # Data Governance Act (longer than Data Act, must come first)
    (r"Data\s+Governance\s+Act\s+(?:Article|Art\.?)\s*(\d+)", "data-governance-act-art{}"),
    # Data Act
    (r"Data\s+Act\s+(?:Article|Art\.?)\s*(\d+)", "data-act-art{}"),
    # EU AI Act
    (r"(?:EU\s+)?AI\s+Act\s+(?:Article|Art\.?)\s*(\d+)", "eu-ai-act-art{}"),
    # ePrivacy Directive
    (r"ePrivacy(?:\s+Directive)?\s+(?:Article|Art\.?)\s*(\d+)", "eprivacy-directive-art{}"),
    # GDPR (default)
    (r"GDPR\s+(?:Article|Art\.?)\s*(\d+)", "gdpr-art{}"),
    (r"(?:Article|Art\.?)\s*(\d+)\s+(?:of\s+the\s+)?GDPR", "gdpr-art{}"),
)

# Recital patterns. Real id format is gdpr-recitals-recital{n} (plural).
RECITAL_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"GDPR\s+Recital\s+(\d+)", "gdpr-recitals-recital{}"),
    (r"Recital\s+(\d+)\s+(?:of\s+the\s+)?GDPR", "gdpr-recitals-recital{}"),
)


def article_citations(text: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for pattern, template in ARTICLE_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.I):
            results.append((match.group(0), template.format(match.group(1))))
    return _dedupe(results)


def recital_citations(text: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for pattern, template in RECITAL_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.I):
            results.append((match.group(0), template.format(match.group(1))))
    return _dedupe(results)


def local_id_citations(text: str) -> list[str]:
    candidates = []
    # EU id prefixes observed in indexes
    for match in re.finditer(
        r"\b(?:gdpr|eu-ai-act|data-act|data-governance-act|eprivacy-directive|"
        r"a-precedent|a-guideline|a-endorsement|a-opinion|a-letter|a-decision)"
        r"-[a-z0-9][a-z0-9.-]*\b",
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


# Recital cited as binding rule. GDPR Recitals are interpretive aids
# (e.g., CJEU C-507/17 confirms operative provisions live in Articles).
# Trigger words that indicate the answerer treats the recital as operative.
RECITAL_AS_BINDING_RE = re.compile(
    r"Recital\s+\d+\s+(?:requires|mandates|obligates|prohibits|imposes|"
    r"gives|grants|compels|provides\s+the\s+(?:right|obligation))\b",
    flags=re.I,
)


def check_recital_as_binding(text: str) -> list[Finding]:
    """Warn when a Recital is cited as a binding rule.

    GDPR Recitals are interpretive aids, not operative provisions. Only
    Articles are binding.
    """
    findings: list[Finding] = []
    for match in RECITAL_AS_BINDING_RE.finditer(text):
        findings.append(Finding(
            severity="warn",
            citation=match.group(0),
            message="GDPR Recital cited as binding rule.",
            suggested_fix=(
                "GDPR Recitals are interpretive aids, not binding provisions. "
                "Cite the underlying GDPR Article that operationalises the rule."
            ),
        ))
    return findings


def audit(text: str) -> dict[str, Any]:
    ids = load_valid_ids()
    findings: list[Finding] = []

    article_hits = article_citations(text)
    recital_hits = recital_citations(text)
    local_ids = local_id_citations(text)

    for citation, source_id in article_hits:
        if source_id not in ids["articles"]:
            findings.append(Finding(
                severity="error",
                citation=citation,
                message=f"Article citation does not exist in article-index.json: {source_id}",
                suggested_fix="Check the article number or refresh the EU article index.",
            ))

    for citation, source_id in recital_hits:
        if source_id not in ids["recitals"]:
            findings.append(Finding(
                severity="error",
                citation=citation,
                message=f"Recital citation does not exist in recital-index.json: {source_id}",
                suggested_fix="Check the recital number or refresh the EU recital index.",
            ))

    all_valid = ids["articles"] | ids["recitals"] | ids["cases"] | ids["edpb"] | ids["enforcement"]
    article_ids_from_text = {sid for _, sid in article_hits}
    recital_ids_from_text = {sid for _, sid in recital_hits}
    for source_id in local_ids:
        if source_id in all_valid:
            continue
        if source_id in article_ids_from_text or source_id in recital_ids_from_text:
            # Already reported via article/recital error path
            continue
        findings.append(Finding(
            severity="warn",
            citation=source_id,
            message="Local EU KB id is not present in any EU index.",
            suggested_fix="Use an indexed KB id or rebuild EU indexes.",
        ))

    findings.extend(check_recital_as_binding(text))

    status = "fail" if any(f.severity == "error" for f in findings) else "warn" if findings else "pass"
    return {
        "status": status,
        "findings": [asdict(f) for f in findings],
        "coverage": {
            "article_citations_checked": len(article_hits),
            "recital_citations_checked": len(recital_hits),
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
