# Architecture

## 시스템 개요

Dev-Blackbox는 개발 플랫폼(GitHub, Jira 등)에서 활동 데이터를 수집하고,
LLM을 통해 일일 업무 일지를 자동 생성하는 시스템이다.

## 레이어 구조

```
┌───────────────────────────────────────────────────────┐
│                  Controller Layer                     │
│  REST API 엔드포인트, DTO 변환, 예외 핸들러, 보안 설정         │
│  api/ — AuthController, UserController,               │
│         GitHubSecretController, GitHubEventController │
│  admin/ — AdminUserController                         │
│  security_config — OAuth2, JWT 인증/인가                │
└──────────────────────┬────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   Service Layer                     │
│  비즈니스 로직, 트랜잭션 조율                              │
│  UserService, GitHubUserSecretService,              │
│  GitHubEventService, JiraUserService,               │
│  JiraEventService, SummaryService                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 Repository Layer                    │
│  데이터 접근 추상화                                     │
│  UserRepository, GitHubUserSecretRepository,        │
│  GitHubEventRepository, JiraUserRepository,         │
│  JiraEventRepository, PlatformSummaryRepository,    │
│  DailySummaryRepository                             │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               Entity / ORM Layer                    │
│  SQLAlchemy ORM 모델                                 │
│  User, GitHubUserSecret, GitHubEvent,               │
│  JiraUser, JiraEvent, PlatformSummary, DailySummary │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               Infrastructure Layer                  │
│  Database, Redis, HTTP Client, LLM Agent,           │
│  EncryptService, JwtService, PasswordService,       │
│  BackgroundScheduler                                │
└─────────────────────────────────────────────────────┘
```

## 디렉토리 상세

### `controller/`

- FastAPI Router 기반 엔드포인트 정의
- `api/` — 사용자 API 엔드포인트 (`/api/v1/*`, 인증 필요)
    - `dto/` — API Request/Response Pydantic 모델
    - `AuthController` — JWT 토큰 발급 (`/api/v1/auth/token`)
    - `UserController` — 내 정보 조회 (`/api/v1/users/me`)
    - `GitHubSecretController`, `GitHubEventController`, `JiraUserController`, `SlackUserController`, `WorkLogController`
- `admin/` — 관리자 API 엔드포인트 (`/admin-api/v1/*`, 관리자 권한 필요)
    - `dto/` — Admin Request/Response Pydantic 모델
    - `AdminUserController` — 사용자 CRUD (관리자 전용)
- `security_config.py` — OAuth2 보안 설정
    - `AuthToken` — Bearer 토큰 의존성
    - `CurrentUser` — 인증된 사용자 의존성 (JWT 디코딩 → DB 조회)
    - `CurrentAdminUser` — 관리자 권한 의존성 (`is_admin` 검증)
- `exception_handler.py` — 전역 예외 핸들러 (`register_exception_handlers()`)
- 라우터는 `main.py`에서 `app.include_router()`로 등록
- 상세: [API 문서](API.md)

### `service/`

- 비즈니스 로직 캡슐화
- Repository를 호출하여 데이터 조작
- `get_db_session()` context manager로 자동 트랜잭션 관리
- `model/` — 서비스 계층 Pydantic 모델 (`UserWithRelated` 등)
- `UserService` — 사용자 CRUD, 인증 (비밀번호 검증), JWT 토큰 생성
- `GitHubUserSecretService` — GitHub 인증 정보 관리 (암호화/복호화 포함)
- `GitHubEventService` — GitHub 이벤트 조회 및 수집 (이벤트/커밋 수집, DB 저장 포함)
- `JiraUserService` — Jira 사용자 동기화 및 User 할당
- `JiraEventService` — Jira 이슈 수집 및 저장 (JQL 기반 검색, changelog 필터링)
- `SummaryService` — 플랫폼별/통합 일일 LLM 요약 저장 및 조회

### `storage/rds/`

- `entity/` — SQLAlchemy ORM 모델 (Base, SoftDeleteMixin)
- `repository/` — 데이터 접근 패턴
- 상세: [데이터베이스 문서](DATABASE.md)

### `client/`

- 외부 API 통신 담당
- `model/` — API 응답 Pydantic 모델
- `GithubClient` — GitHub API v3 연동 (`httpx` 비동기 HTTP)
    - `fetch_events_by_date()` — 특정 날짜의 이벤트 수집 (페이지네이션, 최대 10페이지)
    - `fetch_commit()` — 커밋 상세 조회 (stats, files, patch 포함)
- `JiraClient` — Jira REST API 연동 (`jira` 라이브러리, Basic Auth)
    - `fetch_assignable_users()` — 프로젝트 할당 가능 사용자 조회
    - `fetch_search_issues()` — JQL 기반 이슈 검색
    - `fetch_issue()` — 특정 이슈 상세 조회

### `agent/`

- LLM 연동 계층
- Ollama + LlamaIndex 기반
- `LLMAgent` — `query(prompt, **kwargs)` 메서드로 LLM 호출
- `model/` — LLM 설정 모델 (OllamaConfig, SummaryOllamaConfig), 프롬프트 템플릿
    - `GITHUB_COMMIT_SUMMARY_PROMPT` — GitHub 커밋 기반 업무 일지 요약 프롬프트
    - `JIRA_ISSUE_SUMMARY_PROMPT` — Jira 이슈 기반 업무 일지 요약 프롬프트

### `task/`

- APScheduler 기반 백그라운드 스케줄링 태스크
- 모든 태스크는 분산 락(`distributed_lock`)으로 중복 실행 방지
- `health_check_task()` — 헬스 체크 (매 1분)
- `collect_platform_task()` — 플랫폼별 데이터 수집 + LLM 요약 (매일 00:00 UTC)
- `sync_jira_users_task()` — Jira 사용자 동기화 (매일 15:00 UTC)

### `core/`

- `config.py` — Pydantic Settings 기반 환경 설정 (싱글턴 `@lru_cache`)
- `database.py` — SQLAlchemy Engine, Session 설정
- `encrypt.py` — AES-256-GCM 암호화 서비스 (HKDF-SHA256 키 파생)
- `jwt_handler.py` — JWT 토큰 생성/검증 (`JwtService`, HS256, `@lru_cache` 싱글턴)
- `password.py` — 비밀번호 해싱/검증 (`PasswordService`, Argon2 기반 pwdlib, `@lru_cache` 싱글턴)
- `exception.py` — 커스텀 예외 계층 구조
- `enum.py` — PlatformEnum (GITHUB, JIRA, CONFLUENCE, SLACK)
- `types.py` — 커스텀 Pydantic 타입 (NotBlankStr)
- `cache.py` — Redis 클라이언트 관리 (`get_redis_client()`, `@lru_cache`)
- `background_scheduler.py` — APScheduler `BackgroundScheduler` 설정 및 태스크 등록
- 상세: [인프라 문서](INFRASTRUCTURE.md)

### `util/`

- `datetime_util.py` — ISO 형식 날짜 변환(`get_date_from_iso_format`), 어제 날짜 조회(`get_yesterday`)
- `distributed_lock.py` — Redis 기반 분산 락 (`distributed_lock()` context manager)

## 데이터 수집 파이프라인

### GitHub 수집 + LLM 요약

```
[APScheduler] collect_platform_task() (매일 00:00 UTC)
       │
       ├── distributed_lock 획득
       │
       ├── UserService.get_users() → UserWithRelated 변환
       │
       ▼  (사용자별 반복)
  GitHubEventService.save_github_events()
       │
       ├── 기존 이벤트 삭제 (target_date 기준)
       │
       ├── EncryptService.decrypt()   ← PAT 복호화
       │
       ├── GithubClient.fetch_events_by_date()   ← GitHub API v3
       │       │
       │       ▼
       │   이벤트 필터링 (PushEvent)
       │       │
       │       ▼
       ├── GithubClient.fetch_commit()            ← 커밋 상세 조회
       │
       ▼
  GitHubEventRepository.save_all()               ← DB 저장
       │
       ▼
  LLMAgent.query()                               ← Ollama 요약
       │
       ▼
  SummaryService.save_platform_summary()         ← 요약 DB 저장
```

### Jira 수집 + LLM 요약

```
[APScheduler] collect_platform_task() (매일 00:00 UTC)
       │
       ├── distributed_lock 획득
       │
       ├── UserService.get_users() → UserWithRelated 변환
       │
       ▼  (사용자별 반복, jira_user 할당된 경우만)
  JiraEventService.save_jira_events()
       │
       ├── 기존 이벤트 삭제 (target_date 기준, 멱등성 보장)
       │
       ├── IssueJQL 빌드 (프로젝트, 담당자, 상태, 날짜 범위)
       │
       ├── JiraClient.fetch_search_issues()      ← Jira REST API
       │       │
       │       ▼
       │   JiraIssueModel.from_raw() 변환
       │       │
       │       ▼
       ├── changelog를 target_date + 타임존 기준 필터링
       │
       ▼
  JiraEventRepository.save_all()                 ← DB 저장
       │
       ▼
  JiraIssueModel.issue_detail_text()             ← LLM 입력 텍스트 생성
       │
       ▼
  LLMAgent.query(JIRA_ISSUE_SUMMARY_PROMPT)      ← Ollama 요약
       │
       ▼
  SummaryService.save_platform_summary()         ← 요약 DB 저장 (PlatformEnum.JIRA)
```

### Jira 사용자 동기화

```
[APScheduler] sync_jira_users_task() (매일 15:00 UTC)
       │
       ├── distributed_lock 획득
       │
       ▼
  JiraUserService.sync_jira_users()
       │
       ├── JiraClient.fetch_assignable_users()    ← Jira API
       │
       ├── 기존 account_id 비교 → 신규 사용자만 필터링
       │
       ▼
  JiraUserRepository.save_all()                  ← DB 저장
```

## 인증 플로우

```
POST /api/v1/auth/token  (email + password)
       │
       ▼
  UserService.authenticate()                 ← 비밀번호 검증 (Argon2)
       │
       ▼
  UserService.create_jwt_token()             ← JWT 생성 (HS256)
       │
       ▼
  TokenResponseDto                           ← {access_token, token_type: "bearer"}
```

## 이벤트 조회 플로우

```
GET /api/v1/github-events  (Authorization: Bearer <token>)
       │
       ▼
  security_config.get_current_user()         ← JWT 검증 + 사용자 조회
       │
       ▼
  GitHubEventService.get_events_by_user_id()
       │
       ▼
  GitHubEventRepository.find_all_by_user_id()
       │
       ▼
  list[GitHubEventResponseDto]               ← 응답
```
