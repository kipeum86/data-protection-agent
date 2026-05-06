# California Expert Local KB

Local staging knowledge base for California privacy law materials.

This folder prioritizes public official sources and separates any non-official mirror-backed material by source grade:

- CCPA statute and CPPA regulations.
- High-relevance adjacent California privacy statutes from LegInfo, including CalOPPA, customer records/breach notice, CMIA, SOPIPA, Age-Appropriate Design Code, Data Broker/Delete Act, and CIPA provisions.
- CPPA/OAG guidance.
- OAG/CPPA enforcement and administrative materials.
- Official court-hosted CCPA-related opinions.
- Grade B public mirrors for published cases only when the official California Courts raw source is not locally fetchable; these records must preserve both `official_url` and `source_url`.
- Topic and golden-question indexes for retrieval and answer-quality checks.

Run:

```bash
python3 scripts/build_california_kb.py --all
python3 scripts/build_california_kb.py --fetch-adjacent --index --validate
python3 scripts/build_california_kb.py --index --validate
python3 scripts/build_california_kb.py --validate
```

Generated files are written under `raw/`, `library/`, and `index/`.

## No-Hallucination Contract

- Do not answer a California legal claim unless it is grounded in a local authority id and markdown file.
- Every authority used in an answer must trace to an `official_url` in frontmatter. If `source_url` differs from `official_url`, disclose that the local raw text came from a mirror.
- If a requested claim is not supported by this KB, say that the local KB does not currently support it.
- Do not treat guidance, FAQs, press releases, settlements, or administrative orders as binding judicial precedent.
- Do not treat federal district court orders as California appellate precedent.
- Frame current obligations as CCPA as amended by CPRA, unless discussing CPRA amendment history.

Run the grounding gates before using a rebuilt KB:

```bash
python3 scripts/build_california_kb.py --validate
PYTHONPATH=. pytest -q tests
```
