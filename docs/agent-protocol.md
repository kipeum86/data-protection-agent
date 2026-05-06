# Data Protection Agent Protocol

Status: initial runtime protocol
Date: 2026-05-06

## 1. Purpose

This protocol defines how the merged `data-protection-agent` should classify questions, retrieve local authorities, and produce orchestrator-compatible outputs.

The KB lives under namespaced folders:

- `kb/eu-gdpr`
- `kb/kr-pipa`
- `kb/us-ca`

The agent must use local indexes before relying on external knowledge.

## 2. Runtime Flow

1. Classify the request into one mode:
   - `pipa`
   - `gdpr`
   - `california`
   - `comparative`
   - `fallback_us`
   - `fallback`
2. Retrieve candidate authorities:

```bash
python3 scripts/retrieve_authorities.py "<question>" --top-k 12
```

3. For a standalone contract-compliant research packet, run:

```bash
python3 scripts/run_data_protection_agent.py "<question>" --output-dir <OUTPUT_DIR> --print-summary
```

4. Read the highest-value local markdown authorities.
5. Draft the answer only from grounded authorities.
6. Preserve source-grade and authority-level caveats.
7. Emit result and metadata files if the orchestrator provides an output directory.

## 3. Output Contract

Required result file:

```text
{OUTPUT_DIR}/data-protection-agent-result.md
```

Required metadata file:

```text
{OUTPUT_DIR}/data-protection-agent-meta.json
```

Minimum metadata shape:

```json
{
  "summary": "",
  "research_mode": "pipa|gdpr|california|comparative|fallback_us|fallback",
  "jurisdictions": [],
  "domains": ["data_protection"],
  "issue_map": [],
  "comparison_matrix": [],
  "key_findings": [],
  "sources": [],
  "coverage_gaps": [],
  "error": null
}
```

## 4. Grounding Rules

- Cite local `unified_id` values in internal source lists.
- Prefer Grade A sources for legal rules.
- Use Grade B for practice context, administrative materials, mirror-backed cases, legal interpretations, or enforcement examples with caveats.
- Do not cite Grade C as legal authority.
- If retrieval returns no authority for a claim, mark a coverage gap.
- For comparative answers, analyze each jurisdiction separately before synthesis.

## 5. Local Retrieval Helper

`scripts/retrieve_authorities.py` is deterministic and local-only. It reads:

- `index/jurisdiction-routing.json`
- `index/unified-authority-index.json`
- `index/unified-topic-index.json`
- `config/rag-config.json`

It returns:

- classified research mode
- selected jurisdictions/namespaces
- matched topics
- ranked local authorities
- coverage gaps

## 6. Local Runner

`scripts/run_data_protection_agent.py` wraps retrieval and writes:

- `data-protection-agent-result.md`
- `data-protection-agent-meta.json`

The runner creates a grounded research packet, not a final legal opinion. It is safe to use before orchestrator integration because it only reads local indexes and local authority metadata.

## 7. Golden-Set Evaluation

`scripts/evaluate_golden_set.py` validates the local runner against `config/golden-set.json`.

Run:

```bash
python3 scripts/evaluate_golden_set.py --output-dir /tmp/dpa-golden --clean
```

The evaluator checks:

- routing mode and expected jurisdictions
- required output-contract metadata keys
- expected authority coverage
- forbidden authority leakage
- minimum source counts and local path existence
- coverage-gap handling

This is a local runner evaluation. It does not compare legacy and merged orchestrator profiles.
