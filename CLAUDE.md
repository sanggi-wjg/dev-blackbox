# Dev-Blackbox

개발자 활동 데이터를 수집하고 LLM으로 일일 업무 일지를 자동 생성하는 시스템.

## Quick Reference

- **언어/런타임**: Python 3.14, Poetry
- **프레임워크**: FastAPI + Uvicorn (3 workers)
- **DB**: PostgreSQL 17 + pgvector (port 7400)
- **ORM**: SQLAlchemy (psycopg2-binary)
- **LLM**: Ollama + LlamaIndex
- **타임존**: Asia/Seoul (ZoneInfo)

## Commands

```bash
# 의존성 설치
poetry install

# 서버 실행 (localhost:8000)
python main.py

# DB 실행
docker compose -f docker/docker-compose.yaml up -d

# 포맷팅
poetry run black .

# 타입 체크
poetry run pyright
```

## Code Style

- **Formatter**: Black (line-length=100, skip-string-normalization)
- **Type Checker**: Pyright (standard mode)
- **Python Target**: 3.14
- 문자열은 작은따옴표(`'`) 사용 (Black skip-string-normalization)
- 타입 힌트 필수 (Mapped, Annotated 등 SQLAlchemy/Pydantic 스타일)
- 한국어 주석 사용

## Architecture

Layered Architecture (Controller → Service → Repository → Entity)

```
main.py                          # FastAPI 앱 진입점
dev_blackbox/
├── controller/                  # REST API 엔드포인트 + DTO
├── service/                     # 비즈니스 로직
├── storage/rds/                 # Repository + Entity (SQLAlchemy)
├── client/                      # 외부 API 클라이언트 (GitHub 등) + Model
├── agent/                       # LLM 에이전트 + Prompt
├── task/                        # BackgroundTasks 비동기 작업
└── core/                        # 설정, DB, 예외, Enum
```

상세 아키텍처 문서: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Key Conventions

### Entity 생성

- 팩토리 메서드 `Entity.create(...)` 패턴 사용
- `Base` 상속 (created_at, updated_at 자동 관리)
- 삭제 필요 시 `SoftDeleteMixin` 추가 (is_deleted, deleted_at)

### DB 세션

- **Controller 레벨**: `get_db()` — 수동 commit/rollback
- **Service 레벨**: `get_db_session()` — 자동 commit/rollback (context manager)

### DTO

- Request/Response DTO는 `controller/dto/` 에 정의
- Pydantic v2 BaseModel 사용

### 외부 클라이언트

- `client/` 디렉토리에 클라이언트 클래스 + `client/model/`에 Pydantic 모델
- `httpx` 비동기 HTTP 클라이언트 사용
- `create()` 팩토리 메서드로 인스턴스 생성

### 예외 처리

- `ServiceException` → `EntityNotFoundException` → 구체 예외 (e.g., `UserByIdNotFoundException`)
- `controller/exception_handler.py`에서 FastAPI 핸들러 등록

### 환경 변수

- `.env` 파일 (Pydantic Settings, 구분자: `__`)
- 민감 정보는 `.env`에만 보관, `.env.template` 참고
