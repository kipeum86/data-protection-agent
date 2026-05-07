# Changelog

All notable hardening rounds for this project. Each round corresponds to a
plan document under `docs/integration-hardening-plan-v{N}.md` (or earlier
CA-specific plans for v1-v3).

## v12 — KR/EU coverage reports + CHANGELOG

- KR PIPA coverage report (`scripts/coverage-report-kr.py`) using
  cross-reference-graph (1,309 edges from 428 unique articles) and
  external-law-candidates (154 entries).
- EU GDPR coverage report (`scripts/coverage-report-eu.py`) using
  case-index + edpb-document-index `gdpr_articles` references; 62.6%
  GDPR coverage (62 of 99 articles cited).
- This CHANGELOG.

## v11 — Future-effective + pre-commit + CA coverage report (`a909f51..f2b68cc`)

- CA `check_future_effective_cited_as_current` (warn when authority with
  future `effective_date` is cited with present-tense language). Today
  (2026-05-07) has 0 future-effective authorities; check is forward-looking.
- Opt-in pre-commit hook (`.githooks/pre-commit`) running unified auditor
  on staged .md files (skips meta-docs to avoid false positives).
- CA authority coverage report (`scripts/coverage-report.py`) — first
  measurement: 40.5% coverage (94 of 232) across 5 families. Strongest:
  case (89.7%); weakest: statute (21.7%), adjacent_statute (31%).

## v10 — README + auditors catalog + CI (`fd6c68d..a909f51`)

- README.md expanded from 57 → 183 lines with sub-KB table, architecture
  ASCII tree, test coverage breakdown.
- `docs/auditors.md` — consolidated catalog of ~27 checks across 4 layers.
- `.github/workflows/ci.yml` — push/PR CI: Python 3.12, KB build,
  per-sub-KB tests with KR/EU graceful skip on CI runners (no sibling
  repos available).

## v9 — Unified auditor + STRICT labels + vocab+vague (`4e6b33b..fd6c68d`)

- `unified_auditor/run.py` — single-call runner over all 4 auditors via
  importlib (avoids package-name collision). SKILL.md simplified from
  7-step → 5-step.
- `STRICT_JURISDICTION_LABELS` env toggle — strict mode requires every
  signalled jurisdiction to have an explicit label.
- 4 vocab terms (right to object/opt-out, 위탁, joint controllers).
- 3 vague patterns (depending on jurisdiction, in certain cases, may apply).

## v8 — Jurisdiction labels + vocab + vague refs (`08216bb..4e6b33b`)

- `check_jurisdiction_labels` — multi-juris answer with no labels → warn.
- Vocab expansion: right to erasure / be forgotten / access / delete /
  know / DPO / 수탁자.
- 4 vague law reference patterns with proximity-aware skip (±200 chars).

## v7 — Cross-jurisdiction auditor (`add1d97..08216bb`)

- New `cross_jurisdiction_auditor/` package above the 3 sub-auditors.
- `check_citation_routing` — authority cited from non-signalled jurisdiction.
- `check_vocabulary` — jurisdiction-specific terms in wrong context (10
  initial terms across GDPR/CCPA/PIPA).
- ASCII-letter boundary `(?<![A-Za-z])` for vocab regex (Python `\b` fails
  in Korean+English mixed contexts).

## v6 — EDPB binding + KR 시행규칙 + external laws (`1078c96..add1d97`)

- EU `check_edpb_doc_as_binding` — non-binding EDPB doc cited with
  binding language (only `Binding Decision` exempt by `a-binding-` prefix).
- KR 시행규칙 (network-act-enforcement-rule) pattern.
- KR external-law-candidates info-warn for 154 external Korean laws.

## v5 — EU case-law + KR/EU sanitize (`d3cc1b0..1078c96`)

- EU case_number / ECLI / EDPB document_number lookup-based matching
  (51 cases, 535 recitals, 120 EDPB docs).
- KR sub-KB sanitize.py (mirror CA pattern, 13 patterns).
- EU sub-KB sanitize.py.

## v4 — KR + EU sub-auditors (`f50b938..29dafbd`)

- KR PIPA sub-auditor with article + guideline + PIPC-as-binding checks.
- EU GDPR sub-auditor with article + recital + recital-as-binding.
- Wire up SKILL.md.

## v3 — Integration hardening (`b919b31..add1d97 + earlier rounds`)

- `cross_jurisdiction_auditor/` skeleton.
- `unified_auditor/` skeleton.
- README + AGENTS.md.

## Earlier (CA-only construction)

See `docs/california-local-kb-implementation.md` and
`docs/california-local-kb-hardening-plan.md` for the original CA-only
build (CCPA + adjacent statutes + cases) and the hardening plan that
introduced the unified-KB pattern.

## Test coverage timeline

| Round | Total tests |
|---|---|
| v3 | 11 (CA only) |
| v4 | 48 (+ KR sub 6, EU sub 6) |
| v5 | 72 (+ EU case lookup, KR/EU sanitize) |
| v6 | 79 (+ EDPB binding, KR enforcement-rule, external-law) |
| v7 | 94 (+ cross-jurisdiction 15) |
| v8 | 106 (+ labels, vocab, vague) |
| v9 | 119 (+ unified, STRICT) |
| v10 | 125 (+ docs, CI; no new tests) |
| v11 | 133 (+ future-effective 3, coverage 5) |
| v12 | 144 (+ KR coverage 4, EU coverage 8) |
