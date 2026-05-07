#!/usr/bin/env python3
"""Audit California privacy-law citations against the local KB indexes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BASE_DIR / "index"


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
    statutes = {item["id"] for item in load_json("ca-statute-index.json").get("items", [])}
    adjacent_statutes = {item["id"] for item in load_json("ca-adjacent-statute-index.json").get("items", [])}
    regulations = {item["id"] for item in load_json("ca-regulation-index.json").get("items", [])}
    enforcement = {item["id"] for item in load_json("ca-enforcement-index.json").get("items", [])}
    cases = {item["id"] for item in load_json("ca-case-index.json").get("cases", [])}
    return {
        "statutes": statutes,
        "adjacent_statutes": adjacent_statutes,
        "regulations": regulations,
        "enforcement": enforcement,
        "cases": cases,
    }


def court_system_for(case_id: str, court: str) -> str:
    if case_id.startswith("us-") or "United States" in court:
        return "federal"
    return "state"


def load_case_metadata() -> dict[str, dict[str, str]]:
    cases = load_json("ca-case-index.json").get("cases", [])
    metadata: dict[str, dict[str, str]] = {}
    for case in cases:
        case_id = case.get("id", "")
        court = case.get("court", "")
        if not case_id:
            continue
        metadata[case_id] = {
            "precedential_status": case.get("precedential_status", ""),
            "authority_level": case.get("authority_level", ""),
            "court": court,
            "court_system": case.get("court_system") or court_system_for(case_id, court),
            "official_url": case.get("official_url", ""),
        }
    return metadata


def load_regulation_metadata() -> dict[str, dict[str, str]]:
    regs = load_json("ca-regulation-index.json").get("items", [])
    return {
        reg["id"]: {
            "effective_date": reg.get("effective_date", ""),
            "official_url": reg.get("official_url", ""),
        }
        for reg in regs
        if reg.get("id")
    }


def load_future_effective_authorities() -> dict[str, str]:
    """Returns {authority_id: effective_date} for statutes/regulations whose
    effective date is in the future (after today).

    Used to flag answers that cite future-effective authority with present-tense
    language ("currently requires", "is in effect", etc.).
    """
    today = date.today()
    out: dict[str, str] = {}
    for index_name, key in (
        ("ca-statute-index.json", "items"),
        ("ca-adjacent-statute-index.json", "items"),
        ("ca-regulation-index.json", "items"),
    ):
        for entry in load_json(index_name).get(key, []):
            eff = entry.get("effective_date", "")
            if not eff or not entry.get("id"):
                continue
            try:
                eff_date = date.fromisoformat(eff)
            except ValueError:
                continue
            if eff_date > today:
                out[entry["id"]] = eff
    return out


def load_mirror_case_ids() -> set[str]:
    """Returns set of case ids whose local source is a Grade B mirror.

    Mirror-backed cases (e.g., Stanford SCOCAL copies of California Supreme
    Court opinions) may still cite as binding authority, but the local raw
    source is not the official California Courts archive PDF. Answers must
    disclose the mirror provenance when citing these.
    """
    cases = load_json("ca-case-index.json").get("cases", [])
    return {
        case["id"]
        for case in cases
        if case.get("id")
        and case.get("source_family") == "ca-courts-published-opinion-mirrors"
    }


def statute_citations(text: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    patterns = [
        (r"Cal\.\s*Civ\.\s*Code\s*§+\s*((?:56|1798)\.\d+(?:\.\d+)?)", "ca-civ-{}"),
        (r"Civil Code section\s*((?:56|1798)\.\d+(?:\.\d+)?)", "ca-civ-{}"),
        (r"Civ\.\s*Code\s*§+\s*((?:56|1798)\.\d+(?:\.\d+)?)", "ca-civ-{}"),
        (r"Cal\.\s*Bus\.\s*&\s*Prof\.\s*Code\s*§+\s*(22\d{3})", "ca-bpc-{}"),
        (r"Business and Professions Code section\s*(22\d{3})", "ca-bpc-{}"),
        (r"Bus\.\s*&\s*Prof\.\s*Code\s*§+\s*(22\d{3})", "ca-bpc-{}"),
        (r"Cal\.\s*Penal\s*Code\s*§+\s*(63[0-8](?:\.\d+)?)", "ca-pen-{}"),
        (r"Penal Code section\s*(63[0-8](?:\.\d+)?)", "ca-pen-{}"),
        (r"Pen\.\s*Code\s*§+\s*(63[0-8](?:\.\d+)?)", "ca-pen-{}"),
    ]
    for pattern, source_id_template in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            section = match.group(1).rstrip(".")
            results.append((match.group(0), source_id_template.format(section)))
    return dedupe_pairs_by_id(results)


def regulation_citations(text: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    patterns = [
        r"11\s*CCR\s*§+\s*(7\d{3})",
        r"Cal\.\s*Code\s*Regs\.\s* tit\.\s*11,\s*§+\s*(7\d{3})",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            section = match.group(1)
            results.append((match.group(0), f"ca-11-ccr-{section}"))
    return dedupe_pairs_by_id(results)


def local_id_citations(text: str) -> list[str]:
    candidates = []
    for match in re.finditer(r"\b(?:ca|us|cppa)-[a-z0-9][a-z0-9.-]*\b", text, flags=re.I):
        candidates.append(match.group(0).lower().rstrip(".,;:)"))
    return sorted(set(candidates))


def windows_for_citation(text: str, citation: str, radius: int = 120) -> list[str]:
    windows = []
    for match in re.finditer(re.escape(citation), text, flags=re.I):
        windows.append(text[max(0, match.start() - radius): match.end() + radius])
    return windows


GENERIC_CONTROLLING_RE = re.compile(
    r"\b(?:binding|controlling|binding precedent|controlling precedent|is precedent|must follow|compels)\b",
    flags=re.I,
)
CALIFORNIA_PRECEDENT_RE = re.compile(
    r"\b(?:"
    r"(?:binding|controlling)\s+(?:California|Cal\.)\s+precedent|"
    r"(?:California|Cal\.)\s+(?:binding|controlling)\s+precedent|"
    r"California\s+(?:Supreme Court|Court of Appeal|appellate)\s+precedent|"
    r"(?:California Supreme Court|California Court of Appeal)\s+(?:authority|precedent|holding)"
    r")\b",
    flags=re.I,
)
REGULATION_2026_RE = re.compile(
    r"(?:2026.{0,80}(?:11\s*CCR|regulation|effective)|(?:11\s*CCR|regulation|effective).{0,80}2026)",
    flags=re.I | re.S,
)
OFFICIAL_2026_REGULATION_SOURCES = (
    "ccpa_statute_eff_20260101.pdf",
    "ccpa_updates_cyber_risk_admt_appr_text.pdf",
)
DISCLOSURE_TERMS = (
    "mirror",
    "scocal",
    "stanford",
    "official url",
    "official source",
    "source_mirror_warning",
    "공식 출처",
    "미러",
    "official california courts archive",
)


def check_federal_case_as_ca_binding(text: str, case_meta: dict[str, dict[str, str]], local_ids: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for source_id in local_ids:
        meta = case_meta.get(source_id)
        if not meta or meta.get("court_system") != "federal":
            continue
        windows = windows_for_citation(text, source_id)
        california_binding = any(CALIFORNIA_PRECEDENT_RE.search(window) for window in windows)
        generic_binding = any(GENERIC_CONTROLLING_RE.search(window) for window in windows)
        if california_binding or (generic_binding and meta.get("precedential_status") != "published_citable"):
            findings.append(Finding(
                severity="warn",
                citation=source_id,
                message="Federal court opinion/order cited as binding California precedent.",
                suggested_fix=(
                    "Federal court authorities may interpret California law, but they are not California "
                    "Supreme Court or California Court of Appeal precedent. Cite a published California "
                    "state appellate decision for binding California precedent."
                ),
            ))
    return findings


def check_unpublished_as_controlling(text: str, case_meta: dict[str, dict[str, str]], local_ids: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for source_id in local_ids:
        meta = case_meta.get(source_id)
        if not meta or meta.get("precedential_status") != "unpublished_non_citable":
            continue
        if any(GENERIC_CONTROLLING_RE.search(window) for window in windows_for_citation(text, source_id)):
            findings.append(Finding(
                severity="error",
                citation=source_id,
                message="Unpublished or non-citable decision cited as controlling authority.",
                suggested_fix=(
                    "Check the decision's publication and citation status. Treat unpublished/non-citable "
                    "decisions as non-controlling unless a jurisdiction-specific exception applies."
                ),
            ))
    return findings


PRESENT_TENSE_RE = re.compile(
    r"\b(?:currently|now|is\s+in\s+effect|takes\s+effect\s+now|"
    r"requires|mandates|prohibits|provides|allows)\b",
    flags=re.I,
)
FUTURE_FRAMING_RE = re.compile(
    r"\b(?:will\s+(?:require|mandate|prohibit|take\s+effect|come\s+into\s+force)|"
    r"effective\s+\d{4}|upcoming|forthcoming|pending)\b",
    flags=re.I,
)


def check_future_effective_cited_as_current(
    text: str,
    future_auths: dict[str, str],
) -> list[Finding]:
    """Warn when a future-effective authority is cited with present-tense
    language and no future-framing language nearby.

    Skip when nearby text uses future-framing ('will require', 'effective YYYY',
    'upcoming') — that signals the answer correctly frames the future status.
    """
    findings: list[Finding] = []
    seen: set[str] = set()
    for aid, eff in future_auths.items():
        if aid not in text:
            continue
        for match in re.finditer(re.escape(aid), text, flags=re.I):
            window_start = max(0, match.start() - 200)
            window_end = min(len(text), match.end() + 200)
            window = text[window_start:window_end]
            if not PRESENT_TENSE_RE.search(window):
                continue
            if FUTURE_FRAMING_RE.search(window):
                continue
            if aid in seen:
                continue
            seen.add(aid)
            findings.append(Finding(
                severity="warn",
                citation=aid,
                message=(
                    f"Authority {aid} cited with present-tense language but "
                    f"effective date is {eff} (future)."
                ),
                suggested_fix=(
                    f"Frame as 'will require' or 'effective {eff}' rather than "
                    f"present tense, or remove the citation if the question is "
                    f"about currently-in-force law only."
                ),
            ))
            break
    return findings


def check_mirror_cited_without_disclosure(
    text: str,
    mirror_ids: set[str],
) -> list[Finding]:
    """Warn when a mirror-backed case id is cited without disclosing the mirror source.

    Trigger (AND):
      - text contains a case id that is in mirror_ids
      - text does NOT contain any term from DISCLOSURE_TERMS (case-insensitive)
    """
    if not mirror_ids:
        return []
    text_lower = text.lower()
    if any(term in text_lower for term in DISCLOSURE_TERMS):
        return []
    findings: list[Finding] = []
    for case_id in mirror_ids:
        if case_id in text:
            findings.append(Finding(
                severity="warn",
                citation=case_id,
                message="Mirror-backed opinion cited without disclosing the mirror source.",
                suggested_fix=(
                    "Disclose that the local copy was fetched from a public mirror "
                    "(e.g., SCOCAL) and cite the official California Courts archive "
                    "URL from the case frontmatter."
                ),
            ))
    return findings


def check_regulation_2026_source_required(
    text: str,
    reg_meta: dict[str, dict[str, str]],
    regulation_hits: list[tuple[str, str]],
) -> list[Finding]:
    if not REGULATION_2026_RE.search(text):
        return []

    reg_ids = [source_id for _, source_id in regulation_hits]
    has_accepted_source_in_text = any(source in text for source in OFFICIAL_2026_REGULATION_SOURCES)
    if has_accepted_source_in_text:
        return []
    findings: list[Finding] = []
    for source_id in reg_ids or ["11 CCR regulation"]:
        meta = reg_meta.get(source_id, {})
        official_url = meta.get("official_url", "")
        indexed_source_ok = bool(official_url) and any(source in official_url for source in OFFICIAL_2026_REGULATION_SOURCES)
        effective_date_ok = meta.get("effective_date") == "2026-01-01" if meta else False
        if not has_accepted_source_in_text or not indexed_source_ok or not effective_date_ok:
            findings.append(Finding(
                severity="warn",
                citation=source_id,
                message="2026-effective regulation claim does not cite the 2026-01-01 CPPA source.",
                suggested_fix=(
                    "Cite the CPPA 2026-01-01 regulations PDF or the final approved updates text "
                    "(cyber/risk/ADMT/insurance package)."
                ),
            ))
    return findings


def dedupe_pairs(values: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def dedupe_pairs_by_id(values: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for citation, source_id in values:
        if source_id in seen:
            continue
        seen.add(source_id)
        out.append((citation, source_id))
    return out


def audit(text: str) -> dict[str, Any]:
    ids = load_valid_ids()
    case_meta = load_case_metadata()
    reg_meta = load_regulation_metadata()
    mirror_ids = load_mirror_case_ids()
    future_auths = load_future_effective_authorities()
    findings: list[Finding] = []

    statute_hits = statute_citations(text)
    regulation_hits = regulation_citations(text)
    local_ids = local_id_citations(text)

    statute_ids = ids["statutes"] | ids["adjacent_statutes"]
    for citation, source_id in statute_hits:
        if source_id not in statute_ids:
            findings.append(Finding(
                severity="error",
                citation=citation,
                message=f"Statute citation does not exist in ca-statute-index.json or ca-adjacent-statute-index.json: {source_id}",
                suggested_fix="Check the section number or refresh the California statute indexes.",
            ))

    for citation, source_id in regulation_hits:
        if source_id not in ids["regulations"]:
            findings.append(Finding(
                severity="error",
                citation=citation,
                message=f"Regulation citation does not exist in ca-regulation-index.json: {source_id}",
                suggested_fix="Check the section number or refresh the regulation index.",
            ))

    all_valid = ids["statutes"] | ids["adjacent_statutes"] | ids["regulations"] | ids["enforcement"] | ids["cases"]
    for source_id in local_ids:
        if source_id not in all_valid:
            findings.append(Finding(
                severity="warn",
                citation=source_id,
                message="Local KB id is not present in any California index.",
                suggested_fix="Use an indexed KB id or rebuild indexes.",
            ))

    cpra_mentions = [m for m in re.finditer(r"\bCPRA\b|California Privacy Rights Act", text, flags=re.I)]
    for match in cpra_mentions:
        window = text[max(0, match.start() - 80): match.end() + 120].lower()
        historical_context = any(word in window for word in ["amend", "proposition 24", "history", "historical", "as amended", "amended by"])
        if not historical_context:
            findings.append(Finding(
                severity="warn",
                citation=match.group(0),
                message="CPRA appears to be used as a standalone current law.",
                suggested_fix="Frame current obligations as CCPA as amended by CPRA, unless discussing amendment history.",
            ))

    if re.search(r"\b(?:U\.S\.|US|United States)\s+privacy law\s+(?:requires|mandates|prohibits|allows)", text, flags=re.I):
        if not re.search(r"\bCalifornia\b|\bCCPA\b|\bCPRA\b|Cal\.\s*Civ\.\s*Code|11\s*CCR", text, flags=re.I):
            findings.append(Finding(
                severity="warn",
                message="Answer appears to make a broad U.S. privacy-law claim without California scoping.",
                suggested_fix="Scope the claim to California CCPA/CPRA or cite the specific U.S. authority.",
            ))

    if re.search(r"OAG\s+(?:FAQ|guidance).*?(?:binding|requires|mandates)", text, flags=re.I | re.S):
        findings.append(Finding(
            severity="warn",
            citation="OAG guidance",
            message="OAG FAQ/guidance appears to be cited as binding law.",
            suggested_fix="Cross-check against Cal. Civ. Code or 11 CCR and cite the binding source.",
        ))

    if re.search(r"(?:enforcement example|press release|settlement|administrative order).*?(?:binding precedent|controlling precedent|judicial precedent)", text, flags=re.I | re.S):
        findings.append(Finding(
            severity="warn",
            message="Enforcement/admin material appears to be treated as judicial precedent.",
            suggested_fix="Describe it as administrative/enforcement material and separately cite cases for precedent.",
        ))

    if re.search(r"unpublished.*?(?:controlling|binding)", text, flags=re.I | re.S):
        findings.append(Finding(
            severity="error",
            message="Unpublished disposition appears to be cited as controlling or binding.",
            suggested_fix="Check publication/citation status in ca-case-index.json.",
        ))

    findings.extend(check_unpublished_as_controlling(text, case_meta, local_ids))
    findings.extend(check_federal_case_as_ca_binding(text, case_meta, local_ids))
    findings.extend(check_regulation_2026_source_required(text, reg_meta, regulation_hits))
    findings.extend(check_mirror_cited_without_disclosure(text, mirror_ids))
    findings.extend(check_future_effective_cited_as_current(text, future_auths))

    status = "fail" if any(f.severity == "error" for f in findings) else "warn" if findings else "pass"
    return {
        "status": status,
        "findings": [asdict(finding) for finding in findings],
        "coverage": {
            "statute_citations_checked": len(statute_hits),
            "regulation_citations_checked": len(regulation_hits),
            "local_ids_checked": len(local_ids),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Text/markdown file to audit. Reads stdin when omitted.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    if args.path:
        text = Path(args.path).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
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
