# Documentation Layout

`docs/` is for stable, repository-safe operating documentation:

- `agent-protocol.md`
- `auditors.md`
- `examples.md`
- `kb-operations-guide.md`
- `sub-kb-operations/*.md`

Planning documents, implementation drafts, hardening plans, session logs, and
scratch notes belong under `.local/`, which is ignored by git. Use:

- `.local/planning/` for implementation plans and design drafts.
- `.local/sessions/` for session logs or burn-in notes.
- `.local/scratch/` for temporary analysis.

Do not commit `.local/` contents. If a planning note becomes durable operating
guidance, summarize the stable rule in one of the tracked docs above instead of
moving the whole note back into `docs/`.
