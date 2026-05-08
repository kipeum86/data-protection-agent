# Changelog

All notable hardening rounds for this project. Each round corresponds to a
plan document under `.local/planning/v{N}/` (older plans were tracked at
`docs/integration-hardening-plan-v{N}.md` before v18; the docs/* path is
now gitignored so plan drafts stay local).

## v20 — Retrieval quality + auditor false-positive cleanup (`fcda737..6ad4879`)

Two related rounds driven by the v19 dogfood:

- **v20-mini (false-positive cleanup):** `fallback_us` was treated as
  non-fallback by the validator, producing spurious missing-namespaces /
  empty-sources errors. `local_id_citations()` matched authority-id-shaped
  tokens inside backtick-wrapped paths and prose hyphenations
  (`US-California`), spamming "Local KB id is not present in any index"
  warnings. Cross-jurisdiction labels check fired on fallback memos that
  legitimately mention multiple jurisdictions only to explain they are
  out of scope. All three fixed: `FALLBACK_MODES` set, `_strip_inline_code()`
  helper + lowercase-only id matching + namespace token exclusion (CA/KR/EU),
  and a `Research mode: fallback*` preflight that skips the labels check.
- **v20-retrieval:** Only CA had a topic index, so KR/EU retrieval fell
  back to keyword scoring and surfaced wrong-but-valid authorities
  (data-act-art33 instead of gdpr-art33; pipa-art28-6 instead of
  pipa-art34). Added `kb/kr-pipa/index/kr-topic-index.json` and
  `kb/eu-gdpr/index/eu-topic-index.json` (8 curated topics each — breach
  notification, lawful basis / consent, data-subject rights, sensitive
  data, cross-border transfer, DPIA, ADM, enforcement). Patched
  `import_namespaced_kbs.py` to read per-namespace topic files; patched
  `phrase_in()` to treat space and hyphen as interchangeable separators
  (so `breach notification` matches `breach-notification`); expanded the
  CA primary-law boost beyond ca-ccpa-* to include ca-customer-records,
  ca-caloppa, ca-cipa, ca-cmia, ca-data-broker-delete-act, and
  ca-age-appropriate-design-code. Bonus: added 11 CCR § 7070/7071 to the
  CA `minors_children` topic (golden regression fix).

After v20, T2.1 dogfood (3-way breach-notification) surfaces gdpr-art33,
pipa-art34 + decree art39/40, civ-1798.150 + civ-1798.82 in top-K.

## v19 — Agent answering pipeline (`67b446e..04b1ca5`, planned in `.local/planning/v19/`)

Adds the LLM-facing answering layer on top of the v3-v18 KB and auditor
stack. Five Codex-implemented commits behind a single plan:

- 7 new skills under `.claude/skills/` (intake-and-routing, kb-retrieval,
  trust-boundary, claim-grounding, result-memo-composition,
  comparative-composition, quality-check) — each with
  `disable-model-invocation: true` so the LLM loads them only when
  explicitly told to via `CLAUDE.md` references.
- 6 templates under `templates/` (canonical 9-section result.md +
  meta.example.json + per-mode variants for single-jurisdiction,
  multi-jurisdiction, comparative-matrix, fallback).
- New `scripts/validate-output.py` (538 lines, stdlib only) — dual-mode:
  full v19 strict checks AND legacy_packet compatibility for the
  pre-v19 deterministic runner.
- `/answer` slash command + refreshed `.claude/agents/data-protection-agent.md`
  + `CLAUDE.md` §9 workflow section.
- 5 golden fixtures (`g_ca_001`, `g_kr_001`, `g_eu_001`, `g_multi_001`,
  `g_comp_001`) + parametrised e2e tests covering validator and auditor.

Mirrors `legal-research-agent`'s 8-stage workflow (intake → retrieval →
trust-boundary → claim-grounding → composition → quality-check → write).

## v18 — Quote integrity check (`fbf45c9..05a911c`)

LLM hallucination most commonly takes the form of a correct citation id
paired with a fabricated quote — citation-id checks alone don't catch
this. Adds `check_quote_integrity()` to all three sub-auditors. Pulls
the cited authority's body via `load_authority_body()`, normalises both
the body and the quoted text, and verifies via substring match plus a
token-overlap fallback (>=80% of >=3-letter tokens within a 1.5x window).
KR variant uses substring only (Hangul has no whitespace word
boundaries). +12 tests (CA 49, KR 23, EU 28).

## v17 — KR/EU future-effective check (`02e4f44..633ba93`)

Mirrors v11's CA future-effective check for KR and EU. Both KBs use
YYYYMMDD-format effective_date in their article indexes. KR uses
bilingual present-tense triggers (English `currently`/`requires` plus
Korean `현재`/`지금`/`시행 중`/`반드시`/`해야 한다`); EU uses English-only.
Today (2026-05-07) has 0 future-effective articles in either KB; the
mechanism is forward-looking. +6 tests.

## v16 — Worked-examples cookbook (`e90a627`)

`docs/examples.md` (245 lines) — 7 worked auditor examples with real
inputs and the actual JSON output the unified auditor produces, covering
each of the major check categories. Useful for onboarding new
contributors and for explaining auditor behaviour to non-implementer
users.

## v15 — CI for schema validation + kb-diff + coverage reports (`6db152d`)

Wires the v13-v14 schema validator, KB snapshot diff, and coverage
reports into the GitHub Actions CI as separate steps so each gets its
own pass/fail signal in the PR check log. Graceful skip when KR/EU
sibling repos are unavailable on the CI runner.

## v14 — KB snapshot diff CLI (`905e15c`)

`scripts/kb-diff.py` — set-diff between two snapshots of the unified
authority index, with per-namespace breakdowns. Surfaces additions,
removals, and id renames between any two commits. Used in CI to
flag unexpected churn.

## v13 — KB schema validation + reverse lookup tools (`966f37e..7d5a73a..16c7ca3..8e1d175..9745fcf`)

Five small tools rounded into one round:

- `scripts/validate-kb-schema.py` — checks 14 indexes (2,414 items
  total) against required-field expectations.
- `scripts/who-is.py` — pretty-prints all metadata for a single
  authority id, parsing markdown frontmatter directly.
- `scripts/who-cites.py` — reverse citation lookup ("which authorities
  reference X?").
- `scripts/coverage-report-all.py` — unified CA+KR+EU coverage dashboard.
- `tests/test_e2e_unified_auditor.py` — integration test piping a
  curated multi-juris answer through the full auditor stack.

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

| Round | Total tests | Delta |
|---|---|---|
| v3 | 11 (CA only) | seed |
| v4 | 48 | + KR sub 6, EU sub 6 |
| v5 | 72 | + EU case lookup, KR/EU sanitize |
| v6 | 79 | + EDPB binding, KR enforcement-rule, external-law |
| v7 | 94 | + cross-jurisdiction 15 |
| v8 | 106 | + labels, vocab, vague |
| v9 | 119 | + unified, STRICT |
| v10 | 125 | docs + CI only |
| v11 | 133 | + future-effective 3, coverage 5 |
| v12 | 144 | + KR coverage 4, EU coverage 8 |
| v13 | 162 | + schema 6, who-is/cites 4, coverage-all 4, e2e 4 |
| v14-v16 | 195 | + diff/CI/cookbook validation |
| v17 | 201 | + KR/EU future-effective 6 |
| v18 | 213 | + quote integrity 12 (CA 4, KR 4, EU 4) |
| v19 | 223 | + golden-set e2e 10 (5 fixtures × 2) |
| v20 | 223 | retrieval/auditor fixes; no new tests |
