---
name: intake-and-routing
description: Use first when answering a privacy/data-protection question - parses user intent, classifies mode using index/jurisdiction-routing.json, and emits the routed mode plus selected sub-KBs.
disable-model-invocation: true
---

# Intake and Routing

Use this skill before retrieval, grounding, or drafting.

## Inputs

- `user_question` (required): the question text, Korean or English.
- `orchestrator_classification` (optional): parent orchestrator routing data.

## Valid Modes

- `ca_only`
- `kr_only`
- `eu_only`
- `multi_jurisdiction`
- `comparative`
- `fallback_us`
- `fallback`

Legacy packet modes from deterministic scripts map as follows:

- `california` -> `ca_only`
- `pipa` -> `kr_only`
- `gdpr` -> `eu_only`

## Procedure

1. If `orchestrator_classification.mode` is present and valid, use it directly.
   Set `mode_source` to `orchestrator`.

2. If orchestrator classification is missing or uncertain, self-classify:
   - Read `index/jurisdiction-routing.json`.
   - For each route, count case-insensitive occurrences of each
     `routing_terms` entry in the user question.
   - US privacy signals without California-specific signals route to
     `fallback_us`.
   - 0 scored routes route to `fallback`.
   - 1 scored route maps to that jurisdiction's single-jurisdiction mode.
   - 2+ scored routes plus comparison language (`compare`, `vs`, `비교`,
     `차이`, `differences`) route to `comparative`.
   - 2+ scored routes without comparison language route to
     `multi_jurisdiction`.

3. Emit a routing block:

```json
{
  "research_mode": "comparative",
  "mode_source": "self_classified",
  "jurisdictions": ["KR", "EU", "US-CA"],
  "namespaces": ["kr-pipa", "eu-gdpr", "us-ca"],
  "classification_warnings": []
}
```

## Jurisdiction Map

- `KR` -> `kr-pipa`
- `EU` -> `eu-gdpr`
- `US-CA` -> `us-ca`

## Hard Rules

- If the jurisdiction is genuinely unclear, ask the user a concise clarifying
  question before proceeding.
- Do not silently use a sub-KB that was not routed.
- Never blend jurisdictions in a single paragraph. Multi-jurisdiction output
  uses labelled sections; comparative output uses labelled cells and sections.
- Record `classification_warnings` for close scores, mixed jurisdiction
  signals, or mismatch with an orchestrator-supplied route.
