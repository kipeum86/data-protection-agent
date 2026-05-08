# Documentation Layout

`docs/` is for stable, repository-safe operating documentation:

- `agent-protocol.md` — runtime protocol (v19+ workflow, output contract,
  output_mode axis added in v21)
- `auditors.md` — full catalog of 30+ citation auditor checks across the
  4-layer auditor stack
- `examples.md` — 7 worked citation-auditor I/O examples
- `rendering-examples.md` — v21+v22 deliverable rendering walkthrough
  (md / meta.json / docx / html for one worked question)
- `kb-operations-guide.md` — build / refresh / verify the unified KB
- `release-process.md` — versioning, release-note authoring, GitHub
  Releases publishing cycle
- `releases/RELEASE-vX.Y.Z.md` — per-release notes (EN + KO)
- `sub-kb-operations/*.md` — per-sub-KB (CA / KR / EU) operational notes

Planning documents, implementation drafts, hardening plans, session logs, and
scratch notes belong under `.local/`, which is ignored by git. Use:

- `.local/planning/` for implementation plans and design drafts.
- `.local/sessions/` for session logs or burn-in notes.
- `.local/scratch/` for temporary analysis.

Do not commit `.local/` contents. If a planning note becomes durable operating
guidance, summarize the stable rule in one of the tracked docs above instead of
moving the whole note back into `docs/`.
