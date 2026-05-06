# EU GDPR Sub-KB Operations

Status: active runbook
Date: 2026-05-06
Namespace: `eu-gdpr`
Source of truth: sibling `GDPR-expert`
Runtime copy: `kb/eu-gdpr`

## 1. Scope

The EU sub-KB covers GDPR, recitals, high-relevance adjacent EU instruments, EDPB materials, CJEU cases, enforcement decisions, and legislative proposals.

Current imported source registry highlights:

- Grade A: GDPR articles and recitals, ePrivacy Directive, EU AI Act, Data Act, Data Governance Act, EDPB guidelines/opinions/recommendations/statements/binding decisions/reports, CJEU cases.
- Grade B: enforcement decisions and legislative proposals.
- Grade C: law-firm analyses are reserved/pending.

## 2. Source Hierarchy

| Material | Default grade | Notes |
|---|---|---|
| EUR-Lex legislation and recitals | A | Use canonical article/recital URLs. |
| EDPB official documents | A | Keep document type clear: guideline, opinion, recommendation, statement, binding decision, report. |
| CJEU judgments | A | Prefer official court/EUR-Lex source. |
| Supervisory authority enforcement decisions | B | Useful for practice patterns; do not treat as CJEU-level authority. |
| Legislative proposals | B | Never state as current law unless enacted and separately ingested. |
| Commentary | C | Discovery/context only. |

## 3. Update Triggers

- GDPR amendment or new consolidated EUR-Lex version.
- New or revised EDPB guideline, opinion, recommendation, statement, binding decision, or report.
- New CJEU privacy/data-protection judgment.
- New EU digital law affecting privacy analysis, especially AI Act, Data Act, Data Governance Act, or ePrivacy.
- Major supervisory authority decision that should become a Grade B enforcement item.

## 4. Workflow

1. Work in the sibling `GDPR-expert` source folder.
2. Use that repo's existing collection/build scripts and source-family conventions.
3. Rebuild `library/` and `index/` in `GDPR-expert`.
4. Confirm `GDPR-expert/index/source-registry.json` reflects the changed counts and source families.
5. Return to this repo and run:

```bash
python3 scripts/import_namespaced_kbs.py --clean
PYTHONPATH=. pytest -q tests/test_namespaced_kb_import.py
```

6. Check the root unified index:

```bash
jq '.by_namespace["eu-gdpr"], .count' index/unified-authority-index.json
```

## 5. Validation Gates

Minimum gates from this merged repo:

```bash
python3 scripts/import_namespaced_kbs.py --clean
PYTHONPATH=. pytest -q tests/test_namespaced_kb_import.py
```

Run any GDPR-expert native test suite before importing. If the source repo has no current test for a changed family, inspect at least:

- markdown frontmatter for new/changed authorities
- source registry counts
- topic or case index resolution
- official source URLs

## 6. No-Hallucination Rules

- Do not cite EDPB guidance as CJEU case law.
- Do not cite supervisory authority enforcement as EU-wide binding precedent.
- Do not describe proposals as enacted law.
- Distinguish GDPR text from adjacent EU laws.
- If a CJEU holding is not in the local CJEU case family, say the local KB does not currently contain that case.

## 7. Backlog Watch

- EDPB guidelines and recommendations have partial source-family counts in the current registry; review quarterly.
- Grade C law-firm analyses are pending and should remain non-authoritative unless explicitly promoted with a source-grade rationale.

