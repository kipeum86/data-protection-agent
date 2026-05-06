# California Sub-KB Operations

Status: active runbook
Date: 2026-05-06
Namespace: `us-ca`
Source of truth: `sources/us-ca`
Runtime copy: `kb/us-ca`

## 1. Scope

The California sub-KB covers CCPA as amended by CPRA, 2026 CPPA regulations, high-relevance adjacent California privacy statutes, CPPA/OAG guidance, enforcement/admin materials, and CCPA/California privacy case law.

Current source registry highlights:

- Grade A: CCPA statute, CPPA regulations, CPPA/OAG guidance, official/court-hosted published opinions, GovInfo federal opinions, CalOPPA, customer records/breach notice, CMIA, SOPIPA, Age-Appropriate Design Code, Data Broker/Delete Act, CIPA.
- Grade B: OAG/CPPA enforcement actions, administrative orders, and SCOCAL mirror-backed California Supreme Court published opinions.
- Grade C: reserved discovery folders only.

Current counts:

- `sources/us-ca/index/source-registry.json`: 237 authority files.
- `sources/us-ca/index/ca-case-index.json`: 29 cases.
- State published/citable case coverage: 7 total, including 6 Grade B SCOCAL mirror-backed California Supreme Court opinions.

## 2. Source Hierarchy

| Material | Default grade | Notes |
|---|---|---|
| CPPA statute/regulation PDFs | A | Use per-section markdown and preserve source checksums. |
| California LegInfo adjacent statutes | A | Parse by section; verified-absent section gaps must be documented. |
| CPPA/OAG official guidance | A | Nonbinding guidance, not statute/regulation. |
| Official court-hosted California opinions | A | Only if raw official/court-hosted source is fetched and parsed. |
| GovInfo or court-hosted federal opinions | A source, persuasive authority | Do not call federal cases California appellate precedent. |
| OAG/CPPA enforcement/admin materials | B | Administrative material, not judicial precedent. |
| SCOCAL or other public case mirrors | B | Keep `official_url` and fetched `source_url` separate. |
| Discovery/commentary | C | Do not ground legal conclusions on it. |

## 3. Update Triggers

- CPPA publishes new statute/regulation PDFs or final approved text.
- New CPPA rulemaking, guidance, advisory material, or CPI threshold update.
- New OAG settlement, sweep, complaint, judgment, or enforcement example.
- New CPPA administrative order or decision.
- New California Supreme Court or Court of Appeal published opinion on CCPA, CIPA, CMIA, CalOPPA, data breach, data brokers, minors, ad tech, or related privacy issues.
- Major federal CCPA/CIPA/CMIA opinion from GovInfo or court-hosted source.

## 4. Workflow

Run from `sources/us-ca` unless noted.

```bash
python3 scripts/build_california_kb.py --fetch-legal --index --validate
python3 scripts/build_california_kb.py --fetch-adjacent --index --validate
python3 scripts/build_california_kb.py --fetch-guidance --index --validate
python3 scripts/build_california_kb.py --fetch-enforcement --index --validate
python3 scripts/build_california_kb.py --fetch-cases --index --validate
PYTHONPATH=. pytest -q tests
```

Then return to repo root:

```bash
python3 scripts/import_namespaced_kbs.py --clean
PYTHONPATH=. pytest -q tests/test_namespaced_kb_import.py
```

Check counts:

```bash
jq '.total_files' sources/us-ca/index/source-registry.json
jq '.count' sources/us-ca/index/ca-case-index.json
jq '.by_namespace["us-ca"], .count' index/unified-authority-index.json
```

## 5. California-Specific Guardrails

- Frame current obligations as CCPA as amended by CPRA.
- Do not treat CPRA as a separate current standalone law except when discussing amendment history.
- Do not call CIPA, CMIA, CalOPPA, SOPIPA, Data Broker/Delete Act, or Age-Appropriate Design Code CCPA provisions.
- Do not treat OAG/CPPA guidance as binding law.
- Do not treat OAG settlements, press releases, sweeps, or CPPA administrative orders as judicial precedent.
- Do not treat federal district court orders as California appellate precedent.
- Published 9th Circuit opinions may be citable federal authority, but they are not California Supreme Court or California Court of Appeal precedent.
- Do not cite unpublished/non-citable decisions as controlling authority.
- For 2026-effective regulations, cite the CPPA 2026 source or final approved updates text, not only an older draft.

## 6. Mirror Policy

The current KB includes 6 California Supreme Court published opinions fetched from Stanford SCOCAL because the corresponding California Courts archive PDF raw fetch returned F5 403/HTML bodies locally.

Mirror-backed records must:

- live under `library/grade-b/ca-courts-published-opinion-mirrors/`
- use `source_grade: B`
- preserve the California Courts archive URL in `official_url`
- preserve the fetched mirror URL in `source_url`
- include `source_mirror_warning`
- avoid wording that says the local raw source is an official California Courts PDF

Promote a mirror-backed case to Grade A only after the official/court-hosted PDF or HTML is fetched, parsed, indexed, and validated.

## 7. Validation Gates

Run these after any California source change from repo root:

```bash
cd sources/us-ca
python3 scripts/build_california_kb.py --index --validate
PYTHONPATH=. pytest -q tests
cd ../..
python3 scripts/import_namespaced_kbs.py --clean
PYTHONPATH=. pytest -q tests/test_namespaced_kb_import.py
```

## 8. Backlog Watch

- Official California Courts archive PDF promotion for SCOCAL mirror-backed cases.
- New CPPA/OAG enforcement and administrative materials.
- New federal and California published opinions on CCPA private right of action, CIPA pixels/session replay, CMIA health tracking, and data brokers.
- Periodic review of AADC and Data Broker verified-absent section gaps.
