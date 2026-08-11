# 수정 설계안 — 하네스 phase 번들링 (구현 전, 승인 대기)

> 대상: `openmetadata-test` @ `codex/om-1.13.1-rehearsal-baseline-20260806`, 코드 repo `~/om-work/om-temp-real-1.13.1`(blobless partial clone)
> 상태: **설계안. 코드 미수정.** vendor merge·충돌해결·custom branch 수정 안 함. 구현은 별도 승인 후.
> 근거: Codex 전달문(CODEX_03 검토) 8개 요구 + 2026-08-07 실측.

## 0. 전제와 즉시 보고할 사실 (사용자 수정 반영)

- **정본 candidate = `8ac18ad053d9274774e274ba17b35911ac0b9dcb` 로 확정.** 소스 검사·Runtime Contract 9개·Docker image(`1.13.1-bank-8ac18ad0`)가 모두 이 SHA에 고정됨.
- 다른 SHA는 **정본 후보가 아님(provenance로만 기록)**:
  | SHA | tree | 분류 |
  |---|---|---|
  | `8ac18ad0…` | `e86980f6…` | **정본 candidate(활성)** |
  | `85e60d42…` | `e86980f6…` | **동일 tree의 과거 병렬 commit** — 코드 동일(파일 diff 0), 정본 후보 제외 |
  | `d952a838…` (registry `source.snapshot_sha`) | — | 최초 등록 snapshot(과거) — provenance |
  - 실측 확인: `git rev-parse 8ac18ad^{tree}` == `git rev-parse 85e60d42^{tree}` == `e86980f6d71295465fe6e75e5169fab57cebd4c4`.
- **영향(내 08-07 사전검사):** candidate=`d952a838`로 실행함.
  - 유지 가능: **T42(watch), 공식 구조화 diff(T51/T52)** — base/target(공식)만 사용, candidate 무관.
  - **재실행 필요(정본 `8ac18ad0` 기준): T93 exact-scope, T41, watch-suggest, T43.**
- 따라서 **1번(candidate 정합성 확인)이 candidate 사용 검사들의 선행조건**이다.

## 1. candidate 정본 정합성 (최우선, 수정 반영)

- **정본 lock = 기존 스키마 재사용(중복 모듈 금지):** `harness/acgh/candidate.py`의 `CandidateLock`/`CandidateIdentity`(`repository`·`commit_sha`·`tree_sha`·`artifact_digest`)를 그대로 사용. **별도 `candidate_lock.py`를 새로 만들지 않는다.**
- **candidate-lock에는 기술 기준만:** `commit_sha`(=`8ac18ad0…`)·`tree_sha`(=`e86980f6…`)·`repository`·`artifact_digest`. **승인자·승인 시각·승인 근거는 넣지 않는다.**
- **승인은 별도 파일:** 승인 메타(approver·approved_at·rationale)는 별도 승인 파일에 두고 **`candidate_lock_digest`로 연결**. lock이 바뀌면 digest가 바뀌어 기존 승인 자동 무효.
- **정합성 검사(신규 `candidate-consistency`)는 "활성 기준"만 대조** — 과거 값은 검사에서 제외:
  - 확인 대상(활성): `commit-inventory.custom_head_sha`(현재) · **활성 candidate-lock** · **Runtime candidate-lock** · **Docker image revision**.
  - **제외(=provenance로만 표시, 불일치해도 정상):** `registry.source.snapshot_sha`(=d952a838, 최초 등록 snapshot), 과거 proposal, 과거 evidence.
  - 활성 기준끼리 다르면 **검사 시작 금지 + 어떤 파일의 어떤 값이 다른지 출력**(STOP). 같으면 통과.
  - phase 실행기는 branch 이름/HEAD를 임의로 쓰지 않고 **활성 candidate-lock의 SHA만** 사용.
- **사람 STOP:** 정본을 `8ac18ad0`로 lock하는 승인(및 활성 기준 파일 정렬)은 사람이 결정.

## 2. verdict 4종 유지 + phase_status·execution_status 분리 (수정 반영)

- **verdict는 기존 4종만:** `pass·approval·block·analysis_error`. **`not_evaluated`도 `incomplete`도 verdict로 추가하지 않는다.**
- 두 개의 직교 필드로 표현:
  - **`execution_status`**(gate 단위): `executed | skipped_missing_input | blocked_by_preflight`.
  - **`phase_status`**(실행 전체 단위): `complete | incomplete`.
- **T43(conflict-rate 없음):** gate에 `execution_status=skipped_missing_input`, `verdict=null`.
- **집계 규칙:** 필수 gate가 미실행이면 → `phase_status: incomplete` **그리고** `overall_verdict: analysis_error`(fail-closed). 즉 "미실행"은 **verdict `analysis_error` + phase_status `incomplete`** 조합으로 표현하지, 새 verdict를 만들지 않는다. "T43 미실행인데 전체 pass" 불가.

## 3. 공통 verdict 집계 + 기존 종료코드 재사용 (JSON 정본, 수정 반영)

- 현황(정정): `watch`는 verdict 무관 **exit 0**; `risk`는 pass=0/block·analysis_error=1/approval=2로 **비표준**.
- 설계: 모든 phase가 **동일 `acgh.verdict.aggregate()`** + **기존 `verdict.EXIT_CODE` 그대로** 사용:
  | verdict | exit |
  |---|---|
  | pass | 0 |
  | block | 1 |
  | approval | 2 |
  | analysis_error | 3 |
  - 필수 gate 미실행 → `overall_verdict=analysis_error` → **exit 3**, `phase_status=incomplete`. (incomplete 전용 코드 신설 안 함.)
- **종료코드는 보조 신호, JSON `gate.verdict`/`overall_verdict`/`phase_status`가 정본.** rollup은 항상 JSON을 읽어 판정.

## 4. 구조화 preflight (실행 전 일괄 입력 검사)

- **신규 `preflight`**: phase 실행 전에 한 번에 검사 → `preflight.json` 저장.
  - ref: base/target/candidate **resolve + object 존재**(blobless: structdiff 대상 blob 접근까지 확인, 없으면 upstream promisor로 확보 지시)
  - 필수 파일: gate별 요구(T41=change-intent, T43=debt-thresholds+conflict-rate, layout/zones/manifests/registry)
  - 선택 입력: conflict-rate 존재 여부 → 없으면 T43 `skipped_missing_input` 예고
  - candidate-lock 정합성(1번) 통과 여부
- 결과: 각 항목 `ok | missing | unreachable`. **blocking 결손이면 phase 실행 거부**(중반 실패 방지).
- **om-temp-1.13.1 전용 change-intent 생성·승인(공유 금지):** kb-openmetadata 파일을 복사·공유하지 않음.
  - 신규 `bootstrap-change-intent --version 1.13.1`: active manifest에서 `allowed=declared_scope` 제안(+ forbidden 기본 `['.github/**','harness/**']`) → **사람 승인 후** `registrations/om-temp-1.13.1/change-intent.yaml`로 기록. 승인 전에는 T41 `analysis_error`(입력 없음) 유지.

## 5. 3단 출력 (한 실행 → 동일 수치)

- **5.1 관리자용 한눈 요약**(기술용어 최소): 종합 상태 + 정상/검토/미실행/차단 수 + 검증 대상 수 + 다음 행동.
- **5.2 실무자용**: gate별 verdict, 실제 사용 base/target/candidate SHA, 영향 BANK-OM ID·경로, 누락 입력·보완법, 재실행 phase·결과 경로.
- **5.3 시스템·감사용 JSON**: 입력 경로+digest, commit/tree SHA, 검사기 버전, 전체 입력/출력/사유, 미실행 gate+누락 입력, run-id·시각, 승인자·시각·근거·승인 대상 digest.
- **불변식:** 세 출력은 **같은 실행에서 생성, 서로 다른 verdict·수량 금지.**

## 6. 사람 승인 = 결과 digest 결속

- 승인은 boolean/문자열이 아니라 **`{result_digest, approver, approved_at, rationale}`** 레코드(기존 `result_io` digest 재사용).
- **입력·결과가 바뀌면 digest 변경 → 기존 승인 자동 무효.** 승인 후 재실행 시 digest 대조로 stale 승인 차단.

## 7. 새 phase 명령 — 입력/산출물

| 명령 | 입력 | 산출물 | 사람? |
|---|---|---|---|
| `candidate-consistency --version` | SHA 출처들 + candidate-lock | consistency.json | 불일치 시 STOP |
| `prep-official --version --target-tag` | upstream tag | official/om-X 준비(commit/tree 검증), prep.json | 태그 없으면 STOP |
| `preflight --version --base --target --candidate [--conflict-rate]` | refs·파일·lock | preflight.json | blocking 결손 시 STOP |
| `premerge-check --version --run-id [--conflict-rate]` | 위 통과 후 | gate별 JSON + rollup 3종 | approval 시 검토 STOP |
| `status --run-id` | evidence | 3단 요약(read-only) | — |
| `approve --run-id --approver --rationale` | run 결과 digest | approval 레코드 | 사람 실행 |

- `risk`는 **`--conflict-rate` optional**로 변경(없으면 T43만 `skipped_missing_input`).

## 8. 변경할 파일 목록 (구현 시)

- `harness/om_workflow.py` — 서브커맨드 추가(candidate-consistency, prep-official, preflight, premerge-check, status, approve, bootstrap-change-intent); `risk --conflict-rate` optional.
- `harness/acgh/` 신규: `preflight.py`, `rollup.py`, `approval.py`. **`candidate_lock.py`는 만들지 않음 — 기존 `acgh/candidate.py`(`CandidateLock`) 재사용.** `verdict.py`는 4종·`EXIT_CODE` 유지, `execution_status`/`phase_status` 표현만 추가(집계 헬퍼).
- `harness/acgh/consistency.py`(또는 candidate.py 확장) — 활성 기준만 대조하는 `candidate-consistency`.
- `harness/registrations/kb-openmetadata/run_upgrade_risk_gates.py`(+루트 shim) — T43 conflict-rate 분리, gate별 execution_status.
- `harness/registrations/om-temp-1.13.1/` 신규: `candidate-lock.yaml`(기술 기준만: commit/tree/repo/digest, CandidateLock 스키마), **별도 `candidate-lock-approval.yaml`**(approver·시각·근거 + `candidate_lock_digest`), `change-intent.yaml`(bootstrap 후 승인).
- `docker/rehearsal/*` — candidate SHA를 하드코딩 대신 candidate-lock 참조.
- CI 워크플로 — phase 명령 호출(로컬=CI 동일 코드경로).
- **금지:** custom branch·vendor merge 관련 파일.

## 9. 결과 예시 (gate 단위)

```json
// pass
{"name":"T93_exact_scope","verdict":"pass","execution_status":"executed","reasons":["declared exact scopes equal observed per-ID history"]}
// approval
{"name":"T42_upgrade_watch","verdict":"approval","execution_status":"executed","reasons":["BANK-OM-004: watched path changed ..."]}
// block
{"name":"T41_sensitive_zones","verdict":"block","execution_status":"executed","reasons":["frozen zone changed without approved intent: conf/openmetadata.yaml"]}
// analysis_error
{"name":"T93_policy_drift","verdict":"analysis_error","execution_status":"executed","reasons":["unclassified new upstream module: <path>"]}
// 입력 부족 (verdict 아님 — execution_status로 표현)
{"name":"T43_debt","verdict":null,"execution_status":"skipped_missing_input","missing":["conflict_rate(approved baseline)"]}
```

phase(실행 전체) 수준 예시 — 필수 gate 미실행 시:
```json
{
  "phase_status": "incomplete",
  "overall_verdict": "analysis_error",   // 새 verdict 아님, exit 3
  "reason": "required gate T43 skipped_missing_input: conflict_rate baseline 미승인",
  "candidate": {"commit_sha":"8ac18ad0…","tree_sha":"e86980f6…"}
}
```

## 10. 관리자용 출력 예시

```text
[종합 결과] 담당자 검토 필요
전체 검사 5개: 정상 3, 검토 필요 1, 미실행 1, 차단 0
✓ candidate 기준       정상 — 승인 SHA(8ac18ad0)와 실행 SHA 일치
✓ 변경 범위 검사        정상 — 111개 중 111개 일치
✓ 공용 코드 정의        정상 — 790개 중 790개 검출
△ 공식 변경 영향        검토 필요 — BANK-OM 7개 중 6개 영향
○ 유지 부담 검사        미실행 — 승인된 conflict-rate 필요
[다음 행동] 영향받은 BANK-OM 6개와 conflict-rate 기준을 확인
```

## 11. 회귀 test 계획 (동작 보존 증명)

- **골든 동등성:** 고정 run에서 `premerge-check`의 gate verdict·reasons·검증대상 수 == 기존 개별(`watch`/`risk` gate) 결과. 하나라도 다르면 실패.
- **execution_status:** conflict-rate 없음 → T43 `skipped_missing_input`, overall ≠ pass.
- **preflight:** change-intent 없음 → 특정 메시지로 STOP; 있음 → 통과.
- **candidate-consistency:** SHA 하나 변조 주입 → STOP + 파일/값 출력; 정합 → pass.
- **종료코드:** verdict별 코드 표 일치; incomplete → 비-0.
- **3단 출력 일관성:** 관리자/실무자/JSON의 verdict·수량 동일.
- **승인 무효화:** 승인 후 입력 변경 → digest 변경 → 기존 승인 거부.

## 12. 사람이 반드시 결정하는 STOP 지점

1. candidate 정본 불일치 해소(어느 SHA를 lock할지)
2. change-intent / conflict-rate **최초 기준** 승인
3. T42·T93 `approval` 검토(§7 영향표)
4. 업무 충돌 해소(same-key JSON·코드) — merge 단계
5. 최종 sign-off(T91)

## 13. 구현 순서 (Codex 순서 채택)

1. candidate 기준 정합성 + 불일치 차단
2. phase preflight + 구조화 오류 JSON
3. gate 독립 실행 + T43 선택 입력 처리(execution_status)
4. 공통 verdict 집계·종료코드·상세 결과
5. 관리자/실무자 요약 생성
6. `prep-official` 자동화
7. run-id·evidence 레이아웃·검토표 자동화
8. 결과 digest 결속 승인 단계
9. (동작+회귀 test 확보 후) kb-openmetadata 러너 제품 중립 리팩터링

> 각 단계는 회귀 test 선작성. **d952a838 기준 T42·구조화 diff는 유지, candidate 사용 T41·T43·T93 exact-scope·watch-suggest는 8ac18ad0 기준 재실행**을 계획에 명시.

## 14. 영향 범위 / 승인 대기

- 이 문서는 설계·영향보고까지. **하네스 코드·custom branch·vendor merge 미실행.**
- 구현 착수는 별도 승인 후. 승인 시 1→2→3 순으로 회귀 test와 함께 진행.
