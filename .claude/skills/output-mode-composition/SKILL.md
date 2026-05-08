---
name: output-mode-composition
description: Use when standalone use selects a non-canonical output_mode — composes a mode-shaped deliverable on top of the canonical research record using the matching template and counter-analysis discipline.
disable-model-invocation: true
---

# Output Mode Composition

Use this skill only when:

- the canonical research record (`data-protection-agent-result.md` and
  `data-protection-agent-meta.json`) is already complete and quality-gated; and
- the user, slash command, or intake payload selects an `output_mode`
  other than `canonical`.

This skill does not change the canonical research record. It composes a
*separate* mode-shaped deliverable file under `deliverables/`.

## Inputs

- The completed canonical research record.
- `output_mode` slug (one of `executive_brief`, `comparative_matrix`,
  `enforcement_case_law`, `black_letter_commentary`).
- Selected packaging mode (`standalone_markdown` / `handoff_packet` /
  `docx_ready_markdown`). Default per
  `knowledge/output-modes/mode-index.md`.
- Output language (`ko` / `en` / `bilingual`).
- When `output_mode` is unset on the request and `user-config.json`
  declares `output_preferences.default_output_mode`, use the config
  value as the default. The user's per-request override still wins.
- When `output_preferences.default_packaging` and
  `output_preferences.default_language` are present in the config and
  not overridden by the request, apply them as defaults to the
  packaging and language selections respectively.

## Steps

1. Resolve `output_mode` against `knowledge/output-modes/mode-index.md`:
   - load the matching template;
   - identify required frameworks (counter-analysis always;
     comparative framework for `comparative_matrix`).
2. Load the selected language profile from `knowledge/legal-writing/`.
3. Apply `skills/legal-writing-formatter.md` mandatory preservation rules:
   - all material issues from `issue_map`;
   - all `sources[*].id` anchors used by key findings or issue blocks;
   - source grades and pinpoint limits;
   - confidence levels and limiting caveats;
   - `coverage_gaps`, fallback reasons, and errors;
   - privacy or other specialist handoff boundaries;
   - jurisdiction labels and temporal-status caveats.
4. Render the mode-shaped deliverable into the selected template:
   - every section header from the template appears in the deliverable;
   - inapplicable axes (`comparative_matrix`) are explicitly `N/A`,
     not omitted;
   - every cited `src_*` anchor exists in metadata;
   - per-mode counter-analysis minimum is met.
5. Apply `knowledge/output-modes/counter-analysis-checklist.md` discipline
   per the per-mode minimum table.
6. For `comparative_matrix`, apply
   `knowledge/output-modes/comparative-framework.md`:
   - all ten standard axes appear as rows;
   - inapplicable axes are `N/A`;
   - extended axes are added only when the query requires them.
7. Carry the selected `output_mode`, audience, and format into the
   standalone deliverable manifest.
8. Run `scripts/check-formatter-output.py` with `--output-mode <slug>`
   when local execution is available.

## Mode Dispatch Rules

| `output_mode` | Required template sections (validator-enforced) |
|---|---|
| `executive_brief` | Scope and As-of Date; Key Conclusions; Counter-Analysis and Risk Assessment; Risk and Priority Ranking; Practical Implications; Immediate Action Checklist; Top Sources; Verification Guide |
| `comparative_matrix` | Scope and As-of Date; Comparative Matrix; Divergence Commentary; Counter-Analysis; Practical Implications; Annotated Bibliography; Verification Guide |
| `enforcement_case_law` | Scope and As-of Date; Conclusion Summary; Enforcement Timeline; Case and Decision Summaries; Counter-Analysis; Practical Implications; Annotated Bibliography; Verification Guide |
| `black_letter_commentary` | Scope and As-of Date; Legal System Overview; Core Definitions and Scope; Article-by-Article Commentary; Implementation Relationships; Practical Implications; Annotated Bibliography; Verification Guide |

## Quality Floor

- Do not invent legal propositions absent from the canonical research record.
- Do not collapse `coverage_gaps` into soft prose. They appear as
  visible caveats in the deliverable's body, not only in metadata.
- Do not promote a `medium` or `low` confidence finding into a
  client-facing definitive conclusion.
- Do not omit the per-mode minimum counter-analysis.
- Do not promise advanced DOCX features beyond what `scripts/render-docx.py`
  actually provides.

## Manifest Update

When a mode-shaped deliverable is produced, update the standalone
manifest entry per `docs/standalone-workflow.md`:

```json
{
  "mode": "standalone_markdown",
  "language": "en",
  "output_mode": "executive_brief",
  "output_mode_audience": "C-suite",
  "path": "deliverables/20260507_kr-loot-box-probability_standalone_executive-brief_en_v1.md"
}
```

The filename slug `_<output_mode_slug>_` is inserted between the existing
`_<mode>_` and `_<language>_` segments. See
`docs/standalone-workflow.md` for the canonical naming rules.
