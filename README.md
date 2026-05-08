# Data Protection Agent

Merged privacy/data-protection research agent workspace for:

- EU GDPR
- Korea PIPA
- California CCPA/CPRA

The runtime KB is imported under `kb/<namespace>` and indexed under `index/`.

## Sub-KBs

| Sub-KB    | Jurisdiction        | Records | Primary law              |
|-----------|---------------------|---------|--------------------------|
| eu-gdpr   | EU                  | 1,029   | GDPR (+ ePrivacy, AI Act)|
| kr-pipa   | Korea               | 929     | PIPA (+ Network Act)     |
| us-ca     | California (US)     | 237     | CCPA as amended by CPRA  |
| **total** |                     | **2,195** |                        |

Each sub-KB ships with its own per-section markdown, JSON indexes, and a
regex-based citation auditor. A cross-jurisdiction auditor sits above the
three sub-auditors to catch routing mismatches, vocabulary confusion, and
vague law references. From v19 onward, an LLM-facing answering layer
(skills + templates + slash command + output validator) sits above the
auditor stack so a Claude Code session can run the full intake → routing
→ retrieval → grounding → composition → quality-check workflow against
any privacy-law question.

## Quick Start

### Inside a Claude Code session

```text
/answer Under California law, when must a business provide notice at or before collection?
```

Routes intake → applies the v19 skills (kb-retrieval, trust-boundary,
claim-grounding, result-memo-composition or comparative-composition,
quality-check) → writes the two contract files
(`data-protection-agent-result.md` + `data-protection-agent-meta.json`)
under `$OUTPUT_DIR` or `outputs/data-protection-agent/`.

### Direct CLI (no LLM in the loop)

Refresh imported KBs:

```bash
python3 scripts/import_namespaced_kbs.py --clean
```

Retrieve local authorities for a question:

```bash
python3 scripts/retrieve_authorities.py "Does the CCPA require honoring Global Privacy Control opt-out signals?" --format markdown
```

Write the deterministic research-packet output (no LLM composition):

```bash
python3 scripts/run_data_protection_agent.py "Compare GDPR and CCPA automated decisionmaking obligations." --output-dir /tmp/dpa-output --print-summary
```

Validate output against the v19 contract:

```bash
python3 scripts/validate-output.py /tmp/dpa-output
```

Run the local golden-set evaluator (13 fixtures, both legacy and v19 cases):

```bash
python3 scripts/evaluate_golden_set.py --output-dir /tmp/dpa-golden --clean
```

Audit a draft answer:

```bash
# Single-call unified auditor (recommended) — runs all 4 auditors at once
echo "Per Cal. Civ. Code § 1798.150, businesses must ..." | \
  python3 scripts/audit-unified.py

# Or invoke individual auditors directly
echo "Per Cal. Civ. Code § 1798.150, ..." | \
  python3 sources/us-ca/scripts/audit-california-citations.py

echo "GDPR Article 6 sets lawful bases." | \
  python3 sources/eu-gdpr/scripts/audit-europe-citations.py

echo "개인정보 보호법 제15조에 따라 ..." | \
  python3 sources/kr-pipa/scripts/audit-korea-citations.py
```

Run tests:

```bash
# Cross-cutting tests (top-level)
PYTHONPATH=. pytest -q tests

# Per sub-KB
cd sources/us-ca && PYTHONPATH=. pytest -q tests
cd sources/kr-pipa && PYTHONPATH=. pytest -q tests
cd sources/eu-gdpr && PYTHONPATH=. pytest -q tests
```

### Optional: pre-commit auditor hook

Enable the pre-commit hook to run the unified auditor on staged `.md`
files automatically:

```bash
git config core.hooksPath .githooks
```

The hook aborts commits with `error` findings and prints `warn` findings
inline (without aborting). Disable with `git config --unset core.hooksPath`.

Skip the hook for a single commit with `git commit --no-verify`.

## Architecture

```
data-protection-agent/
├── CLAUDE.md, AGENTS.md       # Agent rules + trust boundary policy
├── README.md, CHANGELOG.md
│
├── kb/                        # Unified runtime KB (generated)
│   ├── eu-gdpr/               #   ← imported from sibling GDPR-expert
│   ├── kr-pipa/               #   ← imported from sibling PIPA-expert
│   └── us-ca/                 #   ← imported from local sources/us-ca/
│       └── index/{ca,kr,eu}-topic-index.json   # Per-namespace topic crosswalk
│
├── index/                     # Unified indexes (jurisdiction-routing,
│                              #   unified-authority-index, unified-topic-index, …)
│
├── sources/{us-ca,kr-pipa,eu-gdpr}/
│   ├── citation_auditor/      # per-jurisdiction regex auditor (10 checks each ~)
│   ├── scripts/               # per-jurisdiction CLI + sanitize.py
│   └── tests/
│   (us-ca additionally has library/, index/, config/, build_california_kb.py)
│
├── cross_jurisdiction_auditor/   # Layer above the 3 sub-auditors
│   └── audit.py    # 4 checks: routing, vocab, labels, vague refs
│
├── unified_auditor/           # Single-invocation runner over all 4 auditors
│   └── run.py
│
├── scripts/                   # Top-level CLIs
│   ├── import_namespaced_kbs.py
│   ├── retrieve_authorities.py
│   ├── run_data_protection_agent.py
│   ├── evaluate_golden_set.py
│   ├── audit-unified.py
│   ├── audit-cross-jurisdiction.py
│   ├── validate-output.py     # v19 output-contract validator
│   ├── coverage-report-all.py, who-cites.py, who-is.py, kb-diff.py,
│   └── validate-kb-schema.py
│
├── tests/                     # Cross-cutting + e2e (123 tests)
│   └── test_e2e_agent_pipeline.py    # v19 golden-fixture parametrised
│
├── templates/                 # v19 result memo + per-mode variants
│   ├── result.md, meta.example.json
│   └── modes/{single-jurisdiction,multi-jurisdiction,
│              comparative-matrix,fallback}.md
│
├── .claude/
│   ├── agents/data-protection-agent.md
│   ├── commands/answer.md     # /answer slash command
│   └── skills/                # 8 skills (1 v8 + 7 v19)
│       ├── citation-auditor/SKILL.md
│       ├── intake-and-routing/SKILL.md
│       ├── kb-retrieval/SKILL.md
│       ├── trust-boundary/SKILL.md
│       ├── claim-grounding/SKILL.md
│       ├── result-memo-composition/SKILL.md
│       ├── comparative-composition/SKILL.md
│       └── quality-check/SKILL.md
│
└── docs/
    ├── auditors.md                              # Catalog of all 30+ checks
    ├── agent-protocol.md
    ├── kb-operations-guide.md
    ├── examples.md                              # 7 worked auditor cases
    ├── california-local-kb-implementation.md
    └── california-local-kb-hardening-plan.md
```

(Round-by-round plan documents live under `.local/planning/v{N}/` and
are not tracked in git after v18; see `docs/README.md`.)

## Citation auditor

The unified auditor catches ~30 distinct error patterns across 4 layers
(3 sub-auditors + 1 cross-jurisdiction layer). See
[docs/auditors.md](docs/auditors.md) for the full catalog.

Notable additions since v12:
- **v17:** KR/EU future-effective check (mirror of v11 CA) — warns when an
  authority with a future `effective_date` is cited with present-tense
  language and no future-framing nearby. Bilingual triggers for KR.
- **v18:** Quote integrity check (CA/KR/EU) — verifies that quoted text
  in an answer actually appears in the cited authority's KB body.
  Catches the most common LLM hallucination pattern: correct citation id
  paired with a fabricated quote.
- **v20:** False-positive cleanup — `_strip_inline_code()` skips backtick
  paths, lowercase-only id matching, namespace tokens excluded;
  `fallback_us` recognised as a fallback mode by the validator;
  cross-jurisdiction labels check skips fallback memos.

Aggregate severity:
- `error` (statute/regulation/case id missing, unpublished as controlling)
  → answer must be revised before sending.
- `warn` (binding misuse, vocabulary mismatch, vague references,
  quote-integrity mismatch)
  → surface to user inline.
- `pass` → ship.

### Test coverage

| Layer | Tests |
|---|---|
| CA sub-auditor | 49 |
| KR sub-auditor | 23 |
| EU sub-auditor | 28 |
| Cross-cutting + e2e (incl. golden-set parametrised) | 123 |
| **Total** | **223** |

### Optional toggles

- `STRICT_JURISDICTION_LABELS=true`: every signalled jurisdiction in a
  multi-juris answer must have an explicit label heading. Default mode
  accepts partial labelling.

## Agent answering pipeline (v19)

The v19 round adds an LLM-facing answering layer on top of the auditor.
Inside a Claude Code session, `/answer "<question>"` walks an 8-stage
workflow:

1. **Intake & routing** — `intake-and-routing` skill classifies the
   question into one of `ca_only / kr_only / eu_only / multi_jurisdiction
   / comparative / fallback_us / fallback`, using
   `index/jurisdiction-routing.json`.
2. **Retrieval** — `kb-retrieval` skill runs `retrieve_authorities.py`
   against the routed namespace(s) with topic-boost from
   `unified-topic-index.json` (29 curated topics: 13 CA + 8 KR + 8 EU).
3. **Trust boundary** — `trust-boundary` skill enforces that ingested
   KB bodies are data, not instructions, before composition.
4. **Claim grounding** — `claim-grounding` skill verifies every material
   claim has a local authority id, a verifiable pinpoint, and a
   currentness status. Fail = block; record in `coverage_gaps`.
5. **Composition** — `result-memo-composition` (or
   `comparative-composition` for multi-juris / comparative modes)
   produces the 9-section memo with strict source-anchor discipline.
6. **Quality-check** — `quality-check` skill runs the citation auditor
   plus `validate-output.py`. Block on any auditor `fail`; surface
   `warn` findings inline.
7. **Write** — emit `data-protection-agent-result.md` and
   `data-protection-agent-meta.json` to the configured output dir.

Output contract validator: `scripts/validate-output.py` (~538 lines,
stdlib only) — both v19 strict and legacy_packet modes.

Golden-set fixtures: `config/golden-set.json` (13 cases — 5 v19
fixtures + 8 legacy CA cases). Parametrised e2e tests run validator +
auditor against every fixture.

## Key Docs

- [Agent protocol](docs/agent-protocol.md)
- [KB operations guide](docs/kb-operations-guide.md)
- [Citation auditor catalog](docs/auditors.md)
- [Worked auditor examples](docs/examples.md)
- [California KB implementation](docs/california-local-kb-implementation.md)
- [California KB hardening plan](docs/california-local-kb-hardening-plan.md)
- [Documentation layout](docs/README.md)

Per-round plan documents (v3-v20) live under `.local/planning/v{N}/`
and are not tracked in git. The `CHANGELOG.md` summarises every round.

## Source of Truth

- `eu-gdpr`: sibling `GDPR-expert`
- `kr-pipa`: sibling `PIPA-expert`
- `us-ca`: local `sources/us-ca`

Do not hand-edit imported files under `kb/`; update the source-of-truth folder and re-import.

## Contributing

Read [CLAUDE.md](CLAUDE.md) (agent rules + jurisdiction routing) and
[AGENTS.md](AGENTS.md) (trust boundary policy) before opening a PR.

CI runs all tests on every PR (see `.github/workflows/ci.yml`).
