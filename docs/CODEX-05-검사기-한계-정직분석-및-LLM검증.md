# CODEX-05 · 검사기 능력·한계 정직 분석 및 LLM 작업 검증 설계

> 작성 목적: acgh 검사기와 BANK-OM 관리 전략이 현재 무엇을 검증하고 무엇을 검증하지 못하는지 구분한다. 또한 LLM이 작성한 작업 기록을 독립 증거와 대조하는 운영 방안을 제안한다.
>
> 검토 기준일: 2026-08-10
>
> 상태 표기: **구현·검증 완료**, **구현됐으나 실행 범위 제한**, **설계안(미구현)**을 구분한다.

---

## 0. 결론

현재 검사기는 다음 두 역할에 강하다.

1. 검사 대상 commit·tree·실행 artifact와 검사 결과를 결속한다.
2. 등록자료 누락, Git 계보 불일치, 필수 검사 미실행, 결과 변경을 자동으로 탐지한다.

그러나 정적 검사만으로는 다음 사항을 확정할 수 없다.

- 공식 코드가 이동·개명·리팩터링된 뒤에도 같은 기능이 유지되는지
- 병합된 코드의 업무 동작이 끝까지 정상인지
- 승인서 작성자가 실제 승인 권한자인지
- 등록자료에 처음부터 누락된 커스터마이징이 없는지

따라서 운영 전략은 **LLM 제안 → 결정론적 정적 검사 → 실제 Runtime Contract → 사람 승인** 순서가 적합하다. Runtime Contract는 실행 환경에서 API·화면·업무 데이터의 실제 동작을 확인하는 검사다. LLM의 판단이나 정적 문자열 검사를 최종 기능 판정으로 사용해서는 안 된다.

> 즉, 검사기는 “어떤 코드와 결과를 검사했는지”는 강하게 고정하지만, “기능의 의미가 완전히 유지됐다”는 사실까지 혼자 증명하지는 못합니다.

---

## 1. 현재 실행 현황

### 1.1 OpenMetadata 1.13.1 기준선

- Runtime Contract 9개를 실제 candidate image에서 실행했다.
- 결과는 `pass 9`, `skip 0`, `fail 0`, `error 0`이다.
- 결과에는 제품 candidate commit·tree, 실행 image digest, 검사기 commit, test run digest가 포함돼 있다.
- 별도의 vanilla negative control에서는 InstanceCode·QueryReport·Data Assertions 화면·확장 컬럼 화면 계약이 실패해, 해당 테스트가 커스터마이징 차이를 실제로 감지함을 확인했다.
- Sybase·Tibero는 소스 patch-kill로 별도 검증했다.

따라서 “Runtime Contract를 사실상 한 번도 실행하지 않았다”는 과거 평가는 현재 사실과 다르다.

### 1.2 OpenMetadata 1.13.2 업그레이드 예행연습

현재까지 확인된 사실은 다음과 같다.

| 항목 | 상태 | 해석 |
|---|---|---|
| 1.13.2 custom server image build | 확인 | 실행 가능한 1.13.2 image를 생성했다. |
| 1.13.1 데이터의 1.13.2 마이그레이션 | 확인 | 마이그레이션 프로세스가 종료코드 0으로 완료됐다. |
| 서버 health와 커스텀 API | 확인 | 서버와 InstanceCode·QueryReport API가 응답했다. |
| InstanceCode Runtime Contract | 통과 | CRUD·검색·삭제 동작을 실제 API에서 확인했다. |
| Sybase·Tibero 소스 계약 | 정적 검사 오판 | 기능 코드가 다른 파일로 이동했지만 옛 경로를 검사해 실패했다. Runtime 동작 통과를 의미하지는 않는다. |
| 브라우저 계약 3개 | 환경 미실행 | ARM Mac에서 amd64 Chromium이 종료됐다. 제품 실패가 아니라 실행환경 제약이다. |
| 일부 계약 | 입력자료 미실행 | 필요한 fixture가 없어 실행하지 못했다. 통과나 실패로 계산하지 않는다. |

1.13.2는 **부분 검증 완료** 상태다. 전체 Runtime Contract, 브라우저 검증, 필요한 fixture 보완이 끝나기 전에는 최종 `pass` 또는 배포 가능으로 표시하지 않는다.

> 즉, 1.13.1은 실제 실행 검증이 완료됐고, 1.13.2는 서버·마이그레이션·일부 커스텀 기능까지 확인했지만 전체 기능 검증은 아직 끝나지 않았습니다.

---

## 2. 검사기가 잘하는 것

| ID | 현재 가능한 검증 | 근거 | 정확한 의미 |
|---|---|---|---|
| S1 | Fail-closed | `verdict.py`, `phase.py` | 필수 입력·검사가 없거나 분석이 실패하면 자동 통과시키지 않는다. |
| S2 | 판정 심각도 보존 | `verdict.py:SEVERITY_RANK`, `phase.py:approval_binds` | 사람 승인이 `block`·`analysis_error`를 `pass`로 바꾸지 못한다. |
| S3 | Candidate 결속 | `candidate.py` | commit SHA·tree SHA와, build-artifact 전략에서는 artifact digest까지 검사 입력으로 고정한다. |
| S4 | 결과 변경 탐지 | `verdict.py:canonical_digest`, `phase.py:verify_phase_result` | 저장된 payload가 바뀌면 기존 digest와 불일치함을 탐지한다. 전자서명이나 외부 공증은 아니다. |
| S5 | Git 계보 확인 | `ancestry.py` | 후보가 설정된 upstream base·target commit을 조상으로 포함하는지 확인한다. upstream commit의 공식성 자체는 별도 신뢰 대상이다. |
| S6 | 등록 범위 대조 | Manifest·commit inventory·exact-scope 계열 검사 | 선언된 BANK-OM ID와 관측된 변경 범위의 불일치를 찾는다. 모든 커스터마이징을 코드에서 자동 발견하는 것은 아니다. |
| S7 | 필수 Runtime Contract 집계 | `pytest_runs.py`, `testruns.py` | 필수 selector가 skip·fail·error이면 통과시키지 않는다. 일반 개발 테스트의 선택적 skip까지 모두 막는 규칙은 아니다. |
| S8 | Patch-kill·negative control | `patchkill.py` | 커스터마이징을 제거했을 때 지정 테스트가 실패하는지 확인해, 테스트의 변경 감지력을 검증한다. 기능 전체의 정확성을 단독으로 증명하지는 않는다. |
| S9 | Manifest 입력 경로 제한 | `manifest.schema.json`, `manifest.py`, `contracts.py` | Manifest에 임의 명령 필드를 넣지 못하게 하고, 경로·selector 이탈을 차단한다. 검사기 전체에 임의 코드 실행 위험이 전혀 없다는 의미는 아니다. |

---

## 3. 검사기와 관리 전략의 한계

> 실패 방향: **False pass**는 문제가 있는데 통과하는 경우이고, **False block**은 기능이 정상인데 중단되는 경우다.

| ID | 한계 | 발생 가능한 문제 | 현재 대응 |
|---|---|---|---|
| L1 | 고정 경로·문자열 검사 기준(anchor) | 코드 이동·개명 시 false block 또는 잘못된 생존 판단 | 구조 탐색은 진단자료로 사용하고, 최종 판정은 Runtime Contract로 확인 |
| L2 | 정적 생존 검사는 업무 동작을 보지 않음 | 파일이 공식 코드와 다르기만 해도 기능이 살아 있다고 오인할 수 있음 | 정적 생존 결과를 최종 기능 pass로 사용하지 않음 |
| L3 | Phase 번들에 모든 행동 검사가 연결되지 않음 | Phase 결과만 보고 Runtime 검증까지 끝났다고 오해 | Runtime·patch-kill 결과를 별도 필수 release gate로 집계해야 함 |
| L4 | digest는 서명이 아님 | 파일 쓰기 권한자가 payload와 digest를 함께 다시 만들 수 있음 | 보호된 CI, 불변 artifact 저장소, 서명·attestation(실행 출처를 증명하는 전자 확인서) 필요 |
| L5 | 승인자 신원 검증 없음 | 승인서에 임의 이름을 기록할 수 있음 | 권한자 목록, SSO 또는 서명된 승인 필요 |
| L6 | conflict-rate·일부 기준값을 사람이 입력 | 잘못된 값으로 위험도를 낮출 수 있음 | 실제 반영 없이 수행하는 시험 병합(dry merge) 결과에서 자동 측정하고 값의 생성 출처를 저장 |
| L7 | 등록자료가 검사 시야를 결정 | 처음부터 누락된 ID·경로는 일부 검사에서 보이지 않을 수 있음 | 전체 Git diff·commit trailer·등록집합을 서로 독립적으로 대조 |
| L8 | T60은 테스트 구현 존재 여부 중심 | `def test_x(): pass` 같은 빈 테스트도 존재검사는 통과 가능 | Patch-kill, mutation test, Runtime Contract를 함께 실행 |
| L9 | Runtime coverage는 기능·fixture·환경에 의존 | 미등록 fixture나 브라우저 제약 때문에 핵심 기능이 미실행될 수 있음 | 필수 selector·fixture·지원 platform을 버전별 완료조건으로 고정 |
| L10 | DB 마이그레이션 성공이 업무 데이터 완전성을 보장하지 않음 | 프로세스는 성공했지만 특정 entity·index·업무 값이 손상될 수 있음 | 전후 개수·핵심 필드·검색 index·CRUD를 별도 계약으로 확인 |
| L11 | structdiff·watch-suggest는 진단 중심 | 사람이 결과를 읽지 않으면 구조 변화가 승인 흐름에서 누락될 수 있음 | `review_required` 항목과 담당자 결정을 명시적으로 남김 |
| L12 | T번호와 코드 gate 이름의 매핑이 문서 의존 | 문서와 코드 이름이 달라질 수 있음 | 기계 판정에는 실제 gate name과 verifier version을 기록 |
| L13 | LLM 자기기록은 독립 증거가 아님 | LLM이 작업·검토·결과 기록을 모두 맡으면 하지 않은 작업도 완료처럼 보일 수 있음 | 보호된 외부 실행자가 증거를 생성하고 LLM 기록과 대조 |

### 3.1 리로케이션 한계에 대한 정확한 판단

Sybase·Tibero 사례는 고정 파일 anchor의 실제 false block 사례다. 그러나 “정적 분석은 아무 도움도 되지 않는다”는 결론도 정확하지 않다.

- 트리 전체 심볼 검색, AST, import·호출 관계, rename similarity는 이동 후보를 찾는 데 도움이 된다.
- 이 결과는 **이관 후보 제안 또는 담당자 검토 요청**으로 사용해야 한다.
- 정적 유사도만으로 “기능이 보존됐다”고 자동 통과시키면 안 된다.
- 최종 기능 판정은 이동된 코드가 포함된 candidate에서 Runtime Contract를 실행해 확인한다.

> 즉, 정적 분석은 “어디로 이동했을 가능성이 있는지”는 찾을 수 있지만, “이동 후에도 기능이 정상인지”는 실제 실행으로 확인해야 합니다.

---

## 4. 정확히 가능한 것과 불가능한 것

| 질문 | 검사기 단독 | Runtime 포함 | 사람 판단 필요 |
|---|---:|---:|---:|
| 특정 commit·tree를 검사했는가 | 가능 | 가능 | 불필요 |
| 실행 image가 고정된 artifact인가 | build-artifact lock이 있으면 가능 | 가능 | 불필요 |
| 후보가 설정된 공식 target을 포함하는가 | 가능 | 가능 | 공식 target 선택은 필요 |
| 선언한 변경 경로와 Git 변경이 일치하는가 | 가능 | 가능 | 불일치 해석은 필요 |
| 필수 테스트가 실제 실행됐는가 | 결과 결속 시 가능 | 가능 | 불필요 |
| 기능 제거 시 테스트가 실패하는가 | patch-kill 실행 범위에서 가능 | 가능 | 실험 범위 선택 필요 |
| 코드 이동 후 의미가 보존됐는가 | 불가능 | 행동 계약 범위에서 가능 | 경계·예외 판단 필요 |
| 등록되지 않은 모든 커스터마이징을 자동 발견하는가 | 불가능 | 불가능 | 기준 정의 필요 |
| 승인자가 실제 권한자인가 | 불가능 | 불가능 | 서명·권한 시스템 필요 |
| 전체 배포가 안전한가 | 불가능 | 테스트 범위 내에서만 판단 | 최종 승인 필요 |

---

## 5. 권장 운영 전략

1. **LLM은 제안자**로 사용한다. 변경안, 이동 후보, 충돌 해결안, 필요한 테스트를 제안한다.
2. **Git·정적 검사기는 범위와 정합성**을 확인한다. commit·tree·변경 경로·등록자료를 대조한다.
3. **독립 CI가 build와 Runtime Contract를 실행**한다. LLM이 직접 작성한 로그를 증거로 사용하지 않는다.
4. **리로케이션은 자동 pass가 아니라 검토 요청**으로 처리한다. 새 anchor와 행동 테스트를 함께 갱신한다.
5. **사람은 업무 의미·권한·예외를 승인**한다. 승인 결과는 machine result digest와 결속한다.
6. **미실행은 통과가 아니다.** fixture 부족이나 지원하지 않는 browser 환경은 운영 보고에서 `UNVERIFIED`로 남긴다. 검사 실행 자체가 실패했다면 검사기 판정은 `analysis_error`로 남긴다.
7. **릴리스 요약은 검사 범위를 함께 표시**한다. 예: `필수 Runtime 9/9 통과`, `브라우저 0/3 미실행`.

---

## 6. LLM 작업 기록을 독립 증거와 대조하는 설계

### 6.1 현재 상태

다음 개념은 **설계안이며 아직 완성된 운영 기능이 아니다.**

- KB-MD의 주장과 검사 결과를 자동 연결하는 주장–증거 대조기(reconciler)
- KB-MD 자체를 포함한 claim digest
- 승인자 전자서명·권한 확인
- 보호된 CI·불변 artifact 저장소에 의한 독립 attestation

현재 phase digest는 판정에 사용한 정규화 결과(canonical payload)를 보호한다. 임의의 `KB-CUSTOM-*.md` 파일을 자동으로 digest에 포함하거나 사후 편집을 탐지하지는 않는다.

### 6.2 주장 상태

LLM 기록의 각 항목은 다음 네 상태 중 하나로 관리한다.

| 상태 | 의미 |
|---|---|
| `VERIFIED` | 독립 실행 증거가 주장과 일치한다. |
| `CONTRADICTED` | 독립 증거가 주장을 반박한다. |
| `UNVERIFIED` | 대응 증거가 없거나 검사가 실행되지 않았다. 가짜 작업으로 확정하지 않는다. |
| `REVIEW_REQUIRED` | 기계 증거만으로 의미를 결정할 수 없어 사람이 검토해야 한다. |

### 6.3 Claim–proof 필수 필드

각 LLM 주장에는 다음 정보가 연결돼야 한다.

```yaml
claim_id: KB-TEST-001
statement: InstanceCode CRUD와 검색이 정상이다
candidate_commit: <40자리 SHA>
candidate_tree: <40자리 tree SHA>
artifact_digest: sha256:<실행 image digest>
verifier_commit: <검사기 commit SHA>
test_selector: tests/bank/contracts/test_instance_code.py::test_crud_search_roundtrip
result: pass
evidence_uri: <보호된 CI artifact 위치>
evidence_digest: sha256:<결과 digest>
coverage: CRUD, search, delete
executor: <CI workflow identity>
```

`evidence_digest`는 결과와 입력이 바뀌었는지 탐지한다. 증거 내용이 업무적으로 충분한지, 실행자가 신뢰할 수 있는지는 별도로 검토한다.

### 6.4 LLM 주장별 검증 방법

| LLM 주장 | 독립 증거 | 증거가 없을 때 |
|---|---|---|
| 파일을 추가·변경했다 | candidate와 기준 commit의 실제 Git diff | `UNVERIFIED` |
| 충돌이 0건이다 | 고정된 base·target·candidate로 실행한 dry merge 결과 | `UNVERIFIED` |
| build가 성공했다 | 보호된 CI의 exit code, artifact digest, 로그 | `UNVERIFIED` |
| API·검색·CRUD가 정상이다 | candidate artifact에서 실행한 Runtime Contract | `UNVERIFIED` |
| 화면이 정상이다 | 지원 platform의 브라우저 test 영상·screenshot·JUnit | `UNVERIFIED` |
| 실행 image가 최신이다 | OCI digest·revision label과 candidate lock 비교 | `CONTRADICTED` 또는 `UNVERIFIED` |
| DB 마이그레이션이 안전하다 | 마이그레이션 종료코드와 전후 데이터·index 계약 | `UNVERIFIED` |
| 코드가 새 파일로 이관됐다 | 구조 탐색 결과 + 새 anchor 검토 + Runtime Contract | `REVIEW_REQUIRED` |
| 승인이 완료됐다 | 권한 시스템 또는 서명된 승인과 result digest 결속 | `UNVERIFIED` |

### 6.5 독립성 조건

LLM이 명령 실행, 결과 파일 작성, digest 생성, 승인 기록을 모두 수행하면 독립 검증이 아니다. 최소 조건은 다음과 같다.

- 보호된 CI가 고정 candidate를 직접 checkout한다.
- CI가 실제 명령을 실행하고 결과와 artifact를 생성한다.
- 증거 저장소는 기존 결과 덮어쓰기와 임의 삭제를 제한한다.
- 검사기 commit과 workflow definition을 증거에 포함한다.
- 사람 승인은 권한 시스템 또는 전자서명으로 신원을 확인한다.
- LLM은 증거를 읽어 보고서를 작성할 수 있지만 원본 증거 판정을 변경하지 못한다.

> 즉, digest가 있다는 사실만으로 작업이 진짜라고 확정할 수 없습니다. 신뢰할 수 있는 독립 실행자가 고정된 코드에서 검사를 수행하고 그 결과를 보존해야 합니다.

---

## 7. 유지할 자산과 바꿀 전략

### 유지할 자산

- Fail-closed 판정
- candidate commit·tree·artifact 결속
- Git 계보 및 exact-scope 검사
- 필수 skip을 통과로 계산하지 않는 Runtime 집계
- patch-kill·negative control
- 결과 digest와 승인 digest 결속

### 바꿀 전략

- 고정 경로 문자열 검사를 최종 기능 판정으로 사용하지 않는다.
- 정적 리로케이션 탐색은 `review_required` 진단으로 사용한다.
- Runtime Contract와 fixture를 BANK-OM ID별 필수 release 조건으로 관리한다.
- LLM 작성 MD를 증거로 보지 않고, 독립 증거의 요약·연결 문서로 사용한다.
- 승인자 신원과 증거 보존을 Git 파일만이 아닌 조직 권한 시스템과 연결한다.
- 관리자 보고에는 `검사 대상 수 / 통과 / 미실행 / 실패 / 검토 필요`를 한 줄로 표시한다.

---

## 8. 최종 판단

현재 검사기는 폐기할 대상이 아니다. 다만 역할을 다음과 같이 제한해야 한다.

```text
검사기 단독 결과
= 코드·등록자료·증거의 정합성 판정
≠ 전체 기능 정상 또는 배포 안전 보증
```

릴리스 판정에는 최소한 다음 네 종류의 증거가 필요하다.

1. Git·등록 범위 정합성
2. build artifact와 candidate 결속
3. 핵심 기능 Runtime Contract 및 negative control
4. 권한이 확인된 사람 승인

이 중 하나라도 필수 범위에서 미실행이면 최종 상태는 `pass`가 아니다. 운영 보고에는 설계 상태인 `UNVERIFIED` 또는 `REVIEW_REQUIRED`를 사용하고, 검사기가 필수 검사를 수행하지 못한 경우에는 현재 기계 판정인 `analysis_error` 또는 `block`을 사용한다.

> 즉, 검사기는 계속 사용하되 “검사기 초록 = 기능 전체 정상”으로 해석하지 않아야 합니다. 정적 증거, 실제 실행, 사람 승인을 분리하고 모두 갖춰졌을 때만 릴리스를 승인해야 합니다.
