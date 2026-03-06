---
name: create-controller-test
description: Controller 레이어의 테스트 코드를 작성합니다. FastAPI TestClient를 사용한 통합 테스트로, 엔드포인트의 라우팅, DTO 변환, 상태 코드, 예외 처리를 검증합니다.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# create-controller-test

Controller 레이어의 통합 테스트를 작성하는 스킬.
FastAPI `TestClient` + Testcontainers로 실제 DB를 사용하며, 인증은 `dependency_overrides`로 우회한다.

## 입력

사용자에게 다음 정보를 확인한다:

1. **대상 Controller 파일 경로** (예: `dev_blackbox/controller/api/task_controller.py`)
2. **테스트할 엔드포인트** (전체 또는 특정 엔드포인트 지정)

## 사전 확인

테스트 작성 전에 반드시 다음 파일을 읽고 분석한다:

1. **대상 Controller** — 엔드포인트, DTO, 파라미터, Service 호출 구조
2. **관련 DTO** (`controller/api/dto/`, `controller/admin/dto/`) — 요청/응답 필드
3. **관련 Param** (`controller/api/param/`) — Query Parameter 구조
4. **관련 Service** — 비즈니스 로직, 예외 발생 조건
5. **관련 Entity** — 팩토리 메서드, 필드 구조
6. **exception_handler.py** — 예외별 HTTP 상태 코드 매핑 확인

## conftest 계층 구조

테스트에서 사용하는 fixture는 3개의 conftest에 계층적으로 정의되어 있다.
각 conftest의 역할을 이해하고, 적절한 fixture를 사용한다.

### `tests/conftest.py` — 전역 fixture

- **DB 인프라**: `test_engine`, `db_session_factory`, `db_session` (Testcontainers PostgreSQL)
- **Entity fixture**: `user_fixture`, `task_fixture`, `slack_user_fixture`, `slack_secret_fixture` 등
- **Redis**: `fake_redis` (fakeredis, session scope, autouse)
- Entity fixture는 평문 파라미터를 받아 내부에서 암호화/해싱 처리 후 DB에 저장한다

### `tests/controller/conftest.py` — Controller 공통 fixture

- **`client`**: `TestClient(app)`, session scope
- 인증이 불필요한 공개 엔드포인트(`/`, `/health`) 테스트에서 사용

### `tests/controller/api/conftest.py` — 인증 API 전용 fixture

- **`authenticated_user`**: 테스트용 User 생성 후 `AuthenticatedUser` 반환
- **`_override_dependencies`** (autouse): `get_db`를 테스트 DB 세션으로, `get_current_user`를 `authenticated_user`로 교체
- **`auth_client`**: `Authorization: Bearer fake-token` 헤더가 설정된 TestClient

## 엔드포인트 분류

### 사용자 API (`/api/v1/*`)

- `auth_client` + `authenticated_user` fixture 사용
- 테스트 파일: `tests/controller/api/{컨트롤러명}_test.py`

### 관리자 API (`/admin-api/v1/*`)

- 관리자 권한이 필요하므로 `_override_dependencies`에서 `get_current_admin_user`도 override 필요
- 테스트 파일: `tests/controller/admin/{컨트롤러명}_test.py`
- 필요 시 `tests/controller/admin/conftest.py`에 관리자용 fixture 추가

### 공개 API (`/`, `/health`)

- `client` fixture만 사용 (인증 불필요)
- 테스트 파일: `tests/controller/{컨트롤러명}_test.py`

## 생성 산출물

### 테스트 파일

소스 디렉토리 구조를 미러링하여 배치한다.

```
dev_blackbox/controller/api/task_controller.py
→ tests/controller/api/task_controller_test.py

dev_blackbox/controller/admin/user_admin_controller.py
→ tests/controller/admin/user_admin_controller_test.py
```

## 테스트 코드 구조

### 클래스/함수 네이밍

```python
class {컨트롤러명}Test:  # 예: TaskControllerTest

    def test_{동작_설명}(self, ...):  # 정상 케이스

    def test_{조건}

    _
    {결과_설명}(self, ...):  # 엣지/예외 케이스
```

### 조회 엔드포인트 (GET) 템플릿

```python
def test_{리소스}


_목록_조회(
    self,
    auth_client: TestClient,
authenticated_user: AuthenticatedUser,
{entity}
_fixture,
):
# given
{entity}
_fixture(user_id=authenticated_user.id, ...)

# when
response = auth_client.get("/api/v1/{리소스}")

# then
assert response.status_code == 200
data = response.json()
assert len(data) == 1
assert data[0]["{필드}"] == expected_value
```

### 생성 엔드포인트 (POST) 템플릿

```python
def test_{리소스}


_생성(
    self,
    auth_client: TestClient,
authenticated_user: AuthenticatedUser,
):
# given
request_body = {
    "title": "새 항목",
    ...
}

# when
response = auth_client.post("/api/v1/{리소스}", json=request_body)

# then
assert response.status_code == 201
data = response.json()
assert data["title"] == request_body["title"]
```

### 수정 엔드포인트 (PUT/PATCH) 템플릿

```python
def test_{리소스}


_수정(
    self,
    auth_client: TestClient,
authenticated_user: AuthenticatedUser,
{entity}
_fixture,
):
# given
entity = {entity}
_fixture(user_id=authenticated_user.id, ...)
request_body = {
    "title": "수정된 제목",
    ...
}

# when
response = auth_client.put(f"/api/v1/{리소스}/{entity.id}", json=request_body)

# then
assert response.status_code == 200
data = response.json()
assert data["title"] == request_body["title"]
```

### 삭제 엔드포인트 (DELETE) 템플릿

```python
def test_{리소스}


_삭제(
    self,
    auth_client: TestClient,
authenticated_user: AuthenticatedUser,
{entity}
_fixture,
):
# given
entity = {entity}
_fixture(user_id=authenticated_user.id)

# when
response = auth_client.delete(f"/api/v1/{리소스}/{entity.id}")

# then
assert response.status_code == 204
```

### 예외 케이스 템플릿

```python
def test_존재하지_않는_{리소스}


_수정시_404(self, auth_client: TestClient):
# given
request_body = {...}

# when
response = auth_client.put("/api/v1/{리소스}/999999", json=request_body)

# then
assert response.status_code == 404
```

## 테스트 케이스 설계 원칙

각 엔드포인트에 대해 다음 케이스를 검토한다:

### GET (조회)

1. **정상 조회** — 데이터가 있으면 반환
2. **빈 결과** — 데이터가 없으면 빈 리스트 (목록 조회 시)
3. **필터링 검증** — Query Parameter 필터가 동작하는지 확인
4. **DTO 변환 검증** — 응답 필드가 올바르게 매핑되는지 확인

### POST (생성)

1. **정상 생성** — 201 + 응답 필드 검증
2. **필수 필드 누락** — 422 (FastAPI 자동 검증)

### PUT/PATCH (수정)

1. **정상 수정** — 200 + 수정된 필드 검증
2. **존재하지 않는 리소스** — 404
3. **상태 변경 검증** — archive/unarchive 등

### DELETE (삭제)

1. **정상 삭제** — 204
2. **존재하지 않는 리소스** — 404

### 비즈니스 예외

- exception_handler.py의 매핑을 확인하여 정확한 상태 코드를 검증한다
- 예외 조건을 fixture로 재현한다 (예: secret mismatch, not assigned 등)

## 주의사항

### DTO에서 암호화/복호화가 있는 경우

`SlackUserResponseDto.from_entity()`처럼 DTO 변환 시 `EncryptService.decrypt()`를 호출하는 경우,
테스트 데이터도 암호화되어 저장되어야 한다.
`tests/conftest.py`의 Entity fixture가 내부에서 암호화 처리를 하므로 해당 fixture를 사용한다.

### `authenticated_user` 파라미터

`authenticated_user`를 직접 참조하지 않는 테스트에서도, `_override_dependencies`(autouse)가
이 fixture에 의존하므로 fixture 체인이 정상 동작한다.
`user_id`가 필요한 경우 `authenticated_user.id`로 접근한다.

### 예외 상태 코드 확인

예외별 HTTP 상태 코드를 추측하지 말고, 반드시 `controller/config/exception_handler.py`를 확인한다.
`ServiceException` 하위 예외라고 모두 500이 아니며, 개별 핸들러로 다른 상태 코드가 매핑될 수 있다.

## 컨벤션

- `# given`, `# when`, `# then` 주석으로 구분
- **`then`에서 `given`의 입력 값을 참조**: 검증 시 리터럴 값을 반복하지 않고, `given`의 변수(`request_body` 등)를 참조
    ```python
    # given
    request_body = {"title": "새 태스크", ...}

    # then
    # Good — given의 변수를 참조
    assert data["title"] == request_body["title"]

    # Bad — 리터럴 값을 반복
    assert data["title"] == "새 태스크"
    ```
- 한글 함수명 사용 가능 (예: `test_존재하지_않는_태스크_수정시_404`)
- `auth_client`에 `TestClient` 타입 힌트 명시
- `authenticated_user`에 `AuthenticatedUser` 타입 힌트 명시
- 테스트 실행 후 `poetry run pytest tests/controller/{경로}_test.py -v`로 검증

## 체크리스트

생성 완료 후 다음을 확인한다:

- [ ] 테스트 파일이 소스 디렉토리 구조를 미러링하는가
- [ ] 클래스명이 `{컨트롤러명}Test` 패턴인가
- [ ] 모든 테스트가 `# given`, `# when`, `# then`으로 구분되는가
- [ ] `auth_client`를 사용하여 인증 헤더를 중복 작성하지 않는가
- [ ] GET 엔드포인트에 정상/빈 결과/필터링 케이스가 있는가
- [ ] POST/PUT 엔드포인트에 정상/예외 케이스가 있는가
- [ ] DELETE 엔드포인트에 정상/존재하지 않는 리소스 케이스가 있는가
- [ ] 예외 상태 코드가 exception_handler.py의 매핑과 일치하는가
- [ ] 암호화/복호화가 필요한 DTO는 암호화된 fixture 데이터를 사용하는가
- [ ] `poetry run pytest`로 전체 테스트가 통과하는가
