---
name: claim-grounding
description: Use after kb-retrieval and before result-memo-composition - verifies every material legal proposition is anchored to a local authority id with a verifiable pinpoint.
disable-model-invocation: true
---

# Claim Grounding

Use this skill before drafting analysis.

## Material Claim Definition

A claim is material if it would change the user's decision, the answer's
confidence, or the practical next step if it were wrong.

Examples:

- "GDPR Article 6 requires a lawful basis for processing." -> material.
- "Privacy law has been around for a while." -> not material.
- "CPRA amended the CCPA in 2020 and key obligations later became operative." -> material.

## Procedure

For each material claim:

1. Identify the supporting `source.id` and `authority_id`.
2. Confirm the `authority_id` exists in the appropriate sub-KB index under
   `kb/{namespace}/index/*.json`.
3. If the claim quotes authority text verbatim, verify the quote appears in the
   loaded body. The unified auditor's quote-integrity checks may fail otherwise.
4. Confirm currentness:
   - For statutes/regulations with `effective_date`, check that
     `effective_date <= today`.
   - If a source is future-effective, mark
     `[Not Yet In Force - effective YYYY-MM-DD]`.
   - If a source is repealed or superseded, mark
     `[Repealed - YYYY-MM-DD]`.
5. Emit a `claim_checks` metadata entry:

```json
{
  "claim_id": "claim_001",
  "issue_id": "issue_001",
  "claim": "GDPR Article 6 requires a lawful basis for processing.",
  "authority_ids": ["src_002"],
  "support_strength": "direct",
  "currentness": "current",
  "verification_method": "kb_body_substring"
}
```

## Hard Rules

- No material claim without a source id.
- If the local KB does not cover a claim, write that the local KB does not
  currently support it and add a `coverage_gaps` entry.
- High-confidence conclusions require direct support from a current or visibly
  caveated source.
- `background` and `unsupported` claim checks may not carry high-confidence
  conclusions.
