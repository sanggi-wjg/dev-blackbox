---
name: create-service
description: 새로운 Service 레이어를 생성합니다. Service 클래스, Command, Query, 예외 클래스를 함께 생성합니다.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# create-service

Service 레이어를 생성하는 스킬.
Service 클래스, Command/Query 객체, 예외 클래스를 프로젝트 컨벤션에 맞게 생성한다.

## 입력

사용자에게 다음 정보를 확인한다:

1. **도메인명** (snake_case, 예: `jira_event`)
2. **Service가 사용할 Repository** (기존 Repository 또는 `create-table`로 생성한 Repository)
3. **메서드 목록** — 각 메서드의 역할 (조회/생성/수정/삭제)
4. **외부 의존성** — 다른 Service, 외부 클라이언트(`Client`), EncryptService 등
5. **필요한 예외 클래스** — NotFoundException, 비즈니스 예외 등

## 사전 확인

생성 전에 반드시 다음 파일을 읽고 참고한다:

1. **사용할 Repository** — 메서드 시그니처, Entity 타입 확인
2. **사용할 Entity** — 팩토리 메서드 `create()`, 비즈니스 메서드 확인
3. **`core/exception.py`** — 기존 예외 클래스 확인, 중복 생성 방지
4. **기존 유사 Service** — 동일 도메인이나 유사 패턴의 Service 참고

## 생성 산출물

다음 파일들을 순서대로 생성/수정한다:

### 1. Service — `dev_blackbox/service/{도메인}_service.py`

```python
from sqlalchemy.orm import Session

from dev_blackbox.core.exception import {엔티티}NotFoundException
from dev_blackbox.service.command.{도메인}_command import Create{엔티티}Command
from dev_blackbox.service.query.{도메인}_query import {엔티티}Query
from dev_blackbox.storage.rds.entity.{테이블명} import {엔티티}
from dev_blackbox.storage.rds.repository import {엔티티}Repository


class {엔티티}Service:

    def __init__(self, session: Session):
        self.{도메인}_repository = {엔티티}Repository(session)

    def get_{도메인}(self, query: {엔티티}Query) -> {엔티티} | None:
        return self.{도메인}_repository.find_by_user_id_and_target_date(
            query.user_id, query.target_date
        )

    def get_{도메인들}(self, query: {엔티티}Query) -> list[{엔티티}]:
        return self.{도메인}_repository.find_all_by_user_id(query.user_id)

    def get_{도메인}_or_throw(self, {도메인}_id: int) -> {엔티티}:
        entity = self.{도메인}_repository.find_by_id({도메인}_id)
        if entity is None:
            raise {엔티티}NotFoundException({도메인}_id)
        return entity

    def create_{도메인}(self, command: Create{엔티티}Command) -> {엔티티}:
        entity = {엔티티}.create(
            field1=command.field1,
            field2=command.field2,
        )
        return self.{도메인}_repository.save(entity)

    def delete_{도메인}(self, {도메인}_id: int) -> None:
        entity = self.get_{도메인}_or_throw({도메인}_id)
        entity.delete()  # SoftDelete인 경우
        # 또는 self.{도메인}_repository.delete_by_id({도메인}_id)  # HardDelete인 경우
```

#### Service 컨벤션

- `Session`을 생성자로 받아 Repository를 내부에서 생성
- Repository 변수명: `self.{도메인}_repository`
- 다른 Service 의존 시 생성자에서 `self.{서비스}_service = {서비스}Service(session)`
- 외부 유틸 서비스 의존 시 생성자에서 팩토리 함수 호출: `self.encrypt_service = get_encrypt_service()`
- 조회 메서드는 Query 객체를 받음
- 쓰기 메서드는 Command 객체를 받음
- `_or_throw` 접미사: Entity가 없으면 예외를 발생시키는 조회 메서드
- `_or_none` 접미사: Entity가 없으면 None을 반환하는 조회 메서드
- 내부 헬퍼 메서드는 `_` 접두사 (예: `_get_user_or_throw`)
- 데이터 수집/동기화 등 루프 기반 로직이 있는 Service는 `logger = logging.getLogger(__name__)` 추가
- 메서드는 Entity를 직접 반환 (Service Model은 실질적 변환 로직이 있을 때만 사용)

#### 다른 Service를 의존하는 경우

```python
class JiraEventService:

    def __init__(self, session: Session):
        self.jira_event_repository = JiraEventRepository(session)
        self.jira_user_service = JiraUserService(session)
        self.jira_secret_service = JiraSecretService(session)
```

#### 외부 클라이언트를 사용하는 경우

```python
class GitHubEventService:

    def __init__(self, session: Session):
        self.github_event_repository = GitHubEventRepository(session)
        self.github_user_secret_service = GitHubUserSecretService(session)
        self.encrypt_service = get_encrypt_service()

    def save_events(self, command: SaveGitHubEventsCommand) -> list[GitHubEvent]:
        secret = self.github_user_secret_service.get_secret_by_user_id_or_throw(command.user_id)
        decrypted_token = self.encrypt_service.decrypt(secret.personal_access_token)

        client = GithubClient.create(
            username=secret.username,
            personal_access_token=decrypted_token,
        )
        # 외부 API 호출 후 Entity 생성/저장
        ...
```

#### Service Model을 반환하는 경우

Entity를 직접 반환하는 것이 기본이지만, **실질적 변환 로직이 있을 때**는 Service Model을 사용한다.
Service Model은 `service/model/{도메인}_model.py`에 정의한다.

##### Service Model 형태 선택 기준

| 조건 | 권장 형태 |
|------|----------|
| Entity + 계산값 조합 (Entity가 메인 데이터) | **NamedTuple** |
| 필드명 중복 가능성 있거나, Entity가 메인이 아닌 조합 데이터 | **BaseModel** |

##### NamedTuple — Entity가 메인 데이터인 경우

```python
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity import {엔티티}


class {엔티티}SearchResult(NamedTuple):
    {엔티티_소문자}: {엔티티}
    distance: float
```

- Entity에 계산값(distance, score 등)을 붙여서 반환할 때 사용
- Entity가 주 데이터이므로 Entity 필드를 첫 번째에 배치

##### BaseModel — Entity가 메인이 아닌 조합 데이터

```python
from datetime import date

from pydantic import BaseModel

from dev_blackbox.core.enum import PlatformEnum


class EventContributionByDate(BaseModel):
    event_date: date
    count: int
    level: int
    platforms: dict[PlatformEnum, int]


class EventContributionSummary(BaseModel):
    total_contributions: int
    active_days: int
    longest_streak: int
    current_streak: int


class EventContribution(BaseModel):
    summary: EventContributionSummary
    contributions: list[EventContributionByDate]
```

- 여러 소스를 조합하거나, Entity 없이 계산된 결과를 반환할 때 사용
- 중첩 모델 가능 (상위 모델이 하위 모델을 포함)

##### Service에서 Service Model 반환 예시

```python
def search_{도메인}(self, query: SearchQuery) -> list[{엔티티}SearchResult]:
    projections = self.{도메인}_repository.find_similar_by_embedding(...)
    return [
        {엔티티}SearchResult(
            {엔티티_소문자}=p.{엔티티_소문자},
            distance=p.distance,
        )
        for p in projections
    ]
```

#### 캐싱이 필요한 경우

```python
from dev_blackbox.core.cache import cacheable, cache_evict, CacheTTL

class SomeService:

    @cacheable(key="some_data:{user_id}", ttl=CacheTTL.ONE_HOUR)
    def get_cached_data(self, user_id: int) -> dict:
        ...

    @cache_evict(key="some_data:{user_id}")
    def update_data(self, user_id: int, command: UpdateCommand) -> Entity:
        ...
```

### 2. Command — `dev_blackbox/service/command/{도메인}_command.py`

쓰기 작업(Create, Update, Delete)의 입력 데이터를 캡슐화한다.

```python
from datetime import date

from pydantic import BaseModel


class Create{엔티티}Command(BaseModel):
    user_id: int
    field1: str
    field2: int
    optional_field: str | None = None


class Update{엔티티}Command(BaseModel):
    user_id: int
    {도메인}_id: int
    field1: str
```

#### Command 컨벤션

- Pydantic `BaseModel` 상속
- 네이밍: `{동사}{엔티티}Command` (예: `CreateGitHubUserSecretCommand`, `SaveDailyWorkLogCommand`)
- 사용자 소유 리소스 작업에는 `user_id` 포함. 단, 최상위 리소스(User, Secret) 생성 등 시스템 레벨 작업은 `user_id` 불필요
- 검증 로직 없음 — 검증은 DTO 레이어에서 수행
- 한 파일에 도메인 관련 Command를 모두 정의

### 3. Query — `dev_blackbox/service/query/{도메인}_query.py`

조회 조건을 캡슐화한다.

```python
from datetime import date

from pydantic import BaseModel


class {엔티티}Query(BaseModel):
    user_id: int
    target_date: date | None = None
    optional_filter: str | None = None
```

#### Query 컨벤션

- Pydantic `BaseModel` 상속
- 네이밍: `{엔티티}Query` (예: `DailyWorkLogQuery`, `UserQuery`)
- 사용자별 조회에는 `user_id` 포함. 관리자 전체 조회(`UserQuery` 등)에서는 `user_id` 불필요하거나 optional
- 선택 필터는 `None` 기본값
- 검증 로직 없음
- 한 파일에 도메인 관련 Query를 모두 정의
- Query가 한 개의 조회 메서드에서만 쓰이더라도 별도 객체로 생성

### 4. 예외 클래스 — `dev_blackbox/core/exception.py`에 추가

#### NotFoundException

```python
class {엔티티}NotFoundException(EntityNotFoundException):

    def __init__(self, identifier: Any):
        super().__init__(entity_name="{엔티티}", identifier=identifier)
```

#### 비즈니스 예외

```python
class {엔티티}{상황}Exception(ServiceException):

    def __init__(self, {파라미터}: {타입}):
        super().__init__(f"{설명 메시지}. ({파라미터명}: {{파라미터}})")
```

#### 예외 컨벤션

- NotFoundException은 `EntityNotFoundException` 상속 → `# Not Found Exception` 섹션에 추가
- 비즈니스 예외는 `ServiceException` 상속 → `# Service Exception` 섹션에 추가
- 예외 메시지는 영문
- 기존 예외와 중복되지 않는지 확인

### 5. 예외 핸들러 등록 (필요한 경우) — `dev_blackbox/controller/config/exception_handler.py`

기본적으로 `EntityNotFoundException`은 404, `ServiceException`은 500으로 처리된다.
특별한 상태 코드가 필요한 예외만 핸들러를 추가한다.

## 메서드 설계 가이드

### 조회 메서드

| 패턴 | 반환 타입 | 설명 |
|------|----------|------|
| `get_{도메인}(query)` | `Entity \| None` | 단건 조회, 없으면 None |
| `get_{도메인}_or_throw(id)` | `Entity` | 단건 조회, 없으면 예외 |
| `get_{도메인}_by_{필터}_or_throw(필터값)` | `Entity` | 특정 필터 기준 조회, 없으면 예외 |
| `get_{도메인}_by_{필터}_or_none(필터값)` | `Entity \| None` | 특정 필터 기준 조회, 없으면 None |
| `get_{도메인들}(query)` | `list[Entity]` | 목록 조회 |
| `search_{도메인}(query)` | `list[ServiceModel]` | 계산값 포함 검색 (Service Model 반환) |
| `get_{집계}(query)` | `ServiceModel` | 조합/집계 결과 (Service Model 반환) |
| `_get_{도메인}_or_throw(id)` | `Entity` | 내부 헬퍼 (다른 Service에서 직접 사용하지 않음) |

### 쓰기 메서드

| 패턴 | 반환 타입 | 설명 |
|------|----------|------|
| `create_{도메인}(command)` | `Entity` | 생성 후 Entity 반환 |
| `save_{도메인}(command)` | `Entity` | 멱등 저장 (기존 삭제 후 재저장) |
| `update_{도메인}(command)` | `Entity` | 수정 후 Entity 반환 |
| `delete_{도메인}(id)` | `None` | 삭제 (SoftDelete 또는 HardDelete) |

### 할당/해제 메서드 (관계 설정)

| 패턴 | 반환 타입 | 설명 |
|------|----------|------|
| `assign_user(user_id, entity_id)` | `Entity` | 관계 설정 |
| `unassign_user(user_id, entity_id)` | `Entity` | 관계 해제 |

## 실행 절차

```
1. Repository/Entity 확인   → 검증: 사용할 Repository 메서드가 존재하는가
2. 예외 클래스 추가          → 검증: 기존 예외와 중복되지 않는가
3. Command 생성             → 검증: 쓰기 메서드의 입력 필드가 포함되었는가
4. Query 생성               → 검증: 조회 조건 필드가 포함되었는가
5. Service 생성             → 검증: Repository/Service 의존성이 올바른가
6. 포맷팅/타입 체크          → 검증: black, pyright 통과
```

## 체크리스트

생성 완료 후 다음을 확인한다:

- [ ] Service 생성자가 `Session`을 받고 내부에서 Repository를 생성하는가
- [ ] 조회 메서드가 Query 객체를 받는가
- [ ] 쓰기 메서드가 Command 객체를 받는가
- [ ] `_or_throw` 메서드가 Entity 부재 시 적절한 예외를 발생시키는가
- [ ] Command/Query가 Pydantic `BaseModel`을 상속하는가
- [ ] 사용자 소유 리소스의 Command/Query에 `user_id`가 포함되어 있는가
- [ ] 예외 클래스가 `exception.py`의 올바른 섹션에 추가되었는가
- [ ] Service가 Entity를 직접 반환하는가 (실질적 변환 로직이 없으면 Service Model 미사용)
- [ ] Service Model이 필요한 경우: Entity가 메인이면 NamedTuple, 아니면 BaseModel을 사용하는가
- [ ] 다른 Service 의존 시 생성자에서 `{Service}(session)`으로 생성하는가
- [ ] `pyright`와 `black` 검사를 통과하는가
