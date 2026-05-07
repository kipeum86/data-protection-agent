---
name: citation-auditor
description: Audit a markdown answer file by extracting cited authorities, routing to the correct sub-KB auditor based on jurisdiction signals, and rendering a findings report. Use when a draft answer is ready for citation verification.
argument-hint: "<file.md>"
disable-model-invocation: false
---

Audit the markdown file at `$0`.

## Procedure

1. Confirm `$0` exists and is a markdown file. If it does not, stop and ask
   for a valid path.

2. Read the file. Detect jurisdiction signals using
   `index/jurisdiction-routing.json`:
   - Load the JSON file.
   - For each `routes[i].routing_terms` array, count case-insensitive
     occurrences in the file body.
   - The route with the highest count is the primary jurisdiction.
   - If two or more routes tie above zero, treat the answer as
     multi-jurisdictional.

3. **Run unified auditor** (single invocation, replaces v8 4-step dispatch):

   `python3 scripts/audit-unified.py --json "$0"`

   The unified runner imports all 4 auditors (CA / KR / EU sub-auditors +
   cross-jurisdiction) via importlib and aggregates their findings into a
   single JSON report. Output schema:
   - `status`: `"fail"` | `"warn"` | `"pass"` (aggregate)
   - `per_auditor[name]`: `{status, finding_count}` for each of
     `us-ca`, `kr-pipa`, `eu-gdpr`, `cross-jurisdiction`
   - `findings[]`: each with an `auditor` field identifying source

   Exit code is 1 on `fail`, 0 otherwise.

   The individual sub-auditor CLIs
   (`sources/{us-ca,kr-pipa,eu-gdpr}/scripts/audit-*.py` and
   `scripts/audit-cross-jurisdiction.py`) still exist for direct invocation
   if needed, but step 3 is the standard entry point.

4. Render the unified runner's output to the user:
   - One row per finding: `[auditor] [severity] message (citation; fix)`
   - A summary line with `aggregate_status` and `finding_count`.

5. If `aggregate_status == "fail"`, the answer MUST be revised before
   sending to the user. If `aggregate_status == "warn"`, surface the
   warnings to the user inline.

## Notes

- This skill does not modify the answer file. It only reads and reports.
- The CA sub-auditor enforces these checks (see
  `sources/us-ca/citation_auditor/california_citation.py`):
  statute/regulation/case id resolution, CPRA-as-standalone warning,
  US-overbreadth warning, OAG-FAQ-as-binding warning,
  enforcement-as-judicial-precedent warning,
  federal-court-as-CA-binding warning,
  unpublished-as-controlling error,
  2026-effective-regulation-source warning,
  mirror-cited-without-disclosure warning.

- Mirror-backed CA Supreme Court cases (source_family ==
  "ca-courts-published-opinion-mirrors") are CITABLE as binding precedent,
  but the answer MUST disclose the mirror source. The sub-auditor catches
  missing disclosure (English: "mirror", "SCOCAL", "official URL";
  Korean: "미러", "공식 출처").

- The KR sub-auditor uses both Korean (개인정보 보호법 제15조) and English
  (PIPA Article 15) citation patterns; either resolves to the same KB id.
  Decree patterns (시행령) are matched before parent-law patterns so the
  longer match wins.

- The EU sub-auditor distinguishes Articles (binding) from Recitals
  (interpretive only). Citing a Recital as a binding rule is a warn.
  Recital ids in the index use the plural form (gdpr-recitals-recital{n}).

- The cross-jurisdiction auditor (step 4) operates ABOVE the sub-auditors.
  It detects the answer's jurisdiction signal from `index/jurisdiction-routing.json`
  routing_terms and warns when cited authorities or jurisdiction-specific
  vocabulary belong to a different jurisdiction. Comparative answers
  (multi-jurisdiction signal) skip both checks to avoid false positives.
