# Korea PIPA Sub-KB Operations

Status: active runbook
Date: 2026-05-06
Namespace: `kr-pipa`
Source of truth: sibling `PIPA-expert`
Runtime copy: `kb/kr-pipa`

## 1. Scope

The Korea sub-KB covers PIPA, enforcement decree, high-relevance adjacent Korean data/privacy laws, PIPC official guidelines, court precedents, and legal interpretations.

Current imported source registry highlights:

- Grade A: PIPA, PIPA Enforcement Decree, PIPC official guidelines, Network Act family, Credit Information Act family, Location Information Act family, E-Government Act.
- Retired: PIPA Enforcement Rule is excluded because it is repealed.
- Grade B: court precedents, legal interpretations, pending PIPC decisions.
- Grade C: law-firm and academic sources are reserved/pending.

## 2. Source Hierarchy

| Material | Default grade | Notes |
|---|---|---|
| Current Korean statutes and decrees | A | Use official Korean law source used by PIPA-expert. |
| PIPC official guidelines | A | Guidance must remain distinguishable from statute/decree text. |
| Supreme Court or Constitutional Court precedent | B unless official judgment text is captured as primary | Preserve case number and source limitations. |
| 법제처 legal interpretations | B | Useful interpretive material; not a court holding. |
| PIPC decisions | B | Currently pending due source endpoint issue. |
| Commentary | C | Discovery/context only. |

## 3. Update Triggers

- PIPA, Enforcement Decree, or adjacent statute amendment.
- New PIPC guideline or revised official guide.
- New major court precedent on consent, data-subject rights, pseudonymization, breach, resident registration number, outsourcing, or sensitive information.
- Legal interpretation update that affects common answer patterns.
- PIPC decision endpoint becomes usable again.

## 4. Workflow

1. Work in the sibling `PIPA-expert` source folder.
2. Use the existing PIPA-expert fetch/build scripts and source-family conventions.
3. Preserve retired status for repealed law families instead of silently deleting them.
4. Rebuild `library/` and `index/` in `PIPA-expert`.
5. Confirm `PIPA-expert/index/source-registry.json` reflects changed counts and source families.
6. Return to this repo and run:

```bash
python3 scripts/import_namespaced_kbs.py --clean
PYTHONPATH=. pytest -q tests/test_namespaced_kb_import.py
```

7. Check the root unified index:

```bash
jq '.by_namespace["kr-pipa"], .count' index/unified-authority-index.json
```

## 5. Validation Gates

Minimum gates from this merged repo:

```bash
python3 scripts/import_namespaced_kbs.py --clean
PYTHONPATH=. pytest -q tests/test_namespaced_kb_import.py
```

Run any PIPA-expert native test suite before importing. If changed material includes case law or legal interpretations, manually verify:

- case number or interpretation number
- court/agency
- date
- source grade
- whether the material is binding law, precedent, interpretation, or guidance

## 6. No-Hallucination Rules

- Do not cite PIPC guidelines as statutory text.
- Do not cite legal interpretations as court precedent.
- Do not revive repealed PIPA Enforcement Rule provisions as current law.
- Keep PIPA, Network Act, Credit Information Act, Location Information Act, and E-Government Act distinct.
- If a current-law question depends on amendment status, verify the source family and retrieved date.

## 7. Backlog Watch

- PIPC decisions are pending because the prior endpoint returned empty responses. Resume only when full decision text can be captured and indexed.
- Court precedents and legal interpretations are partial collections; expand by topic and keep authority limits explicit.
- Grade C commentary remains pending and should not enter answer grounding unless separately approved as context-only material.

