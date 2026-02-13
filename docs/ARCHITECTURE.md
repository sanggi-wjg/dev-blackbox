# Architecture

## 시스템 개요

Dev-Blackbox는 개발 플랫폼(GitHub 등)에서 활동 데이터를 수집하고,
LLM을 통해 일일 업무 일지를 자동 생성하는 시스템이다.

## 레이어 구조

```
┌─────────────────────────────────────────────────────┐
│                  Controller Layer                    │
│  REST API 엔드포인트, DTO 변환, 예외 핸들러 등록       │
│  UserController, GitHubSecretController,             │
│  GitHubCollectController, GitHubEventController      │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   Service Layer                      │
│  비즈니스 로직, 트랜잭션 조율                          │
│  UserService, GitHubUserSecretService,               │
│  GitHubCollectService, GitHubEventService            │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 Repository Layer                     │
│  데이터 접근 추상화                                    │
│  UserRepository, GitHubUserSecretRepository,         │
│  GitHubEventRepository                               │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               Entity / ORM Layer                     │
│  SQLAlchemy ORM 모델                                 │
│  User, GitHubUserSecret, GitHubEvent                 │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               Infrastructure Layer                   │
│  Database, HTTP Client, LLM Agent, EncryptService    │
└─────────────────────────────────────────────────────┘
```

## 디렉토리 상세

### `controller/`

- FastAPI Router 기반 엔드포인트 정의
- `dto/` — Request/Response Pydantic 모델
- `exception_handler.py` — 전역 예외 핸들러 (`register_exception_handlers()`)
- 라우터는 `main.py`에서 `app.include_router()`로 등록
- 상세: [API 문서](API.md)

### `service/`

- 비즈니스 로직 캡슐화
- Repository를 호출하여 데이터 조작
- `get_db_session()` context manager로 자동 트랜잭션 관리
- `UserService` — 사용자 CRUD
- `GitHubUserSecretService` — GitHub 인증 정보 관리 (암호화/복호화 포함)
- `GitHubCollectService` — GitHub 이벤트/커밋 수집 및 DB 저장
- `GitHubEventService` — GitHub 이벤트 조회

### `storage/rds/`

- `entity/` — SQLAlchemy ORM 모델 (Base, SoftDeleteMixin)
- `repository/` — 데이터 접근 패턴
- 상세: [데이터베이스 문서](DATABASE.md)

### `client/`

- 외부 API 통신 담당
- `httpx` 비동기 HTTP 클라이언트
- `model/` — API 응답 Pydantic 모델
- `create()` 팩토리 메서드로 인스턴스 생성
- `GithubClient` — GitHub API v3 연동
    - `fetch_events_by_date()` — 특정 날짜의 이벤트 수집 (페이지네이션, 최대 10페이지)
    - `fetch_commit()` — 커밋 상세 조회 (stats, files, patch 포함)

### `agent/`

- LLM 연동 계층
- Ollama + LlamaIndex 기반
- `LLMAgent` — `query(prompt, **kwargs)` 메서드로 LLM 호출
- `model/` — LLM 설정 모델 (OllamaConfig, SummaryOllamaConfig), 프롬프트 템플릿
    - `GITHUB_COMMIT_SUMMARY_PROMPT` — GitHub 커밋 기반 업무 일지 요약 프롬프트

### `task/`

- FastAPI `BackgroundTasks` 기반 비동기 작업
- `collect_by_platform_task()` — 플랫폼별 데이터 수집 + LLM 요약 태스크

### `core/`

- `config.py` — Pydantic Settings 기반 환경 설정 (싱글턴 `@lru_cache`)
- `database.py` — SQLAlchemy Engine, Session 설정
- `encrypt.py` — AES-256-GCM 암호화 서비스 (HKDF-SHA256 키 파생)
- `exception.py` — 커스텀 예외 계층 구조
- `enum.py` — PlatformEnum 등 열거형
- `types.py` — 커스텀 Pydantic 타입 (NotBlankStr)
- 상세: [인프라 문서](INFRASTRUCTURE.md)

### `datetime_util.py`

- ISO 형식 날짜 문자열을 특정 타임존의 `date`로 변환하는 유틸리티

## 데이터 수집 파이프라인

```
POST /collect/github/users/{user_id}
       │
       ▼
  GitHubCollectService.collect_github_events()
       │
       ├── 기존 이벤트 삭제 (target_date 기준)
       │
       ├── GitHubUserSecretService.get_decrypted_token_by_secret()
       │       └── EncryptService.decrypt()   ← PAT 복호화
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
  (향후) LLMAgent.query()                        ← Ollama 요약
       │
       ▼
  일일 업무 일지 생성
```

## 이벤트 조회 플로우

```
GET /github-events/users/{user_id}
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
