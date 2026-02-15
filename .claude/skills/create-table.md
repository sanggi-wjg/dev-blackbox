# create-table

새로운 데이터베이스 테이블을 생성하는 스킬.
`init.sql`의 기존 패턴을 따라 SQL DDL, Entity, Repository를 함께 생성한다.

## 입력

사용자에게 다음 정보를 확인한다:

1. **테이블명** (snake_case, 예: `jira_issue`)
2. **컬럼 목록** (이름, 타입, 제약조건)
3. **SoftDelete 필요 여부** (기본: 불필요)
4. **FK 관계** (참조 테이블, ON DELETE 정책)
5. **UNIQUE 제약조건** (복합 유니크 포함)

## 생성 산출물

다음 파일들을 순서대로 생성/수정한다:

### 1. SQL DDL — `docker/postgres/init.sql` 하단에 추가

기존 테이블 정의와 빈 줄 2개로 구분하여 추가한다:

```sql


-- {테이블명} 테이블 ({설명})
CREATE TABLE IF NOT EXISTS {테이블명}
(
    id          BIGSERIAL PRIMARY KEY,
    -- 비즈니스 컬럼들...

    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- SoftDelete 필요 시 created_at/updated_at 바로 뒤에 추가:
    -- is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE,
    -- deleted_at  TIMESTAMPTZ NOT NULL DEFAULT '9999-12-31 14:59:59+00',

    -- FK 제약조건 (마지막 블록)
    CONSTRAINT fk_{테이블명}_{참조} FOREIGN KEY ({fk_컬럼}) REFERENCES {참조테이블} (id) ON DELETE RESTRICT,

    -- UNIQUE 제약조건
    CONSTRAINT uq_{테이블명}_{컬럼들} UNIQUE ({컬럼들})
);

CREATE TRIGGER tr_{테이블명}_updated_at
    BEFORE UPDATE ON {테이블명}
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 인덱스: FK 컬럼, 자주 조회하는 컬럼, created_at DESC
CREATE INDEX idx_{테이블명}_001 ON {테이블명} ({주요_조회_컬럼});
CREATE INDEX idx_{테이블명}_002 ON {테이블명} (created_at DESC);

-- 코멘트
COMMENT ON TABLE {테이블명} IS '{설명}';
COMMENT ON COLUMN {테이블명}.{컬럼} IS '{컬럼설명}';
```

#### SQL 컨벤션

- PK는 `BIGSERIAL` 사용 (단, 작은 테이블은 `SERIAL` 허용)
- FK 컬럼은 `{참조테이블}_id` 네이밍
- FK는 모두 `ON DELETE RESTRICT`
- `created_at`, `updated_at`은 항상 포함 (Base에서 상속)
- 인덱스 네이밍: `idx_{테이블명}_{순번3자리}` (001, 002, ...)
- 제약조건 네이밍: `fk_{테이블명}_{참조}`, `uq_{테이블명}_{컬럼들}`
- JSONB 컬럼은 NOT NULL이 기본, nullable이면 명시적으로 NULL
- `vector(1024)` 타입은 임베딩 컬럼에 사용, 항상 nullable
- COMMENT는 테이블과 모든 비즈니스 컬럼에 작성

### 2. Entity — `dev_blackbox/storage/rds/entity/{테이블명}.py`

파일명은 테이블명(snake_case)과 동일, 클래스명은 PascalCase로 변환한다.
(예: 테이블 `jira_issue` → 파일 `jira_issue.py` → 클래스 `JiraIssue`)

```python
from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.storage.rds.entity.base import Base  # 또는 SoftDeleteMixin 추가


class {엔티티명}(Base):  # SoftDelete 필요 시: class {엔티티명}(SoftDeleteMixin, Base)
    __tablename__ = '{테이블명}'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # 비즈니스 컬럼들...

    # FK 컬럼
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
    )

    def __repr__(self) -> str:
        # 의미 있는 비즈니스 식별 필드를 사용 (id만 사용하지 않음)
        # 예: User → name, email / GitHubEvent → event_id, user_id
        return f'<{엔티티명}({식별필드1}={self.{식별필드1}}, {식별필드2}={self.{식별필드2}})>'

    @classmethod
    def create(cls, ...) -> '{엔티티명}':
        return cls(...)
```

#### Entity 컨벤션

- `Base` 상속 (created_at, updated_at 자동 관리)
- 삭제 필요 시 `SoftDeleteMixin` 추가 (MRO: `SoftDeleteMixin, Base`)
- 팩토리 메서드 `create()` 필수
- `__repr__` 필수
- 타입 매핑:
  - `BIGSERIAL/BIGINT` → `BigInteger`
  - `SERIAL/INT` → `Integer`
  - `VARCHAR(n)` → `String(n)`
  - `TEXT` → `Text`
  - `DATE` → `Date`
  - `TIMESTAMPTZ` → `DateTime(timezone=True)`
  - `JSONB` → `JSONB` (from `sqlalchemy.dialects.postgresql`)
  - `BOOLEAN` → 기본 `bool` (mapped_column default 사용)
  - `vector(1024)` → `Vector(1024)` (from `pgvector.sqlalchemy`)
- JSONB 컬럼이 Pydantic 모델과 매핑되면 `@cached_property`로 변환 메서드 추가
- Enum 컬럼은 `PlatformEnum` 등 Python Enum을 `Mapped` 타입으로 사용하되, DB 컬럼은 `String`으로 매핑
- 문자열은 작은따옴표 사용

### 3. Repository — `dev_blackbox/storage/rds/repository/{테이블명}_repository.py`

파일명은 `{테이블명}_repository.py`, 클래스명은 `{엔티티명}Repository`로 한다.

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.{테이블명} import {엔티티명}


class {엔티티명}Repository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, entity: {엔티티명}) -> {엔티티명}:
        self.session.add(entity)
        self.session.flush()
        return entity

    def find_by_id(self, entity_id: int) -> {엔티티명} | None:
        stmt = select({엔티티명}).where({엔티티명}.id == entity_id)
        return self.session.scalar(stmt)

    def find_all_by_user_id(self, user_id: int) -> list[{엔티티명}]:
        stmt = (
            select({엔티티명})
            .where({엔티티명}.user_id == user_id)
            .order_by({엔티티명}.id.asc())
        )
        return list(self.session.scalars(stmt).all())
```

#### Repository 컨벤션

- `Session`을 생성자 주입
- `save()` → `add` + `flush`
- `save_all()` → `add_all` + `flush` (벌크 저장 필요 시)
- `find_by_id()` → `scalar` (단건 조회)
- `find_all_by_*()` → `scalars().all()` (목록 조회), `list()`로 감싸기
- `delete_by_*()` → `delete` statement + `flush`
- `exists_by_*()` → `select(Entity.id)` + `scalar is not None`
- SoftDelete 엔티티의 조회 메서드는 `.where(Entity.is_deleted == False)` 조건 필수

### 4. `__init__.py` 업데이트

#### Entity `__init__.py` — `dev_blackbox/storage/rds/entity/__init__.py`

새 Entity를 import 목록과 `__all__`에 알파벳순으로 추가.

#### Repository `__init__.py` — `dev_blackbox/storage/rds/repository/__init__.py`

새 Repository를 import 목록과 `__all__`에 알파벳순으로 추가.

### 5. 문서 업데이트 — `docs/DATABASE.md`

Entity 상세 섹션과 Repository 패턴 섹션에 새 테이블 정보를 추가한다.

## 체크리스트

생성 완료 후 다음을 확인한다:

- [ ] SQL DDL이 `init.sql` 하단에 추가되었는가
- [ ] updated_at 트리거가 등록되었는가
- [ ] 인덱스가 FK 컬럼 및 주요 조회 컬럼에 생성되었는가
- [ ] COMMENT가 테이블과 모든 비즈니스 컬럼에 작성되었는가
- [ ] Entity가 `Base` (또는 `SoftDeleteMixin, Base`)를 상속하는가
- [ ] `create()` 팩토리 메서드가 있는가
- [ ] Repository의 조회 메서드가 SoftDelete 조건을 포함하는가 (해당 시)
- [ ] `__init__.py`가 업데이트되었는가
- [ ] `pyright`와 `black` 검사를 통과하는가
