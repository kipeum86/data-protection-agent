---
name: result-memo-composition
description: Use when writing data-protection-agent-result.md - enforces the 9-section structure with source-anchor discipline.
disable-model-invocation: true
---

# Result Memo Composition

Use this skill when writing `data-protection-agent-result.md`.

## Required Sections

Write these sections in order:

1. `# Data Protection Agent - Result`
2. `## Question`
3. `## Route Context`
4. `## Short Answer`
5. `## Issues`
6. `## Analysis`
7. `## Sources`
8. `## Coverage Gaps`
9. `## Handoff Notes`

For `multi_jurisdiction` and `comparative` modes, sections 5 and 6 are replaced
by `comparative-composition` output. Sections 1-4 and 7-9 remain required.

## Source-Anchor Rules

- Every key finding cites at least one `src_*` id.
- Every `issue_map[*].authority_ids[*]` exists in `meta.sources[*].id`.
- Cite local authority id alongside the official citation form, e.g.
  `Cal. Civ. Code § 1798.100 [us-ca:ca-civ-1798.100] [src_001]`.
- Mirror-backed cases must disclose mirror provenance, e.g.
  `(local copy from SCOCAL mirror; official URL: ...)`.

## Quality Floor

The memo must be useful to a privacy lawyer. For every material issue, include:

1. The legal issue.
2. The controlling rule from local authority.
3. How the rule applies to the user's facts.
4. Limits, uncertainty, or counter-analysis.
5. Practical next steps or handoff points.

A summary that omits these for a material issue fails `quality-check`.
