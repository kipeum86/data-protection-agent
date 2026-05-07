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
from datetime import date
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


def load_case_lookup() -> dict[str, str]:
    """Returns {case_number: case_id} for human-readable case citations.

    Example: {'C-131/12': 'a-precedent-c-131-12-google-spain'}.
    """
    cases = load_json("case-index.json").get("cases", [])
    return {
        c["case_number"]: c["id"]
        for c in cases
        if c.get("case_number") and c.get("id")
    }


def load_ecli_lookup() -> dict[str, str]:
    """Returns {ecli: case_id}. ECLI is European Case Law Identifier.

    Example: {'ECLI:EU:C:2014:317': 'a-precedent-c-131-12-google-spain'}.
    """
    cases = load_json("case-index.json").get("cases", [])
    return {
        c["ecli"]: c["id"]
        for c in cases
        if c.get("ecli") and c.get("id")
    }


def _parse_yyyymmdd(s: str) -> date | None:
    if not s or len(s) != 8 or not s.isdigit():
        return None
    try:
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except ValueError:
        return None


def load_future_effective_articles() -> dict[str, str]:
    """Returns {article_id: effective_date_str} for EU articles whose
    effective_date (YYYYMMDD) is in the future.

    Used to flag answers that cite future-effective EU authority with
    present-tense language ('currently', 'requires', 'is in effect').
    """
    today = date.today()
    out: dict[str, str] = {}
    for art in load_json("article-index.json").get("articles", []):
        aid = art.get("id")
        eff = art.get("effective_date", "")
        ed = _parse_yyyymmdd(eff)
        if aid and ed and ed > today:
            out[aid] = eff
    return out


def load_edpb_lookup() -> dict[str, str]:
    """Returns {document_number: edpb_doc_id} for human-readable EDPB doc citations.

    Example: {'Guidelines 01/2020': 'a-guideline-guidelines-01-2020'}.
    """
    docs = load_json("edpb-document-index.json").get("documents", [])
    return {
        d["document_number"]: d["id"]
        for d in docs
        if d.get("document_number") and d.get("id")
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

# CJEU/General Court case number: 'Case C-131/12' or just 'C-131/12'.
# T- prefix is the General Court.
CASE_NUMBER_RE = re.compile(r"\b(?:Case\s+)?([CT]-\d+/\d+)\b")

# ECLI (European Case Law Identifier): 'ECLI:EU:C:2014:317'.
ECLI_RE = re.compile(r"\bECLI:EU:[CT]:\d{4}:\d+\b")

# EDPB document references. Common forms:
#   "Guidelines 01/2020" / "EDPB Guidelines 01/2020"
#   "Opinion 5/2019"
#   "Statement 02/2019"
#   "Recommendation 01/2020"
#   "Binding Decision 1/2021"
EDPB_DOC_RE = re.compile(
    r"\b(?:EDPB\s+)?"
    r"(Guidelines?|Opinion|Statement|Recommendation|Endorsement|Binding\s+Decision)"
    r"\s+(\d{1,2}/\d{4})\b",
    flags=re.I,
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


def case_number_citations(
    text: str, case_lookup: dict[str, str]
) -> list[tuple[str, str | None]]:
    """Returns [(citation_text, case_id_or_None_for_missing)].

    None means the case_number was found in text but not in case-index.json.
    """
    results: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    for match in CASE_NUMBER_RE.finditer(text):
        case_num = match.group(1)
        if case_num in seen:
            continue
        seen.add(case_num)
        results.append((match.group(0), case_lookup.get(case_num)))
    return results


def ecli_citations(
    text: str, ecli_lookup: dict[str, str]
) -> list[tuple[str, str | None]]:
    results: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    for match in ECLI_RE.finditer(text):
        ecli = match.group(0)
        if ecli in seen:
            continue
        seen.add(ecli)
        results.append((ecli, ecli_lookup.get(ecli)))
    return results


def edpb_citations(
    text: str, edpb_lookup: dict[str, str]
) -> list[tuple[str, str | None]]:
    """Match EDPB document references; reconstruct canonical document_number."""
    results: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    for match in EDPB_DOC_RE.finditer(text):
        doc_type = match.group(1).strip()
        # Normalize: index uses plural 'Guidelines'. Other types: first letter
        # upper, rest as-is to preserve 'Binding Decision' (compound).
        if doc_type.lower().rstrip("s") == "guideline":
            doc_type = "Guidelines"
        else:
            # Preserve compound types ('Binding Decision') by lowercasing all
            # then upper-casing each word's first letter.
            doc_type = " ".join(w[:1].upper() + w[1:].lower() for w in doc_type.split())
        canonical = f"{doc_type} {match.group(2)}"
        if canonical in seen:
            continue
        seen.add(canonical)
        results.append((match.group(0), edpb_lookup.get(canonical)))
    return results


def _strip_inline_code(text: str) -> str:
    """Remove backtick-delimited code spans and fenced blocks before
    id-pattern matching (markdown paths in backticks are not citations).
    """
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    return text


def local_id_citations(text: str) -> list[str]:
    candidates = []
    cleaned = _strip_inline_code(text)
    # EU id prefixes observed in indexes. Citation IDs are lowercase by
    # convention; no re.I flag, to avoid matching prose hyphenations.
    for match in re.finditer(
        r"\b(?:gdpr|eu-ai-act|data-act|data-governance-act|eprivacy-directive|"
        r"a-precedent|a-guideline|a-endorsement|a-opinion|a-letter|a-decision)"
        r"-[a-z0-9][a-z0-9.-]*\b",
        cleaned,
    ):
        candidates.append(match.group(0).rstrip(".,;:)"))
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

# EDPB binding-language verbs. Used in conjunction with EDPB doc citations
# to detect treating non-binding docs (Guidelines/Statement/Opinion/etc.)
# as operative rules. EDPB Binding Decisions (Art. 65 GDPR) are exempt.
EDPB_BINDING_VERBS_RE = re.compile(
    r"\b(?:requires|mandates|obligates|prohibits|imposes|"
    r"compels|must\s+follow|are\s+binding|is\s+binding)\b",
    flags=re.I,
)


EU_PRESENT_TENSE_RE = re.compile(
    r"\b(?:currently|now|is\s+in\s+effect|requires|mandates|prohibits|"
    r"provides|allows)\b",
    flags=re.I,
)
EU_FUTURE_FRAMING_RE = re.compile(
    r"\b(?:will\s+(?:require|mandate|prohibit|take\s+effect|come\s+into\s+force)|"
    r"effective\s+\d{4}|upcoming|forthcoming|pending|adopted\s+but\s+not\s+yet)\b",
    flags=re.I,
)


def check_future_effective_cited_as_current(
    text: str,
    future_arts: dict[str, str],
) -> list[Finding]:
    """Warn when a future-effective EU article id is cited with present-tense
    language and no future-framing nearby.
    """
    findings: list[Finding] = []
    seen: set[str] = set()
    for aid, eff in future_arts.items():
        if aid not in text:
            continue
        for match in re.finditer(re.escape(aid), text, flags=re.I):
            window_start = max(0, match.start() - 200)
            window_end = min(len(text), match.end() + 200)
            window = text[window_start:window_end]
            if not EU_PRESENT_TENSE_RE.search(window):
                continue
            if EU_FUTURE_FRAMING_RE.search(window):
                continue
            if aid in seen:
                continue
            seen.add(aid)
            findings.append(Finding(
                severity="warn",
                citation=aid,
                message=(
                    f"EU authority {aid} cited with present-tense language "
                    f"but effective date is {eff} (future)."
                ),
                suggested_fix=(
                    f"Frame as 'will require' or note effective date {eff}, "
                    f"rather than present tense."
                ),
            ))
            break
    return findings


def check_edpb_doc_as_binding(
    text: str,
    edpb_hits: list[tuple[str, str | None]],
) -> list[Finding]:
    """Warn when a non-binding EDPB doc (Guidelines/Statement/Opinion/etc.)
    is cited with binding language.

    EDPB Binding Decisions (Art. 65 GDPR consistency mechanism) ARE binding
    on supervisory authorities. All other EDPB doc types are interpretive
    guidance and must not be cited as operative rule.

    Detection rule: doc_id startswith 'a-binding-' is the only binding type.
    """
    findings: list[Finding] = []
    seen: set[str] = set()
    for citation, doc_id in edpb_hits:
        if doc_id is None or citation in seen:
            continue
        if doc_id.startswith("a-binding-"):
            continue
        seen.add(citation)
        for match in re.finditer(re.escape(citation), text, flags=re.I):
            window_start = max(0, match.start() - 80)
            window_end = min(len(text), match.end() + 120)
            window = text[window_start:window_end]
            if EDPB_BINDING_VERBS_RE.search(window):
                findings.append(Finding(
                    severity="warn",
                    citation=citation,
                    message="EDPB non-binding document cited as binding rule.",
                    suggested_fix=(
                        "EDPB Guidelines/Statements/Opinions/Recommendations are "
                        "interpretive guidance, not operative rules. Only EDPB "
                        "Binding Decisions (Art. 65 GDPR) are binding. Cite the "
                        "underlying GDPR Article for binding obligations."
                    ),
                ))
                break
    return findings


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


EU_INDEXES_WITH_PATH = (
    ("article-index.json", "articles"),
    ("recital-index.json", "recitals"),
    ("case-index.json", "cases"),
    ("edpb-document-index.json", "documents"),
)

QUOTE_PATTERNS_EU = (
    re.compile(r'"([^"]{25,500})"'),
    re.compile(r"“([^”]{25,500})”"),
)

EU_KB_ROOT = BASE_DIR / "kb" / "eu-gdpr"


def _build_path_lookup() -> dict[str, str]:
    """Returns {authority_id: relpath} from EU indexes that carry a path."""
    out: dict[str, str] = {}
    for index_name, key in EU_INDEXES_WITH_PATH:
        for item in load_json(index_name).get(key, []):
            aid = item.get("id")
            relpath = item.get("path")
            if aid and relpath:
                out[aid] = relpath
    return out


def _strip_frontmatter(content: str) -> str:
    m = re.match(r"^---\n.*?\n---\n", content, flags=re.S)
    return content[m.end():] if m else content


def load_authority_body(authority_id: str, path_lookup: dict[str, str]) -> str | None:
    relpath = path_lookup.get(authority_id)
    if not relpath:
        return None
    fpath = EU_KB_ROOT / relpath
    if not fpath.exists():
        return None
    return _strip_frontmatter(fpath.read_text(encoding="utf-8"))


def _extract_quotes(text: str) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for pat in QUOTE_PATTERNS_EU:
        for match in pat.finditer(text):
            out.append((match.group(1), match.start(1)))
    return out


def _looks_like_citation_only(quote: str) -> bool:
    if len(quote) < 30 and re.match(r"^[A-Z][\w\s.§/-]+$", quote):
        return True
    if re.match(r"^\s*(?:Article|Art\.|Recital|Case|ECLI)", quote, flags=re.I):
        return True
    return False


def _normalize_for_match(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _quote_matches_body(quote: str, body: str) -> bool:
    nq = _normalize_for_match(quote)
    nb = _normalize_for_match(body)
    if nq in nb:
        return True
    qt = [t for t in re.split(r"\W+", nq) if len(t) >= 3]
    if len(qt) < 5:
        return False
    threshold = max(1, int(len(qt) * 0.8))
    bt = re.split(r"\W+", nb)
    win = max(int(len(qt) * 1.5), len(qt) + 5)
    step = max(1, len(qt) // 4)
    for i in range(0, max(0, len(bt) - len(qt)) + 1, step):
        if sum(1 for t in qt if t in bt[i:i + win]) >= threshold:
            return True
    return False


def _build_citation_positions(
    text: str,
    case_lookup: dict[str, str],
    ecli_lookup: dict[str, str],
    edpb_lookup: dict[str, str],
) -> list[tuple[int, str]]:
    positions: list[tuple[int, str]] = []
    pairs: list[tuple[str, str | None]] = (
        article_citations(text)
        + recital_citations(text)
        + case_number_citations(text, case_lookup)
        + ecli_citations(text, ecli_lookup)
        + edpb_citations(text, edpb_lookup)
    )
    for citation, source_id in pairs:
        if not source_id:
            continue
        for match in re.finditer(re.escape(citation), text, flags=re.I):
            positions.append((match.start(), source_id))
    for source_id in local_id_citations(text):
        for match in re.finditer(re.escape(source_id), text, flags=re.I):
            positions.append((match.start(), source_id))
    return positions


def check_quote_integrity(
    text: str,
    path_lookup: dict[str, str],
    case_lookup: dict[str, str],
    ecli_lookup: dict[str, str],
    edpb_lookup: dict[str, str],
) -> list[Finding]:
    findings: list[Finding] = []
    quotes = _extract_quotes(text)
    if not quotes:
        return findings
    positions = _build_citation_positions(text, case_lookup, ecli_lookup, edpb_lookup)
    if not positions:
        return findings
    for quote, qstart in quotes:
        if _looks_like_citation_only(quote):
            continue
        nearby = sorted({sid for off, sid in positions if abs(off - qstart) <= 300})
        if not nearby:
            continue
        checked: list[str] = []
        matched = False
        for cid in nearby:
            body = load_authority_body(cid, path_lookup)
            if body is None:
                continue
            checked.append(cid)
            if _quote_matches_body(quote, body):
                matched = True
                break
        if checked and not matched:
            preview = quote[:80] + ("..." if len(quote) > 80 else "")
            findings.append(Finding(
                severity="warn",
                citation=", ".join(checked),
                message=f'Quoted text not found in cited authority: "{preview}"',
                suggested_fix=(
                    "Verify the quote against the local authority body, "
                    "or paraphrase and remove quotation marks."
                ),
            ))
    return findings


def audit(text: str) -> dict[str, Any]:
    ids = load_valid_ids()
    case_lookup = load_case_lookup()
    ecli_lookup = load_ecli_lookup()
    edpb_lookup = load_edpb_lookup()
    future_arts = load_future_effective_articles()
    findings: list[Finding] = []

    article_hits = article_citations(text)
    recital_hits = recital_citations(text)
    case_hits = case_number_citations(text, case_lookup)
    ecli_hits = ecli_citations(text, ecli_lookup)
    edpb_hits = edpb_citations(text, edpb_lookup)
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

    for citation, case_id in case_hits:
        if case_id is None:
            findings.append(Finding(
                severity="error",
                citation=citation,
                message=f"CJEU/GC case citation does not exist in case-index.json: {citation}",
                suggested_fix="Check the case number or refresh the EU case index.",
            ))

    for citation, ecli_id in ecli_hits:
        if ecli_id is None:
            findings.append(Finding(
                severity="error",
                citation=citation,
                message=f"ECLI does not resolve to any case in case-index.json: {citation}",
                suggested_fix="Check the ECLI or refresh the EU case index.",
            ))

    for citation, doc_id in edpb_hits:
        if doc_id is None:
            findings.append(Finding(
                severity="error",
                citation=citation,
                message=f"EDPB document citation does not exist in edpb-document-index.json: {citation}",
                suggested_fix="Check the document number or refresh the EU EDPB index.",
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
    findings.extend(check_edpb_doc_as_binding(text, edpb_hits))
    findings.extend(check_future_effective_cited_as_current(text, future_arts))
    findings.extend(check_quote_integrity(
        text, _build_path_lookup(), case_lookup, ecli_lookup, edpb_lookup
    ))

    status = "fail" if any(f.severity == "error" for f in findings) else "warn" if findings else "pass"
    return {
        "status": status,
        "findings": [asdict(f) for f in findings],
        "coverage": {
            "article_citations_checked": len(article_hits),
            "recital_citations_checked": len(recital_hits),
            "case_citations_checked": len(case_hits),
            "ecli_citations_checked": len(ecli_hits),
            "edpb_citations_checked": len(edpb_hits),
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
