#!/usr/bin/env python3
"""Cross-jurisdiction citation routing auditor.

Catches mismatches between (a) the jurisdiction signal of the answer text
and (b) the jurisdictions of the actual authorities cited. Operates on top
of the per-sub-KB citation auditors which only see one jurisdiction.

Per CLAUDE.md §2: 'Single-jurisdiction question -> answer from that
sub-KB only. Do not pull authorities from other sub-KBs.'
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
ROUTING_PATH = BASE_DIR / "index" / "jurisdiction-routing.json"


@dataclass
class Finding:
    severity: str
    message: str
    citation: str = ""
    suggested_fix: str = ""


# Authority id prefix -> jurisdiction namespace.
# Order matters: longer prefix MUST come before shorter for correct match.
PREFIX_TO_JURISDICTION: tuple[tuple[str, str], ...] = (
    # CA - longer prefixes first
    ("ca-11-ccr-", "us-ca"),
    ("ca-supreme-", "us-ca"),
    ("ca-appeal-", "us-ca"),
    ("ca-civ-", "us-ca"),
    ("ca-bpc-", "us-ca"),
    ("ca-pen-", "us-ca"),
    ("ca-oag-", "us-ca"),
    ("us-9th-", "us-ca"),
    ("us-fed-", "us-ca"),
    ("cppa-", "us-ca"),
    # KR - longer prefixes first
    ("network-act-enforcement-rule-", "kr-pipa"),
    ("network-act-enforcement-decree-", "kr-pipa"),
    ("pipa-enforcement-decree-", "kr-pipa"),
    ("credit-info-act-enforcement-decree-", "kr-pipa"),
    ("location-info-act-enforcement-decree-", "kr-pipa"),
    ("network-act-", "kr-pipa"),
    ("credit-info-act-", "kr-pipa"),
    ("location-info-act-", "kr-pipa"),
    ("e-government-act-", "kr-pipa"),
    ("pipc-guideline-", "kr-pipa"),
    ("kr-court-", "kr-pipa"),
    ("pipa-", "kr-pipa"),
    # EU - 'a-' prefix and modern act prefixes
    ("a-precedent-", "eu-gdpr"),
    ("a-guideline-", "eu-gdpr"),
    ("a-opinion-", "eu-gdpr"),
    ("a-statement-", "eu-gdpr"),
    ("a-binding-", "eu-gdpr"),
    ("a-recommendation-", "eu-gdpr"),
    ("a-endorsement-", "eu-gdpr"),
    ("a-report-", "eu-gdpr"),
    ("eu-ai-act-", "eu-gdpr"),
    ("data-governance-act-", "eu-gdpr"),
    ("data-act-", "eu-gdpr"),
    ("eprivacy-directive-", "eu-gdpr"),
    ("gdpr-recitals-", "eu-gdpr"),
    ("gdpr-art", "eu-gdpr"),
    ("gdpr-", "eu-gdpr"),
)

# Recognize id-like tokens broadly. Per-jurisdiction sub-auditors handle
# their own validation; here we only need to detect the prefix.
ID_TOKEN_RE = re.compile(
    r"\b(?:ca|us|cppa|pipa|network-act|credit-info-act|location-info-act|"
    r"e-government-act|pipc-guideline|kr-court|gdpr|eu-ai-act|data-act|"
    r"data-governance-act|eprivacy-directive|"
    r"a-precedent|a-guideline|a-opinion|a-statement|a-binding|"
    r"a-recommendation|a-endorsement|a-report)"
    r"-[a-z0-9][a-z0-9.-]*\b",
    flags=re.I,
)


def load_routing() -> list[dict[str, Any]]:
    if not ROUTING_PATH.exists():
        return []
    return json.loads(ROUTING_PATH.read_text(encoding="utf-8")).get("routes", [])


def detect_jurisdictions_from_signals(text: str) -> set[str]:
    """Returns set of jurisdictions detected via routing_terms in the text.

    For ASCII terms, hyphen is treated as a word-boundary so 'gdpr' inside
    an authority id like 'gdpr-art6' is NOT counted as a routing signal —
    only standalone mentions like 'GDPR' or 'gdpr' (whitespace/punctuation
    bordered) count.
    """
    routes = load_routing()
    found: set[str] = set()
    text_lower = text.lower()
    for route in routes:
        for term in route.get("routing_terms", []):
            if not term:
                continue
            if term.isascii():
                # (?<![\w-]) and (?![\w-]) make hyphen part of the boundary
                # so 'gdpr' in 'gdpr-art6' is excluded as a signal.
                if re.search(
                    rf"(?<![\w-]){re.escape(term.lower())}(?![\w-])",
                    text_lower,
                ):
                    found.add(route["namespace"])
                    break
            else:
                if term in text:
                    found.add(route["namespace"])
                    break
    return found


def jurisdiction_for_id(authority_id: str) -> str | None:
    """Returns jurisdiction namespace for a given authority id, or None."""
    aid = authority_id.lower()
    for prefix, juris in PREFIX_TO_JURISDICTION:
        if aid.startswith(prefix):
            return juris
    return None


def detect_cited_jurisdictions(text: str) -> dict[str, list[str]]:
    """Returns {namespace: [authority_id, ...]} for each cited authority."""
    out: dict[str, list[str]] = {}
    seen: set[str] = set()
    for match in ID_TOKEN_RE.finditer(text):
        aid = match.group(0).lower().rstrip(".,;:)")
        if aid in seen:
            continue
        seen.add(aid)
        juris = jurisdiction_for_id(aid)
        if juris:
            out.setdefault(juris, []).append(aid)
    return out


def check_citation_routing(text: str) -> list[Finding]:
    """Warn when an answer cites authorities from a jurisdiction the text
    does not signal as in-scope.

    Edge cases:
      - No routing terms detected: skip (cannot determine intent).
      - Multi-jurisdiction signal AND multi-jurisdiction citations: pass
        (comparative answer is legitimate).
    """
    signalled = detect_jurisdictions_from_signals(text)
    if not signalled:
        return []
    cited = detect_cited_jurisdictions(text)
    findings: list[Finding] = []
    for juris, ids in cited.items():
        if juris in signalled:
            continue
        for aid in ids:
            findings.append(Finding(
                severity="warn",
                citation=aid,
                message=(
                    f"Authority from {juris} cited but answer's jurisdiction "
                    f"signal is {sorted(signalled)}. Cross-jurisdiction "
                    f"authority used without scope label."
                ),
                suggested_fix=(
                    f"If the answer is intentionally comparative, label each "
                    f"jurisdiction explicitly (e.g., 'EU GDPR:', 'California:'). "
                    f"Otherwise, remove the {juris} authority and stick to the "
                    f"in-scope jurisdiction."
                ),
            ))
    return findings


def audit(text: str) -> dict[str, Any]:
    findings: list[Finding] = []
    findings.extend(check_citation_routing(text))

    status = "fail" if any(f.severity == "error" for f in findings) else "warn" if findings else "pass"
    return {
        "status": status,
        "findings": [asdict(f) for f in findings],
        "coverage": {
            "signalled_jurisdictions": sorted(detect_jurisdictions_from_signals(text)),
            "cited_jurisdictions": sorted(detect_cited_jurisdictions(text).keys()),
        },
    }


def main(argv: list[str] | None = None) -> int:
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
        print(f"signalled: {result['coverage']['signalled_jurisdictions']}")
        print(f"cited:     {result['coverage']['cited_jurisdictions']}")
        for finding in result["findings"]:
            print(f"- {finding['severity']}: {finding['message']}")
            if finding.get("citation"):
                print(f"  citation: {finding['citation']}")
            if finding.get("suggested_fix"):
                print(f"  fix: {finding['suggested_fix']}")
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
