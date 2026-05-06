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

3. For each in-scope jurisdiction, dispatch to the sub-KB auditor:

   - `us-ca`: run
     `python3 sources/us-ca/scripts/audit-california-citations.py --json "$0"`
     This CLI wraps `citation_auditor.california_citation.audit()` and prints
     a JSON findings report. Exit code is 1 on `fail`, 0 otherwise.
   - `eu-gdpr`: TBD. If a `kb/eu-gdpr/scripts/audit-*.py` exists, run it.
     If not, emit a warning: "EU sub-auditor not yet wired up; manual
     verification required for EU authorities in this answer."
   - `kr-pipa`: TBD. Same pattern as EU.

4. Aggregate findings from all sub-auditors.

5. Render a single combined report with:
   - Per-jurisdiction sub-section
   - One row per finding: `[severity] message (citation; suggested_fix)`
   - A summary line:
     `aggregate_status = fail if any finding.severity == "error"
                        else (warn if any finding else pass)`

6. If `aggregate_status == "fail"`, the answer MUST be revised before
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
