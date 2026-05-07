# Citation Auditor Catalog

This document catalogs every check across the 4-layer auditor stack.
Use it as a reference when interpreting auditor output or when adding
new checks.

## Layer overview

```
┌─────────────────────────────────────────────────────────────┐
│ Unified runner (scripts/audit-unified.py)                   │
│ Runs all 4 auditors in one invocation, aggregates findings. │
└─────────────────────────────────────────────────────────────┘
   │
   ├─→ CA sub-auditor    sources/us-ca/citation_auditor/california_citation.py
   │     10 checks, validates against ca-statute-index, ca-regulation-index,
   │     ca-case-index, ca-enforcement-index, ca-adjacent-statute-index.
   │
   ├─→ KR sub-auditor    sources/kr-pipa/citation_auditor/korea_citation.py
   │     5 checks, validates against article-index, guideline-index,
   │     external-law-candidates.
   │
   ├─→ EU sub-auditor    sources/eu-gdpr/citation_auditor/europe_citation.py
   │     8 checks, validates against article-index, recital-index,
   │     case-index, edpb-document-index, enforcement-index.
   │
   └─→ Cross-jurisdiction auditor
       cross_jurisdiction_auditor/audit.py
       4 checks, layered above sub-auditors. Detects mismatches between
       the answer's jurisdiction signal and the cited authorities or
       terminology.
```

Total: ~27 distinct checks across the 4 layers.

## CA sub-auditor (10 checks)

| Check | Severity | Trigger |
|---|---|---|
| `statute_id_missing` | error | `Cal. Civ. Code § X` (or adjacent statute citation) not in `ca-statute-index.json` or `ca-adjacent-statute-index.json` |
| `regulation_id_missing` | error | `11 CCR § X` not in `ca-regulation-index.json` |
| `local_kb_id_missing` | warn | Direct id (`ca-civ-...`, `us-fed-...`, etc.) not in any CA index |
| `cpra_standalone` | warn | "CPRA requires X" without amendment-history context (CCPA-as-amended-by-CPRA framing required) |
| `us_overbreadth` | warn | "US privacy law requires X" without California scoping |
| `oag_faq_as_binding` | warn | "OAG FAQ ... requires/binding/mandates" — guidance is non-binding |
| `enforcement_as_judicial_precedent` | warn | enforcement/admin material treated as judicial precedent |
| `federal_court_as_ca_binding` | warn | `us-fed-...` or `us-9th-...` cited as binding California precedent (9th Cir published opinion is exempt) |
| `unpublished_as_controlling` | error | case id with `precedential_status=unpublished_non_citable` cited with binding language (Cal. Rules of Court rule 8.1115) |
| `regulation_2026_source_required` | warn | "2026 regulation" claim without 2026-01-01 CPPA source URL |
| `mirror_cited_without_disclosure` | warn | mirror-backed case (source_family `ca-courts-published-opinion-mirrors`) cited without disclosing mirror provenance (English: "mirror"/"SCOCAL"/"official URL"; Korean: "미러"/"공식 출처") |

CLI: `python3 sources/us-ca/scripts/audit-california-citations.py [path|stdin] [--json]`

## KR sub-auditor (5 checks)

| Check | Severity | Trigger |
|---|---|---|
| `article_id_missing` | error | Article citation in any of the 5 supported laws not in `article-index.json` |
| `guideline_id_missing` | error | `pipc-guideline-{n}` not in `guideline-index.json` |
| `local_kb_id_missing` | warn | Direct id with KR prefix not in any KR index |
| `pipc_guideline_as_binding` | warn | "PIPC 가이드라인 ... 구속력/binding/반드시/must" — guidelines are administrative, not statute |
| `external_law_referenced` | warn | External Korean law cited (전기통신사업법 etc., listed in `external-law-candidates.json`) but full text not in local KB |

Citation patterns recognize both Korean and English forms:
- 개인정보 보호법 / 시행령
- 정보통신망법 / 시행령 / 시행규칙
- 신용정보법
- 위치정보법
- PIPC 가이드라인 N
- English: PIPA Article N, Network Act Article N

CLI: `python3 sources/kr-pipa/scripts/audit-korea-citations.py [path|stdin] [--json]`

## EU sub-auditor (8 checks)

| Check | Severity | Trigger |
|---|---|---|
| `article_id_missing` | error | Article citation (GDPR / EU AI Act / Data Act / Data Governance Act / ePrivacy Directive) not in `article-index.json` |
| `recital_id_missing` | error | `gdpr-recitals-recital{n}` not in `recital-index.json` (note plural form) |
| `case_number_missing` | error | `Case C-XXX/YY` (CJEU) or `Case T-XXX/YY` (General Court) not resolvable to `a-precedent-...` id |
| `ecli_missing` | error | `ECLI:EU:[CT]:YYYY:N` not resolvable in case-index |
| `edpb_document_missing` | error | EDPB document_number (`Guidelines 01/2020`, `Opinion 5/2019`, `Binding Decision 1/2021`, etc.) not in `edpb-document-index.json` |
| `local_kb_id_missing` | warn | Direct id with EU prefix not in any EU index |
| `recital_as_binding` | warn | GDPR Recital cited with binding-rule language (Recitals are interpretive aids, not operative provisions per CJEU C-507/17) |
| `edpb_doc_as_binding` | warn | Non-binding EDPB doc (Guidelines / Opinion / Statement / Recommendation / Endorsement / Report) cited with binding language. Only `Binding Decision` (Art. 65 GDPR consistency mechanism) is exempt. |

Lookups cover ID prefixes:
- `gdpr-art{n}`, `gdpr-recitals-recital{n}`
- `eu-ai-act-art{n}`, `data-act-art{n}`, `data-governance-act-art{n}`
- `eprivacy-directive-art{n}`
- `a-precedent-{slug}` (CJEU + General Court)
- `a-{guideline,opinion,statement,binding,recommendation,endorsement,report}-{slug}` (EDPB)

CLI: `python3 sources/eu-gdpr/scripts/audit-europe-citations.py [path|stdin] [--json]`

## Cross-jurisdiction auditor (4 checks)

| Check | Severity | Trigger |
|---|---|---|
| `citation_routing_mismatch` | warn | Authority cited from a jurisdiction the answer's text does not signal (per `index/jurisdiction-routing.json` routing_terms). Skip when ≥2 jurisdictions signalled (comparative answer is legitimate). |
| `vocabulary_mismatch` | warn | Jurisdiction-specific terminology used in single-jurisdiction answer that signals the wrong jurisdiction. 17 terms across GDPR/CCPA/PIPA. Skip on multi-juris signal. |
| `jurisdiction_labels_missing` | warn | Multi-jurisdiction answer lacks explicit jurisdiction labels (`EU GDPR:`, `California:`, `Korea PIPA:`). Default mode: at least one label OK. STRICT mode (`STRICT_JURISDICTION_LABELS=true`): all signalled juris must be labelled. |
| `vague_law_reference` | warn | Vague phrase without a specific authority id within ±200 chars. Patterns: `the law requires`, `this regulation states`, `in some jurisdictions`, `applicable law requires`, `depending on the jurisdiction`, `in certain cases`, `may apply`. |

CLI: `python3 scripts/audit-cross-jurisdiction.py [path|stdin] [--json]`

### Vocabulary table (vocabulary_mismatch)

GDPR-specific (warn if used in CCPA-only or PIPA-only answer):
- `personal data`, `lawful basis`, `data subject`, `controller`, `processor`,
  `right to erasure`, `right to be forgotten`, `right of access`,
  `data protection officer`, `right to object`, `joint controllers`

CCPA-specific (warn if used in GDPR-only or PIPA-only answer):
- `personal information`, `notice at collection`, `service provider`,
  `right to delete`, `right to know`, `right to opt-out`

PIPA-specific (warn if used in GDPR-only or CCPA-only answer):
- `개인정보처리자`, `정보주체`, `수탁자`, `위탁`/`위탁자`/`위탁처리`

Boundary: ASCII vocab uses `(?<![A-Za-z]) ... (?![A-Za-z])` lookarounds
(NOT `\b`, which treats Hangul as word character). Korean vocab uses
substring match.

## Unified runner

`scripts/audit-unified.py` (or `python3 -c "from unified_auditor.run import audit_unified"`)
imports all 4 auditors via `importlib` (avoids package-name collision)
and aggregates findings.

Output schema:
```json
{
  "status": "fail | warn | pass",
  "per_auditor": {
    "us-ca":              {"status": ..., "finding_count": N},
    "kr-pipa":            {"status": ..., "finding_count": N},
    "eu-gdpr":            {"status": ..., "finding_count": N},
    "cross-jurisdiction": {"status": ..., "finding_count": N}
  },
  "findings": [
    {"auditor": "...", "severity": "...", "message": "...", "citation": "...", "suggested_fix": "..."},
    ...
  ],
  "finding_count": N
}
```

Aggregate severity:
- `error` (statute/regulation/case id missing, unpublished as controlling)
  → answer must be revised before sending.
- `warn` (binding misuse, vocabulary mismatch, vague references)
  → surface to user inline.
- `pass` → ship.

## Source grading

All sub-KBs share an A/B/C/D source-grade vocabulary (see
`config/source-grades.json` in each sub-KB):

| Grade | Meaning |
|---|---|
| A | Official primary or current guidance source |
| B | Official but nonbinding, explanatory, enforcement, or secondary authority. Includes mirror-backed primary authorities (e.g., SCOCAL mirrors of CA Supreme Court opinions) where the local raw source is not the official PDF. |
| C | Commentary or discovery-only source requiring official verification |
| D | Excluded source |

## Sanitizer (per sub-KB)

Each sub-KB has a `scripts/sanitize.py` (per AGENTS.md Rule 3) that
neutralizes 13 prompt-injection patterns across 4 severities:

- role-marker (`<|im_start|>system`, `^Human:`, `^Assistant:`)
- role-tag (`[system]`, `[/system]`, `[assistant]`, `[/assistant]`)
- jailbreak (`ignore previous instructions`, `disregard above`, `you are now`, `forget instructions`)
- forged-firewall (`<tool_use>`, `<|endoftext|>`, `<|stop|>`, `<system-reminder>`)

Patterns are identical across sub-KBs but each sub-KB owns its own copy
so jurisdiction-specific patterns can diverge later.

Library use:
```python
from scripts.sanitize import sanitize    # any sub-KB sys.path
result = sanitize(untrusted_text)
if result.aborted:
    raise RuntimeError("[SANITIZER UNAVAILABLE]")
safe_text = result.text                   # patterns replaced with [REDACTED-N-chars]
matches = result.matches                  # what was found, sorted by start
```

CLI:
```bash
echo "Test <|im_start|>system payload" | python3 sources/us-ca/scripts/sanitize.py
# JSON: {text, matches, aborted, aborted_reason, timestamp}
```

## Test coverage (v9 baseline)

| Layer | Tests |
|---|---|
| CA sub-auditor | 42 (incl. 6 sanitize, 4 mirror, 4 federal-binding) |
| KR sub-auditor | 16 (incl. 6 sanitize, 2 enforcement-rule, 2 external-law) |
| EU sub-auditor | 21 (incl. 6 sanitize, 6 case/ECLI/EDPB lookup, 3 EDPB-binding) |
| Cross-jurisdiction | 35 (incl. 4 labels, 4 vocab, 4 vague, 3 strict mode) |
| Unified runner | 5 (load all 4, aggregate findings) |
| KB import | 6 |
| **Total** | **125** |

Run all:
```bash
PYTHONPATH=. python3 -m pytest -q tests
cd sources/us-ca && PYTHONPATH=. python3 -m pytest -q tests
cd sources/kr-pipa && PYTHONPATH=. python3 -m pytest -q tests
cd sources/eu-gdpr && PYTHONPATH=. python3 -m pytest -q tests
```
