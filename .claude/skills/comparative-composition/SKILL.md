---
name: comparative-composition
description: Use only in comparative or multi_jurisdiction mode - produces side-by-side authority tables and per-jurisdiction commentary blocks without blending authorities.
disable-model-invocation: true
---

# Comparative Composition

Use this skill only when `research_mode` is `comparative` or
`multi_jurisdiction`.

## Procedure

1. For `multi_jurisdiction`, produce one labelled section per jurisdiction.
   Each section contains its own Issues and Analysis. Do not synthesize across
   jurisdictions unless the user asked for comparison.

2. For `comparative`, produce a comparison matrix followed by per-jurisdiction
   commentary:

```markdown
## Comparison Matrix

| Topic / Question | KR (PIPA) | EU (GDPR) | US-CA (CCPA) | Practical delta |
|---|---|---|---|---|
| Lawful basis / consent / notice | KR rule [src_003] | EU rule [src_007] | CA rule [src_001] | Practical difference |
```

3. After the matrix, write per-jurisdiction commentary subsections:
   - `### KR`
   - `### EU`
   - `### US-CA`

Each subsection follows the standard issue/analysis structure but is scoped to
one jurisdiction.

## Hard Rules

- Never blend authorities across jurisdictions in the same paragraph.
- "Personal data" (GDPR) and "personal information" (CCPA/PIPA) are not
  interchangeable terms.
- GDPR lawful basis, PIPA consent/legal exceptions, and CCPA notice/opt-out are
  different legal mechanisms. Do not collapse them.
- Each matrix cell must cite source ids from that jurisdiction only.
