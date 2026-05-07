---
description: Answer a privacy/data-protection question using the unified KR PIPA / EU GDPR / US-CA CCPA KBs with full source-grounding and citation auditing.
argument-hint: "<question text> [mode=ca_only|kr_only|eu_only|multi_jurisdiction|comparative]"
---

Run the data-protection-agent workflow described in `CLAUDE.md` for the
question in `$ARGUMENTS`.

If `$ARGUMENTS` is empty, ask the user for:

1. The privacy/data-protection question.
2. Whether they want a research packet only or a full answered memo.
3. Specific jurisdiction(s), if obvious.

Then execute the 8-stage workflow:

1. Apply `intake-and-routing` skill.
2. Apply `kb-retrieval` skill.
3. Apply `trust-boundary` skill before any retrieved text enters reasoning.
4. Apply `claim-grounding` skill for material propositions.
5. Apply `result-memo-composition` skill, or `comparative-composition` for
   comparative and multi-jurisdiction modes.
6. Apply `quality-check` skill. Block on any auditor fail.
7. Write `data-protection-agent-result.md` and
   `data-protection-agent-meta.json` to `$OUTPUT_DIR`, or
   `outputs/data-protection-agent/` if unset.
8. Print a one-line summary: mode, jurisdictions, source count, audit status.

Defaults:

- Output directory: `outputs/data-protection-agent/` if `$OUTPUT_DIR` is unset.
- Top-K retrieval: 12.
- Mode: self-classified unless explicitly provided.
