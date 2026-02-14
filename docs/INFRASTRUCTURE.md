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
- 향후 임베딩 저장에 활용 예정

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
DATABASE__DEBUG=True
DATABASE__HOST=localhost
DATABASE__PORT=7400
DATABASE__DATABASE=dev_blackbox
DATABASE__USER=blackbox
DATABASE__PASSWORD=passw0rd

ENCRYPTION__KEY=...
ENCRYPTION__PEPPER=...
```

### 설정 클래스 계층

- `Settings` — 최상위 설정 (싱글턴, `@lru_cache`)
    - `PostgresDatabaseSecrets` — DB 연결 정보 + 커넥션 풀 설정
    - `EncryptionSecrets` — 암호화 키/페퍼

### 커넥션 풀 설정

| 설정              | 기본값             | 설명                   |
|-----------------|-----------------|----------------------|
| pool_size       | 5               | 풀에 유지할 연결 수          |
| max_overflow    | 10              | pool_size 초과 시 추가 허용 |
| pool_timeout    | 60초             | 연결 대기 타임아웃           |
| pool_recycle    | 1800초 (30분)     | 연결 재생성 주기            |
| pool_pre_ping   | True            | 사용 전 연결 검증           |
| isolation_level | REPEATABLE READ | 트랜잭션 격리 수준           |

## 암호화 (AES-256-GCM)

GitHub PAT 등 민감 정보를 암호화하여 DB에 저장.

- 알고리즘: AES-256-GCM
- 키 파생: HKDF-SHA256 (key + pepper + salt)
- 바이너리 형식: `salt(16) + nonce(12) + tag(16) + ciphertext`
- 인코딩: URL-safe Base64
- `EncryptService.encrypt(plaintext)` / `decrypt(encrypted)`

## Redis (예정)

Docker Compose에 정의되어 있으나 현재 비활성화 (주석 처리).

- 이미지: `redis:8-alpine`
- 포트: `7410:6379`
