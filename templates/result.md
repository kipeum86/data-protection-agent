# Data Protection Agent - Result

## Question

{{user_question}}

## Route Context

- Active profile: `{{active_profile}}`
- Research mode: `{{research_mode}}`
- Mode source: `{{mode_source}}`
- Jurisdictions: {{jurisdictions}}
- Namespaces: {{namespaces}}
- Co-running agents: `{{co_running_agents}}`

## Short Answer

{{short_answer_with_at_least_one_src_anchor}}

## Issues

### Issue 1: {{issue_label}}

- Answer: {{issue_answer}}
- Sources: {{issue_source_ids}}
- Confidence: {{high|medium|low}}
- Limits: {{limits_or_caveats}}

Repeat for additional issues. Multi-jurisdiction and comparative modes replace
this section per the `comparative-composition` skill.

## Analysis

### Rule and Authority

{{rule_summary_with_src_anchors}}

### Application

{{application_to_user_facts}}

### Counter-Analysis or Caveat

{{counter_arguments_and_uncertainty}}

### Practical Next Step

{{action_oriented_recommendation}}

{{comparison_matrix_section_if_comparative_mode}}

## Sources

| ID | Authority ID | Citation | Title | Grade | Pinpoint | Local path |
|---|---|---|---|---|---|---|
| src_001 | {{authority_id}} | {{citation}} | {{title}} | {{grade}} | {{pinpoint}} | `{{local_path}}` |

## Coverage Gaps

{{list_or_None.}}

## Handoff Notes

{{handoff_or_None.}}
