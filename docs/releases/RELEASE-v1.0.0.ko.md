# Data Protection Agent v1.0.0

**최초 공개 릴리즈** — KP Legal Orchestrator 의 개인정보 리서치 모듈. EU GDPR · 한국 PIPA 두 specialist 에이전트를 하나의 cross-jurisdictional 응답 표면으로 통합하고, 캘리포니아 (CCPA-as-amended-by-CPRA) 를 세 번째 sub-KB 로 in-tree 빌드 추가.

---

## 이 레포가 존재하는 이유

KP Legal Orchestrator 는 그동안 개인정보 질문을 두 개의 별도 sibling 에이전트로 dispatch 했습니다:

- **`GDPR-expert`** — EU specialist (GDPR + ePrivacy + AI Act + Data Act + Data Governance Act, 1,029 레코드)
- **`PIPA-expert`** — 한국 specialist (개인정보 보호법 + 정보통신망법 + 신용정보법 + 위치정보법 + PIPC 가이드라인, 929 레코드)

이 구조는 작동은 했지만 세 가지 구조적 문제가 있었습니다:

1. **실무 개인정보 컴플라이언스는 단일 법역으로 끝나는 경우가 드물다.** 사용자 데이터를 다루는 SaaS 제품은 GDPR · PIPA · CCPA-as-amended-by-CPRA 분석을 동시에 요구하는 경우가 일상. 한국 전용 회사도 API 를 통해 EU 고객을 받고, EU 전용 회사도 캘리포니아 마케팅 노출이 있습니다. 이런 질문을 두 개의 단일 법역 specialist 에 dispatch 하면 *두 번* 토큰이 청구되고 *두 개*의 별도 메모가 나오며, 그 둘을 사용자 (또는 또 다른 에이전트) 가 손으로 reconcile 해야 했습니다.
2. **경계를 책임지는 specialist 가 없었다.** GDPR-expert 가 "GDPR vs PIPA" 질문에 답하면 GDPR 쪽만 다룰 수 있고, PIPA-expert 가 같은 질문에 답하면 PIPA 쪽만 다룰 수 있었습니다. 그 누구도 가장 위험한 다중 법역 실패 모드 — *한 문단 안에 다른 법역 권위를 섞어버리는 것* — 를 catch 할 수 없었습니다. GDPR `controller` + CCPA `business` + PIPA `개인정보처리자` 를 같은 개념인 것처럼 합치거나, GDPR Recital 71 을 binding 으로 인용하면서 CCPA opt-out 을 논하는 것을 막을 책임자가 없었던 것입니다.
3. **캘리포니아 specialist 자체가 없었다.** CCPA / CPRA / CPPA 규정 / CIPA / CMIA / AADC — 어떤 sibling 에이전트도 다루지 않았습니다. CCPA 질문은 orchestrator 의 `fallback` 경로를 타거나 일반 웹 검색에 의존했는데, 둘 다 primary law 에 grounded 되지 못한 답변이었습니다.

`data-protection-agent` 는 GDPR + PIPA pair 를 하나의 에이전트로 합치고, 누락된 캘리포니아 sub-KB 를 in-tree 로 빌드하며, 단일 법역 specialist 만으로는 절대 만들 수 없었던 cross-jurisdictional 레이어를 추가합니다.

### Orchestrator 입장에서의 변화

| Before | After |
|---|---|
| 개인정보 질문 → orchestrator 가 GDPR-expert *와* PIPA-expert 양쪽에 dispatch (두 번 실행) | 개인정보 질문 → orchestrator 가 data-protection-agent 에 dispatch (한 번 실행) |
| 각 specialist 가 자체 intake / retrieval / audit / composition 파이프라인 로드 | 한 에이전트가 한 번 로드하고 3개 법역 모두 서비스 |
| 캘리포니아 경로 부재; CCPA/CPRA 는 `fallback` 또는 웹 검색 | 자체 auditor 가 붙은 first-class 캘리포니아 sub-KB (CCPA · CPRA · CPPA 규정 · CIPA · CMIA · AADC) |
| Cross-jurisdiction 품질 게이트 부재 | 4-layer auditor 가 blending · 용어 drift · 막연한 인용 · 라벨 누락 catch |
| 비교 답변은 downstream 에서 수동 조립 | `comparative` 모드가 side-by-side 매트릭스 + 법역별 commentary 를 한 문서에 |

### 토큰 규율

토큰 절감은 진짜 benefit 이지만 목표는 아닙니다. 품질 후퇴를 막기 위해서라면 에이전트는 *더 많은* 토큰을 씁니다. 하지만 다중 법역 개인정보 질문에 대해 두 specialist 에 dispatch 하던 구조적 낭비는 사라졌습니다. 자동화된 결정 (ADM) 비교 질문 (GDPR Art. 22 / PIPA 제37조의2 / CCPA ADMT) 의 경우, v1.0.0 의 single-dispatch 경로는 한 번의 슬래시 명령으로 14-source 비교 메모 + auditor pass 를 생성합니다. 기존 two-agent 경로는 두 개의 별도 메모를 만들어 reconcile 이 필요했습니다.

### Codex-driven 에이전트: 미래 방향

레포가 Codex-driven 구현체가 동일한 KB + auditor 스택을 쓸 수 있도록 구조화되어 있습니다:

- 모든 audit / validation / retrieval 이 **결정론적 stdlib-only Python** (`scripts/audit-unified.py`, `scripts/validate-output.py`, `scripts/retrieve_authorities.py`) — Claude Code 전용 의존성 없음.
- 출력 컨트랙트가 **머신 readable JSON 메타데이터** (`data-protection-agent-meta.json`) + 프로그램 검증기.
- `.claude/skills/*/SKILL.md` 의 스킬은 markdown — 동일한 워크플로우 규율을 instruction 으로 인코딩한 형태로, Codex 셋업에 직접 portable.
- DOCX / HTML 렌더러 (v21+v22 에서 `legal-research-agent` 로부터 vendor) 는 순수 Python CLI.

별도 슬래시 명령 표면 + 동일 KB·auditor + 다른 orchestration shell 을 가지는 Codex-resident `data-protection-agent` 가 v1 이후 로드맵에 있습니다.

---

## 지식베이스

| Sub-KB | Source-of-truth | 레코드 | 주요 법령 | 권위 유형 |
|---|---|---:|---|---|
| `eu-gdpr` | sibling [GDPR-expert](https://github.com/kipeum86/GDPR-expert) | **1,029** | GDPR | Articles · Recitals · EDPB 문서 · CJEU 판례 · enforcement decisions |
| `kr-pipa` | sibling [PIPA-expert](https://github.com/kipeum86/PIPA-expert) | **929** | 개인정보 보호법 | 법조문 · 시행령 · 정보통신망법 · 신용정보법 · 위치정보법 · PIPC 가이드라인 · 법원 판결 |
| `us-ca` | local `sources/us-ca/` (in-tree 빌드) | **237** | CCPA-as-amended-by-CPRA | CCPA 본법 · CPPA 규정 (11 CCR § 7000–7300) · CalOPPA · CIPA · CMIA · AADC · Customer Records Act · OAG 가이드 · 법원 판결 |
| **합계** | | **2,195** | | |

추가로 **29개 큐레이션 토픽 매핑** (CA 13 + KR 8 + EU 8) 이 자주 묻는 개인정보 질문 (통지 / 동의 / 정보주체 권리 / 민감정보 / 유출 통지 / 국외 이전 / ADM / DPIA / enforcement / 미성년자) 의 retrieval 을 boost.

EU/KR sub-KB 의 source-of-truth 는 sibling 레포 (별도 유지·릴리스). importer (`scripts/import_namespaced_kbs.py`) 가 결정론적으로 re-fetch. 캘리포니아 sub-KB 는 in-tree 빌드·유지 (`sources/us-ca/scripts/build_california_kb.py`).

---

## v1.0.0 에 포함된 것

내부 CHANGELOG 가 v3 → v22 라운드별 개발 히스토리를 기록. 핵심 capability:

### 지식 + retrieval
- 3개 namespaced sub-KB 를 하나의 `kb/` 트리로 통합
- 2,195 indexed 권위 + grade A/B/C/D 어휘
- 결정론적 로컬 retrieval + topic-boost 스코어링 (29개 큐레이션 토픽)
- `unified-authority-index.json` + `unified-topic-index.json` + `jurisdiction-routing.json`

### 인용 감사기 (4-layer 위 ~30개 체크)
- **CA sub-auditor** — statute / regulation / case id 누락 · CPRA standalone framing · OAG FAQ 를 binding 으로 · enforcement 를 judicial precedent 로 · 연방법원 을 CA binding 으로 · unpublished 를 controlling 으로 · 2026 regulation source required · mirror 공시 · future-effective 를 현재형으로 · 인용 무결성
- **KR sub-auditor** — Article id 누락 · 시행규칙 (정보통신망법) · PIPC 가이드라인 binding 오용 · 외부 한국법 인용 (KB 미커버) · future-effective bilingual triggers · 인용 무결성
- **EU sub-auditor** — Article / Recital / Case id 누락 · ECLI 조회 · EDPB document number 조회 · Recital binding 오용 · EDPB non-binding doc binding 오용 · future-effective · 인용 무결성
- **Cross-jurisdiction** — Citation routing · 용어 drift · 다중 법역 라벨 누락 · 막연한 법령 인용

### 에이전트 응답 파이프라인
- 8단계 워크플로우 (intake → retrieval → trust-boundary → claim-grounding → composition → quality-check → write → optional render)
- `.claude/skills/*/SKILL.md` 아래 10개 모듈러 스킬
- 7개 research 모드 (`ca_only` / `kr_only` / `eu_only` / `multi_jurisdiction` / `comparative` / `fallback_us` / `fallback`)
- 6개 output 모드 (`canonical` / `legal_opinion` / `executive_brief` / `comparative_matrix` / `enforcement_case_law` / `black_letter_commentary`) — research 모드와 직교
- Claude Code 용 `/answer` 슬래시 명령; 비-LLM 용 결정론적 packet runner CLI

### 출력 deliverable
- **Markdown** — 9-section 리서치 메모 (항상)
- **JSON 메타데이터** — 머신 readable 컨트랙트 (항상)
- **DOCX** — basic + 폴리시 legal-opinion (표지 + 기밀 banner + 자동 번호 헤딩 + 각주 변환)
- **HTML** — browser/email/intranet 용 self-contained 스타일 문서

DOCX + HTML 렌더러는 sibling `legal-research-agent` 에서 verbatim 으로 vendor (production 검증된 렌더링 인프라).

### 검증 + 품질 게이트
- 출력 컨트랙트 검증기 (538줄, stdlib only) — strict v19 모드 + legacy_packet compat 모드
- 13개 golden fixture (5 v19 + 8 legacy CA cases) — auditor + validator + DOCX + HTML 모두 parametrize
- 234개 테스트 (CA 49 / KR 23 / EU 28 / cross-cutting + e2e 134)
- 모든 push + PR 에서 11-step CI

### 문서
- 영문 README + 한국어 README (parallel, 각 700줄)
- CHANGELOG.md (라운드별 v3 → v22)
- `docs/agent-protocol.md` (머신 readable runtime 컨트랙트)
- `docs/auditors.md` (30+ 체크 전체 카탈로그)
- `docs/examples.md` (auditor I/O 7개 worked example)
- `docs/rendering-examples.md` (한 worked question 의 md / meta.json / docx / html walkthrough)
- `docs/kb-operations-guide.md` (build / refresh / verify)
- `docs/sub-kb-operations/` 아래 sub-KB 별 운영 노트

---

## 빠른 시작

### Claude Code 안에서

```text
/answer 캘리포니아 법상 사업자가 개인정보 수집 시점 또는 그 이전에 통지를 제공해야 하는 시점은?
```

폴리시 DOCX legal-opinion 출력 원할 시:

```text
/answer <질문> output_mode=legal_opinion
```

### CLI (LLM 없이)

```bash
git clone https://github.com/kipeum86/data-protection-agent.git
cd data-protection-agent
pip install -r requirements.txt

# Imported KB refresh (sibling 레포에서 EU/KR, in-tree 에서 CA 다시 가져옴)
python3 scripts/import_namespaced_kbs.py --clean

# Top-K 권위 결정론적 retrieve
python3 scripts/retrieve_authorities.py "GDPR Art 22 와 PIPA 제37조의2 비교" --top-k 12

# Draft 답변 audit
python3 scripts/audit-unified.py path/to/answer.md
```

→ 전체 quick-start, 아키텍처, 사용 가이드는 [`README.ko.md`](../../README.ko.md) 참조.

---

## 호환성

- **Python** 3.11+
- **Claude Code** — `/answer` 슬래시 명령 경로용
- **CLI-only** (Claude Code 없이) — retrieval, audit, validation, render 전부 지원
- **MCP 통합** — 아직 wire up 안 됨; v1 이후 로드맵

---

## 감사

sibling [GDPR-expert](https://github.com/kipeum86/GDPR-expert) + [PIPA-expert](https://github.com/kipeum86/PIPA-expert) 지식베이스 위에 빌드. DOCX + HTML 렌더링 스택은 sibling [legal-research-agent](https://github.com/kipeum86/legal-research-agent) 에서 vendor. **KP Legal Orchestrator** specialist 그래프의 일부.

---

## 면책사항

이 도구는 **법률 리서치 보조 전용**이며, 법률 자문을 제공하지 않고, 변호사-의뢰인 관계를 형성하지 않으며, 자격 있는 법률 자문을 대체할 수 없습니다. 출력은 AI 가 생성한 결과이며, 내장 인용 감사기와 출력 검증기에도 불구하고 오류가 있을 수 있습니다. 본 도구가 생성한 모든 법적 인용은 전문적·규제적·소송 컨텍스트에서 의존하기 전에 **공식 source 를 통해 독립적으로 확인**해야 합니다. 개인정보 법은 빠르게 진화합니다 — 시행일, 개정, 규제 가이드는 자주 변경됩니다.

구체적인 법률 사안에 직면해 있다면, 해당 법역에서 자격을 갖춘 변호사에게 자문을 받으세요.

---

## 라이선스

Apache 2.0 — [LICENSE](../../LICENSE) 참조.
