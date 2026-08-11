# SETUP — 툴체인 · 빌드 · 실행

## 1. Docker (Colima)

macOS Apple Silicon 환경. Docker Desktop 대신 **Colima + docker CLI** 사용.

```bash
colima status              # 상태
colima start               # 시작 (로그인 시 자동시작 등록됨: brew services)
```

리소스: **6 CPU / 10GB RAM / 100GB disk** 로 설정됨 (OpenMetadata 풀스택 기동에 필요).
변경하려면:
```bash
colima stop && colima start --cpu 6 --memory 10 --disk 100
```

## 2. 빌드 툴체인 (호스트)

`OM_TEMP/.devcontainer/dev/devcontainer.json` 과 동일 버전으로 Homebrew 설치됨:

| 도구 | 버전 | 용도 |
|---|---|---|
| openjdk@21 | 21.0.12 | Maven 백엔드 빌드 (**필수**) |
| maven | 3.9.16 | 빌드 오케스트레이션 (**필수**) |
| node@22 | 22.23.2 | 호스트 `yarn start` UI 개발 (docker 빌드엔 불필요) |
| python@3.11 | 3.11.15 | ingestion 개발 |

> **Docker 이미지 빌드에는 호스트 Java 21 + Maven만 있으면 됩니다.**
> UI 빌드는 `openmetadata-ui/pom.xml`의 frontend-maven-plugin이 Node 22.17 / Yarn 1.22를
> 빌드 시점에 자동 다운로드해서 처리합니다.

재설치 (필요 시):
```bash
brew install openjdk@21 maven python@3.11 node@22
```

환경변수는 `scripts/env.sh`가 세팅 (JAVA_HOME, PATH, MAVEN_OPTS 등):
```bash
source scripts/env.sh
```

## 3. 빌드 & 실행 흐름

빌드는 `OM_TEMP/docker/run_local_docker.sh`를 그대로 사용하며,
`scripts/build-and-up.sh`가 툴체인 환경을 세팅한 뒤 호출합니다.

내부 동작:
1. `mvn -DskipTests clean package` — 백엔드 + UI 빌드 → `openmetadata-dist/target/openmetadata-*.tar.gz`
2. `docker compose -f docker/development/docker-compose.yml build` — dist 로 이미지 빌드
3. `docker compose ... up -d` — mysql · elasticsearch · migrate · server (+ ingestion) 기동

```bash
scripts/build-and-up.sh            # 풀빌드 + UI + mysql + ingestion
scripts/build-and-up.sh -s         # mvn 빌드 스킵, 기존 이미지로 재기동
scripts/build-and-up.sh -m no-ui   # 백엔드만 (UI 제외)
scripts/build-and-up.sh -d postgresql
scripts/build-and-up.sh -i false   # ingestion(airflow) 제외 → 가벼움
```

## 4. 접속 · 확인

| | URL | 비고 |
|---|---|---|
| UI | http://localhost:8585 | admin@open-metadata.org / admin |
| API | http://localhost:8585/api | REST |
| Health | http://localhost:8586/healthcheck | Dropwizard admin port |
| Elasticsearch | http://localhost:9200 | |
| Airflow(ingestion) | http://localhost:8080 | admin / admin |

```bash
scripts/status.sh          # 컨테이너 + 헬스체크
scripts/logs.sh            # server 로그 tail
scripts/logs.sh elasticsearch
scripts/down.sh            # 중지 (데이터 유지)
scripts/down.sh -v         # 중지 + 데이터 볼륨 삭제
```

## 5. 포트 요약

| 포트 | 서비스 |
|---|---|
| 8585 | OpenMetadata UI/API |
| 8586 | Server admin/health |
| 3306 | MySQL |
| 9200 / 9300 | Elasticsearch |
| 8080 | Airflow (ingestion) |
| 5005 | JVM 디버그 (`-x true` 시) |

## 6. VSCode

루트의 `openmetadata-lab.code-workspace`를 열면 OM_TEMP · openmetadata-test · lab 3개
폴더가 멀티루트로 붙고, Java 21 런타임 · Maven 경로 · 권장 확장이 자동 설정됩니다.

대안: OM_TEMP를 devcontainer로 열기 — `.devcontainer/dev` (Java21/Node22/Py3.11/Yarn 자동 구성).

## 7. 트러블슈팅

- **`grep`/`rg` 셸 함수 에러** (`claude native binary not installed`): 이 셸 세션 한정 스냅샷 이슈.
  `command grep` / `/usr/bin/grep` 로 우회. Docker/빌드와 무관.
- **메모리 부족으로 컨테이너 OOM**: `colima stop && colima start --memory 12` 로 상향.
- **빌드 느림**: 최초 빌드는 Maven 의존성 + Node/Yarn 다운로드로 30분~1시간+. 이후 캐시됨.
