# Citation Auditor — Worked Examples

7 representative scenarios showing what the unified citation auditor
catches and what it lets through. All `audit output` blocks below are
the actual output of `python3 scripts/audit-unified.py < input` on the
v15 KB baseline.

For the full catalog of checks, see [auditors.md](auditors.md).

---

## E1 — Clean CCPA-only answer (status: pass)

**Input:**
```
Per Cal. Civ. Code § 1798.150, consumers have a private right of action
for data breaches. The business must comply with notice obligations under
ca-civ-1798.100.
```

**Audit output:**
```
=== Aggregate status: pass (0 finding(s)) ===

Per-auditor:
  us-ca                  status=pass   findings=0
  kr-pipa                status=pass   findings=0
  eu-gdpr                status=pass   findings=0
  cross-jurisdiction     status=pass   findings=0
```

Both citations resolve in `ca-statute-index`. No cross-jurisdiction
mismatch. Ship.

---

## E2 — Cross-jurisdiction citation in single-juris answer (status: warn)

**Input:**
```
Under CCPA, businesses must honor opt-out within 15 days. The relevant
authority is gdpr-art6 for European data subjects.
```

**Audit output:**
```
=== Aggregate status: warn (1 finding(s)) ===

Per-auditor:
  us-ca                  status=pass   findings=0
  kr-pipa                status=pass   findings=0
  eu-gdpr                status=pass   findings=0
  cross-jurisdiction     status=warn   findings=1

Findings:
  [cross-jurisdiction] [warn] Authority from eu-gdpr cited but answer's
  jurisdiction signal is ['us-ca']. Cross-jurisdiction authority used
  without scope label.
    citation: gdpr-art6
    fix: If the answer is intentionally comparative, label each
    jurisdiction explicitly (e.g., 'EU GDPR:', 'California:'). Otherwise,
    remove the eu-gdpr authority and stick to the in-scope jurisdiction.
```

The answer signals US-CA only (CCPA + opt-out + 15 days) but cites a
GDPR authority. Fix: either label both jurisdictions explicitly (see E6)
or remove the GDPR reference.

Why no per-sub-KB error: each sub-auditor only sees its own jurisdiction.
The CA auditor doesn't know about `gdpr-art6`; the EU auditor doesn't
know about CCPA. Cross-jurisdiction layer catches the mismatch.

---

## E3 — Vocabulary mismatch in single-juris answer (status: warn)

**Input:**
```
Under CCPA, the business must protect personal data of California
residents and appoint a data protection officer.
```

**Audit output:**
```
=== Aggregate status: warn (2 finding(s)) ===

Findings:
  [cross-jurisdiction] [warn] Term 'personal data' is eu-gdpr terminology
  but answer signals us-ca.
    citation: personal data
    fix: Use 'personal information' (CCPA/PIPA term). If the answer is
    intentionally comparative, label each jurisdiction explicitly.

  [cross-jurisdiction] [warn] Term 'data protection officer' is eu-gdpr
  terminology but answer signals us-ca.
    citation: data protection officer
    fix: Use CCPA does not require a DPO; PIPA has 개인정보 보호책임자.
    If the answer is intentionally comparative, label each jurisdiction
    explicitly.
```

Two CCPA terminology violations: "personal data" (GDPR term) and "data
protection officer" (GDPR-only role; CCPA has no DPO). The answer
signals CCPA via the keyword but uses GDPR vocabulary, which confuses
the legal framework.

Multi-jurisdiction signal would skip this check (see E6 below) — the
auditor assumes comparative answers legitimately use both vocabularies.

---

## E4 — Mirror-backed case cited without disclosure (status: warn)

**Input:**
```
Per ca-supreme-kearney-v-salomon-smith-barney-2006, this is binding
California Supreme Court precedent on all-party consent.
```

**Audit output:**
```
=== Aggregate status: warn (1 finding(s)) ===

Per-auditor:
  us-ca                  status=warn   findings=1

Findings:
  [us-ca] [warn] Mirror-backed opinion cited without disclosing the
  mirror source.
    citation: ca-supreme-kearney-v-salomon-smith-barney-2006
    fix: Disclose that the local copy was fetched from a public mirror
    (e.g., SCOCAL) and cite the official California Courts archive URL
    from the case frontmatter.
```

The case IS binding precedent, but our local copy comes from the
Stanford SCOCAL mirror — not the official courts.ca.gov archive PDF
(which was unreachable when collected). The reader must know this so
they don't treat the local text as authoritative.

To pass: add a parenthetical like
`"(local copy from SCOCAL mirror; official URL: https://www.courts.ca.gov/opinions/archive/S124739.PDF)"`.

---

## E5 — Vague law references (status: warn)

**Input:**
```
The law requires businesses to obtain explicit consent before collection.
In some jurisdictions, additional notice is mandatory.
```

**Audit output:**
```
=== Aggregate status: warn (2 finding(s)) ===

Findings:
  [cross-jurisdiction] [warn] Vague law reference: 'The law requires'.
    fix: Vague reference to 'the law'. Cite the specific statute and
    section.

  [cross-jurisdiction] [warn] Vague law reference: 'In some jurisdictions'.
    fix: Vague jurisdiction reference. Name the specific jurisdictions.
```

Both phrases assert legal obligations without naming the source. The
auditor's proximity check (±200 chars) finds no specific authority id
anywhere nearby, so both fire.

The check skips when a real authority appears within ±200 chars — for
example, `Per ca-civ-1798.100, the law requires X` would pass because
the vague phrase becomes acceptable shorthand for the explicit cite.

---

## E6 — Multi-jurisdiction with labels (status: pass)

**Input:**
```
EU GDPR: Article 6 sets the lawful bases for processing personal data.

California: CCPA covers personal information per Cal. Civ. Code § 1798.100.
```

**Audit output:**
```
=== Aggregate status: pass (0 finding(s)) ===

Per-auditor:
  us-ca                  status=pass   findings=0
  kr-pipa                status=pass   findings=0
  eu-gdpr                status=pass   findings=0
  cross-jurisdiction     status=pass   findings=0
```

Multi-jurisdiction signal (`GDPR` + `CCPA` + `California`), explicit
labels (`EU GDPR:`, `California:`), each jurisdiction's terminology used
in its own paragraph. Citation routing, vocabulary, and label checks all
skip / pass. Ship.

This is the canonical comparative-answer template per CLAUDE.md §2.

---

## E7 — Invalid citation (status: fail)

**Input:**
```
Per Cal. Civ. Code § 1798.999, businesses must do something.
```

**Audit output:**
```
=== Aggregate status: fail (1 finding(s)) ===

Per-auditor:
  us-ca                  status=fail   findings=1

Findings:
  [us-ca] [error] Statute citation does not exist in ca-statute-index.json
  or ca-adjacent-statute-index.json: ca-civ-1798.999
    citation: Cal. Civ. Code § 1798.999
    fix: Check the section number or refresh the California statute
    indexes.
```

`§ 1798.999` does not exist in CCPA. CA sub-auditor returns `error`
severity, which propagates to aggregate `fail`. The pre-commit hook (if
enabled) would abort the commit; CI would fail the PR.

Fix: replace with a real section (e.g., `1798.150` for the private right
of action) or remove the citation entirely.

---

## Notes

- Examples assume v15 KB baseline (commits up to `905e15c`). Re-running
  audit-unified.py against a refreshed KB may produce slightly different
  per-auditor counts as the KB grows.
- For invocation details and the full catalog of checks, see
  [auditors.md](auditors.md).
- For setup including the optional pre-commit hook, see
  [README.md](../README.md).
