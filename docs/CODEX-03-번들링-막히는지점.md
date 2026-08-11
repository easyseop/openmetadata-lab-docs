# [Codex 질문] 하네스 명령 번들링 — 요구사항과 막히는 지점

> 대상 하네스(실측): `.../work/review-openmetadata-test`, 브랜치 `codex/om-1.13.1-rehearsal-baseline-20260806`
> 코드 repo: `~/om-work/om-temp-real-1.13.1` (blobless partial clone)
> 아래는 2026-08-07에 **1.13.2 사전검사(T42·T93·T51/T52)를 실제로 손으로 실행하며 부딪힌** 지점들이다. 각 지점을 "어떻게 풀지" Codex에게 묻는다.

## 요구사항
사람 손을 최대한 덜 타게, 하네스 명령을 **phase 단위로 묶고** 싶다. 원칙:
- 실체는 `harness/om_workflow.py` 확장(새 도구 X), 래퍼/skill은 얇게(판정 로직 없음)
- **결정론적** 준비·실행·파싱만 자동화, **사람 판단(분류·승인·업무충돌·sign-off)은 명시 STOP** 유지
- verdict는 JSON `gate.verdict`로 읽음(종료코드 아님), 입력 누락은 fail-closed(지어내지 않음)

참고: 사전검사 1건에 실제로 친 명령이 **8~10개 + 즉석 커스텀 드라이버**였는데, 이 중 **사람 판단이 필요한 건 0개**였다. 아래가 그 자동화를 가로막은 지점이다.

---

## 막히는 지점 (요구사항 : 문제 → Codex 질문)

### 1. `risk`가 게이트를 한 덩어리로 묶고 `--conflict-rate`가 필수
- **현상:** T93/T41/T43/T51/T52를 개별로 못 돌린다. conflict-rate가 없으면(승인된 기준 없음) T43 하나 때문에 나머지 4개까지 실행 불가 → 나는 커스텀 드라이버를 짜서 우회함.
- **근거:** `harness/om_workflow.py` `risk.add_argument("--conflict-rate", required=True)`; `harness/registrations/kb-openmetadata/run_upgrade_risk_gates.py:145` `gates=[t42,t41,t43,t93_policy,t93_scope]`, conflict_rate는 `debt.collect_metrics(... conflict_rate=...)`(T43)에서만 사용.
- **Codex 질문:** conflict-rate를 optional로 바꿔 **없으면 T43만 `not_evaluated`로 자동 스킵**하고 나머지는 실행하도록 해도 되나? 아니면 게이트 선택 플래그(`--gates T93,T41,T51`)가 나은가?

### 2. verdict를 종료코드로 알 수 없음
- **현상:** `watch`/`risk`는 approval/block이어도 정상 실행이면 exit 0. 번들이 자동 판단하려면 매번 evidence JSON을 파싱해야 하는데 표준 rollup이 없다.
- **근거:** 1.13.2 사전검사 가이드 §5 "종료코드만 보지 말고 `gate.verdict`를 읽어라"; 실제 `watch` approval에도 exit 0.
- **Codex 질문:** 여러 evidence JSON을 읽어 **gate별 판정 + overall(REVIEW/BLOCK)** 을 내는 read-only `status <run-id>` 명령을 om_workflow에 추가하는 게 맞나? verdict 우선순위(ANALYSIS_ERROR/BLOCK > APPROVAL > PASS)는 기존 `verdict.aggregate`를 재사용하면 되나?

### 3. 입력 누락을 실행 중반에 발견 (preflight 부재)
- **현상:** `om-temp-1.13.1` 등록에 change-intent 파일이 없어 T41(zones)이 실행 도중 막힘. 사전 입력검사가 없어 phase 중간에 깨진다.
- **근거:** `run_upgrade_risk_gates` 핸들러가 `require_file(registration/"change-intent.yaml")`; 실제 `harness/registrations/om-temp-1.13.1/`에는 change-intent 계열 파일 없음(contracts/registry/manifests/layout/zones/shared-*만 존재).
- **Codex 질문:** phase 실행 전에 필요한 입력(change-intent, conflict-rate, base/target/candidate ref, blob 접근)을 검사해 **없으면 "X 제공하라"는 analysis_error로 즉시 STOP**하는 preflight를 넣어야 하나? 그리고 **om-temp-1.13.1의 change-intent는 어디서 오는 게 정본인가** — 파일 추가? active manifest에서 유도(`allowed_from_active_manifests: true`)? kb-openmetadata의 `change-intent-current.yaml`을 공유?

### 4. git 준비 단계가 수동·분산 + blobless 함정
- **현상:** upstream 등록 → 태그 fetch → SHA/tree 검증 → `official/om-1.13.2` 생성이 별도 명령들. 게다가 blobless clone라 1.13.2 commit이 promisor(fork origin)에 없어 lazy-fetch가 "not our ref"로 실패 → upstream에서 명시 fetch해야 성공.
- **근거:** 가이드 §3~4의 다단계 명령; `git config remote.origin.partialclonefilter=blob:none`; `git show <1.13.2-sha>`가 origin lazy-fetch로 실패 후 `git fetch upstream tag 1.13.2-release`로 해결.
- **Codex 질문:** 이 준비를 idempotent `prep-official <version>` 한 명령으로 묶어도 되나? blobless 환경에서 target commit/tree(및 structdiff용 blob)를 **upstream promisor로 확실히 확보**하는 표준 방법은? (`extensions.partialClone`을 upstream으로? 명시 fetch?)

### 5. 승인된 candidate ref를 자동 확정할 수 없음
- **현상:** `risk --candidate` 가이드 예시명 `codex/om-1.13.1-registration-baseline`이 실제로 없다. 승인된 candidate SHA(`d952a838…`)를 사람이 알려줘야 했다.
- **근거:** OM_CODE_REPO 브랜치엔 `custom/om-1.13.1`, `codex/om-1.13.1-id-series(-upstream)`만 있고 가이드 예시명 없음. 실제 승인 candidate = `codex/om-1.13.1-id-series-upstream@d952a838`(사용자 지정).
- **Codex 질문:** 승인된 candidate(브랜치+40자리 SHA)를 **registry/candidate-lock 같은 정본에 고정**해서 번들이 자동으로 읽게 해야 하나? 지금 정본은 어디인가(candidate-lock 파일이 없어 보임)?

### 6. run-id·evidence 폴더·§7 검토표가 수동
- **현상:** evidence 디렉터리 명명, affected-ID → §7 검토표 렌더가 손작업.
- **Codex 질문:** run-id 자동생성 + phase별 evidence 레이아웃 표준화 + `review-affected <run>`(T42 affected를 표로 렌더하고 **타이핑 승인 전까지 다음 단계 차단**)을 넣는 게 맞나?

### 7. 루트 러너가 제품 등록 폴더에 결합
- **현상:** `harness/run_*.py` 5개가 `registrations/kb-openmetadata/` 구현으로 runpy 위임. 제품 중립 phase 번들을 만들면 구현이 한 등록 폴더에 묶여 재사용이 꼬인다.
- **근거:** `harness/{run_source_candidate_gates,run_source_patch_kills,run_runtime_contracts,run_upgrade_risk_gates,compare_ui_typecheck}.py` = runpy shim; `run_upgrade_watch.py`는 실제 구현.
- **Codex 질문:** phase 번들을 넣기 전에 러너 구현을 제품 중립 위치(`harness/lib/`)로 옮기고 registration은 데이터만 갖게 하는 게 선행돼야 하나, 아니면 om_workflow 확장만으로 충분한가?

### 8. conflict-rate baseline 정책 미정
- **현상:** 승인된 과거 conflict-rate가 없어 T43을 아예 못 돌린다.
- **Codex 질문:** 최초 baseline conflict-rate를 **누가·어떻게 승인**해 정본에 남기나? 그전까지 번들은 T43을 항상 `not_evaluated`로 두면 되나?

### 9. 자동/사람 경계가 코드로 표시돼 있지 않음
- **현상:** 어느 단계가 자동이고 어느 단계가 "타이핑 승인 STOP"인지 산문(가이드)에만 있고 phase 커맨드 수준에서 구분이 없다.
- **Codex 질문:** phase 정의에 `human_gate: true/false`(또는 STOP 지점) 메타를 넣어, 번들이 사람 게이트에서 자동으로 멈추고 승인 토큰을 요구하게 설계하는 게 맞나? 자동화하면 안 되는 게이트 목록(분류·§7·업무충돌·T91 sign-off)을 어디에 정본으로 두나?

---

## 요약 (Codex에게)
"실체 = om_workflow phase 커맨드, 래퍼 = 얇게, verdict = JSON, 입력누락 = fail-closed, 사람게이트 = 명시 STOP" 방향으로 묶고 싶다. **위 9개가 그 번들을 막는 실제 지점**이다. 각 지점의 해법(특히 1·2·3·4가 최우선)과, 번들 도입 전에 선행해야 할 리팩터 순서를 제안해 달라.
