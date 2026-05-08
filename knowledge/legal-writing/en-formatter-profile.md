# English Formatter Profile

Use this compact profile for English standalone legal research deliverables.

## Purpose

Transform completed legal research into a polished English legal research memo.
The output should be clear, professional, and audit-ready, without adding legal
judgment beyond the research result and metadata.

## Register

- Use formal but readable legal prose.
- Prefer direct, source-anchored conclusions over rhetorical advocacy.
- Avoid contractions, marketing language, and unsupported certainty.
- Use `may`, `should`, and `must` only when the research output supports the
  legal force of the statement.
- Do not promise Bluebook, OSCOLA, or jurisdiction-specific citation perfection
  unless those citations are already supplied in the research output.

## Default Structure

Use this structure unless the user requests another one:

1. `# Title`
2. `## Executive Summary`
3. `## Issues Presented`
4. `## Short Answer`
5. `## Analysis`
6. `## Limitations and Next Steps`
7. `## Sources`

For multi-jurisdiction matters, analyze each jurisdiction separately before
cross-jurisdiction synthesis. If a comparison matrix exists in metadata,
preserve it as a visible table.

## Section Drafting Rules

### `## Executive Summary`

- Start with the answer and its confidence limit.
- State the controlling jurisdiction and main source anchor.
- If the output is fallback, error-bearing, or source-limited, say so in the
  first paragraph.
- Keep it useful to a legal professional who reads only the summary.

### `## Issues Presented`

- Convert each material `issue_map` item into a question or short issue label.
- Preserve jurisdiction and domain boundaries.
- For game regulation, keep game-law taxonomy visible when material.

### `## Short Answer`

- Give the practical answer issue by issue.
- Use source IDs in the answer, not only in the final source table.
- Preserve confidence levels and currentness caveats.
- Do not use definitive language for source-limited or medium/low-confidence
  conclusions.

### `## Analysis`

- Use CRAC by default: conclusion, rule/source, application, caveat.
- Use IRAC when the issue is complex and the reader needs a separate issue
  setup.
- For multi-jurisdiction analysis, write jurisdiction-specific paragraphs first
  and synthesize after.

### `## Limitations and Next Steps`

- Move all `coverage_gaps`, `fallback_reason`, `error`, and specialist handoffs
  into this section.
- Explain how each limitation affects confidence or use of the conclusion.
- Make next steps concrete: verify a source, confirm a fact, run a specialist
  review, or update the jurisdictional comparison.

### `## Sources`

- Include every metadata source exactly once.
- Preserve source ID, grade, title, citation, pinpoint, and access note.
- Do not improve citation form by inventing missing reporter, section, date, or
  pinpoint details.

## Analysis Style

- Use CRAC or IRAC when it improves clarity, but keep the structure lean.
- Start each major issue with a concise answer.
- Tie each legal proposition to a visible `src_*` source anchor.
- Preserve jurisdiction labels, currentness caveats, and confidence limits.
- Distinguish verified rules from tentative or source-limited conclusions.
- Keep practical next steps concrete and traceable to coverage gaps.

## Paragraph Patterns

Use patterns like these:

```text
Based on the current official-source anchor, the conclusion should be treated as
source-limited until the specific regulator text and effective date are verified
(src_001).
```

```text
For Korea, the issue is best framed as a game-regulation disclosure and
enforcement question. The research record supports that framing through src_001,
but it does not yet support a final sanction amount or deadline.
```

Avoid patterns like these:

```text
The company is clearly liable.
```

```text
This is generally prohibited under consumer protection law.
```

These drop source, jurisdiction, confidence, and legal-rule specificity.

## Citation Style

- Preserve source IDs such as `src_001`.
- Use the citation text already supplied in metadata.
- Do not invent reporters, statutory sections, regulator titles, effective
  dates, or pinpoint references.
- If the citation form is incomplete, keep the source ID and mark the missing
  detail as a limitation.

## Terminology

- Use one English term consistently for each concept.
- When Korean legal terms are material in an English memo, introduce a readable
  translation and preserve the Korean term in parentheses when useful.
- Do not convert game-law terms into broad consumer-law terms unless the
  research output does that.
- Do not use `must`, `prohibited`, `liable`, `sanctioned`, or `exempt` unless
  the source support and confidence level allow it.

## Source And Gap Handling

- Every material paragraph should cite a `src_*` anchor or clearly synthesize
  already cited analysis.
- Do not hide `coverage_gaps`.
- If support is missing, write
  `[Source Coverage Gap: describe the missing authority or verification]`.
- If privacy, IP, tax, finance, employment, or another specialist issue was
  delegated, keep the handoff visible rather than converting it into a final
  conclusion.

## DOCX-Ready Markdown

When producing `docx_ready_markdown`, use stable Markdown headings and simple
tables. Do not claim that page layout, Word styles, native footnotes, or tracked
changes have been applied unless a real DOCX generation workflow was run.
