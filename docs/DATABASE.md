# Database

PostgreSQL 데이터 모델, ORM 엔티티, 세션 관리.

> 인프라 설정(Docker, 연결 정보)은 [INFRASTRUCTURE.md](INFRASTRUCTURE.md) 참고.

## Entity 패턴

### Base 클래스

모든 Entity가 상속하는 `DeclarativeBase`:

- `created_at` — 생성 시각 (`server_default: NOW()`)
- `updated_at` — 수정 시각 (`server_default: NOW()`, `onupdate: NOW()`)

### SoftDeleteMixin

논리 삭제가 필요한 Entity에 혼합:

- `is_deleted` — 삭제 여부 (default: `False`)
- `deleted_at` — 삭제 시각 (default: `9999-12-31 14:59:59+00`)
- `delete()` 메서드로 논리 삭제 수행

### 팩토리 메서드

모든 Entity는 `Entity.create(...)` 클래스 메서드로 생성.

## Entity 상세

### User

테이블: `users`

| 컬럼       | 타입           | 제약 조건                          | 설명     |
|----------|--------------|--------------------------------|--------|
| id       | BIGSERIAL    | PK, AUTO_INCREMENT             | 사용자 ID |
| name     | VARCHAR(100) | NOT NULL                       | 이름     |
| email    | VARCHAR(255) | NOT NULL, UNIQUE               | 이메일    |
| timezone | VARCHAR(50)  | NOT NULL, DEFAULT 'Asia/Seoul' | 타임존    |

- Mixin: `SoftDeleteMixin`
- Relationship: `github_user_secrets` (1:N → GitHubUserSecret)
- Property: `tz_info` → `ZoneInfo(self.timezone)`

### GitHubUserSecret

테이블: `github_user_secret`

| 컬럼                    | 타입           | 제약 조건              | 설명           |
|-----------------------|--------------|--------------------|--------------|
| id                    | SERIAL       | PK, AUTO_INCREMENT | 시크릿 ID       |
| user_id               | BIGINT       | FK → users.id      | 사용자 FK       |
| username              | VARCHAR(50)  | NOT NULL           | GitHub 사용자명  |
| personal_access_token | VARCHAR(255) | NOT NULL           | PAT (암호화 저장) |
| is_active             | BOOLEAN      | DEFAULT TRUE       | 활성 상태        |
| deactivate_at         | TIMESTAMPTZ  | NULLABLE           | 비활성화 시각      |

- Mixin: `SoftDeleteMixin`
- Relationship: `user` (N:1 → User)
- Method: `deactivate()` — 비활성화 처리

### GitHubEvent

테이블: `github_event`

| 컬럼                    | 타입           | 제약 조건                      | 설명            |
|-----------------------|--------------|----------------------------|---------------|
| id                    | BIGSERIAL    | PK, AUTO_INCREMENT         | 이벤트 ID        |
| user_id               | BIGINT       | FK → users.id              | 사용자 FK        |
| github_user_secret_id | INT          | FK → github_user_secret.id | 시크릿 FK        |
| event_id              | VARCHAR(100) | NOT NULL, UNIQUE           | GitHub 이벤트 ID |
| target_date           | DATE         | NOT NULL                   | 수집 대상 날짜      |
| event                 | JSONB        | NOT NULL                   | 이벤트 원본 데이터    |
| commit                | JSONB        | NULLABLE                   | 커밋 상세 데이터     |

- Mixin: 없음 (Base만 상속)
- Method: `get_event()` → `GithubEventModel`, `get_commit()` → `GithubCommitModel`

### 외래 키

모든 FK는 `ON DELETE RESTRICT`.

## Repository 패턴

Repository는 `Session`을 주입받아 데이터 접근을 캡슐화.

### UserRepository

| 메서드                 | 반환 타입        | 설명             |
|---------------------|--------------|----------------|
| save(user)          | User         | 사용자 저장         |
| find_by_id(user_id) | User \| None | ID로 조회 (삭제 제외) |
| find_all()          | list[User]   | 전체 조회 (삭제 제외)  |
| is_exist(user_id)   | bool         | 존재 여부 확인       |

### GitHubUserSecretRepository

| 메서드                  | 반환 타입                    | 설명              |
|----------------------|--------------------------|-----------------|
| save(secret)         | GitHubUserSecret         | 시크릿 저장          |
| find_by_user_id(uid) | GitHubUserSecret \| None | 활성 + 미삭제 시크릿 조회 |

### GitHubEventRepository

| 메서드                                            | 반환 타입             | 설명                            |
|------------------------------------------------|-------------------|-------------------------------|
| save(event)                                    | GitHubEvent       | 이벤트 저장                        |
| save_all(events)                               | list[GitHubEvent] | 벌크 저장                         |
| delete_all(events)                             | None              | 벌크 삭제                         |
| find_all_by_user_id(uid)                       | list[GitHubEvent] | 사용자별 이벤트 조회 (target_date ASC) |
| find_all_by_user_id_and_target_date(uid, date) | list[GitHubEvent] | 사용자+날짜별 이벤트 조회                |
| exists_by_event_id(event_id)                   | bool              | 이벤트 ID 존재 여부                  |

## DB 세션 관리

두 가지 세션 관리 방식 모두 자동 commit/rollback 처리:

### `get_db()` — FastAPI 의존성 주입용

```python
# Controller에서 Depends()로 주입
@router.post("/users")
async def create_user(db: Session = Depends(get_db)):
    service = UserService(db)
    ...
```

### `get_db_session()` — Service 로직용

```python
# Context manager로 자동 트랜잭션 관리
with get_db_session() as db:
    repo.save(entity)
```

### 세션 설정

- `autocommit=False`, `autoflush=False`, `expire_on_commit=True`
- Isolation level: `REPEATABLE READ`

## 스키마

초기화 SQL: `docker/postgres/init.sql`

### 트리거

- `update_updated_at_column()` — `updated_at` 자동 갱신 (BEFORE UPDATE)
- 모든 테이블에 등록

### 인덱스

| 테이블                | 인덱스                        | 컬럼                     |
|--------------------|----------------------------|------------------------|
| users              | idx_users_001              | email                  |
| users              | idx_users_002              | created_at DESC        |
| github_user_secret | idx_github_user_secret_001 | user_id                |
| github_user_secret | idx_github_user_secret_002 | created_at DESC        |
| github_event       | idx_github_event_001       | (user_id, target_date) |
| github_event       | idx_github_event_002       | target_date            |
| github_event       | idx_github_event_003       | created_at DESC        |
