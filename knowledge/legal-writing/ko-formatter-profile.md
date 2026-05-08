# Korean Formatter Profile

Use this compact profile for Korean standalone legal research deliverables.

## Purpose

Transform completed legal research into a Korean legal research memo or
opinion-style note. The output should read like careful Korean legal work
product, while staying within the research record.

## Register

- Use formal Korean legal prose.
- Default to `합니다` style for client-facing or colleague-facing research
  notes.
- Use `한다` style only when the requested deliverable is a formal internal
  legal memorandum or statutory commentary.
- Avoid conversational phrasing, marketing language, exaggerated certainty, and
  translated-English sentence structure.
- Prefer precise verbs such as `검토합니다`, `확인됩니다`, `볼 여지가 있습니다`,
  `추가 확인이 필요합니다`, and `단정하기 어렵습니다`.

## Default Structure

Use this structure unless the user requests another one:

1. `# 제목`
2. `## 요약`
3. `## 쟁점`
4. `## 검토의견`
5. `## 분석`
6. `## 한계 및 추가 확인사항`
7. `## 출처`

For multi-jurisdiction matters, separate jurisdiction-specific analysis before
the synthesis. If a comparison matrix exists in metadata, preserve it as a
visible table.

## Section Drafting Rules

### `## 요약`

- Start with the answer the reader needs, then immediately state the main
  source or confidence limit.
- Keep the first paragraph short enough to be read independently.
- Include at least one visible `src_*` anchor when any legal conclusion is
  stated.
- If the result is fallback, error-bearing, or source-limited, say so in the
  first paragraph.

### `## 쟁점`

- Convert each material `issue_map` item into a concise issue.
- Use Korean issue labels, but preserve source IDs and specialist boundaries.
- For game regulation, keep taxonomy concepts visible when they matter to the
  analysis, for example 확률형 보상, 청소년 보호, 광고/표시, 제재.

### `## 검토의견`

- Lead with conclusion plus limit:
  `현재 수집된 자료 기준으로는 ...로 검토됩니다. 다만 ... 확인이 필요합니다 (src_001).`
- Keep this section shorter than `## 분석`; it is the opinion-style answer, not
  the full authority discussion.
- Do not state a definitive obligation, exemption, sanction, or deadline unless
  the research output gives sufficient source support.

### `## 분석`

- Use subheadings when there is more than one issue or jurisdiction.
- Recommended order: `관련 근거`, `사안 적용`, `반대 검토 및 한계`,
  `실무상 다음 조치`.
- In each paragraph, connect the legal proposition to source ID, jurisdiction,
  and confidence.

### `## 한계 및 추가 확인사항`

- Move all `coverage_gaps`, `fallback_reason`, `error`, and specialist handoffs
  into this section.
- Explain why each gap matters, not only that it exists.
- Use direct language: `추가 확인이 필요합니다`, `단정하기 어렵습니다`,
  `별도 전문가 검토 대상입니다`.

### `## 출처`

- Include every metadata source exactly once.
- Preserve source ID, grade, title, citation, pinpoint, and access note.
- Do not translate or "clean up" source titles in a way that breaks auditability.

## Analysis Style

- Lead with the practical conclusion, then explain issue, authority, and
  application.
- Keep each conclusion tied to a visible `src_*` source anchor.
- Name the jurisdiction before discussing the rule.
- Preserve confidence limits from metadata.
- State missing facts or missing official-source coverage explicitly.
- If the research result is fallback, say so plainly in the summary and limits.

## Paragraph Patterns

Use patterns like these:

```text
현재 수집된 공식 출처 기준으로는 [쟁점]에 관하여 [잠정 결론]으로
검토됩니다. 다만 [한계/미확인 사항] 때문에 최종 결론 전 [추가 확인]이
필요합니다 (src_001).
```

```text
[관할]에서는 [규율 대상]이 문제됩니다. 이 쟁점은 [source grade/official
source]인 src_001에 근거하여 검토하되, [시행일/하위 규정/가이드라인] 확인
전에는 제재 수준을 단정하기 어렵습니다.
```

Avoid patterns like these:

```text
관련 법령상 문제가 될 수 있습니다.
```

```text
일반적으로 금지됩니다.
```

These are too vague unless tied to a jurisdiction, rule, source ID, and
confidence limit.

## Citation Style

- Preserve source IDs such as `src_001`.
- Korean statutes should be displayed as `「법률명」 제N조` when that citation is
  present in the research output.
- Korean cases should follow the form `대법원 YYYY. M. D. 선고 사건번호 판결`
  when supplied by the research output.
- Do not fabricate Korean 법령명, 조문번호, 사건번호, regulator guidance titles,
  or effective dates.

## Terminology

- Use one Korean term consistently for each concept.
- When an English platform/game term is material, introduce it once in
  parentheses: `확률형 아이템(randomized item)`.
- Prefer `표시의무`, `고지의무`, `이용자 보호`, `제재`, `시정명령`,
  `과태료`, `영업정지` only when the research record supports the term.
- Do not substitute a broader term such as `소비자보호법` for a specific
  statute or regulator source unless the source record does so.

## Source And Gap Handling

- Every material paragraph should cite a `src_*` anchor or clearly synthesize
  already cited analysis.
- Do not hide `coverage_gaps`.
- If a proposition is useful but insufficiently sourced, write
  `[Source Coverage Gap: 필요한 공식 출처 또는 추가 확인사항]`.
- If privacy, IP, tax, finance, employment, or another specialist issue was
  delegated, keep the handoff visible rather than converting it into a final
  conclusion.

## DOCX-Ready Markdown

When producing `docx_ready_markdown`, use stable Markdown headings and simple
tables. Do not claim that fonts, margins, Word styles, or tracked changes have
been applied unless a real DOCX generation workflow was run.
