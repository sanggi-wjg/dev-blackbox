# Architecture

## 시스템 개요

Dev-Blackbox는 개발 플랫폼(GitHub, Jira, Slack, Wakatime)에서 활동 데이터를 수집하고,
LLM을 통해 일일 업무 일지를 자동 생성하는 시스템이다.

## 레이어 구조

```
┌─────────────────────────────────────┐
│         Controller Layer            │
│  REST API 엔드포인트, DTO 변환       │
│  예외 핸들러 등록                     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          Service Layer              │
│  비즈니스 로직, 트랜잭션 조율         │
│  UserService, GitHubCollectService  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Repository Layer             │
│  데이터 접근 추상화                   │
│  UserRepository                     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Entity / ORM Layer           │
│  SQLAlchemy ORM 모델                │
│  Base, SoftDeleteMixin              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Infrastructure Layer          │
│  Database, HTTP Client, LLM Agent   │
└─────────────────────────────────────┘
```

## 디렉토리 상세

### `controller/`

- FastAPI Router 기반 엔드포인트 정의
- `dto/` — Request/Response Pydantic 모델
- `exception_handler.py` — 전역 예외 핸들러 (`register_exception_handlers()`)
- 라우터는 `main.py`에서 `app.include_router()`로 등록

### `service/`

- 비즈니스 로직 캡슐화
- Repository를 호출하여 데이터 조작
- `get_db_session()` context manager로 자동 트랜잭션 관리

### `storage/rds/`

- `entity/` — SQLAlchemy ORM 모델
    - `Base`: created_at, updated_at 자동 관리 (DeclarativeBase)
    - `SoftDeleteMixin`: 논리 삭제 (is_deleted, deleted_at)
    - 각 Entity는 `create()` 팩토리 메서드 제공
- `repository/` — 데이터 접근 패턴
    - `save()`, `find_by_id()`, `find_all()` 등

### `client/`

- 외부 API 통신 담당
- `httpx` 비동기 HTTP 클라이언트
- `model/` — API 응답 Pydantic 모델
- `create()` 팩토리 메서드로 인스턴스 생성

### `agent/`

- LLM 연동 계층
- Ollama + LlamaIndex 기반
- `model/` — LLM 설정 모델 (OllamaConfig), 프롬프트 템플릿

### `task/`

- FastAPI `BackgroundTasks` 기반 비동기 작업
- `POST /collect/{platform}` 엔드포인트에서 호출

### `core/`

- `config.py` — Pydantic Settings 기반 환경 설정 (싱글턴 `@lru_cache`)
- `database.py` — SQLAlchemy Engine, Session 설정
- `exception.py` — 커스텀 예외 계층 구조
- `enum.py` — PlatformEnum 등 열거형

## 데이터 수집 파이프라인

```
POST /collect/github
       │
       ▼
  BackgroundTasks
       │
       ▼
  collect_by_platform_task()
       │
       ▼
  GitHubCollectService
       │
       ├── GithubClient.fetch_events_by_date()   ← GitHub API v3
       │       │
       │       ▼
       │   이벤트 필터링 (PushEvent, PullRequestEvent)
       │       │
       │       ▼
       ├── GithubClient.fetch_commit()            ← 커밋 상세 조회
       │
       ▼
  LLMAgent.chat()                                 ← Ollama 요약
       │
       ▼
  일일 업무 일지 생성
```

## DB 세션 관리

두 가지 세션 관리 방식을 목적에 따라 분리:

### `get_db()` — FastAPI 의존성 주입용

```python
# Controller에서 Depends()로 주입
# 수동 commit/rollback 필요
@router.post("/users")
async def create_user(db: Session = Depends(get_db)):
    ...
    db.commit()
```

### `get_db_session()` — Service 로직용

```python
# Context manager로 자동 트랜잭션 관리
# 성공 시 commit, 예외 시 rollback
with get_db_session() as db:
    repo.save(entity)
```

## 예외 계층

```
ServiceException (500)
└── EntityNotFoundException (404)
    ├── UserByIdNotFoundException
    └── UserByNameNotFoundException
```

- `exception_handler.py`에서 FastAPI에 핸들러 등록
- 각 예외는 적절한 HTTP 상태 코드로 변환

## 환경 설정

Pydantic Settings 기반, `.env` 파일에서 로드.
중첩 구분자는 `__` (이중 밑줄).

```
TIMEZONE=Asia/Seoul

DATABASE__HOST=localhost
DATABASE__PORT=7400
DATABASE__DATABASE=dev_blackbox
DATABASE__USER=blackbox
DATABASE__PASSWORD=passw0rd
DATABASE__POOL_SIZE=5
DATABASE__MAX_OVERFLOW=10

GITHUB__ENABLED=true
GITHUB__PERSONAL_ACCESS_TOKEN=ghp_xxxx
GITHUB__USERNAME=username
```

설정 클래스 계층:

- `Settings` — 최상위 설정 (싱글턴)
    - `PostgresDatabaseSecrets` — DB 연결 정보 + 풀 설정
    - `GithubSecrets` — GitHub 인증 정보 (enabled 시 필수값 검증)

## 인프라

### PostgreSQL

- Docker: `pgvector/pgvector:pg17` (port 7400)
- 초기화: `docker/postgres/init.sql`
- pgvector 확장 활성화 (임베딩 저장 대비)

### Ollama (LLM)

- 로컬 서버: `http://localhost:11434`
- 요약 전용 설정: temperature 0.1, context_window 64K
