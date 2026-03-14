# Infrastructure

인프라 구성 및 환경 설정.

> 아키텍처 개요는 [ARCHITECTURE.md](ARCHITECTURE.md) 참고.

## Docker

```bash
docker compose -f docker/docker-compose.yaml up -d
```

| 서비스        | 이미지                      | 포트          |
|------------|--------------------------|-------------|
| PostgreSQL | `pgvector/pgvector:pg17` | `7400:5432` |
| Redis      | `redis:8-alpine`         | `7410:6379` |

- PostgreSQL 튜닝: `docker/postgres/postgresql.conf`
- 스키마 초기화: `docker/postgres/init.sql`

## Redis 사용 목적

- **APScheduler JobStore** — 스케줄링 태스크 상태 저장
- **분산 락** — 동일 태스크 중복 실행 방지 (`distributed_lock()`)
- **캐싱** — `CacheService`를 통한 데이터 캐싱 (`@cacheable`, `@cache_put`, `@cache_evict`), TTL은 `CacheTTL` Enum으로 관리
- **멱등성** — `idempotent_request`를 통한 요청 중복 처리 방지

Redis 불가용 시 `None` 반환 (graceful degradation).

## 분산 락

Redis 기반 분산 락으로 동일 태스크 중복 실행 방지. Redis 불가용 시 락 없이 진행.

- 스케줄 태스크: `LockKey` Enum 기반 전역 락
- 수동 동기화: 사용자+날짜 조합 동적 락

## 로깅

`setup_logging()`으로 중앙 집중식 로깅을 설정한다 (`main.py` 최상단에서 호출).

- **핸들러**: `console` (stdout) + `file` (RotatingFileHandler). `LoggingConfig.handlers`로 설정 가능
- **파일 로그**: `logs/app.log` (기본 경로: 프로젝트 루트 `logs/`). `LoggingConfig.log_file_dir`로 변경 가능
- **로테이션**: 파일당 최대 10MB, 최대 5개 백업 파일
- **인코딩**: UTF-8

## 환경 설정

Pydantic Settings 기반, `.env` 파일에서 로드 (중첩 구분자: `__`).

설정 상세는 `core/config.py` 코드 및 `.env.template` 참고.
