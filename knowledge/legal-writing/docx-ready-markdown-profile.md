# DOCX-Ready Markdown Profile

Use this profile only when the selected formatter mode is
`docx_ready_markdown`.

This profile prepares Markdown that can be converted later by a DOCX workflow.
It does not claim that a DOCX file, Word styles, native footnotes, page layout,
or tracked changes have already been generated.

Binary DOCX generation is available as an MVP through `scripts/render-docx.py`.
The renderer is intended for standalone legal research deliverables that already
passed formatter validation. It supports headings, paragraphs, simple lists,
simple tables, block quotes, basic inline bold/italic, headers, and page footer
fields. It does not support native Word footnotes, tracked changes, comments, or
complex nested Markdown.

## Structure

- Use exactly one `#` title.
- Use `##` for major sections and `###` for issue-level sections.
- Avoid heading levels deeper than `####` unless the user supplies a template
  that requires them.
- Keep tables as simple pipe tables with a header separator row.
- Keep source IDs visible in body text or parentheticals.
- Put the final source table at the end unless the user asks for footnote-style
  source handling.

## Conversion-Safe Markdown

Prefer:

- short paragraphs;
- stable numbered lists for procedural steps;
- simple bullets for limitations;
- tables with short cell text;
- explicit bracketed placeholders for missing facts or source gaps.

Avoid:

- nested tables;
- HTML blocks;
- embedded images;
- markdown callouts;
- chat-only commentary;
- hidden assumptions;
- decorative formatting that may not survive conversion.

## Source Appendix

The source appendix must include:

| ID | Grade | Title | Citation | Pinpoint | Access |
|---|---|---|---|---|---|

Each row must mirror metadata. Do not shorten titles, remove access notes, or
replace source IDs with ordinary footnote numbers unless the source-ID mapping is
also preserved.

## DOCX Honesty Rule

If only Markdown was produced, describe it as `DOCX-ready Markdown`, not as a
DOCX file. Do not say that fonts, margins, page numbers, native footnotes,
headers, or tracked changes have been applied.

If `scripts/render-docx.py` was run, describe the result as `MVP DOCX rendering`
unless a later workflow verifies richer Word features. Run DOCX extraction or
audit checks before treating the binary as a final external deliverable.
