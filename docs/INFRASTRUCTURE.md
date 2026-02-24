# Infrastructure

인프라 구성 및 환경 설정.

> 아키텍처 개요는 [ARCHITECTURE.md](ARCHITECTURE.md) 참고.

## PostgreSQL

### Docker Compose

- 이미지: `pgvector/pgvector:pg17`
- 컨테이너: `dev-blackbox-postgres`
- 포트: `7400:5432`
- 리소스: CPU 0.5, Memory 512MB
- Healthcheck: `pg_isready -U blackbox` (30s interval)
- 볼륨:
    - `init.sql` — 초기화 스크립트 (테이블/인덱스/트리거 생성)
    - `postgresql.conf` — 커스텀 설정
    - `data/` — 데이터 영속화

```bash
docker compose -f docker/docker-compose.yaml up -d
```

### PostgreSQL 튜닝

`docker/postgres/postgresql.conf` (512MB 기준):

| 설정                         | 값     | 설명                 |
|----------------------------|-------|--------------------|
| shared_buffers             | 128MB | 공유 버퍼              |
| effective_cache_size       | 384MB | 캐시 크기 추정           |
| work_mem                   | 4MB   | 쿼리 작업 메모리          |
| maintenance_work_mem       | 64MB  | 유지보수 작업 메모리        |
| max_connections            | 30    | 최대 연결 수            |
| random_page_cost           | 1.1   | SSD 기준 랜덤 I/O 비용   |
| log_min_duration_statement | 500   | 슬로우 쿼리 로깅 (500ms+) |
| timezone                   | UTC   | DB 타임존             |

### pgvector

- `CREATE EXTENSION IF NOT EXISTS vector`로 활성화
- PlatformSummary, DailySummary 임베딩 벡터 저장에 활용 (`vector(1024)`)

## Redis

- 이미지: `redis:8-alpine`
- 컨테이너: `dev-blackbox-redis`
- 포트: `7410:6379`
- 리소스: CPU 0.5, Memory 512MB
- Healthcheck: `redis-cli ping` (30s interval)

### 사용 목적

- **APScheduler JobStore** — 스케줄링 태스크 상태 저장
- **분산 락** — 동일 태스크 중복 실행 방지 (`distributed_lock()`)

### Redis 클라이언트

`get_redis_client(database)` — `@lru_cache` 기반 Redis 클라이언트 팩토리.
연결 실패 시 `None` 반환 (graceful degradation).

## APScheduler (백그라운드 스케줄러)

APScheduler `BackgroundScheduler` 기반 태스크 스케줄링.

### 설정

| 설정                 | 값                      | 설명           |
|--------------------|------------------------|--------------|
| JobStore           | RedisJobStore          | Redis 기반 저장소 |
| Executor (default) | ThreadPoolExecutor(20) | 스레드 풀        |
| Executor (process) | ProcessPoolExecutor(5) | 프로세스 풀       |
| misfire_grace_time | 3600 (1시간)             | 미실행 허용 시간    |
| max_instances      | 1                      | 동일 작업 중복 방지  |
| coalesce           | False                  | 밀린 작업 병합 안함  |
| timezone           | UTC                    | 스케줄러 타임존     |

### 등록된 태스크

| 태스크                       | 스케줄                 | 설명               |
|---------------------------|---------------------|------------------|
| `health_check_task()`     | 매 1분 (interval)     | 헬스 체크            |
| `collect_platform_task()` | 매일 00:00 UTC (cron) | 플랫폼별 데이터 수집 + 요약 |
| `sync_jira_users_task()`  | 매일 15:00 UTC (cron) | Jira 사용자 동기화     |

### Lifespan

`main.py`에서 FastAPI lifespan으로 관리:

- 시작: `scheduler.start()`
- 종료: `scheduler.shutdown(wait=True)` → `engine.dispose()`

## 분산 락

Redis 기반 분산 락으로 동일 태스크 중복 실행 방지.

```python
with distributed_lock(DistributedLockName.COLLECT_PLATFORM_TASK, timeout=300) as acquired:
    if not acquired:
        return  # 이미 실행 중, 스킵
    do_work()
```

| 파라미터             | 기본값 | 설명                                |
|------------------|-----|-----------------------------------|
| lock_name        | -   | 락 이름 (`DistributedLockName` Enum) |
| timeout          | 60  | 락 자동 해제 시간 (초, 데드락 방지)            |
| blocking_timeout | 0   | 락 획득 대기 시간 (0: non-blocking)      |

**DistributedLockName:**

- `SYNC_JIRA_USERS_TASK`
- `COLLECT_PLATFORM_TASK`

**Fallback:** Redis 불가용 시 락 없이 진행 (graceful degradation).

## Ollama (LLM)

Ollama API 기반, LlamaIndex 연동.

### 기본 설정 (OllamaConfig)

| 설정              | 기본값                            |
|-----------------|--------------------------------|
| base_url        | `http://localhost:11434`       |
| model           | `gemini-3-flash-preview:cloud` |
| temperature     | 0.6                            |
| top_k           | 30                             |
| top_p           | 0.85                           |
| context_window  | 8,000                          |
| request_timeout | 240초                           |
| keep_alive      | 300초                           |
| repeat_penalty  | 1.2                            |
| num_predict     | 1,024                          |

### 요약 전용 설정 (SummaryOllamaConfig)

OllamaConfig를 상속하며 다음 값만 오버라이드:

| 설정             | 값      |
|----------------|--------|
| temperature    | 0.1    |
| context_window | 64,000 |
| num_predict    | 4,096  |

## 환경 설정

Pydantic Settings 기반, `.env` 파일에서 로드.
중첩 구분자는 `__` (이중 밑줄).

### `.env` 예시

```
ENV=local

DATABASE__DEBUG=True
DATABASE__HOST=localhost
DATABASE__PORT=7400
DATABASE__DATABASE=dev_blackbox
DATABASE__USER=blackbox
DATABASE__PASSWORD=passw0rd

REDIS__HOST=localhost
REDIS__PORT=7410

ENCRYPTION__KEY=your-base64-key-here
ENCRYPTION__PEPPER=your-pepper-secret-here

AUTH__SECRET_KEY=your-secret-key-here
AUTH__ALGORITHM=HS256
AUTH__ACCESS_TOKEN_EXPIRE_MINUTES=30

JIRA__URL=your-jira-base-url-here
JIRA__USERNAME=your-jira-username-here
JIRA__API_TOKEN=your-jira-api-token-here

CONFLUENCES__SPACES='["target-space-1", "target-space-2"]'

SLACK__BOT_TOKEN=xoxb-your-slack-bot-token-here
```

### 설정 클래스 계층

- `Settings` — 최상위 설정 (싱글턴, `@lru_cache`)
    - `PostgresDatabaseSecrets` — DB 연결 정보 + 커넥션 풀 설정
    - `RedisSecrets` — Redis 연결 정보 (host, port)
    - `EncryptionSecrets` — 암호화 키/페퍼
    - `AuthSecrets` — JWT 인증 설정 (secret_key, algorithm, access_token_expire_minutes)
    - `JiraSecrets` — Jira 연결 정보 (url, username, api_token)
    - `SlackSecrets` — Slack 봇 토큰 (bot_token)
    - `ConfluenceSecrets` — Confluence 대상 스페이스 목록
    - `LoggingConfig` — 로깅 설정 (레벨, 포맷)

### 커넥션 풀 설정

| 설정              | 기본값             | 설명                   |
|-----------------|-----------------|----------------------|
| pool_size       | 5               | 풀에 유지할 연결 수          |
| max_overflow    | 10              | pool_size 초과 시 추가 허용 |
| pool_timeout    | 60초             | 연결 대기 타임아웃           |
| pool_recycle    | 1800초 (30분)     | 연결 재생성 주기            |
| pool_pre_ping   | True            | 사용 전 연결 검증           |
| isolation_level | REPEATABLE READ | 트랜잭션 격리 수준           |

## 인증 (JWT + OAuth2)

JWT Bearer Token 기반 인증 시스템.

- 알고리즘: HS256 (설정 가능)
- 토큰 만료: 30분 (설정 가능)
- 토큰 페이로드: `{sub: email, is_admin: bool, exp: timestamp}`
- `JwtService.create_token(data)` / `decode_token(token)` — `@lru_cache` 싱글턴
- OAuth2 Password Grant 플로우 (`/api/v1/auth/token`)

### AuthSecrets 설정

| 설정                          | 기본값   | 설명           |
|-----------------------------|-------|--------------|
| secret_key                  | -     | JWT 서명 시크릿 키 |
| algorithm                   | HS256 | JWT 알고리즘     |
| access_token_expire_minutes | 30    | 토큰 만료 시간 (분) |

## 비밀번호 해싱

사용자 비밀번호를 안전하게 해싱하여 DB에 저장.

- 라이브러리: `pwdlib` (Argon2 기본, PBKDF2 fallback)
- `PasswordService.hash_password(password)` / `verify_password(password, hashed_password)`
- `@lru_cache` 싱글턴

## 암호화 (AES-256-GCM)

GitHub PAT 등 민감 정보를 암호화하여 DB에 저장.

- 알고리즘: AES-256-GCM
- 키 파생: HKDF-SHA256 (key + pepper + salt)
- 바이너리 형식: `salt(16) + nonce(12) + tag(16) + ciphertext`
- 인코딩: URL-safe Base64
- `EncryptService.encrypt(plaintext)` / `decrypt(encrypted)`
