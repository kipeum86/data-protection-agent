# Korean Legal-Opinion Profile

Use this profile when producing a polished Korean DOCX legal-opinion-letter
deliverable. It is the default Korean profile when:

- `language=ko`; AND
- `mode=docx_ready_markdown`; AND
- the deliverable is intended as a finished legal opinion / 검토 보고서.

Fall back to `ko-formatter-profile.md` when:

- the user explicitly requests a quick draft, internal memo, or handoff packet;
- the deliverable will not be rendered to DOCX;
- the requested register is conversational rather than formal opinion-letter.

## Renderer Pairing

This profile is paired with `scripts/render-legal-opinion-docx.py`, not
`scripts/render-docx.py`. The polished renderer provides:

- Cover page with title + subtitle + recipient + date + classification banner.
- Auto-numbered top-level headings (`1.`, `2.`, `3.`, ...) with bottom-border
  underline.
- Auto-numbered sub-headings (`1.1.`, `1.1.1.`, ...).
- Page break before every H2.
- Block-quoted text rendered as indented italic — used for statutory excerpts.
- Footnote markers `[^xxx]` rendered as superscript numerals with a master
  `각주 (Endnotes)` section at the document end.
- Page-numbered footer with confidentiality classification on every page.
- Justified body paragraphs in 맑은 고딕 + Times New Roman, line spacing 1.45.

## CLI Invocation Convention

Invoke the renderer with cover-page metadata derived from the matter context:

```bash
python3 scripts/render-legal-opinion-docx.py <input.md> <output.docx> \
  --title "<formal report title>" \
  --subtitle "<audience or scope qualifier, optional>" \
  --recipient "<recipient, default '사내 법무팀 귀중'>" \
  --date "<YYYY년 M월 D일>" \
  --classification "CONFIDENTIAL — INTERNAL LEGAL REVIEW" \
  --author "Data Protection Agent (data-protection-agent)"
```

Conventional defaults when the user has not specified:

| Flag | Default |
|---|---|
| `--recipient` | `사내 법무팀 귀중` |
| `--classification` | `CONFIDENTIAL — INTERNAL LEGAL REVIEW` |
| `--author` | `Data Protection Agent (data-protection-agent)` |
| `--date` | today in `YYYY년 M월 D일` Korean format (e.g., `2026년 5월 8일`) |

`--title` and `--subtitle` are derived from the user question and the
metadata's `summary` / `output_mode_audience`. The first H1 of the markdown is
skipped at render time (the renderer uses the CLI `--title`); keep the H1 in
the markdown for human readability.

## Heading Hierarchy

| Markdown | Rendered | Purpose |
|---|---|---|
| `#` | (skipped; replaced by cover page) | Document title |
| `##` | `1.` `2.` `3.` ... | Chapter; page break before |
| `###` | `1.1.` `1.2.` ... | Sub-section (or use `가.` `나.` `다.` in body text) |
| `####` | `1.1.1.` `1.1.2.` ... | Sub-sub-section (or `(1)` `(2)` `(3)`) |

When the chosen `output_mode` requires specific English section headers (e.g.,
`## Scope and As-of Date`, `## Comparative Matrix`), keep them and append
Korean after an em dash:

```markdown
## Scope and As-of Date — 검토 개요 및 적용 범위
```

The validator (`scripts/check-formatter-output.py --output-mode <slug>`) checks
the English heading as a substring; the Korean tail is invisible to the
validator but visible to the reader.

## Source Anchor Convention

### Body

Every inline citation MUST use the footnote-marker form `[^src_NNN]`. Never
use the inline-parenthetical form `(src_NNN)` in body text under this
profile. The renderer converts `[^src_NNN]` into a superscript numeral and
adds the source to the master 각주 list.

### Footnote definitions

At the END of the markdown, define every footnote used in the body:

```markdown
[^src_001]: 「게임산업진흥에 관한 법률」제12조의3 (게임과몰입 예방조치 등). 법률,
법령ID 010196. Grade A. 핀포인트: 제12조의3제1항제1호 ~ 제4호. 법제처 국가법령정보센터.
```

Define each `src_NNN` exactly once even if referenced many times in the body
— the same key reuses the same superscript number throughout.

### Source table

The deliverable still includes a master `### 출처 일람표 (Sources Cited)` table
inside `## Annotated Bibliography`, mirroring `meta.json` `sources[*]` rows
(`id / grade / title / citation / pinpoint`). This is read by
`check-formatter-output.py` for the source-table-row check.

## Korean Register

- Use 합니다체 throughout (not 한다체).
- Open the report with a 의뢰 sentence:
  `본 보고서는 [의뢰인] [사안]에 관하여 [기준일] 현재 검토한 결과를
  정리한 것입니다.`
- Close the body with: `이상의 검토 결과를 보고드립니다.` (placed immediately
  before the footnote definitions block).
- For recommendations: `권고드립니다`, `검토를 권고드립니다`,
  `우선 도입할 것을 권고드립니다`.
- For uncertainty: `단정하기 어렵습니다`, `추가 확인이 필요합니다`,
  `별도 전문가 검토 대상입니다`.
- Avoid marketing language, exaggerated certainty, conversational filler, and
  English code-switching that the matter does not require.

## Statutory Text Block Quotes

Render verbatim 법령 / regulator text as Markdown block quotes (`>`). The
renderer renders block quotes as indented italic with a left border.

```markdown
> 제12조의3(게임과몰입 예방조치 등) ① 게임물 관련사업자[…]는 […]
> 1. 게임물 이용자의 회원가입 시 실명·연령 확인 및 본인 인증
> 2. 청소년의 회원가입 시 친권자 등 법정대리인의 동의 확보
```

Limit block quotes to controlling statute / regulation / case text only —
not to prose summaries or commentary.

## Risk Matrix Tables

For per-jurisdiction risk lists, use a 5-column table:

```markdown
| 순위 | 리스크 | 가능성 | 영향도 | 근거 |
|---|---|---|---|---|
| 1 | ... | 중간 (3) | 매우 높음 (5) | [^src_001] |
```

For cross-jurisdiction matrices, add a `종합` column:

```markdown
| 관할권 | 리스크 | 가능성 | 영향도 | 종합 |
```

Mark risks scoring ≥ 12 (or any high-likelihood × very-high-impact cell) with
inline `**[Material Risk]**` per `knowledge/output-modes/counter-analysis-checklist.md`.

## Mandatory Section Additions

In addition to the validator-required sections of the chosen `output_mode`
(see `knowledge/output-modes/mode-index.md`), include:

1. Inside `## Scope and As-of Date — 검토 개요 및 적용 범위`, sub-sections for
   사안 및 의뢰 사항 / 검토 범위 및 관할권 선별 근거 / 기준일·가정·한정 사항 /
   경영진 요약.
2. A trailing 결어 line `이상의 검토 결과를 보고드립니다.` placed
   immediately before the footnote definitions block.
3. Footnote definitions in `[^src_NNN]: ...` form for every `src_NNN` used in
   the body — exactly one definition per ID, full pinpoint citation matching
   `meta.json` `sources[*]`.

## Forbidden Moves

- Inline `(src_NNN)` anchors in body text — convert all to `[^src_NNN]`.
- Bullet points where 가./나./(1)/(2) hierarchy is appropriate.
- Block quotes around prose summary — only verbatim statutory or regulator
  text qualifies.
- Promising native Word footnotes, tracked changes, comments, or page-layout
  precision — the polished renderer does not produce these.
- Skipping the 결어 line — required for the formal opinion-letter shape.
- Letting the literal placeholder `src_NNN` (uppercase NNN) appear in body
  text — the validator treats it as an unknown source anchor and fails.

## Quality Examples

Good — formal opening:

```text
본 보고서는 한국 본사 기반 글로벌 영업 게임사의 사내 법무팀이 의뢰한
온라인 게임 산업의 연령 보증(age assurance) 규제 동향에 관한 다관할권
검토 결과입니다.
```

Bad — narrative / presentation opening:

```text
오늘 우리가 살펴볼 것은 게임 산업의 연령 인증 트렌드입니다.
```

The bad version uses informal conversational style, lacks the 의뢰 framing,
and reads as a slide-deck intro rather than a legal opinion.

## Final Check

Before delivery:

- Cover-page CLI args populated and consistent with `meta.json`.
- All `(src_NNN)` body references converted to `[^src_NNN]` markers.
- Every body footnote marker has a matching `[^src_NNN]: ...` definition.
- Block quotes used for statutory text only.
- Output-mode required English section headers present
  (`check-formatter-output.py --output-mode <slug>`).
- Final 결어 line present.
- DOCX extraction confirms every `src_NNN` anchor survives.
