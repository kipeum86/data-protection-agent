# Rendering Examples (v21 + v22)

This document walks through the four output forms a single `/answer`
invocation can produce, using a real worked example from the v20+v21
dogfood. The example question is a 3-jurisdiction comparative on
automated decision-making (GDPR Art. 22 / PIPA 제37조의2 / CCPA ADMT
regs) — reproduced here because it exercises every renderer feature
(comparison matrix table, per-jurisdiction labeled sections, statutory
citations, source table with mirror-disclosure parentheticals).

---

## The Question

```text
For a global SaaS company that uses an AI model to automatically deny
customer refund requests above a certain threshold: under each of GDPR,
Korea PIPA, and California (CCPA as amended by CPRA), what does the
company need to do regarding (a) the customer's right to challenge or
be free from that automated decision, (b) the company's obligation to
explain the decision logic, and (c) the notice or consent required
before deploying the system?
```

`/answer` classifies this as `comparative` mode (3 jurisdictions
signalled, "compare" intent inferred from the parallel "(a)/(b)/(c)
under each of X, Y, Z" structure).

---

## The Four Outputs

A single run produces, depending on flags and `output_mode`:

| File | When | Bytes (this example) | Audience |
|:---|:---|---:|:---|
| `data-protection-agent-result.md` | always (the v19 contract) | 25,626 | Privacy lawyer / paralegal — primary working artifact |
| `data-protection-agent-meta.json` | always (the v19 contract) | 27,644 | Tooling, validators, downstream agents |
| `data-protection-agent-result.docx` | `output_mode=legal_opinion` (auto), or `--docx` | 49,562 | Client / GC / 사내 법무팀 — circulation deliverable |
| `data-protection-agent-result.html` | `--html` | 27,989 | Browser / email / intranet circulation |

All four are parallel renderings of the same underlying analysis.
Citation IDs (`src_001` … `src_014`), authority anchors
(`us-ca:ca-civ-1798.150`, `eu-gdpr:gdpr-art22`,
`kr-pipa:pipa-art37-2`), and the comparison matrix all carry through.

---

## 1. Markdown Result (`*.md`) — The Primary Artifact

The 9-section memo described in [the README](../README.md#output-contract).
Excerpt of the Comparison Matrix:

```markdown
## Comparison Matrix

| Topic | EU GDPR | Korea PIPA | California (CCPA as amended by CPRA) | Practical delta |
|---|---|---|---|---|
| (a) Right to challenge / be free from the decision | Default right ... [src_001] | Statutory right to refuse ... [src_005] | Right to opt-out of ADMT, or human-appeal ... [src_010, src_012] | EU/KR have a baseline statutory right that triggers automatically; California's right is triggered only by the regulatory definition of significant decision |
| (b) Duty to explain the decision logic | At collection ... "meaningful information about the logic involved" [src_002, src_003] | "concise and meaningful explanation" ... [src_007] | "information about the logic of the ADMT" ... but only for ADMT used for a significant-decision [src_010, src_013] | EU and KR explanation duties are statute-level and apply to ADM decisions generally; CA's analogue is regulation-level and scope-limited |
| (c) Notice / consent before deployment | Lawful basis under Art. 6 plus Art. 22(2) gateway [src_001] ... | Controller must, before deployment, publish ... [src_006, src_008] | Pre-use Notice required before processing PI with ADMT for a significant decision [src_011] | EU treats consent as one of three Art. 22 gateways; PIPA does not require fresh ADM-specific consent; CA requires the Pre-use Notice but does not require consent |
```

This is the source of truth for every other rendered form.

---

## 2. Metadata JSON (`*-meta.json`) — Machine-Readable

Excerpt of the source envelopes (14 sources total — 5 EU + 4 KR + 5 CA):

```json
{
  "research_mode": "comparative",
  "output_mode": "canonical",
  "jurisdictions": ["EU", "KR", "US-CA"],
  "namespaces": ["eu-gdpr", "kr-pipa", "us-ca"],
  "sources": [
    {
      "id": "src_001",
      "authority_id": "eu-gdpr:gdpr-art22",
      "namespace": "eu-gdpr",
      "jurisdiction": "EU",
      "title": "Automated individual decision-making, including profiling",
      "citation": "GDPR Art. 22",
      "pinpoint": "(1)–(3)",
      "grade": "A",
      "official_url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
      "local_path": "kb/eu-gdpr/library/grade-a/gdpr/art22.md"
    }
    /* ... 13 more */
  ],
  "claim_checks": [/* 10 entries */],
  "comparison_matrix": [/* 3 rows × 4 columns */]
}
```

`scripts/validate-output.py` enforces the schema. Downstream tooling
(orchestrators, e2e harnesses, golden-set evaluators) consume this
file rather than parsing the markdown.

---

## 3. DOCX Legal Opinion (`*.docx`) — Client Deliverable

Rendered via:

```bash
python3 scripts/render-legal-opinion-docx.py \
  outputs/data-protection-agent/data-protection-agent-result.md \
  outputs/data-protection-agent/data-protection-agent-result.docx \
  --title "AI 자동화 환불 거절 — GDPR / PIPA / CCPA 3법역 검토" \
  --recipient "사내 법무팀 귀중" \
  --date "2026년 5월 8일" \
  --classification "CONFIDENTIAL — INTERNAL LEGAL REVIEW" \
  --author "Data Protection Agent (data-protection-agent)"
```

Structure of the rendered file (verified via `python-docx` introspection):

| Element | Count |
|:---|---:|
| Paragraphs | 72 |
| Tables | 2 (Comparison Matrix + Sources) |
| Sections | 1 (with footer + page numbers) |
| File size | 49,562 bytes |

Cover page (first four paragraphs of the rendered DOCX):

```
CONFIDENTIAL — INTERNAL LEGAL REVIEW
AI 자동화 환불 거절 — GDPR / PIPA / CCPA 3법역 검토
──────────────────────────────
수신: 사내 법무팀 귀중
```

The body uses:

- 맑은 고딕 (한글) + Times New Roman (ASCII) typography
- Auto-numbered top-level headings (`1.`, `2.`, ...) with bottom-border underline
- Auto-numbered sub-headings (`1.1.`, `1.1.1.`, ...)
- Indented italic for verbatim statutory excerpts (e.g., GDPR Art. 22 quoted text)
- Footnote markers (`[^xxx]`) converted to superscript numerals with a
  master `각주 (Endnotes)` section at document end (when present)
- Page-numbered footer with the classification banner repeated on every page

This is the form a client or in-house counsel would receive.

---

## 4. HTML (`*.html`) — Browser-Viewable

Rendered via:

```bash
python3 scripts/render-html.py \
  outputs/data-protection-agent/data-protection-agent-result.md \
  outputs/data-protection-agent/data-protection-agent-result.html \
  --title "AI 자동화 환불 거절 — 3법역 검토" \
  --lang ko
```

Self-contained HTML (no external CSS / JS / image dependencies — safe
to email or host on a static page). Inline styling provides:

- Readable serif body, max-width 760px
- Clear H1/H2 hierarchy with horizontal rules
- Bordered tables for the Comparison Matrix and Sources
- Code-block styling for inline `src_NNN` anchors and citation IDs

Useful when the recipient does not need a Word file but should be able
to read the analysis in a browser (intranet hosting, email archive,
GitHub Pages snapshot).

---

## Choosing an Output Form

| You want | Use |
|:---|:---|
| Working memo a privacy lawyer can edit and revise | `*.md` — default |
| Audit-trail / downstream tooling consumption | `*-meta.json` — default |
| Polished client circulation, client-facing branding, opinion-letter conventions | `*.docx` via `output_mode=legal_opinion` |
| Browser viewing, email-friendly link, intranet snapshot | `*.html` via `--html` |

The four forms are not mutually exclusive — a single `/answer`
invocation can emit all four at once:

```text
/answer <question> output_mode=legal_opinion --html
```

…produces md + meta.json (always) + docx (auto from `legal_opinion`) +
html (from `--html`). All four files in one `OUTPUT_DIR`.

---

## Verification

The renderers are exercised by parametrised e2e tests in
[`tests/test_e2e_agent_pipeline.py`](../tests/test_e2e_agent_pipeline.py)
across all 5 v19 golden fixtures:

| Test | Coverage |
|:---|:---|
| `test_packet_renders_basic_docx` | 5 fixtures × `render-docx.py` → DOCX > 10 KB |
| `test_legal_opinion_renderer_smoke` | 1 fixture × `render-legal-opinion-docx.py` → DOCX > 10 KB |
| `test_packet_renders_html` | 5 fixtures × `render-html.py` → HTML > 2 KB + DOCTYPE present |

Tests gracefully skip (`pytest.importorskip`) when `python-docx` or
`marko` is not installed.

---

## Provenance

The DOCX renderer stack (`scripts/render-docx.py`,
`scripts/render-legal-opinion-docx.py`, `knowledge/legal-writing/`,
`templates/modes/{black-letter-commentary,comparative-matrix,
enforcement-case-law,executive-brief}.md`, and the two
`legal-writing-formatter` / `output-mode-composition` skills) is
**vendored verbatim from the sibling `legal-research-agent`** with
DPA-domain rewrites applied (filename references, author defaults).
The HTML renderer (v22) is also vendored from LRA (87 lines, generic —
no domain rewrites needed). Original source-of-truth lives at
`legal-research-agent/scripts/` and `legal-research-agent/knowledge/`.

For the round-by-round vendoring history see
[`CHANGELOG.md`](../CHANGELOG.md) entries v21 (DOCX) and v22 (HTML).
