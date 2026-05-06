# Data Protection Agent

Merged privacy/data-protection research agent workspace for:

- EU GDPR
- Korea PIPA
- California CCPA/CPRA

The runtime KB is imported under `kb/<namespace>` and indexed under `index/`.

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

Run smoke tests:

```bash
PYTHONPATH=. pytest -q tests
```

## Key Docs

- [Agent protocol](docs/agent-protocol.md)
- [KB operations guide](docs/kb-operations-guide.md)
- [California KB implementation](docs/california-local-kb-implementation.md)
- [California KB hardening plan](docs/california-local-kb-hardening-plan.md)

## Source of Truth

- `eu-gdpr`: sibling `GDPR-expert`
- `kr-pipa`: sibling `PIPA-expert`
- `us-ca`: local `sources/us-ca`

Do not hand-edit imported files under `kb/`; update the source-of-truth folder and re-import.
