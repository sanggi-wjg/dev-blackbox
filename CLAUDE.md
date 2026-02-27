## 행동 가이드라인

### 1. 코딩 전에 먼저 생각하기

**추측하지 말 것. 혼란을 감추지 말 것. 트레이드오프를 드러낼 것.**

구현 전:

- 가정을 명시적으로 밝힐 것. 불확실하면 질문할 것.
- 여러 해석이 가능하면 제시할 것 — 조용히 하나만 고르지 말 것.
- 더 단순한 방법이 있으면 말할 것. 필요하면 반박할 것.
- 불분명한 것이 있으면 멈출 것. 무엇이 혼란스러운지 밝히고 질문할 것.

### 2. 단순함 우선

**문제를 해결하는 최소한의 코드. 추측성 코드는 금지.**

- 요청받지 않은 기능은 추가하지 말 것.
- 한 번만 쓰이는 코드에 추상화를 만들지 말 것.
- 요청되지 않은 "유연성"이나 "설정 가능성"은 넣지 말 것.
- 발생할 수 없는 시나리오에 대한 에러 처리를 하지 말 것.
- 200줄로 짰는데 50줄로 가능하다면, 다시 작성할 것. (단, 라인을 줄일 때 가독성과 유지보수성이 떨어진다면 진행하지 말 것)

자문할 것: "시니어 엔지니어가 보면 과하게 복잡하다고 할까?" 그렇다면 단순화할 것.

### 3. 외과적 변경

**필요한 부분만 수정할 것. 자기가 만든 지저분함만 정리할 것.**

기존 코드를 수정할 때:

- 인접한 코드, 주석, 포매팅을 "개선"하지 말 것.
- 망가지지 않은 것을 리팩터링하지 말 것.
- 본인이라면 다르게 하더라도 기존 스타일을 따를 것.
- 관련 없는 죽은 코드를 발견하면 언급은 하되 삭제하지 말 것.

내 변경으로 인해 고아가 된 코드가 있을 때:

- 내 변경으로 사용되지 않게 된 import/변수/함수는 제거할 것.
- 기존에 있던 죽은 코드는 요청받지 않는 한 제거하지 말 것.

검증 기준: 변경된 모든 라인이 사용자의 요청으로 직접 추적 가능해야 한다.

### 4. 목표 지향 실행

**성공 기준을 정의하고, 검증될 때까지 반복할 것.**

작업을 검증 가능한 목표로 변환할 것:

- "유효성 검사 추가" → "잘못된 입력에 대한 테스트를 작성하고, 통과시키기"
- "버그 수정" → "재현하는 테스트를 작성하고, 통과시키기"
- "X 리팩터링" → "리팩터링 전후로 테스트가 통과하는지 확인하기"

여러 단계 작업일 경우 간단한 계획을 밝힐 것:

```
1. [단계] → 검증: [확인 사항]
2. [단계] → 검증: [확인 사항]
3. [단계] → 검증: [확인 사항]
```

---

# Dev-Blackbox

개발자 활동 데이터를 수집하고 LLM으로 일일 업무 일지를 자동 생성하는 시스템.

## Quick Reference

- **언어/런타임**: Python 3.14, Poetry
- **프레임워크**: FastAPI + Uvicorn
- **DB**: PostgreSQL 17 + pgvector (port 7400)
- **Cache**: Redis (port 7410)
- **ORM**: SQLAlchemy (psycopg2-binary)
- **인증**: JWT (PyJWT, HS256) + OAuth2 Bearer Token
- **비밀번호**: pwdlib (Argon2)
- **LLM**: Ollama + LlamaIndex
- **스케줄러**: APScheduler (Redis JobStore)

## Commands

```bash
# 의존성 설치
poetry install

# 서버 실행 (localhost:8000)
python main.py

# DB 실행
docker compose -f docker/docker-compose.yaml up -d

# 테스트
poetry run pytest

# 포맷팅
poetry run black .

# 타입 체크
poetry run pyright
```

## Code Style

- **Formatter**: Black (line-length=100)
- **Type Checker**: Pyright (standard mode)
- **Python Target**: 3.14
- 문자열은 큰따옴표(`"`) 사용, f-string 허용, 작은따옴표(`'`) 금지
- 타입 힌트 필수 (Mapped, Annotated 등 SQLAlchemy/Pydantic 스타일)
- 한국어 주석 사용
- `except A, B:`는 Python 3.14에서 `except (A, B):`와 동일하게 유효한 문법 (PEP 758)

## Architecture

Layered Architecture (Controller → Service → Repository → Entity)

```
main.py                          # FastAPI 앱 진입점
dev_blackbox/
├── controller/
│   ├── api/                     # 사용자 API 엔드포인트 (/api/v1/*, 인증 필요)
│   │   ├── dto/                 # API Request/Response DTO
│   │   └── param/               # Query Parameter 모델 (Pydantic)
│   ├── admin/                   # 관리자 API 엔드포인트 (/admin-api/v1/*, 관리자 권한 필요)
│   │   └── dto/                 # Admin Request/Response DTO
│   └── config/                  # 보안, 예외 핸들러, 인증 모델
│       ├── model/               # AuthenticatedUser (인증된 사용자 모델)
│       ├── security_config.py   # OAuth2 보안 설정 (AuthToken, CurrentUser, CurrentAdminUser)
│       └── exception_handler.py # 전역 예외 핸들러
├── service/                     # 비즈니스 로직
│   ├── command/                 # Command 객체 (쓰기 작업 입력)
│   ├── query/                   # Query 객체 (조회 조건)
│   └── model/                   # Service Model (실질적 변환 로직이 있는 경우만)
├── storage/rds/                 # Repository + Entity (SQLAlchemy)
├── client/                      # 외부 API 클라이언트 (GitHub, Jira, Slack) + Model
├── agent/                       # LLM 에이전트 + Prompt
├── task/                        # APScheduler 백그라운드 태스크
│   └── context/                 # 태스크 실행 컨텍스트 모델 (UserContext)
├── core/                        # 설정, DB, Redis, 캐시(CacheService), 예외, Enum, 스케줄러, JWT, Password
└── util/                        # 분산 락, 날짜 유틸리티, 마스킹, 멱등성 처리
```

## 상세 문서:

- @docs/ARCHITECTURE.md — 시스템 구조, 레이어, 파이프라인
- @docs/API.md — 엔드포인트, DTO, 예외 처리
- @docs/DATABASE.md — Entity, Repository, 세션 관리
- @docs/ERD.md — 도메인별 ERD (Mermaid)
- @docs/PIPELINE.md — 데이터 수집, LLM 요약, 동기화 파이프라인
- @docs/INFRASTRUCTURE.md — Docker, PostgreSQL, Redis, APScheduler, Ollama, 환경 설정
- @docs/TEST.md — 테스트 구성, 작성 가이드, 컨벤션

## Key Conventions

### Entity 생성

- 팩토리 메서드 `Entity.create(...)` 패턴 사용
- `Base` 상속 (created_at, updated_at 자동 관리)
- 삭제 필요 시 `SoftDeleteMixin` 추가 (is_deleted, deleted_at)

### DB 세션

- **Controller 레벨**: `get_db()` — 수동 commit/rollback
- **Service 레벨**: `get_db_session()` — 자동 commit/rollback (context manager)

### 레이어 의존 방향

Controller(DTO) → Service(Model/Entity) → Repository(Entity). 역방향 참조 금지.

### DTO

- API DTO는 `controller/api/dto/`에, Admin DTO는 `controller/admin/dto/`에 정의
- Pydantic v2 BaseModel 사용
- DTO는 같은 레이어의 다른 DTO만 참조 가능. `service/model/`을 import하지 말 것
- DTO에 `from_entity()` / `from_model()` 팩토리 메서드로 변환 로직을 캡슐화. Controller에서 직접 필드를 매핑하지 말 것
- Query Parameter는 `controller/api/param/`에 Pydantic 모델로 정의

### Service Command / Query

- **Command** (`service/command/`): 쓰기 작업의 입력 데이터. Service 메서드가 Controller의 DTO에 직접 의존하지 않도록 중간 객체 역할
- **Query** (`service/query/`): 조회 조건 객체. 기존 `storage/rds/condition/`을 대체하여 Service 레이어에서 관리
- Controller에서 DTO → Command/Query 변환 후 Service에 전달

### Service Model

- `service/model/`에 Pydantic 모델로 정의. `from_entity()` 팩토리 메서드 사용
- **실질적 변환 로직이 있을 때만 사용** (암호화/복호화, 관계 엔티티 조합 등)
- 필드 단순 복사만 하는 경우 Service Model을 만들지 말 것 — Entity를 직접 반환
- Service Model은 Entity, 다른 Service Model만 참조 가능. `controller/`의 DTO를 import하지 말 것

### Task Context

- `task/context/`에 태스크 실행에 필요한 컨텍스트 모델 정의 (e.g., `UserContext`)
- DB 세션 밖에서 안전하게 사용할 수 있도록 Entity에서 필요한 필드만 추출
- `from_entity()` 팩토리 메서드로 Entity → Context 변환

### 외부 클라이언트

- `client/` 디렉토리에 클라이언트 클래스 + `client/model/`에 Pydantic 모델
- `GithubClient` — `httpx` 동기 HTTP, `create()` 팩토리 메서드
- `JiraClient` — `jira` 라이브러리 (Basic Auth), `create()` 팩토리 메서드, `get_jira_client()` `@lru_cache` 팩토리
- `SlackClient` — `slack_sdk` 라이브러리, `create()` 팩토리 메서드, `get_slack_client()` `@lru_cache` 팩토리

### 인증/인가

- JWT Bearer Token 기반 인증 (OAuth2PasswordBearer)
- `AuthenticatedUser` (`controller/config/model/`) — 인증된 사용자 정보 모델. `from_entity()` 팩토리 메서드 사용
- `CurrentUser` — 인증된 사용자 의존성 (API 엔드포인트용)
- `CurrentAdminUser` — 관리자 권한 의존성 (Admin 엔드포인트용)
- 비밀번호는 `PasswordService` (Argon2)로 해싱 후 DB 저장

### 예외 처리

- `ServiceException` → `EntityNotFoundException` → 구체 예외 (e.g., `UserNotFoundException`, `JiraSecretNotFoundException`)
- `ServiceException` → `IdempotentRequestException` → `ConflictRequestException`(409), `CompletedRequestException`(422)
- `ServiceException` → `JiraUserSecretMismatchException`, `JiraUserNotAssignedException`, `JiraUserProjectNotAssignedException`
- `ServiceException` → `SlackUserSecretMismatchException`, `SlackUserNotAssignedException`, `SlackClientException`, `NoSlackChannelsFound`
- `controller/config/exception_handler.py`에서 FastAPI 핸들러 등록

### 환경 변수

- `.env` 파일 (Pydantic Settings, 구분자: `__`)
- 민감 정보는 `.env`에만 보관, `.env.template` 참고

## Gotchas

- **비밀번호 해싱 필수**: 사용자 비밀번호는 반드시 `PasswordService.hash_password()`로 해싱 후 DB 저장. `User.create()`는 `hashed_password`를 받음
- **PAT 암호화 필수**: GitHub Personal Access Token은 반드시 `EncryptService`로 암호화 후 DB 저장. 평문 저장 금지
- **타임존 검증**: 사용자 timezone 값은 `ZoneInfo`로 검증 필수 — 잘못된 값 입력 시 런타임 에러 발생
- **REPEATABLE READ**: DB 격리 수준이 `REPEATABLE READ`이므로 동일 트랜잭션 내에서 다른 트랜잭션의 커밋을 볼 수 없음
- **SoftDelete 주의**: `find_by_id()` 등 Repository 조회 메서드는 `is_deleted=False` 조건을 포함해야 함
- **날짜 기본값**: `target_date`가 null이면 유저 타임존 기준 어제 날짜로 자동 설정
- **분산 락**: 백그라운드 태스크는 `distributed_lock()`으로 중복 실행 방지. Redis 불가용 시 락 없이 진행 (graceful degradation)
- **JiraUser 할당**: `jira_user.user_id`와 `project`는 NULLABLE — Jira에서 동기화된 사용자는 `assign_user_and_project()`로 User와 프로젝트를 수동 할당해야 함. 미할당 시 Jira 데이터 수집이 건너뛰어짐
- **SlackUser 할당**: `slack_user.user_id`는 NULLABLE — Slack에서 동기화된 사용자는 `assign_user()`로 User를 수동 할당해야 함. 미할당 시 Slack 데이터 수집이 건너뛰어짐
- **인증 정보 암호화**: JiraSecret의 `username`/`api_token`, SlackSecret의 `bot_token`은 `EncryptService`로 암호화 후 DB 저장
