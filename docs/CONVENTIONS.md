# Conventions

프로젝트 코드 컨벤션 및 레이어별 패턴.

> 아키텍처 개요는 [ARCHITECTURE.md](ARCHITECTURE.md) 참고.

## Entity 생성

- 팩토리 메서드 `Entity.create(...)` 패턴 사용
- `Base` 상속 (created_at, updated_at 자동 관리)
- 삭제 필요 시 `SoftDeleteMixin` 추가 (is_deleted, deleted_at)

## DB 세션

- **Controller 레벨**: `get_db()` — 수동 commit/rollback
- **Service 레벨**: `get_db_session()` — 자동 commit/rollback (context manager)

## 레이어 의존 방향

Controller(DTO) → Service(Model/Entity) → Repository(Entity). 역방향 참조 금지.

## DTO

- API DTO는 `controller/api/dto/`에, Admin DTO는 `controller/admin/dto/`에 정의
- Pydantic v2 BaseModel 사용
- DTO는 같은 레이어의 다른 DTO만 참조 가능. `service/model/`을 import하지 말 것
- DTO에 `from_entity()` / `from_model()` 팩토리 메서드로 변환 로직을 캡슐화. Controller에서 직접 필드를 매핑하지 말 것
- Query Parameter는 `controller/api/param/`에 Pydantic 모델로 정의

## Service Command / Query

- **Command** (`service/command/`): 쓰기 작업의 입력 데이터. Service 메서드가 Controller의 DTO에 직접 의존하지 않도록 중간 객체 역할
- **Query** (`service/query/`): 조회 조건 객체. 기존 `storage/rds/condition/`을 대체하여 Service 레이어에서 관리
- Controller에서 DTO → Command/Query 변환 후 Service에 전달

## Service Model

- `service/model/`에 Pydantic 모델로 정의. `from_entity()` 팩토리 메서드 사용
- **실질적 변환 로직이 있을 때만 사용** (암호화/복호화, 관계 엔티티 조합 등)
- 필드 단순 복사만 하는 경우 Service Model을 만들지 말 것 — Entity를 직접 반환
- Service Model은 Entity, 다른 Service Model만 참조 가능. `controller/`의 DTO를 import하지 말 것

## Task Context

- `task/context/`에 태스크 실행에 필요한 컨텍스트 모델 정의 (e.g., `UserContext`)
- DB 세션 밖에서 안전하게 사용할 수 있도록 Entity에서 필요한 필드만 추출
- `from_entity()` 팩토리 메서드로 Entity → Context 변환

## 외부 클라이언트

- `client/` 디렉토리에 클라이언트 클래스 + `client/model/`에 Pydantic 모델
- `GithubClient` — `httpx` 동기 HTTP, `create()` 팩토리 메서드
- `JiraClient` — `jira` 라이브러리 (Basic Auth), `create()` 팩토리 메서드, `get_jira_client()` `@lru_cache` 팩토리
- `SlackClient` — `slack_sdk` 라이브러리, `create()` 팩토리 메서드, `get_slack_client()` `@lru_cache` 팩토리

## 인증/인가

- JWT Bearer Token 기반 인증 (OAuth2PasswordBearer)
- `AuthenticatedUser` (`controller/config/model/`) — 인증된 사용자 정보 모델. `from_entity()` 팩토리 메서드 사용
- `CurrentUser` — 인증된 사용자 의존성 (API 엔드포인트용)
- `CurrentAdminUser` — 관리자 권한 의존성 (Admin 엔드포인트용)
- 비밀번호는 `PasswordService` (Argon2)로 해싱 후 DB 저장

## 예외 처리

- `ServiceException` → `EntityNotFoundException` → 구체 예외 (e.g., `UserNotFoundException`, `JiraSecretNotFoundException`)
- `ServiceException` → `IdempotentRequestException` → `ConflictRequestException`(409), `CompletedRequestException`(422)
- `ServiceException` → `JiraUserSecretMismatchException`, `JiraUserNotAssignedException`, `JiraUserProjectNotAssignedException`
- `ServiceException` → `SlackUserSecretMismatchException`, `SlackUserNotAssignedException`, `SlackClientException`, `NoSlackChannelsFound`
- `controller/config/exception_handler.py`에서 FastAPI 핸들러 등록

## 환경 변수

- `.env` 파일 (Pydantic Settings, 구분자: `__`)
- 민감 정보는 `.env`에만 보관, `.env.template` 참고
