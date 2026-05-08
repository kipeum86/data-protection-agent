# Release Process

How releases are tagged, documented, and published for this repository.

Modeled on the sibling [`legal-research-agent` release process](../../legal-research-agent/docs/release-process.md)
and the family convention used by `GDPR-expert` and `PIPA-expert`.

---

## Versioning

This repo follows [Semantic Versioning](https://semver.org) (`vMAJOR.MINOR.PATCH`).

| Version bump | When | Examples |
|---|---|---|
| **MAJOR** | Breaking change to the output contract, the `/answer` slash command, the meta JSON schema, or the auditor severity model | Renaming `data-protection-agent-result.md` to a new filename; removing or renaming a `meta_version: "1.x"` required field; changing an auditor `warn` → `error` |
| **MINOR** | New backward-compatible capability — new output_mode, new auditor check, new sub-KB, new renderer, new skill | v22 HTML renderer (added `--html` flag, new optional output form); v21 `legal_opinion` output_mode (additive `output_mode` axis); v17 future-effective check |
| **PATCH** | Bug fix, false-positive cleanup, KB refresh from sibling, doc-only changes | v20-mini auditor false-positive cleanup; sibling-repo re-import; README typos |

The internal `CHANGELOG.md` documents the round-by-round development (v3 → v22 produced v1.0.0). Once we move past v1.0.0, the round number → semver mapping will be recorded in each release note.

---

## Release Cycle

For each release:

1. **Land all changes on `main`** through the normal PR cycle. CI must be green.
2. **Update `CHANGELOG.md`** with a new top-level entry summarising the round.
3. **Write the release note** at `docs/releases/RELEASE-vX.Y.Z.md` as a **single bilingual file** (English paragraph + Korean paragraph stacked under each section heading; no separate `.ko.md`). Keep it tight — release notes are not a re-explanation of the README. Cover only:
   - One-line bilingual summary of what shipped.
   - Why it shipped (rationale, not just the diff).
   - Highlights table (stats / capabilities), with bilingual column headers.
   - Forward-looking note where relevant.
   - Pointer to README + CHANGELOG for full content.
   - Disclaimer + license footer (bilingual).
4. **Update the README banner** — change the `> Latest release: ...` line at the top of both `README.md` and `README.ko.md` to point at the new release note.
5. **Commit + push** the release-note files and README banner update.
6. **Tag** the commit:

   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z — <one-line summary>"
   git push origin vX.Y.Z
   ```

7. **Publish on GitHub Releases**:
   - Web UI → Releases → Draft a new release.
   - Choose the existing tag `vX.Y.Z`.
   - Title: `vX.Y.Z — <one-line summary>`.
   - Description: paste the body of `docs/releases/RELEASE-vX.Y.Z.md` (or use the auto-fill from the tag annotation + a link to the full note).
   - "Set as the latest release" + Publish.

The published release fires GitHub's release-notification hook (RSS, watcher emails, repo timeline), which is why we wait for the GitHub publish step rather than relying on the tag alone.

---

## Bilingual Notes

Every release ships **a single bilingual file** at `docs/releases/RELEASE-vX.Y.Z.md`. The English text and the Korean text live side by side under the same headings. Both READMEs (EN + KO) point to the same file from the top banner.

This pattern was chosen over separate `.md` + `.ko.md` files because:

- Release notes are short by design (~70 lines total). Two files of that length is more friction than benefit.
- Readers of the GitHub Releases page see a single description either way; bilingual-in-one keeps that surface coherent.
- Translation drift is easier to spot when both languages live next to each other.

The English text is the source-of-truth for technical content; the Korean text may localise idioms, examples, and ordering as long as the substantive coverage matches.

---

## Pre-Public-Release Notes

For the v1.0.0 initial public release specifically:

- The repo was developed in private from v3 through v22 (internal CHANGELOG entries).
- v1.0.0 was tagged on the v22 tip while the repo was still private; the tag and release-note files were prepared in advance so that the GitHub publish step could fire at the moment of the public-visibility flip, capturing the marketing benefit of a single coordinated launch (private → public + first release notification simultaneously).
- Subsequent releases follow the standard cycle above; no need for the "private-prep" choreography.

---

## Things That Are NOT Releases

- **KB refresh from a sibling repo** — when GDPR-expert or PIPA-expert publishes a new release and we re-import via `scripts/import_namespaced_kbs.py --clean`, that is *not* a DPA release on its own. It becomes part of the next release that bundles other changes.
- **Internal hardening rounds (CHANGELOG-only)** — small auditor false-positive cleanups, retrieval scoring tweaks, etc. Several of these may accumulate before producing a single PATCH release.
- **Doc-only changes after public** — typo fixes, link updates, etc. Unless they ship together with code, they live on `main` without a separate release.

---

## Cross-References

- [`CHANGELOG.md`](../CHANGELOG.md) — round-by-round development history (the source for what to write in each release note)
- [`docs/agent-protocol.md`](agent-protocol.md) — the runtime protocol (the public surface that MAJOR bumps protect)
- [`docs/releases/`](releases/) — all published release notes (EN + KO)
