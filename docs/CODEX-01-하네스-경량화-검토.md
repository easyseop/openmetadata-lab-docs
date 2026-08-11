# [Codex 평가 요청] OpenMetadata 거버넌스 하네스 — 경량화·정리 검토

> 대상: `openmetadata-test` (검사기/거버넌스 하네스), 제품 `OM_TEMP@custom/om-1.13.1`
> 형식: **요구사항 : 답변(판단)**. Codex는 각 답변의 타당성·반례·누락을 비판적으로 평가해 주세요.
> 근거: 검사기 54개 전수 + 관리파일 전수 + 예행연습 가이드 11종에 대한 심층조사.
> 전제: **이 하네스는 현재 원격 CI에서 source gate 8 + patch-kill 2가 통과하는, 잘 돌아가는 fail-closed 시스템이다. 보수적으로 판단했다.**

---

## 요구사항 1
관리 파일이 너무 많다. 어떤 부분을 합치고 경량화할 수 있나?

### 답변
**"파일이 많다 = 낭비"가 아니다. 정본은 유지하고, "손관리되는 파생 데이터"만 생성기로 전환하라.**

단일 정본(SSOT) 계층:
- **L1 정본(손편집 유지):** `manifests/BANK-OM-*.yaml`(퍼-ID scope·watch·contract·series), `contracts.yaml`(업무 불변식+테스트 selector), `customization-registry.yaml` 중 `owner/criticality/provenance/source:헤더/unregistered_findings/limitations`만, `shared-path-owners.yaml`의 **hunk 단위 의미**.
- **L2 정책(손편집 유지):** `policies/{repository-layout,sensitive-zones,debt-thresholds}.yaml`, `change-intent-current.yaml`, `fixtures/fetch_upstream.sh`(pinned SHA).
- **L3 생성/파생(손편집 금지 → 생성기):** `source-diff-paths.txt`(=`git diff --name-only`), registry의 `entries[].{id,title,manifest,contracts,status}`(⟵manifests), `shared-path-owners`의 **경로 집합**(⟵manifest 교집합), `*-evidence.yaml`의 비교부(⟵러너), `preparation-plans/**`(⟵`prepare_registration.py plan`), 루트 `run_*.py` 셈.
- **L4 손관리 집계(냄새):** `source-candidate-evidence.yaml`.

우선순위 정리 대상:
1. **루트 `run_*.py` 셈 4종**(`run_source_candidate_gates/run_source_patch_kills/run_runtime_contracts/compare_ui_typecheck`) — CI도 안 쓰는 `runpy` 위임. **삭제가 목적이 아니라**, 구현이 한 제품 폴더(`registrations/kb-openmetadata/`)에 결합된 걸 **`harness/lib/`로 이동**하고 registration은 데이터만 갖게 → 셈 불필요 + 2번째 제품 등록 시 복붙 0.
2. **`source-candidate-evidence.yaml` 3분할** — 기계 verdict(생성)/원격 CI 사실(API append-only)/사람 limitations(손관리). 지금은 매 배치 수동 재동기화 = 최대 드리프트 위험.
3. **파생물 생성기**(`make registry|diff-paths|shared-paths`) + 생성물≠커밋본이면 CI fail(=현재 tripwire 성질 유지).

### 근거
- 루트 셈은 ~15줄 `runpy.run_path`이고 CI 워크플로는 registration 구현을 직접 호출(셈 미사용)로 확인됨.
- `customization-registry` entries의 `title/contracts/status`는 manifest와 중복이나, `criticality/owner/provenance/source:/unregistered_findings`는 정본(다른 데서 파생 불가).

### 반례/한계 (Codex 검증 요망)
- **`harness/tools/` 내용 미확인** — 이번 조사에서 셸 부재로 열거 실패. 여기 진짜 중복/데드코드가 있을 수 있음. **Codex가 가장 먼저 열거**할 것.

---

## 요구사항 2
검사기의 중복 검사가 너무 많으면 어떻게 합치나?

### 답변
**전수 검토 결과, 삭제·통합 대상 "진짜 중복"은 없다. 54개 모두 계층 방어(layered defense)다. 합치더라도 "assertion 감소"는 금지, DRY 리팩터만 하라.**

- 유일한 완전중복 assertion: `V.aggregate([])==ANALYSIS_ERROR`가 `test_verdict`·`test_runner_exit_codes` 둘 다 존재. **그러나** 전자는 집계 로직, 후자는 "러너가 `to_exit_code`를 실제 호출하는지(AST)"를 검사 → 실패모드 상이 → **둘 다 유지**.
- 허용되는 경량화 = **DRY만**:
  1. 공유 셋업 픽스처 추출(예: reapply/resolve/replay/finalstate의 실제 auth git 시나리오 셋업 중복 → `conftest.py`).
  2. 동형 테스트 `parametrize`(3개 `*_workflow`, staleness 계열) — **parametrize id를 명확히** 해 실패 시 대상 즉시 식별.
  3. 파일을 합쳐도 서로 다른 실패를 잡는 assertion은 보존.

### 근거 (겹쳐 보여도 계층 방어인 대표 클러스터)
- verdict/exit-code(4): 집계로직 / 러너 손코딩 / 저장결과 위변조 / 검증기 크래시 — 4개 다른 실패.
- GitHub Actions(3): 워크플로 파일·필드가 각기 다름, 하나 지우면 그 워크플로 무방비.
- staleness/digest(10): 같은 primitive를 **증거 타입별로** 재검증.
- scope 상·하한(4): `registration_prep`이 `drift`와 **같은 verdict 도달**을 의도적으로 교차검증(설계 불변식).

### 반례/한계
- dead/미사용 테스트 0개. **"검사기 수가 많다"는 이유만으로 줄이면 fail-closed 강도가 떨어진다.**

---

## 요구사항 3
각각 만들어둔 이유가 있을 수 있으니 한 번 더 면밀히 검토하라. 지금도 잘 돌아가는 것 같다.

### 답변
**옳은 우려다. 재검토 결과 "의도된 중복(tripwire)"이 다수이고, 이는 절대 제거하면 안 된다.**

절대 건드리면 안 되는 의도된 중복:
- `source-diff-paths.txt` ↔ git: `vendor_rebuild`가 실제 트리 diff와 비교 → 불일치 시 `analysis_error`(드리프트 tripwire). registry `changed_path_count:113`은 2차 가드.
- registry ↔ manifest, `contracts.customization_ids` ↔ `manifest.assurance.contracts`: 양방향 닫힌 그래프 검증(`registry.validate_references`), 각 방향이 다른 누락을 잡음.
- `shared-path-owners.yaml` ↔ manifest 경로: hunk 단위 진실(로케일 semantic-key vs 들여쓰기 churn 구분)을 담아 `reconstruct_series.py`가 정직한 퍼-ID 커밋 생성.
- 두 patch-kill 플랜의 ID 겹침: 러너가 `runtime_ids == source pending_ids`를 assert → 겹침이 곧 불변식.

### 정정 고지 (Codex가 평가할 지점)
초기 인상은 "검사기 55개는 11개 커스텀에 과설계 → 쳐내라"였으나 **전수 검토로 이 판단을 철회**한다. 계층 방어라 삭제 대상이 없다. (이 정정 자체의 타당성을 Codex가 재검증해 주면 좋다.)

---

## 요구사항 4
예행연습 가이드가 흐름상 너무 구체적이고 실행 명령어가 많으면 어떻게 축소하나?

### 답변
**총 ~188개(퍼-ID 루프 포함 시 250+). "이미 있는 오케스트레이션(`om_workflow.py` 묶음실행, `.sh` 래퍼)을 완성"해 60~80개 축소하라. 단 사람 판단 단계는 유지.**

축소안(레버리지 순):
- **R3** Guide4 §5-2: 퍼-ID 11명령×7ID → 기존 `reconstruct_remaining_ids.sh` 경로로 001도 통합해 `reconstruct_all_ids.sh`(퍼-ID 타이핑 승인 유지, diff는 스크립트가 출력).
- **R5** Guide7&10: 동일 검사 4~6명령 2회 → `rehearse checks --version <X>` 하나로 fan-out.
- **R6** Guide10 §2-1: 9파일 `cp` → `om_workflow.py carry-forward --from 1.13.1 --to 1.13.2`(목록은 manifest에서 생성).
- **R2** Guide2: 12명령이 100% 결정론(`echo $?` 3회) → `rehearse attach-and-verify 1.13.1`가 PASS/FAIL 표 출력.
- **R4** Guide4 §7-4-4: 리터럴 7 SHA `cherry-pick` → `--reverse` 로그 기반 `rebase-onto-official`.
- R1/R7/R8: preflight 검증전용·`cd`+`source` 의식·표시용 `sed/find`는 스크립트/노트로.

축소 금지(사람 판단·안전 코어):
- Guide3(파일→ID 분류), Guide6(개념 학습), Guide9 §4(업무 충돌 해소), Guide4 §5-3/§6-1(타이핑 승인), Guide11 T91(정직한 fail-closed block), SHA/digest 동일성 확인 표.

### 근거
- Guide2의 모든 검사에 기대값이 하드코딩돼 있고 `echo $?`가 3회 등장 = 기계 assert 신호.
- 저자들이 이미 `rehearsal_env.sh`, `om_workflow.py validate|source`, 4개 `.sh` 래퍼 보유 → 새 패러다임 아님.

---

## 실행 태스크 (Codex용, 수용기준)
- **T-A** `harness/tools/` 먼저 enumerate(미확인 영역).
- **T-B** 러너 구현 `harness/lib/`로 이동 + registration은 데이터만 → 루트 셈 제거. (수용: 8 source gate+2 patch-kill 재통과)
- **T-C** 파생물 생성기 + 생성물≠커밋본 시 CI fail. (수용: 손편집 없이 현 커밋본 재생성 일치)
- **T-D** `source-candidate-evidence.yaml` 3분할.
- **T-E** 검사기 DRY(픽스처·parametrize), assertion·실패모드 100% 보존.
- **T-F** 예행연습 오케스트레이션 R3/R5/R6/R2/R4.

## 가드레일 (하지 말 것)
- ❌ 검사기 통합으로 assertion 감소 ❌ 의도된 tripwire 제거 ❌ 사람 승인 자동-pass화 ❌ 파생물 손편집 회귀
- ✅ 목표 = **손관리 표면 축소 + 오케스트레이션**, 검증 강도 축소 아님.
