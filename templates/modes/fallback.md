<!--
Audience: user asking a question outside, or not clearly inside, the local KB.
Length target: 500-900 words.
Use this for fallback_us and fallback modes.
-->

# Data Protection Agent - Result

## Question

{{user_question}}

## Route Context

- Active profile: `{{active_profile}}`
- Research mode: `{{fallback_us|fallback}}`
- Mode source: `{{mode_source}}`
- Jurisdictions: {{jurisdictions}}
- Namespaces: {{namespaces}}
- Co-running agents: `{{co_running_agents}}`

## Short Answer

The local KB does not adequately cover this question. See coverage gaps.

## Issues

### Issue 1: Coverage boundary

- Answer: {{coverage_boundary_answer}}
- Sources: {{source_ids_or_none}}
- Confidence: low
- Limits: Local KB coverage is limited to KR PIPA, EU GDPR, and US-CA privacy authorities.

## Analysis

### Rule and Authority

{{known_local_authority_boundary_if_any}}

### Application

{{why_the_question_falls_outside_or_needs_clarification}}

### Counter-Analysis or Caveat

{{possible_in_scope_interpretation_if_any}}

### Practical Next Step

{{clarifying_question_or_external_research_handoff}}

## Sources

| ID | Authority ID | Citation | Title | Grade | Pinpoint | Local path |
|---|---|---|---|---|---|---|
| {{source_id_or_blank}} | {{authority_id_or_blank}} | {{citation_or_blank}} | {{title_or_blank}} | {{grade_or_blank}} | {{pinpoint_or_blank}} | `{{local_path_or_blank}}` |

## Coverage Gaps

{{largest_section_list_each_missing_jurisdiction_or_authority}}

## Handoff Notes

{{handoff_or_None.}}
