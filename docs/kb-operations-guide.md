# KB Operations Guide

Status: active operating guide
Date: 2026-05-06
Scope: `kb/eu-gdpr`, `kb/kr-pipa`, `kb/us-ca`, and their source folders

## 1. Purpose

This guide turns the jurisdiction KBs from one-time build artifacts into maintained legal knowledge bases.

The merged agent uses three namespaced sub-KBs:

| Namespace | Jurisdiction | Source of truth | Merged output |
|---|---|---|---|
| `eu-gdpr` | EU | sibling `GDPR-expert` repo/folder | `kb/eu-gdpr` |
| `kr-pipa` | Korea | sibling `PIPA-expert` repo/folder | `kb/kr-pipa` |
| `us-ca` | California | local `sources/us-ca` | `kb/us-ca` |

The merged `kb/` tree is an imported runtime copy. Do not hand-edit `kb/<namespace>/library` or `kb/<namespace>/index`; update the source-of-truth folder, rebuild there, then run the namespaced import.

## 2. Operating Principles

- Every legal claim must be grounded in a local authority id and markdown file.
- Every indexed authority must preserve source metadata, including `source_grade`, `official_url`, and retrieval/conversion metadata where available.
- Source grade is part of the legal answer. Grade B and C materials can support context but must not be described as Grade A authority.
- Guidance, FAQs, press releases, settlements, administrative orders, and regulator examples are not judicial precedent.
- Unpublished or non-citable cases must not be treated as controlling authority.
- If the local KB does not support a claim, say that instead of filling the gap from memory.
- Do not edit generated indexes by hand unless the source builder explicitly documents a manual index.

## 3. Source Grades

Use these defaults unless a jurisdiction runbook gives a stricter rule.

| Grade | Meaning | Typical use |
|---|---|---|
| A | Official or primary legal source | statutes, regulations, official court judgments/opinions, regulator official guidance |
| B | Reliable but limited source | enforcement summaries, administrative decisions, public mirrors, legal interpretations, court materials from non-official databases |
| C | Discovery or commentary | law-firm notes, academic commentary, issue trackers, candidate lists |

Promotion rules:

- Promote Grade B to Grade A only when the official/primary source has been fetched, parsed, indexed, and validated.
- Never promote a mirror-backed case merely because the opinion itself is precedential; the source path still matters.
- Retain old source metadata when replacing a mirror with an official copy so the provenance trail remains clear.

## 4. Update Cadence

| Cadence | Action |
|---|---|
| Monthly | Check source registries, run validation gates, refresh known official-source endpoints if builders support it. |
| Quarterly | Review partial/pending source families, topic coverage, and golden-question quality. |
| Event-driven | Update immediately for major statutory amendments, new effective regulations, landmark judgments, regulator binding decisions, or major enforcement actions. |
| Before release | Rebuild source KB, import namespaces, run tests, update docs/counts. |

## 5. Standard Update Workflow

1. Identify the jurisdiction and source family.
2. Read the relevant runbook in `docs/sub-kb-operations/`.
3. Update only the source-of-truth KB folder.
4. Fetch or add raw source material according to that KB's builder.
5. Generate markdown and JSON indexes.
6. Run the jurisdiction validation gates.
7. Run the root namespaced import:

```bash
python3 scripts/import_namespaced_kbs.py --clean
```

8. Run root smoke tests:

```bash
PYTHONPATH=. pytest -q tests/test_namespaced_kb_import.py
```

9. Update operation docs or implementation snapshots if counts, grade policy, or source families changed.

## 6. Release Checklist

- `index/unified-source-registry.json` contains all three namespaces.
- `index/unified-authority-index.json` count and `by_namespace` counts match expectations.
- Each changed authority has a local markdown file and frontmatter.
- Each changed source family has an updated source registry entry.
- New authorities resolve from topic/golden-question indexes where applicable.
- No answer rule depends on a source that is only present in `raw/` but absent from `library/` and `index/`.
- Known caveats are documented in the jurisdiction runbook.

## 7. Runbooks

- [EU GDPR operations](sub-kb-operations/eu-gdpr.md)
- [Korea PIPA operations](sub-kb-operations/kr-pipa.md)
- [California operations](sub-kb-operations/us-ca.md)

