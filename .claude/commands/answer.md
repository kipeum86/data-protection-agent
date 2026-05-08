---
description: Answer a privacy/data-protection question using the unified KR PIPA / EU GDPR / US-CA CCPA KBs with full source-grounding, citation auditing, and optional DOCX legal-opinion rendering.
argument-hint: "<question text> [mode=ca_only|kr_only|eu_only|multi_jurisdiction|comparative] [output_mode=canonical|legal_opinion] [--docx]"
---

Run the data-protection-agent workflow described in `CLAUDE.md` for the
question in `$ARGUMENTS`.

If `$ARGUMENTS` is empty, ask the user for:

1. The privacy/data-protection question.
2. Whether they want the canonical 9-section research memo or a polished
   legal-opinion DOCX (`output_mode=legal_opinion`).
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
   `outputs/data-protection-agent/` if unset. Set `output_mode` in the meta
   JSON (default `canonical`; `legal_opinion` when the user asked for a
   formal opinion).
8. **Optional DOCX rendering** — when `output_mode=legal_opinion` or the
   user passed `--docx`, apply `legal-writing-formatter` skill, then run:

   - `output_mode=canonical` + `--docx` →
     `python3 scripts/render-docx.py <result.md> <result.docx> --language <ko|en> --jurisdiction <korea|us|intl> --overwrite`
   - `output_mode=legal_opinion` (auto-renders) →
     `python3 scripts/render-legal-opinion-docx.py <result.md> <result.docx>
       --title "<formal report title>" --recipient "사내 법무팀 귀중"
       --date "$(date +'%Y년 %-m월 %-d일')"
       --classification "CONFIDENTIAL — INTERNAL LEGAL REVIEW"
       --author "Data Protection Agent (data-protection-agent)"`

   For Korean output use the `ko-legal-opinion-profile.md` knowledge file;
   for English the `en-formatter-profile.md`. Profiles live under
   `knowledge/legal-writing/`.

9. Print a one-line summary: mode, jurisdictions, source count, audit
   status, output_mode, and (if DOCX) rendered file path.

Defaults:

- Output directory: `outputs/data-protection-agent/` if `$OUTPUT_DIR` is unset.
- Top-K retrieval: 12.
- Research mode: self-classified unless explicitly provided.
- Output mode: `canonical` (the 9-section research memo).
- DOCX: rendered automatically when `output_mode=legal_opinion`; otherwise
  only when the user passes `--docx`.
