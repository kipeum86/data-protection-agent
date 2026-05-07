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
import os
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


# ASCII-letter boundary (NOT Python's \b, which treats Hangul as word
# character and so '\bcontroller\b' fails to match 'controller' inside
# 'controller는'). These lookarounds restrict the boundary to ASCII letters
# only, so any non-ASCII-letter neighbor (whitespace, hyphen, Hangul,
# punctuation) counts as a boundary.
_ASCII_LB = r"(?<![A-Za-z])"
_ASCII_LA = r"(?![A-Za-z])"


# Canonical jurisdiction labels and common variants.
# Pattern matches a label-like phrase (jurisdiction name + ':' or '—' or '-')
# at the start of a line OR after a paragraph break.
JURISDICTION_LABEL_PATTERNS: dict[str, str] = {
    "us-ca": r"(?:^|\n\n|\n)\s*(?:\*\*)?(?:California|CCPA|CPRA|US-CA|미국 캘리포니아)(?:\*\*)?\s*[:：—–\-]",
    "eu-gdpr": r"(?:^|\n\n|\n)\s*(?:\*\*)?(?:EU\s+GDPR|GDPR|EU|유럽|유럽연합)(?:\*\*)?\s*[:：—–\-]",
    "kr-pipa": r"(?:^|\n\n|\n)\s*(?:\*\*)?(?:Korea\s+PIPA|PIPA|한국|대한민국)(?:\*\*)?\s*[:：—–\-]",
}


def find_labelled_jurisdictions(text: str) -> set[str]:
    """Returns set of jurisdictions whose canonical label appears in text."""
    found: set[str] = set()
    for juris, pattern in JURISDICTION_LABEL_PATTERNS.items():
        if re.search(pattern, text, flags=re.M | re.I):
            found.add(juris)
    return found


def _is_strict_labels() -> bool:
    """STRICT_JURISDICTION_LABELS env var toggle.

    When true, every signalled jurisdiction must have an explicit label.
    Default (false) accepts partial labelling (at least one label is OK).
    """
    return os.environ.get("STRICT_JURISDICTION_LABELS", "").lower() in {"true", "1", "yes"}


def check_jurisdiction_labels(text: str) -> list[Finding]:
    """Warn when a multi-jurisdiction answer has no explicit jurisdiction labels.

    Per CLAUDE.md §2, comparative answers must label each jurisdiction in
    its own section ('EU GDPR:', 'California:', 'Korea PIPA:').

    Default mode:
      Trigger: ≥2 signals AND no jurisdiction has a label.
      Skip: at least one labelled jurisdiction (partial structure is OK).

    STRICT mode (STRICT_JURISDICTION_LABELS=true):
      Trigger: ≥2 signals AND any signalled juris missing a label.
      Skip: only when every signalled juris has a label.
    """
    signalled = detect_jurisdictions_from_signals(text)
    if len(signalled) < 2:
        return []
    labelled = find_labelled_jurisdictions(text)

    if _is_strict_labels():
        unlabelled = signalled - labelled
        if not unlabelled:
            return []
        return [Finding(
            severity="warn",
            message=(
                f"Multi-jurisdiction answer (signals: {sorted(signalled)}) is "
                f"missing labels for: {sorted(unlabelled)} (STRICT mode)."
            ),
            suggested_fix=(
                "STRICT_JURISDICTION_LABELS env var is set. Each signalled "
                "jurisdiction must have an explicit label heading. Add labels "
                "for the missing jurisdictions or unset STRICT_JURISDICTION_LABELS."
            ),
        )]

    if labelled:
        return []
    return [Finding(
        severity="warn",
        message=(
            f"Multi-jurisdiction answer (signals: {sorted(signalled)}) lacks "
            f"explicit jurisdiction labels."
        ),
        suggested_fix=(
            "Per CLAUDE.md §2, comparative answers must label each "
            "jurisdiction in its own section. Use headings like "
            "'EU GDPR:', 'California:', 'Korea PIPA:' or equivalent."
        ),
    )]


# Vocabulary that "belongs" to one jurisdiction. If the text signals only
# OTHER jurisdiction(s) but uses these terms, warn. Comparative context
# (multi-jurisdiction signal) skips this check.
VOCAB_BY_JURISDICTION: tuple[tuple[str, str, str], ...] = (
    # GDPR-specific terminology
    (_ASCII_LB + r"personal\s+data" + _ASCII_LA, "eu-gdpr",
     "'personal information' (CCPA/PIPA term)"),
    (_ASCII_LB + r"lawful\s+bas[ei]s" + _ASCII_LA, "eu-gdpr",
     "CCPA does not use 'lawful basis'; cite § 1798.100 notice-at-collection"),
    (_ASCII_LB + r"data\s+subject" + _ASCII_LA, "eu-gdpr",
     "'consumer' (CCPA) or '정보주체' (PIPA)"),
    (_ASCII_LB + r"controller" + _ASCII_LA, "eu-gdpr",
     "'business' (CCPA) or '개인정보처리자' (PIPA)"),
    (_ASCII_LB + r"processor" + _ASCII_LA, "eu-gdpr",
     "'service provider' (CCPA) or '수탁자' (PIPA)"),

    # CCPA-specific terminology
    (_ASCII_LB + r"personal\s+information" + _ASCII_LA, "us-ca",
     "'personal data' (GDPR)"),
    (_ASCII_LB + r"notice\s+at\s+collection" + _ASCII_LA, "us-ca",
     "GDPR uses Article 13/14 information duties instead"),
    (_ASCII_LB + r"service\s+provider" + _ASCII_LA, "us-ca",
     "GDPR uses 'processor'"),

    # PIPA-specific terminology (Korean — substring match is fine)
    (r"개인정보처리자", "kr-pipa", "GDPR uses 'controller' or CCPA uses 'business'"),
    (r"정보주체", "kr-pipa", "GDPR uses 'data subject' or CCPA uses 'consumer'"),

    # GDPR rights terminology
    (_ASCII_LB + r"right\s+to\s+erasure" + _ASCII_LA, "eu-gdpr",
     "CCPA uses 'right to delete' (Cal. Civ. Code § 1798.105)"),
    (_ASCII_LB + r"right\s+to\s+be\s+forgotten" + _ASCII_LA, "eu-gdpr",
     "CCPA uses 'right to delete'; GDPR Art. 17 is also called 'right to erasure'"),
    (_ASCII_LB + r"right\s+of\s+access" + _ASCII_LA, "eu-gdpr",
     "CCPA uses 'right to know' (Cal. Civ. Code § 1798.110)"),

    # CCPA rights terminology
    (_ASCII_LB + r"right\s+to\s+delete" + _ASCII_LA, "us-ca",
     "GDPR uses 'right to erasure' (Art. 17, also 'right to be forgotten')"),
    (_ASCII_LB + r"right\s+to\s+know" + _ASCII_LA, "us-ca",
     "GDPR uses 'right of access' (Art. 15)"),

    # GDPR-only role: DPO
    (_ASCII_LB + r"data\s+protection\s+officer" + _ASCII_LA, "eu-gdpr",
     "CCPA does not require a DPO; PIPA has 개인정보 보호책임자"),

    # PIPA processor
    (r"수탁자", "kr-pipa", "GDPR uses 'processor' or CCPA uses 'service provider'"),
)


def check_vocabulary(text: str) -> list[Finding]:
    """Warn when text uses terminology that doesn't fit its jurisdiction signal.

    Skip when text is multi-jurisdiction (comparative answer is legitimate)
    or when no jurisdiction is signalled (cannot determine intent).
    """
    signalled = detect_jurisdictions_from_signals(text)
    if not signalled or len(signalled) >= 2:
        return []
    primary = next(iter(signalled))
    findings: list[Finding] = []
    seen: set[str] = set()
    for pattern, term_juris, alternative in VOCAB_BY_JURISDICTION:
        if term_juris == primary:
            continue
        for match in re.finditer(pattern, text, flags=re.I):
            term = match.group(0)
            if term.lower() in seen:
                continue
            seen.add(term.lower())
            findings.append(Finding(
                severity="warn",
                citation=term,
                message=(
                    f"Term '{term}' is {term_juris} terminology but answer "
                    f"signals {primary}."
                ),
                suggested_fix=(
                    f"Use {alternative}. If the answer is intentionally "
                    f"comparative, label each jurisdiction explicitly."
                ),
            ))
    return findings


# Vague law reference patterns. Each entry: (regex, suggested_fix).
# Trigger only when no specific authority id is cited within ±200 chars
# (proximity check in check_vague_law_reference()).
VAGUE_LAW_REFERENCES: tuple[tuple[str, str], ...] = (
    (r"\bthe\s+law\s+(?:requires|mandates|states|prohibits|allows|provides)\b",
     "Vague reference to 'the law'. Cite the specific statute and section."),
    (r"\bthis\s+regulation\s+(?:requires|mandates|states|prohibits)\b",
     "Vague reference to 'this regulation'. Cite the specific regulation and section."),
    (r"\bin\s+some\s+jurisdictions?\b",
     "Vague jurisdiction reference. Name the specific jurisdictions."),
    (r"\bapplicable\s+law\s+(?:requires|may\s+require|provides)\b",
     "'Applicable law' is too vague. Cite the specific governing law."),
)


def check_vague_law_reference(text: str) -> list[Finding]:
    """Warn when text uses vague law references without nearby specific authority.

    Looks for vague phrases ('the law requires', 'this regulation states', etc.)
    and checks whether a specific authority id citation appears within 200 chars
    before/after. If yes, skip (the vague phrase is acceptable shorthand for
    the explicit citation). If no, warn.
    """
    findings: list[Finding] = []
    seen: set[str] = set()
    for pattern, fix in VAGUE_LAW_REFERENCES:
        for match in re.finditer(pattern, text, flags=re.I):
            phrase = match.group(0)
            if phrase.lower() in seen:
                continue
            window_start = max(0, match.start() - 200)
            window_end = min(len(text), match.end() + 200)
            window = text[window_start:window_end]
            if ID_TOKEN_RE.search(window):
                continue  # Specific authority nearby; vague phrase is OK shorthand
            seen.add(phrase.lower())
            findings.append(Finding(
                severity="warn",
                citation=phrase,
                message=f"Vague law reference: '{phrase}'.",
                suggested_fix=fix,
            ))
    return findings


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
    findings.extend(check_vocabulary(text))
    findings.extend(check_jurisdiction_labels(text))
    findings.extend(check_vague_law_reference(text))

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
