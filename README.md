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
vague law references.

## Quick Start

Refresh imported KBs:

```bash
python3 scripts/import_namespaced_kbs.py --clean
```

Retrieve local authorities for a question:

```bash
python3 scripts/retrieve_authorities.py "Does the CCPA require honoring Global Privacy Control opt-out signals?" --format markdown
```

Write output-contract files locally:

```bash
python3 scripts/run_data_protection_agent.py "Compare GDPR and CCPA automated decisionmaking obligations." --output-dir /tmp/dpa-output --print-summary
```

Run the local golden-set evaluator:

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

## Architecture

```
data-protection-agent/
├── CLAUDE.md, AGENTS.md       # Agent rules + trust boundary policy
├── README.md
│
├── kb/                        # Unified runtime KB (generated)
│   ├── eu-gdpr/library/       #   ← imported from sibling GDPR-expert
│   ├── kr-pipa/library/       #   ← imported from sibling PIPA-expert
│   └── us-ca/library/         #   ← imported from local sources/us-ca/
│
├── index/                     # Unified indexes (jurisdiction-routing,
│                              #   unified-authority-index, etc.)
│
├── sources/{us-ca,kr-pipa,eu-gdpr}/
│   ├── citation_auditor/      # per-jurisdiction regex auditor
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
│   └── audit-cross-jurisdiction.py
│
├── tests/                     # Cross-cutting tests
│
├── .claude/skills/citation-auditor/SKILL.md   # Slash skill for Claude Code
│
└── docs/
    ├── auditors.md                              # Catalog of all checks
    ├── agent-protocol.md
    ├── kb-operations-guide.md
    ├── california-local-kb-implementation.md
    ├── california-local-kb-hardening-plan.md
    ├── integration-hardening-plan.md            # v3
    └── integration-hardening-plan-v{4..10}.md
```

## Citation auditor

The unified auditor catches ~25 distinct error patterns across 4 layers
(3 sub-auditors + 1 cross-jurisdiction layer). See
[docs/auditors.md](docs/auditors.md) for the full catalog.

Aggregate severity:
- `error` (statute/regulation/case id missing, unpublished as controlling)
  → answer must be revised before sending.
- `warn` (binding misuse, vocabulary mismatch, vague references)
  → surface to user inline.
- `pass` → ship.

### Test coverage

| Layer | Tests |
|---|---|
| CA sub-auditor | 42 |
| KR sub-auditor | 16 |
| EU sub-auditor | 21 |
| Cross-jurisdiction | 35 |
| Unified runner | 5 |
| KB import | 6 |
| **Total** | **125** |

### Optional toggles

- `STRICT_JURISDICTION_LABELS=true`: every signalled jurisdiction in a
  multi-juris answer must have an explicit label heading. Default mode
  accepts partial labelling.

## Key Docs

- [Agent protocol](docs/agent-protocol.md)
- [KB operations guide](docs/kb-operations-guide.md)
- [Citation auditor catalog](docs/auditors.md)
- [California KB implementation](docs/california-local-kb-implementation.md)
- [California KB hardening plan](docs/california-local-kb-hardening-plan.md)
- Integration hardening rounds: `docs/integration-hardening-plan-v{3..10}.md`

## Source of Truth

- `eu-gdpr`: sibling `GDPR-expert`
- `kr-pipa`: sibling `PIPA-expert`
- `us-ca`: local `sources/us-ca`

Do not hand-edit imported files under `kb/`; update the source-of-truth folder and re-import.

## Contributing

Read [CLAUDE.md](CLAUDE.md) (agent rules + jurisdiction routing) and
[AGENTS.md](AGENTS.md) (trust boundary policy) before opening a PR.

CI runs all tests on every PR (see `.github/workflows/ci.yml`).
