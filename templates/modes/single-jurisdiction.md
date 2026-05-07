<!--
Audience: privacy counsel or compliance owner.
Length target: 900-1,500 words unless the user asks for a short answer.
Use this for ca_only, kr_only, and eu_only modes.
-->

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

{{short_answer_with_src_anchor}}

## Issues

### Issue 1: {{issue_label}}

- Answer: {{issue_answer_with_src_anchor}}
- Sources: {{issue_source_ids}}
- Confidence: {{high|medium|low}}
- Limits: {{limits_or_caveats}}

## Analysis

### Rule and Authority

{{rule_summary_with_src_anchors}}

### Application

{{application_to_user_facts}}

### Counter-Analysis or Caveat

{{counter_arguments_and_uncertainty}}

### Practical Next Step

{{action_oriented_recommendation}}

## Sources

| ID | Authority ID | Citation | Title | Grade | Pinpoint | Local path |
|---|---|---|---|---|---|---|
| src_001 | {{authority_id}} | {{citation}} | {{title}} | {{grade}} | {{pinpoint}} | `{{local_path}}` |

## Coverage Gaps

{{list_or_None.}}

## Handoff Notes

{{handoff_or_None.}}
