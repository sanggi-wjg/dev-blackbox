---
name: create-endpoint
description: 새로운 API 엔드포인트를 생성합니다. Controller, DTO, Param, 라우터 등록까지 컨벤션에 맞게 생성합니다.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# create-endpoint

새로운 API 엔드포인트를 생성하는 스킬.
Controller, Request/Response DTO, Query Param, 라우터 등록까지 프로젝트 컨벤션에 맞게 생성한다.

## 입력

사용자에게 다음 정보를 확인한다:

1. **리소스명** (kebab-case, 예: `github-events`)
2. **API 유형** — 사용자 API (`/api/v1/*`) 또는 관리자 API (`/admin-api/v1/*`)
3. **엔드포인트 목록** — HTTP 메서드, 경로, 설명, 상태 코드
4. **Request DTO 필드** (POST/PUT/PATCH 엔드포인트인 경우)
5. **Response DTO 필드** (응답이 있는 경우)
6. **Query Parameter** (GET 엔드포인트의 필터가 필요한 경우)
7. **사용할 Service 클래스** (기존 Service 또는 새로 생성할 Service)

## 사전 확인

생성 전에 반드시 다음 파일을 읽고 참고한다:

1. **기존 유사 Controller** — 동일 도메인이나 유사 패턴의 Controller 참고
2. **사용할 Service** — Service 메서드 시그니처 확인
3. **관련 Entity** — `from_entity()` DTO 변환에 필요한 필드 확인
4. **`main.py`** — 라우터 등록 위치 확인
5. **`core/exception.py`** — 필요한 예외 클래스 확인

## 생성 산출물

다음 파일들을 순서대로 생성/수정한다:

### 1. Controller — `dev_blackbox/controller/api/{리소스}_controller.py`

사용자 API는 `controller/api/`에, 관리자 API는 `controller/admin/`에 배치한다.

#### 사용자 API Controller 템플릿

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.{리소스}_dto import (
    {리소스}ResponseDto,
    Create{리소스}RequestDto,  # POST가 있는 경우
)
from dev_blackbox.controller.api.param.{리소스}_param import {리소스}Param  # Query Parameter가 있는 경우
from dev_blackbox.controller.config.security_config import AuthToken, CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.service.{서비스}_service import {서비스}Service
from dev_blackbox.service.command.{리소스}_command import Create{리소스}Command  # POST가 있는 경우
from dev_blackbox.service.query.{리소스}_query import {리소스}Query  # Query 객체가 있는 경우

router = APIRouter(prefix="/api/v1/{리소스-kebab}", tags=["{태그명}"])


@router.get(
    "",
    response_model=list[{리소스}ResponseDto],
)
async def get_{리소스들}(
    token: AuthToken,
    current_user: CurrentUser,
    param: Annotated[{리소스}Param, Query()],
    db: Session = Depends(get_db),
):
    service = {서비스}Service(db)
    query = {리소스}Query(user_id=current_user.id, ...)
    entities = service.get_{리소스들}(query)
    return [{리소스}ResponseDto.from_entity(entity) for entity in entities]


@router.post(
    "",
    response_model={리소스}ResponseDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_{리소스}(
    request: Create{리소스}RequestDto,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = {서비스}Service(db)
    command = Create{리소스}Command(
        user_id=current_user.id,
        ...  # request 필드를 command로 변환
    )
    entity = service.create_{리소스}(command)
    return {리소스}ResponseDto.from_entity(entity)


@router.delete(
    "/{entity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_{리소스}(
    {entity_id}: int,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = {서비스}Service(db)
    service.delete_{리소스}(current_user.id, {entity_id})
```

#### 관리자 API Controller 템플릿

```python
from dev_blackbox.controller.config.security_config import CurrentAdminUser

router = APIRouter(prefix="/admin-api/v1/{리소스-kebab}", tags=["Admin {태그명}"])


@router.get(...)
async def get_{리소스들}(
    current_admin_user: CurrentAdminUser,  # token 불필요, CurrentAdminUser만 사용
    db: Session = Depends(get_db),
):
    ...
```

#### Controller 컨벤션

- `router` 변수명 고정 (main.py에서 alias로 import)
- 엔드포인트 함수는 `async def`
- 함수 파라미터 순서는 유동적이나 일반적으로: `path_param` / `request`(Body) → `token` → `current_user` → `param`(Query) → `db`
- 관리자 API는 `token: AuthToken` 없이 `current_admin_user: CurrentAdminUser`만 사용
- Service는 엔드포인트 함수 내에서 `{Service}(db)`로 생성
- DTO → Command/Query 변환은 Controller에서 수행
- Entity → DTO 변환도 Controller에서 수행 (`DTO.from_entity()`)
- 삭제 엔드포인트는 `response_model=None` 명시
- `status` import는 `from fastapi import status` 또는 `from starlette import status` 모두 허용 (기존 파일의 스타일을 따를 것)

### 2. Response DTO — `dev_blackbox/controller/api/dto/{리소스}_dto.py`

DTO 파일에 Request/Response DTO를 함께 정의한다.

```python
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.{테이블명} import {엔티티명}


class {리소스}ResponseDto(BaseModel):
    id: int
    # 비즈니스 필드들...
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: {엔티티명}) -> {리소스}ResponseDto:
        return cls(
            id=entity.id,
            # 필드 매핑...
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
```

#### Request DTO (POST/PUT/PATCH가 있는 경우)

```python
from dev_blackbox.core.types import NotBlankStr


class Create{리소스}RequestDto(BaseModel):
    field1: NotBlankStr
    field2: str
    optional_field: str | None = None
```

#### DTO 컨벤션

- 파일 최상단에 `from __future__ import annotations` 선언
- Entity import는 `TYPE_CHECKING` 블록 안에 배치 (순환 참조 방지)
- Response DTO에 `from_entity()` 클래스 메서드 필수
- 암호화된 필드가 있으면 `from_entity(entity, encrypt_service)` 시그니처 사용
- 민감 정보 마스킹이 필요하면 `@field_validator`로 `mask()` 적용
- Request DTO의 필수 문자열 필드는 `NotBlankStr` 타입 사용
- `from_entity()` 반환 타입은 클래스명 문자열이 아닌 클래스 직접 참조 (파일 상단 `from __future__ import annotations` 덕분에 가능)

### 3. Query Parameter (GET 필터가 필요한 경우) — `dev_blackbox/controller/api/param/{리소스}_param.py`

```python
from datetime import date

from pydantic import BaseModel, Field


class {리소스}Param(BaseModel):
    target_date: date = Field(..., description="조회 대상 날짜 (YYYY-MM-DD)")
    optional_filter: str | None = Field(default=None, description="필터 설명")
```

#### Param 컨벤션

- 필수 필드는 `Field(...)`, 선택 필드는 `Field(default=None)`
- `description`에 한국어 설명 포함 (OpenAPI 문서용)
- Controller에서 `Annotated[{리소스}Param, Query()]`로 바인딩 (`Depends()` 금지)

### 4. 라우터 등록 — `main.py`

```python
# import 추가 (알파벳순 또는 도메인 그룹 기준)
from dev_blackbox.controller.api.{리소스}_controller import router as {리소스}_router

# Api 섹션에 추가
app.include_router({리소스}_router)
```

#### 등록 컨벤션

- import 시 `as {리소스}_router` alias 사용
- 사용자 API는 `# Api` 섹션에, 관리자 API는 `# Admin` 섹션에 추가
- 같은 도메인의 라우터는 인접하게 배치

## 엔드포인트 유형별 가이드

### GET (목록 조회)

- `response_model=list[{Dto}]` — 목록 반환
- Query Parameter로 필터링 조건 전달
- Service에 Query 객체 전달
- 상태 코드: 200 (기본값, 생략 가능)

### GET (단건 조회)

- `response_model={Dto} | None` — 없을 수 있는 경우
- `response_model={Dto}` — 없으면 예외 발생하는 경우
- Path Parameter로 ID 전달

### POST (생성)

- `status_code=status.HTTP_201_CREATED`
- Request Body → Command 변환 후 Service 호출
- 생성된 Entity → Response DTO 변환

### PATCH (부분 수정)

- `status_code=status.HTTP_204_NO_CONTENT`, `response_model=None`
- 또는 수정된 Entity를 반환하는 경우 200 + Response DTO

### DELETE (삭제)

- `status_code=status.HTTP_204_NO_CONTENT`, `response_model=None`
- `return None` 명시 또는 반환문 생략

### POST (비동기 작업 트리거)

- `status_code=status.HTTP_202_ACCEPTED`
- `BackgroundTasks`로 비동기 실행
- 멱등성 키가 필요한 경우 `Idempotency-Key` 헤더 처리

## 실행 절차

```
1. 엔드포인트 설계 확인     → 검증: HTTP 메서드, 경로, 상태 코드가 RESTful한가
2. DTO 생성               → 검증: from_entity() 변환이 올바른가
3. Param 생성 (필요 시)    → 검증: Query Parameter 바인딩이 Annotated[..., Query()]인가
4. Controller 생성         → 검증: 파라미터 순서, Service 생성, DTO 변환이 컨벤션에 맞는가
5. main.py 라우터 등록     → 검증: import alias, 섹션 위치가 올바른가
6. 포맷팅/타입 체크         → 검증: black, pyright 통과
```

## 체크리스트

생성 완료 후 다음을 확인한다:

- [ ] Controller 파일이 `controller/api/` 또는 `controller/admin/`에 배치되었는가
- [ ] `router` 변수명이 사용되었는가
- [ ] 엔드포인트 함수가 `async def`인가
- [ ] 인증이 `CurrentUser` 또는 `CurrentAdminUser`로 처리되는가
- [ ] Query Parameter가 `Annotated[Param, Query()]`로 바인딩되었는가 (`Depends()` 미사용)
- [ ] Service가 엔드포인트 함수 내에서 `Service(db)`로 생성되었는가
- [ ] DTO에 `from_entity()` 클래스 메서드가 있는가
- [ ] Entity import가 `TYPE_CHECKING` 블록 안에 있는가
- [ ] 삭제 엔드포인트에 `response_model=None`이 명시되었는가
- [ ] `main.py`에 라우터가 등록되었는가
- [ ] `pyright`와 `black` 검사를 통과하는가
