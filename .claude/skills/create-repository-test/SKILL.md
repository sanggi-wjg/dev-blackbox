---
name: create-repository-test
description: Repository 레이어의 테스트 코드를 작성합니다. 대상 Repository의 CRUD 메서드를 분석하여 DB 연동 테스트를 생성합니다.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# create-repository-test

Repository 레이어(`dev_blackbox/storage/rds/repository/`)의 테스트 코드를 작성하는 스킬.
대상 Repository의 메서드를 분석하여 실제 DB(Testcontainers) 기반 테스트를 생성한다.

## 입력

사용자에게 다음 정보를 확인한다:

1. **대상 Repository 파일 경로** (예: `dev_blackbox/storage/rds/repository/user_repository.py`)
2. **테스트할 메서드** (전체 또는 특정 메서드 지정)

## 특징

- **모든 테스트는 실제 DB 연동**. Mock 없이 Testcontainers PostgreSQL로 테스트한다.
- `db_session` fixture (function scope) — 테스트마다 새 세션, 종료 시 자동 롤백.
- `*_fixture` — Entity 팩토리 fixture (conftest.py에 정의됨).
- SQLAlchemy Identity Map 덕분에 같은 세션 내 조회 결과는 `==`로 객체 참조 비교 가능.

## 생성 산출물

### 1. 테스트 파일 — `tests/storage/rds/{리포지토리명}_test.py`

소스 디렉토리 구조를 미러링하여 배치한다.

```
dev_blackbox/storage/rds/repository/user_repository.py
→ tests/storage/rds/user_repository_test.py
```

### 2. conftest fixture (필요 시) — `tests/conftest.py`

테스트에 필요한 Entity 팩토리 fixture가 conftest.py에 없으면 추가한다.
기존 `user_fixture` 패턴을 따른다.

```python
@pytest.fixture()
def {entity}_fixture(
    db_session: Session,
) -> Callable[..., {Entity}]:

    def _create(
        # FK 등 필수 파라미터
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
class {리포지토리명}Test:  # 예: UserRepositoryTest

    def test_{메서드명}(self, ...):  # 정상 케이스

    def test_{메서드명}_{조건}_한글설명(self, ...):  # 엣지/예외 케이스
```

### find_by_* 테스트 템플릿

```python
def test_find_by_id(
    self,
    db_session,
    user_fixture,
):
    # given
    repository = {Repository}(db_session)
    user = user_fixture()

    # when
    result = repository.find_by_id(user.id)

    # then
    assert result == user
```

### find_all_by_* 테스트 템플릿

```python
def test_find_all_by_user_id(
    self,
    db_session,
    user_fixture,
    {entity}_fixture,
):
    # given
    repository = {Repository}(db_session)
    user = user_fixture()
    entity1 = {entity}_fixture(user_id=user.id)
    entity2 = {entity}_fixture(user_id=user.id, ...)

    # when
    result = repository.find_all_by_user_id(user.id)

    # then
    assert result == [entity1, entity2]
```

### save 테스트 템플릿

```python
def test_save(
    self,
    db_session,
    user_fixture,
):
    # given
    repository = {Repository}(db_session)
    user = user_fixture()
    entity = {Entity}.create(user_id=user.id, ...)

    # when
    result = repository.save(entity)

    # then
    assert result.id is not None
    assert result.user_id == user.id
```

### save_all 테스트 템플릿

```python
def test_save_all(
    self,
    db_session,
    user_fixture,
):
    # given
    repository = {Repository}(db_session)
    user = user_fixture()
    entities = [
        {Entity}.create(user_id=user.id, ...),
        {Entity}.create(user_id=user.id, ...),
    ]

    # when
    result = repository.save_all(entities)

    # then
    assert len(result) == 2
    assert all(e.id is not None for e in result)
```

### delete_by_* 테스트 템플릿

```python
def test_delete_by_user_id(
    self,
    db_session,
    user_fixture,
    {entity}_fixture,
):
    # given
    repository = {Repository}(db_session)
    user = user_fixture()
    {entity}_fixture(user_id=user.id)

    # when
    repository.delete_by_user_id(user.id)

    # then
    result = repository.find_all_by_user_id(user.id)
    assert result == []
```

### SoftDelete 조회 테스트 템플릿

```python
def test_find_by_id_삭제된_엔티티는_조회되지_않는다(
    self,
    db_session,
    {entity}_fixture,
):
    # given
    repository = {Repository}(db_session)
    entity = {entity}_fixture(...)
    entity.delete()
    db_session.flush()

    # when
    result = repository.find_by_id(entity.id)

    # then
    assert result is None
```

### 빈 결과 테스트 템플릿

```python
def test_find_by_id_존재하지_않으면_None을_반환한다(self, db_session):
    # given
    repository = {Repository}(db_session)

    # when
    result = repository.find_by_id(9999)

    # then
    assert result is None
```

## 테스트 케이스 설계 원칙

### find_by_* (단건 조회)

1. **정상 조회** — Entity가 있으면 반환
2. **존재하지 않음** — `None` 반환
3. **SoftDelete** — 삭제된 Entity는 조회 안 됨 (해당 시)

### find_all_by_* (목록 조회)

1. **정상 조회** — 여러 Entity 반환, 순서 검증
2. **빈 결과** — 데이터 없으면 빈 리스트
3. **필터링 검증** — 조건에 맞지 않는 데이터도 함께 생성하여 필터 동작 확인
4. **정렬 검증** — 정렬 기준이 있으면 순서 확인

### save / save_all

1. **정상 저장** — id가 생성되고 필드 값 유지
2. **FK 제약 검증** — 참조 Entity가 존재해야 저장 가능 (필요 시)

### delete_by_*

1. **정상 삭제** — 삭제 후 조회 시 빈 결과
2. **대상 없음** — 삭제 대상이 없어도 예외 없이 완료

### exists_by_*

1. **존재함** — `True` 반환
2. **존재하지 않음** — `False` 반환

## 컨벤션

- `# given`, `# when`, `# then` 주석으로 구분
- **`then`에서 `given`의 입력 값을 참조**: fixture에서 생성한 Entity의 필드를 참조
- 한글 함수명 사용 가능 (예: `test_find_by_id_삭제된_엔티티는_조회되지_않는다`)
- `db_session` 내 조회 결과는 SQLAlchemy Identity Map 덕분에 `==`로 객체 비교
- 모든 테스트는 `{Repository}Test` 클래스로 그룹화
- fixture 생성 시 UNIQUE 제약조건 충돌을 피하도록 파라미터 분리 (예: 다른 email 사용)
- 테스트 실행 후 `poetry run pytest tests/storage/rds/{파일}_test.py -v`로 검증

## 체크리스트

생성 완료 후 다음을 확인한다:

- [ ] 테스트 파일이 `tests/storage/rds/{리포지토리명}_test.py`에 배치되었는가
- [ ] 클래스명이 `{리포지토리명}Test` 패턴인가
- [ ] 모든 테스트가 `# given`, `# when`, `# then`으로 구분되는가
- [ ] 각 메서드에 정상/빈 결과/필터링 케이스가 있는가
- [ ] SoftDelete Entity의 조회 테스트에 삭제 케이스가 있는가 (해당 시)
- [ ] 필요한 fixture가 `tests/conftest.py`에 추가되었는가
- [ ] `poetry run pytest`로 전체 테스트가 통과하는가
