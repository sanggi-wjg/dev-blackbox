---
name: create-test
description: 인프라 의존성 없는 레이어(util, core, client/model 등)의 테스트 코드를 작성합니다. 순수 함수, 유틸리티 클래스, 데코레이터 등을 분석하여 테스트 케이스를 생성합니다.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# create-unit-test

인프라 의존성 없는 레이어의 테스트 코드를 작성하는 스킬.
`util/`, `core/`, `client/model/` 등 DB 연동이 불필요한 모듈의 테스트를 생성한다.

## 대상 레이어

- `dev_blackbox/util/` — 날짜, 마스킹, 분산 락, 멱등성 등
- `dev_blackbox/core/` — 캐시, 암호화, JWT, 상수, Enum 등
- `dev_blackbox/client/model/` — 외부 API Pydantic 모델

## 입력

사용자에게 다음 정보를 확인한다:

1. **대상 파일 경로** (예: `dev_blackbox/util/datetime_util.py`, `dev_blackbox/core/cache.py`)
2. **테스트할 함수/클래스** (전체 또는 특정 지정)

## 함수 분류

대상 모듈의 각 함수/클래스를 분석하여 다음으로 분류한다:

### 순수 함수/클래스 테스트

외부 의존성이 없는 순수 함수 또는 설정값만으로 동작하는 클래스.

- `mocker` 불필요
- 순수 함수는 클래스 없이 독립 테스트 함수로 작성
- 클래스(예: `EncryptService`)는 테스트에서 직접 인스턴스 생성

### Redis 의존 테스트

`CacheService`, `LockService`, 캐시 데코레이터 등 Redis를 사용하는 컴포넌트.

- `fake_redis` fixture 사용 (conftest.py에 정의됨)
- 관련 테스트는 클래스로 그룹화

### Mock 테스트

내부적으로 외부 서비스를 호출하거나 모듈 수준 의존성이 있는 함수.

- `unittest.mock.patch`로 의존성 격리
- `MagicMock(spec=ClassName)` type-safe mock 사용
- 관련 테스트는 클래스로 그룹화

## 생성 산출물

### 테스트 파일 — 소스 디렉토리 구조 미러링

```
dev_blackbox/util/datetime_util.py    → tests/util/datetime_util_test.py
dev_blackbox/core/encrypt.py          → tests/core/encrypt_test.py
dev_blackbox/client/model/jira_api_model.py → tests/client/model/jira_model_test.py
```

## 테스트 코드 구조

### 순수 함수 테스트 템플릿

클래스 없이 독립 함수로 작성한다. 함수가 많으면 논리적 그룹별로 클래스를 사용할 수 있다.

```python
from dev_blackbox.{레이어}.{모듈명} import {함수명}


def test_{함수명}():
    # given
    input_value = ...

    # when
    result = {함수명}(input_value)

    # then
    assert result == expected


def test_{함수명}_{엣지케이스_설명}():
    # given
    input_value = ...

    # when
    result = {함수명}(input_value)

    # then
    assert result == expected
```

### 순수 클래스 테스트 템플릿

설정값을 직접 전달하여 인스턴스를 생성한다.

```python
from dev_blackbox.core.{모듈명} import {클래스명}


def test_{동작_설명}():
    # given
    service = {클래스명}(config_param="test_value")
    input_data = ...

    # when
    result = service.{메서드명}(input_data)

    # then
    assert result == expected
```

### Redis 의존 테스트 템플릿

```python
from redis import Redis

from dev_blackbox.{레이어}.{모듈명} import {함수명}


class {모듈명_PascalCase}Test:

    def test_{동작_설명}(self, fake_redis: Redis):
        # given
        ...

        # when
        result = {함수명}(...)

        # then
        assert result == expected
```

### 데코레이터 테스트 템플릿

```python
from unittest.mock import MagicMock

from redis import Redis

from dev_blackbox.core.{모듈명} import {데코레이터명}
from dev_blackbox.core.const import {CacheKey}, {CacheTTL}


class {데코레이터명_PascalCase}Test:

    def test_{동작_설명}(self, fake_redis: Redis):
        # given
        mock_fn = MagicMock(return_value=expected_value)

        @{데코레이터명}(key={CacheKey}.SOME_KEY, ttl={CacheTTL}.DEFAULT)
        def decorated_fn(*args) -> dict:
            return mock_fn(*args)

        # when
        result = decorated_fn(arg1, arg2)

        # then
        assert result == expected_value
        mock_fn.assert_called_once_with(arg1, arg2)
```

### Mock 테스트 템플릿

```python
from unittest.mock import MagicMock, patch

from dev_blackbox.{레이어}.{모듈명} import {함수명}


class {모듈명_PascalCase}Test:

    def test_{동작_설명}(self):
        # given
        mock_dep = MagicMock()
        mock_dep.{method}.return_value = ...

        with patch("dev_blackbox.{레이어}.{모듈명}.{의존성}", return_value=mock_dep):
            # when
            result = {함수명}(...)

        # then
        assert result == expected
```

### 예외 테스트 템플릿

```python
import pytest

from dev_blackbox.{레이어}.{모듈명} import {함수명}
from dev_blackbox.core.exception import {Exception}


def test_{함수명}_{예외조건}():
    # given
    ...

    # when & then
    with pytest.raises({Exception}):
        {함수명}(invalid_input)
```

### Enum / 상수 테스트 템플릿

```python
from dev_blackbox.core.{모듈명} import {EnumClass}


def test_{enum_설명}():
    # given & when & then
    assert {EnumClass}.VALUE == "expected_string"
    assert len({EnumClass}) == expected_count
```

## 테스트 케이스 설계 원칙

각 함수/클래스에 대해 해당하는 케이스를 검토한다:

### 순수 함수

1. **정상 입력** — 기본 동작 검증
2. **경계값** — 빈 문자열, 0, None, 최솟값/최댓값
3. **엣지 케이스** — 타임존 변환, 날짜 경계 등 도메인 특수 케이스

### 암호화/해싱

1. **암호화 후 복호화** — 원본 데이터 복원 확인
2. **빈 입력** — 빈 문자열 처리
3. **다른 키로 복호화** — 실패 확인 (해당 시)

### 캐시

1. **캐시 미스** — 함수 실행 + 결과 캐시
2. **캐시 히트** — 함수 미실행 + 캐시 반환
3. **TTL 적용** — 만료 시간 검증
4. **캐시 덮어쓰기** — `cache_put` 동작
5. **캐시 삭제** — `cache_evict` 동작

### JWT

1. **토큰 생성/검증** — 정상 페이로드 검증
2. **만료된 토큰** — 예외 발생
3. **잘못된 토큰** — 예외 발생

### Redis 의존 함수

1. **정상 동작** — Redis 사용 가능한 상태에서의 기본 동작
2. **상태 변화** — Redis에 저장된 데이터 검증
3. **Redis 불가용** — graceful degradation 검증 (예외 전파 안 함)
4. **중복 호출** — 멱등성 또는 충돌 검증

### Context Manager / Decorator

1. **정상 진입/탈출** — 블록 내부 실행 확인
2. **예외 발생** — 블록 내부 예외 시 리소스 정리 확인
3. **중첩 호출** — 동일 키로 중첩 호출 시 동작

### Enum / 상수

1. **값 검증** — 각 Enum 멤버의 값 확인
2. **조합 검증** — 리스트 반환 메서드 등

## 컨벤션

- `# given`, `# when`, `# then` 주석으로 구분 (mock이 있으면 `# mock` 또는 `with patch` 블록)
- **`then`에서 `given`의 입력 값을 참조**: 검증 시 리터럴 값을 반복하지 않고, `given`에서 생성한 변수를 참조
- 한글 함수명 사용 가능 (예: `test_락을_획득하면_True를_반환한다`)
- `MagicMock`에는 반드시 `spec=ClassName` 지정 (가능한 경우)
- `unittest.mock.patch` 사용 (pytest-mock 없이도 가능)
  - Redis 의존 함수처럼 `mocker`가 필요한 경우 `pytest-mock`의 `mocker` fixture 사용 가능
- `fake_redis` fixture는 `tests/conftest.py`에 이미 정의되어 있음 — 재정의하지 말 것
- 테스트 실행 후 `poetry run pytest tests/{레이어}/{파일}_test.py -v`로 검증

## 체크리스트

생성 완료 후 다음을 확인한다:

- [ ] 테스트 파일이 소스 디렉토리 구조를 미러링하는가
- [ ] 순수 함수는 클래스 없이 독립 함수로, Redis/Mock 의존은 클래스로 그룹화되었는가
- [ ] 모든 테스트가 `# given`, `# when`, `# then`으로 구분되는가
- [ ] 정상/경계값/엣지 케이스가 포함되었는가
- [ ] Redis 의존 테스트에 `fake_redis` fixture가 사용되었는가
- [ ] Redis 불가용 시 graceful degradation 테스트가 있는가 (해당 시)
- [ ] `poetry run pytest`로 전체 테스트가 통과하는가