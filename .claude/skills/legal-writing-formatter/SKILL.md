---
name: legal-writing-formatter
description: Use only after the research result and metadata are complete, or when the user explicitly asks for a standalone legal research deliverable.
disable-model-invocation: true
---

# Legal Writing Formatter

Use this skill only after the research result and metadata are complete, or when
the user explicitly asks for a standalone legal research deliverable.

The detailed formatting reference (typography, headings, citation
form, table style, list patterns) is in
`references/legal-writing-formatting-guide.md`. Load that file when
preparing a polished standalone deliverable. The compact instructions
below summarize the high-level shape; the guide is the source of
truth on typographic choices.

This is a formatter for research work product. It is not a separate drafting
agent, and it must not invent legal conclusions, authorities, risk assessments,
or recommendations beyond `data-protection-agent-result.md` and
`data-protection-agent-meta.json`.

For standalone artifact layout, naming, manifest, and audit sequencing, apply
`docs/standalone-workflow.md`.

## When To Apply

Apply this skill when:

- the repo is being used standalone and the user wants a polished memo,
  opinion-style research note, client-ready research summary, or executive
  research brief;
- the user asks for a DOCX-ready source document;
- the orchestrator asks for a handoff packet for a downstream legal-writing
  specialist.

Do not apply it when the task is only to produce the normal orchestrator
contract files.

## Output Modes

Select exactly one mode unless the user requests multiple artifacts.

| Mode | Use When | Output |
|---|---|---|
| `standalone_markdown` | Default standalone deliverable | Polished Markdown memo or opinion-style research note |
| `handoff_packet` | Downstream legal-writing agent will draft | Compact packet preserving issues, sources, gaps, and style target |
| `docx_ready_markdown` | User wants Word-ready source or a binary DOCX generated from Markdown | Markdown with stable headings, tables, citation anchors, and no chat-only commentary |

This repo includes a binary DOCX MVP via `scripts/render-docx.py`. If the user
asks for DOCX, first produce and validate `docx_ready_markdown`, then render the
DOCX and run DOCX extraction or audit checks. Do not promise native Word
footnotes, tracked changes, comments, or complex page layout.

## Cross-Cutting Output Mode

When `output_mode` is set to `executive_brief`, `comparative_matrix`,
`enforcement_case_law`, or `black_letter_commentary`, apply
`skills/output-mode-composition.md` after deliverable selection but
before legal prose rewrite. The composition skill resolves the mode
template, applies the per-mode counter-analysis minimum, and produces
the mode-shaped deliverable file.

The packaging mode (`standalone_markdown` / `handoff_packet` /
`docx_ready_markdown`) is independent. A given run can produce
`comparative_matrix` + `docx_ready_markdown` or `executive_brief` +
`handoff_packet`. Defaults are recorded in
`knowledge/output-modes/mode-index.md`.

## Transformation Workflow

The formatter rewrites research work product into a deliverable. It does not
research, rank, or decide new legal points.

1. Input audit
   - Read `data-protection-agent-result.md` and
     `data-protection-agent-meta.json`.
   - Confirm the result already passed the output contract and quality standard.
   - Build a source map from `sources[*].id`, `grade`, `citation`,
     `pinpoint`, and `url_or_access`.
   - Build an issue map from `issue_map[*]`, `key_findings`,
     `coverage_gaps`, and `co_running_agents`.
2. Deliverable selection
   - Select `standalone_markdown`, `handoff_packet`, or
     `docx_ready_markdown`.
   - Select exactly one language profile unless bilingual output is requested.
   - For `docx_ready_markdown`, also apply
     `knowledge/legal-writing/docx-ready-markdown-profile.md`.
3. Issue condensation
   - Convert each `issue_map` item into a visible issue or sub-issue.
   - Merge duplicate issues only if their authority IDs and confidence limits
     remain visible.
   - Preserve `comparison_matrix` as a table when present.
4. Source anchoring
   - Attach `src_*` anchors to every material conclusion.
   - Use source IDs from metadata exactly; do not create display-only aliases.
   - If a conclusion needs a source that is absent, mark a source coverage gap
     instead of filling it with general legal knowledge.
5. Legal prose rewrite
   - Convert the result memo's mechanical sections into the selected legal
     writing structure.
   - Improve flow, headings, paragraph order, and terminology.
   - Preserve confidence and currentness limits in the body, not only in a
     final caveat.
6. Final audit
   - Check every cited `src_*` against metadata.
   - Check every metadata source appears in the final source table.
   - Check every coverage gap, fallback reason, error, and handoff remains
     visible.
   - Run `scripts/check-formatter-output.py` when local execution is available.
   - For external or client-facing standalone deliverables, run citation audit
     on the formatted deliverable and record the audit status in
     `standalone-deliverable-manifest.json`.
   - If binary DOCX is generated, record the DOCX path and render report in the
     manifest, and verify extracted DOCX text preserves material source anchors.

## Profile Selection

Load only the compact profile that matches both the language and the
packaging mode:

| Language | Packaging mode | Profile |
|---|---|---|
| `ko` | `docx_ready_markdown` (DOCX requested) | `knowledge/legal-writing/ko-legal-opinion-profile.md` |
| `ko` | `standalone_markdown`, `handoff_packet`, or no DOCX | `knowledge/legal-writing/ko-formatter-profile.md` |
| `en` | any | `knowledge/legal-writing/en-formatter-profile.md` |
| `bilingual` | any | both Korean profiles per ko language row + `en-formatter-profile.md` |

The default Korean DOCX path is the legal-opinion profile because the polished
renderer (`scripts/render-legal-opinion-docx.py`) supplies cover page,
hierarchical numbering, statutory block quotes, footnote markers, and a
master 각주 section that depend on the markdown patterns documented in that
profile. For non-DOCX Korean deliverables, the existing `ko-formatter-profile.md`
remains the right fit.

Override the default to `ko-formatter-profile.md` when the user explicitly
requests a quick draft, internal memo, or handoff packet, or when the requested
register is conversational. Record the override in the run's manifest
`audit.claim` field with a one-sentence reason.

Prefer Korean when the user question, result memo, or requested final output is
primarily Korean. Prefer English when the requested final output is primarily
English. For mixed-language matters, choose the output language requested by the
user and preserve foreign legal terms in parentheses where useful.

Do not load both profiles unless the user requests a bilingual deliverable.
Do not load a broad bilingual formatting guide by default.

## Mandatory Preservation Rules

The formatter must preserve:

- all material issues from `issue_map`;
- all `sources[*].id` anchors used by key findings or issue blocks;
- source grades and pinpoint limits;
- confidence levels and limiting caveats;
- `coverage_gaps`, fallback reasons, and errors;
- privacy or other specialist handoff boundaries;
- jurisdiction labels and temporal-status caveats.

Every substantive paragraph in the formatted output should either cite a known
`src_*` anchor or clearly state that it is a synthesis from cited analysis. If a
claim lacks support, mark it as `[Source Coverage Gap: describe missing support]`
instead of smoothing it away.

## Standalone Markdown Structure

For Korean, follow the selected Korean profile and use this default structure:

1. 제목
2. 요약
3. 쟁점
4. 검토의견
5. 분석
6. 한계 및 추가 확인사항
7. 출처

For English, follow the selected English profile and use this default structure:

1. Title
2. Executive Summary
3. Issues Presented
4. Short Answer
5. Analysis
6. Limitations and Next Steps
7. Sources

The final document may be more polished than the result memo, but it must remain
traceable to the result memo and metadata.

## Section Conversion Rules

Use this mapping when turning the research result into a standalone memo:

| Research Result | Korean Standalone | English Standalone |
|---|---|---|
| `## Question` | 제목 footnote/context or first summary sentence | title context or first executive-summary sentence |
| `## Route Context` | not usually shown unless route uncertainty matters | not usually shown unless route uncertainty matters |
| `## Short Answer` | `## 요약` and `## 검토의견` lead paragraph | `## Executive Summary` and `## Short Answer` |
| `## Issues` | `## 쟁점` | `## Issues Presented` |
| `## Analysis` | `## 분석` | `## Analysis` |
| `## Sources` | `## 출처` | `## Sources` |
| `## Coverage Gaps` | `## 한계 및 추가 확인사항` | `## Limitations and Next Steps` |
| `## Handoff Notes` | `## 한계 및 추가 확인사항` handoff paragraph | `## Limitations and Next Steps` handoff paragraph |

Do not drop route context when it explains a classification mismatch, fallback
mode, or specialist boundary.

## Handoff Packet Structure

When producing `handoff_packet`, include:

- target language and formatter profile;
- research mode, jurisdictions, domains, and route warnings;
- issue map with authority IDs;
- key findings with source IDs;
- source table;
- coverage gaps and handoff notes;
- requested tone, length, or document type if supplied by the user.

The packet should be compact enough for a downstream writing agent to load
without re-reading the full research corpus.

## DOCX-Ready Markdown Rules

For `docx_ready_markdown`:

- use one `#` title and stable `##`/`###` headings;
- keep tables simple Markdown tables;
- avoid chat commentary, markdown callouts, and invisible assumptions;
- keep source IDs visible next to propositions;
- include a final source table;
- keep any unresolved items as bracketed placeholders or coverage gaps.

Do not imply that DOCX conversion, Word styles, page layout, or tracked changes
have been applied unless a real DOCX generation workflow was run. When using
`scripts/render-docx.py`, describe the output as MVP DOCX rendering and keep the
known limitations visible when material.

## Prohibited Formatter Moves

- Do not add a new statute, case, regulator, article number, sanction, or
  effective date that is absent from metadata or the result memo.
- Do not convert `medium` or `low` confidence into a definitive client-facing
  conclusion.
- Do not collapse a coverage gap into soft prose such as "further review may be
  helpful" when the gap affects a material conclusion.
- Do not turn a privacy, tax, IP, finance, employment, or other handoff issue
  into this agent's final analysis.
- Do not omit source IDs for readability. If the user wants a cleaner final
  copy, keep source IDs in footnote-style parentheticals or a source appendix.
- Do not promise advanced page layout, tracked changes, native footnotes,
  comments, or Word styles unless a real generation workflow supports them.

## Quality Examples

Good:

```text
The current sanction conclusion should be treated as source-limited until the
official regulator text is verified (src_001).
```

Bad:

```text
The company will be sanctioned if it fails to disclose probabilities.
```

The bad version drops the confidence limit and states a sanction conclusion not
supported by the cited research record.

## Final Check

Before delivery:

- no new legal proposition was added without a source anchor;
- all cited `src_*` IDs exist in metadata;
- coverage gaps are visible in the formatted document;
- the language profile matches the requested output language;
- the output mode is named in the handoff or final note when ambiguity matters.
