# Data Protection Agent v1.0.0

**Initial public release** — the unified privacy-research nucleus of the KP Legal Orchestrator, combining the EU GDPR and Korea PIPA expert agents into one cross-jurisdictional surface and adding California (CCPA-as-amended-by-CPRA) as the third sub-KB built in-tree.

---

## Why This Repo Exists

The KP Legal Orchestrator previously dispatched privacy questions to two separate sibling agents:

- **`GDPR-expert`** — EU specialist (GDPR + ePrivacy + AI Act + Data Act + Data Governance Act, 1,029 records)
- **`PIPA-expert`** — Korea specialist (PIPA + Network Act + Credit Information Act + Location Information Act + PIPC guidelines, 929 records)

That worked, but it had three structural problems:

1. **Real-world privacy compliance is rarely single-jurisdiction.** A SaaS product handling user data routinely needs simultaneous analysis across GDPR, PIPA, and CCPA-as-amended-by-CPRA. Even a Korea-only company often has EU customers via API; even an EU-only company often has California marketing exposure. Routing such a question to two single-jurisdiction specialists meant *two* token-billed runs producing *two* separate memos, which the user (or another agent) then had to reconcile by hand.
2. **No specialist was responsible for the boundary.** When GDPR-expert answered a "GDPR vs PIPA" question, it could only cover the GDPR side. When PIPA-expert answered the same question, it could only cover the PIPA side. Neither could catch the most damaging multi-juris failure mode — *blending authorities from different jurisdictions in a single paragraph*, mixing GDPR `controller` with CCPA `business` with PIPA `개인정보처리자` as if they were the same concept, or treating GDPR Recital 71 as binding when discussing CCPA opt-out.
3. **California had no specialist at all.** CCPA / CPRA / CPPA regulations / CIPA / CMIA / AADC — none of it was covered by any sibling agent. A CCPA question got the orchestrator's `fallback` path or a generic web-search answer, neither of which is grounded in primary law.

`data-protection-agent` collapses the GDPR + PIPA pair into one agent, builds the missing California sub-KB in-tree, and adds the cross-jurisdictional layer that no single-jurisdiction specialist could ever provide.

### What this means for the orchestrator

| Before | After |
|---|---|
| Privacy question → orchestrator dispatches to GDPR-expert *and* PIPA-expert (two runs) | Privacy question → orchestrator dispatches to data-protection-agent (one run) |
| Each specialist loads its own intake / retrieval / audit / composition pipeline | One agent loads once, serves all three jurisdictions |
| No California path; CCPA/CPRA falls to `fallback` or web search | First-class California sub-KB with its own auditor (CCPA, CPRA, CPPA regs, CIPA, CMIA, AADC) |
| No cross-jurisdiction quality gate | 4-layer auditor catches blending, vocabulary drift, vague refs, missing labels |
| Comparative answers assembled manually downstream | `comparative` mode produces side-by-side matrix + per-jurisdiction commentary in one document |

### Token discipline

Token savings are a real benefit, not the goal. The agent will spend *more* tokens — not fewer — when the alternative is a quality regression. But the structural waste of dispatching to two specialists for a multi-jurisdiction privacy question is gone. For a typical comparative ADM question (GDPR Art. 22 / PIPA 제37조의2 / CCPA ADMT), the v1.0.0 single-dispatch path produces a 14-source comparative memo with auditor pass in one slash-command invocation; the legacy two-agent path produced two separate memos that had to be reconciled.

### Codex-driven agent: forward-looking

The repo is structured so a Codex-driven implementation can use the same KB + auditor stack:

- All audit / validation / retrieval is **deterministic stdlib-only Python** (`scripts/audit-unified.py`, `scripts/validate-output.py`, `scripts/retrieve_authorities.py`) — no Claude-Code-specific dependencies.
- Output contract is **machine-readable JSON metadata** (`data-protection-agent-meta.json`) with a programmable validator.
- Skills under `.claude/skills/*/SKILL.md` are markdown — directly portable to a Codex setup that needs the same workflow discipline encoded as instructions.
- DOCX / HTML renderers (vendored from `legal-research-agent` in v21+v22) are pure Python CLIs.

A Codex-resident `data-protection-agent` (separate slash command surface, same KB and auditor, different orchestration shell) is on the post-v1 roadmap.

---

## Knowledge Base

| Sub-KB | Source-of-truth | Records | Primary law | Authority types |
|---|---|---:|---|---|
| `eu-gdpr` | sibling [GDPR-expert](https://github.com/kipeum86/GDPR-expert) | **1,029** | GDPR | Articles · Recitals · EDPB documents · CJEU cases · enforcement decisions |
| `kr-pipa` | sibling [PIPA-expert](https://github.com/kipeum86/PIPA-expert) | **929** | 개인정보 보호법 | Articles · Enforcement Decree · Network Act · Credit Info Act · Location Info Act · PIPC guidelines · court decisions |
| `us-ca` | local `sources/us-ca/` (built in-tree) | **237** | CCPA-as-amended-by-CPRA | CCPA statute · CPPA regulations (11 CCR § 7000–7300) · CalOPPA · CIPA · CMIA · AADC · Customer Records Act · OAG guidance · court opinions |
| **Total** | | **2,195** | | |

Plus **29 curated topic crosswalks** (CA 13 + KR 8 + EU 8) that boost retrieval for common privacy questions (notice / consent / data subject rights / sensitive data / breach notification / cross-border transfer / ADM / DPIA / enforcement / minors).

For the EU and KR sub-KBs the source-of-truth lives in the sibling repos (separately maintained, separately released). The importer at `scripts/import_namespaced_kbs.py` re-fetches them deterministically. The California sub-KB is built and maintained in-tree (`sources/us-ca/scripts/build_california_kb.py`).

---

## What's In v1.0.0

The internal CHANGELOG documents the v3 → v22 round-by-round development that produced this release. Headline capabilities:

### Knowledge + retrieval
- 3 namespaced sub-KBs unified under one `kb/` tree
- 2,195 indexed authorities with grade A/B/C/D vocabulary
- Deterministic local retrieval with topic-boost scoring (29 curated topics)
- `unified-authority-index.json` + `unified-topic-index.json` + `jurisdiction-routing.json`

### Citation auditor (~30 checks across 4 layers)
- **CA sub-auditor** — statute / regulation / case id missing · CPRA standalone framing · OAG FAQ as binding · enforcement as judicial precedent · federal court as CA binding · unpublished as controlling · 2026 regulation source required · mirror disclosure · future-effective cited as current · quote integrity
- **KR sub-auditor** — article id missing · 시행규칙 (Network Act enforcement rule) · PIPC guideline as binding · external Korean law referenced (not in KB) · future-effective bilingual triggers · quote integrity
- **EU sub-auditor** — article / recital / case id missing · ECLI lookup · EDPB document number lookup · Recital cited as binding rule · EDPB non-binding doc cited as binding · future-effective · quote integrity
- **Cross-jurisdiction** — citation routing · vocabulary drift · multi-juris labels missing · vague law references

### Agent answering pipeline
- 8-stage workflow (intake → retrieval → trust-boundary → claim-grounding → composition → quality-check → write → optional render)
- 10 modular skills under `.claude/skills/*/SKILL.md`
- 7 research modes (`ca_only` / `kr_only` / `eu_only` / `multi_jurisdiction` / `comparative` / `fallback_us` / `fallback`)
- 6 output modes (`canonical` / `legal_opinion` / `executive_brief` / `comparative_matrix` / `enforcement_case_law` / `black_letter_commentary`) — orthogonal to research mode
- `/answer` slash command for Claude Code; deterministic packet runner CLI for non-LLM use

### Output deliverables
- **Markdown** — 9-section research memo (always)
- **JSON metadata** — machine-readable contract (always)
- **DOCX** — basic + polished legal-opinion (cover page, classification banner, auto-numbered headings, endnote-style 각주)
- **HTML** — self-contained styled document for browser/email/intranet

DOCX + HTML renderers vendored verbatim from sibling `legal-research-agent` (rendering infrastructure already proven in production).

### Validation + quality gate
- Output contract validator (538 lines, stdlib only) — strict v19 mode + legacy_packet compat mode
- 13 golden fixtures (5 v19 + 8 legacy CA cases) parametrised over auditor + validator + DOCX + HTML
- 234 tests across 4 sub-suites: CA 49 / KR 23 / EU 28 / cross-cutting + e2e 134
- 11-step CI on every push and PR

### Documentation
- English README + Korean README (parallel, 700 lines each)
- CHANGELOG.md (round-by-round v3 → v22)
- `docs/agent-protocol.md` (machine-readable runtime contract)
- `docs/auditors.md` (full catalog of 30+ checks)
- `docs/examples.md` (7 worked auditor I/O examples)
- `docs/rendering-examples.md` (md / meta.json / docx / html walkthrough for one worked question)
- `docs/kb-operations-guide.md` (build / refresh / verify)
- Per-sub-KB operational notes under `docs/sub-kb-operations/`

---

## Quick Start

### Inside Claude Code

```text
/answer Under California law, when must a business provide notice at or before collection?
```

For polished DOCX legal-opinion output:

```text
/answer <question> output_mode=legal_opinion
```

### CLI (no LLM in the loop)

```bash
git clone https://github.com/kipeum86/data-protection-agent.git
cd data-protection-agent
pip install -r requirements.txt

# Refresh imported KBs (re-pulls EU/KR from sibling repos, CA from in-tree)
python3 scripts/import_namespaced_kbs.py --clean

# Retrieve top-K authorities deterministically
python3 scripts/retrieve_authorities.py "Compare GDPR Art 22 with PIPA 제37조의2" --top-k 12

# Audit a draft answer
python3 scripts/audit-unified.py path/to/answer.md
```

→ See [`README.md`](../../README.md) for the full quick-start, architecture, and usage guides.

---

## Compatibility

- **Python** 3.11+
- **Claude Code** for the `/answer` slash command path
- **CLI-only** (no Claude Code) is fully supported for retrieval, audit, validation, render
- **MCP integration** — not yet wired up; on the post-v1 roadmap

---

## Acknowledgments

Built on top of the sibling [GDPR-expert](https://github.com/kipeum86/GDPR-expert) and [PIPA-expert](https://github.com/kipeum86/PIPA-expert) knowledge bases. DOCX + HTML rendering stack vendored from sibling [legal-research-agent](https://github.com/kipeum86/legal-research-agent). Part of the **KP Legal Orchestrator** specialist graph.

---

## Disclaimer

This tool is for **legal research assistance only** and does not provide legal advice, does not create an attorney-client relationship, and is not a substitute for qualified legal counsel. Outputs are AI-generated and may contain errors despite the built-in citation auditor and output validator. Every legal citation produced by this tool **must be independently verified** against the official source before reliance in any professional, regulatory, or litigation context. Privacy law evolves rapidly — effective dates, amendments, and regulatory guidance change frequently.

If you are facing a specific legal question, consult a qualified attorney licensed in the relevant jurisdiction.

---

## License

Apache 2.0 — see [LICENSE](../../LICENSE).
