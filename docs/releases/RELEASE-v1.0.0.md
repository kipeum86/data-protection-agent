# Data Protection Agent v1.0.0

**Initial public release** · **최초 공개 릴리즈**

The unified privacy-research nucleus of the **KP Legal Orchestrator** — folds the [GDPR-expert](https://github.com/kipeum86/GDPR-expert) and [PIPA-expert](https://github.com/kipeum86/PIPA-expert) sibling agents into one cross-jurisdictional surface and adds California (CCPA-as-amended-by-CPRA) as the third sub-KB built in-tree.

**KP Legal Orchestrator** 의 개인정보 리서치 모듈 — [GDPR-expert](https://github.com/kipeum86/GDPR-expert) + [PIPA-expert](https://github.com/kipeum86/PIPA-expert) sibling 에이전트를 하나의 cross-jurisdictional 응답 표면으로 통합하고, 캘리포니아 (CCPA-as-amended-by-CPRA) 를 세 번째 sub-KB 로 in-tree 빌드 추가.

---

## Why one agent, not two specialists / 두 specialist 가 아니라 하나의 에이전트인 이유

A SaaS handling user data routinely needs simultaneous GDPR + PIPA + CCPA analysis. Routing such a question to two single-jurisdiction specialists meant *two* token-billed runs producing *two* memos to reconcile by hand — and California had no specialist at all. This release collapses the pair into one agent, builds the missing California sub-KB in-tree, and adds the cross-jurisdictional auditor that catches authority-blending across borders (`controller` vs `business` vs `개인정보처리자` collapsed as one concept, GDPR Recital 71 cited as binding under CCPA, etc.).

사용자 데이터를 다루는 SaaS 는 GDPR · PIPA · CCPA 분석을 동시에 요구하는 경우가 일상. 두 단일 법역 specialist 에 dispatch 하면 토큰이 *두 번* 청구되고 두 개의 별도 메모를 손으로 reconcile 해야 했고, 캘리포니아 specialist 는 아예 없었음. 이번 릴리즈가 GDPR + PIPA pair 를 하나로 합치고, 누락된 캘리포니아 sub-KB 를 in-tree 빌드하며, 국경 너머 권위 혼용을 잡는 cross-jurisdictional auditor 를 추가합니다 (`controller` vs `business` vs `개인정보처리자` 동일시, CCPA 맥락에서 GDPR Recital 71 을 binding 으로 인용 등).

---

## Highlights / 주요 내용

| | |
|---|---|
| Sub-KBs / 서브-KB | **3** (eu-gdpr 1,029 · kr-pipa 929 · us-ca 237 = **2,195** indexed authorities) |
| Topic crosswalks / 토픽 매핑 | **29** (CA 13 + KR 8 + EU 8) |
| Audit checks / 감사 체크 | **~30** across 4 layers (3 sub-auditors + cross-jurisdiction) |
| Tests | **234** (CA 49 / KR 23 / EU 28 / cross-cutting + e2e 134) |
| Research modes / 리서치 모드 | **7** (`ca_only` / `kr_only` / `eu_only` / `multi_jurisdiction` / `comparative` / `fallback_us` / `fallback`) |
| Output modes / 출력 모드 | **6** (`canonical` / `legal_opinion` / `executive_brief` / `comparative_matrix` / `enforcement_case_law` / `black_letter_commentary`) |
| Output forms / 출력 형식 | Markdown · JSON metadata · DOCX · HTML |
| Slash command / 슬래시 명령 | `/answer` (Claude Code) · CLI-only path also supported |

---

## Forward-looking / 앞으로

A separate **Codex-resident `data-protection-agent`** (different orchestration shell, same KB + auditor stack) is on the post-v1 roadmap. The repo is structured to support this — all retrieval / audit / validation / rendering is deterministic stdlib-or-pure-Python with a machine-readable JSON contract; skills are markdown that ports across hosts.

별도의 **Codex-resident `data-protection-agent`** (다른 orchestration shell, 동일 KB + auditor 스택) 가 v1 이후 로드맵. 레포가 이를 지원하도록 구조화되어 있음 — 모든 retrieval / audit / validation / rendering 이 결정론적 stdlib-or-pure-Python + 머신 readable JSON 컨트랙트, 스킬은 호스트 간 portable 한 markdown.

---

## Quick start / 빠른 시작

In Claude Code / Claude Code 안에서:

```text
/answer Under California law, when must a business provide notice at or before collection?
/answer <question> output_mode=legal_opinion    # polished DOCX legal opinion
```

Full quick-start, architecture, and CLI usage — see the README:

전체 quick-start, 아키텍처, CLI 사용법은 README 참조:

- **English** — [`README.md`](https://github.com/kipeum86/data-protection-agent#readme)
- **한국어** — [`README.ko.md`](https://github.com/kipeum86/data-protection-agent/blob/main/README.ko.md)
- Round-by-round / 라운드별 — [`CHANGELOG.md`](https://github.com/kipeum86/data-protection-agent/blob/main/CHANGELOG.md)

---

## Disclaimer / 면책사항

This tool is for **legal research assistance only** — it does not provide legal advice. AI-generated output may contain errors despite the built-in citation auditor and output validator. Every legal citation must be independently verified against the official source before reliance.

본 도구는 **법률 리서치 보조 전용** — 법률 자문이 아닙니다. 내장 인용 감사기와 출력 검증기에도 불구하고 AI 출력에 오류가 있을 수 있습니다. 모든 법적 인용은 공식 source 를 통해 의존 전 독립적으로 확인해야 합니다.

## License / 라이선스

Apache 2.0 — see [LICENSE](https://github.com/kipeum86/data-protection-agent/blob/main/LICENSE).
