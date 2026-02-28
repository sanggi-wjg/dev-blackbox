---
name: create-service-test
description: Service 레이어의 테스트 코드를 작성합니다. 대상 Service 파일의 메서드를 분석하여 테스트 클래스와 테스트 케이스를 생성합니다.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# create-service-test

Service 레이어의 테스트 코드를 작성하는 스킬.
대상 Service 파일의 메서드를 분석하여 테스트 클래스와 테스트 케이스를 생성한다.

## 입력

사용자에게 다음 정보를 확인한다:

1. **대상 Service 파일 경로** (예: `dev_blackbox/service/github_event_service.py`)
2. **테스트할 메서드** (전체 또는 특정 메서드 지정)

## 메서드 분류

대상 Service의 각 메서드를 분석하여 다음 두 가지로 분류한다:

### DB 연동 테스트 (외부 API 호출 없음)

Repository 조회/저장만 하는 메서드. 실제 DB(Testcontainers)로 테스트한다.

- `mocker` 불필요
- `db_session`, `user_fixture` 등 conftest fixture 사용
- 조회 결과는 `assert result == [entity]` 형태로 객체 참조 비교

### Mock 테스트 (외부 API 호출 포함)

외부 클라이언트(`GitHubClient`, `JiraClient`, `SlackClient` 등)를 사용하는 메서드.
`pytest-mock`의 `mocker`로 외부 호출만 격리한다.

- `mocker.patch`로 클라이언트 팩토리(`Client.create`)를 패치
- `MagicMock(spec=ClientClass)`로 type-safe mock 생성
- DB 조회/저장은 실제 DB로 동작 (mock하지 않음)

## 생성 산출물

### 1. 테스트 파일 — `tests/service/{서비스명}_test.py`

소스 디렉토리 구조를 미러링하여 배치한다.

```
dev_blackbox/service/github_event_service.py
→ tests/service/github_event_service_test.py
```

### 2. Fixture 파일 (필요 시) — `tests/fixtures/{도메인}_fixture.py`

테스트에서 반복 사용되는 Pydantic 모델 팩토리를 별도 모듈로 분리한다.
DB 저장이 필요 없는 순수 모델 생성 함수만 배치한다.

```python
# tests/fixtures/github_fixture.py
from dev_blackbox.client.model.github_api_model import GithubEventModel, GithubRepositoryModel


def create_github_event_model(
    event_id: str,
    event_type: str = "PushEvent",
) -> GithubEventModel:
    return GithubEventModel(
        id=event_id,
        type=event_type,
        # ... 최소한의 필드
    )
```

### 3. conftest fixture (필요 시) — `tests/conftest.py`

DB에 Entity를 저장하는 팩토리 fixture는 `tests/conftest.py`에 추가한다.
기존 `user_fixture` 패턴을 따른다.

```python
@pytest.fixture()
def {entity}_fixture(
    db_session: Session,
) -> Callable[..., {Entity}]:

    def _create(
        # 필수 파라미터 (FK 등)
        user_id: int,
        # 선택 파라미터 (기본값 제공)
        name: str = "default",
    ) -> {Entity}:
        entity = {Entity}.create(...)
        db_session.add(entity)
        db_session.flush()
        return entity

    return _create
```

## 테스트 코드 구조

### 클래스/함수 네이밍

```python
class {서비스명}Test:  # 예: GitHubEventServiceTest

    def test_{메서드명}(self, ...):  # 정상 케이스

    def test_{메서드명}_{조건}_한글설명(self, ...):  # 엣지/예외 케이스
```

### DB 연동 테스트 템플릿

```python
def test_{메서드명}(
    self,
    db_session,
    user_fixture,
    {entity}_fixture,
):
    # given
    user = user_fixture()
    entity = {entity}_fixture(user_id=user.id)

    service = {Service}(db_session)

    # when
    result = service.{메서드명}(user.id)

    # then
    assert result == [entity]
```

### Mock 테스트 템플릿

```python
def test_{메서드명}(
    self,
    mocker,
    db_session,
    user_fixture,
    {secret}_fixture,
):
    # given
    user = user_fixture()
    secret = {secret}_fixture(user_id=user.id)

    service = {Service}(db_session)
    target_date = date(2025, 1, 1)

    # mock
    mock_client = MagicMock(spec={Client})
    mock_client.{api_method}.return_value = {expected_api_response}

    mocker.patch(
        "dev_blackbox.service.{서비스_모듈}.{Client}.create",
        return_value=mock_client,
    )

    # when
    result = service.{메서드명}(user.id, target_date)

    # then
    assert len(result) == 1
    mock_client.{api_method}.assert_called_once_with(...)
```

### 예외 테스트 템플릿

```python
def test_{메서드명}_{예외조건}(self, db_session):
    # given
    service = {Service}(db_session)

    # when & then
    with pytest.raises({Exception}):
        service.{메서드명}(9999, date(2025, 1, 1))
```

## 테스트 케이스 설계 원칙

각 메서드에 대해 다음 케이스를 검토한다:

### 조회 메서드

1. **정상 조회** — 데이터가 있으면 반환
2. **빈 결과** — 데이터가 없으면 빈 리스트
3. **필터링 검증** (조건 조회 시) — 조건에 맞지 않는 데이터도 함께 생성하여 필터가 동작하는지 확인

### 저장/수정 메서드

1. **정상 저장** — 저장 후 결과 검증
2. **선행 조건 실패** — 필수 엔티티 부재 시 예외 (`EntityNotFoundException`)
3. **외부 API 빈 응답** — API가 빈 결과를 반환하면 빈 리스트 저장
4. **API 호출 검증** — `assert_called_once_with()`로 올바른 파라미터 전달 확인

### 삭제 메서드

1. **정상 삭제** — 삭제 후 상태 검증 (SoftDelete: `is_deleted`, `deleted_at`)
2. **존재하지 않는 엔티티** — 예외 발생

## 컨벤션

- `# given`, `# when`, `# then` 주석으로 구분 (mock이 있으면 `# mock` 섹션 추가)
- 한글 함수명 사용 가능 (예: `test_get_events_이벤트가_없으면_빈_리스트`)
- `db_session` 내 조회 결과는 SQLAlchemy Identity Map 덕분에 `==`로 객체 비교
- `MagicMock`에는 반드시 `spec=ClassName` 지정 (type-safe mock)
- `mocker.patch` 경로는 **대상 클래스가 import된 위치** 기준 (원본 모듈이 아님)
    - 예: Service에서 `from dev_blackbox.client.github_client import GitHubClient` →
      patch 경로: `"dev_blackbox.service.{모듈}.GitHubClient.create"`
- fixture 파일(Pydantic 모델)은 `tests/fixtures/`에, DB 저장 fixture는 `tests/conftest.py`에 배치
- 테스트 실행 후 `poetry run pytest tests/service/{파일}_test.py -v`로 검증

## 체크리스트

생성 완료 후 다음을 확인한다:

- [ ] 테스트 파일이 소스 디렉토리 구조를 미러링하는가
- [ ] 클래스명이 `{서비스명}Test` 패턴인가
- [ ] 모든 테스트가 `# given`, `# when`, `# then`으로 구분되는가
- [ ] 조회 메서드에 정상/빈 결과/필터링 검증 케이스가 있는가
- [ ] 저장 메서드에 정상/예외/빈 응답 케이스가 있는가
- [ ] 외부 API 호출 메서드에 `mocker.patch`가 적용되었는가
- [ ] `MagicMock`에 `spec`이 지정되었는가
- [ ] 필요한 fixture가 `tests/fixtures/` 또는 `tests/conftest.py`에 추가되었는가
- [ ] `poetry run pytest`로 전체 테스트가 통과하는가
