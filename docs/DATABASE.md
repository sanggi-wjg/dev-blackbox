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

## Entity 목록

| Entity           | 테이블                  | Mixin             | UNIQUE 제약                          | 비고                                                        |
|------------------|----------------------|-------------------|------------------------------------|-----------------------------------------------------------|
| User             | `users`              | `SoftDeleteMixin` | `email`                            | Relationship: GitHubUserSecret, JiraUser, SlackUser (1:1) |
| GitHubUserSecret | `github_user_secret` | `SoftDeleteMixin` | —                                  | PAT 암호화 저장, `deactivate()` 비활성화                           |
| GitHubEvent      | `github_event`       | —                 | `event_id`                         | `event`/`commit` JSONB 저장                                 |
| JiraUser         | `jira_user`          | —                 | `account_id`, `user_id` (NULLABLE) | `assign_user_and_project()`로 User 할당                      |
| JiraEvent        | `jira_event`         | —                 | `issue_id`                         | `changelog` JSONB (target_date 기준 필터링)                    |
| PlatformWorkLog  | `platform_work_log`  | —                 | `(user_id, target_date, platform)` | `markdown_text` property, `update_content()`              |
| DailyWorkLog     | `daily_work_log`     | —                 | `(user_id, target_date)`           | 플랫폼별 WorkLog 병합 결과                                        |

- 모든 FK는 `ON DELETE RESTRICT`
- 컬럼 상세는 `storage/rds/entity/` 코드 또는 `docker/postgres/init.sql` 참고

## Repository 패턴

- `Session`을 생성자로 주입받아 데이터 접근을 캡슐화
- 메서드명은 `find_by_*`, `find_all_by_*`, `save`, `save_all`, `delete_by_*` 등 서술적 네이밍
- SoftDeleteMixin 사용 Entity의 조회 메서드는 `is_deleted=False` 조건 포함
- 상세 메서드 목록은 `storage/rds/repository/` 코드 참고

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

인덱스 상세는 `docker/postgres/init.sql` 참고.
