# OpenMetadata Lab

OpenMetadata **1.13.1** 커스터마이징 버전업 검증용 로컬 환경.

공식 버전이 올라가도 행내 커스터마이징(`BANK-OM-xxx`)이 **누락 없이 살아있는지**,
버전업이 **영향 없이 되는지**를 서버를 실제로 띄우고 검사기로 확인하기 위한 워크스페이스.

## 📌 전략 문서·발표 자료 (이 저장소 포함)
- **이어받기 핸드오프(작업 히스토리)**: [docs/HISTORY-2026-08-10.md](docs/HISTORY-2026-08-10.md) ← 다른 컴퓨터는 이거부터
- **검사기 능력·한계 정본**: [docs/CODEX-05-검사기-한계-정직분석-및-LLM검증.md](docs/CODEX-05-검사기-한계-정직분석-및-LLM검증.md)
- **전략 발표덱**: `docs/CODEX-05-전략발표.html` · `.pptx` · `_gen.py`(pptx 생성기)

## 폴더 구조

```
openmetadata-lab/
├── README.md                     ← 이 문서
├── openmetadata-lab.code-workspace  ← VSCode 멀티루트 워크스페이스
├── docs/
│   └── SETUP.md                  ← 툴체인 · 빌드 · 실행 상세 가이드
├── scripts/
│   ├── env.sh                    ← 툴체인 환경변수 (Java21/Maven/Node22/Py3.11)
│   ├── build-and-up.sh           ← 소스 빌드 + 스택 기동
│   ├── down.sh                   ← 스택 중지
│   ├── status.sh                 ← 상태 · 헬스체크
│   └── logs.sh                   ← 서비스 로그 tail
├── logs/                         ← 빌드 로그 (gitignored)
└── repos/                        ← 소스 (각자 독립 git 클론, gitignored)
    ├── OM_TEMP/                  ← 제품 소스 (branch: custom/om-1.13.1)
    └── openmetadata-test/        ← 버전업 생존 검사기 하네스
```

## 두 레포의 역할

| 레포 | 역할 | 현재 브랜치 |
|---|---|---|
| **OM_TEMP** | OpenMetadata 전체 소스 포크. 커스텀 코드 포함. 실제 빌드·기동 대상 | `custom/om-1.13.1` |
| **openmetadata-test** | 버전업 시 커스터마이징 생존을 검증하는 거버넌스/검사기 | `main` |

OM_TEMP 관련 브랜치:
- `custom/om-1.13.1` — **커스텀 코드가 반영된 1.13.1** (기동 대상)
- `official/om-1.13.1` — 공식 1.13.1 스냅샷 (비교 기준)
- `custom/om-1.13.0`, `patch/om-1.13.0` — 이전 1.13.0 계열

## 빠른 시작

> 사전: Docker(Colima) 실행 중이어야 함 — `colima start` (자동시작 설정됨).
> 최초 1회 툴체인 설치는 `docs/SETUP.md` 참고.

```bash
cd ~/openmetadata-lab

# 1) 소스 빌드 + 전체 스택 기동 (최초: mvn 빌드 30분~1시간+)
scripts/build-and-up.sh

# 2) 상태 확인
scripts/status.sh

# 3) 접속
#   UI : http://localhost:8585   (admin@open-metadata.org / admin)
#   API: http://localhost:8585/api

# 코드만 바꾸고 다시 빌드/기동
scripts/build-and-up.sh            # 다시 빌드
scripts/build-and-up.sh -s         # 빌드 건너뛰고 기존 이미지로 재기동

# 중지 / 데이터까지 삭제
scripts/down.sh
scripts/down.sh -v
```

## 커스텀 코드 (버전업 시 보존 대상)

`custom/om-1.13.1` vs `official/om-1.13.1` 주요 커스텀 기능:
- Data Assertions 페이지 / API (`DataAssertionsPage`, `dataAssertionsAPI`)
- Instance Code 상세 페이지 / API (`InstanceCode*`, `instanceCodeAPI`)
- Query Report 페이지 / API (`QueryReport*`, `queryReportAPI`)
- 관련 util 확장 (`EntityUtils`, `SearchClassBase`, `RouterUtils`, `DatabaseServiceUtils` 등)

전체 diff:
```bash
cd repos/OM_TEMP
git diff --stat origin/official/om-1.13.1..custom/om-1.13.1
```

자세한 내용은 [`docs/SETUP.md`](docs/SETUP.md).
