# API

REST API 엔드포인트 명세.

> 아키텍처 개요는 [ARCHITECTURE.md](ARCHITECTURE.md) 참고.

## 인증

모든 API 엔드포인트(`/`, `/health` 제외)는 JWT Bearer Token 인증이 필요하다.

1. `POST /api/v1/auth/token`으로 토큰 발급 (OAuth2 Password Grant)
2. 이후 요청에 `Authorization: Bearer <token>` 헤더 포함

### 권한 모델

- **공개**: `/`, `/health` — 인증 불필요
- **사용자**: `/api/v1/*` — `CurrentUser` (유효한 JWT 토큰)
- **관리자**: `/admin-api/v1/*` — `CurrentAdminUser` (JWT 토큰 + `is_admin=True`)

## 엔드포인트 목록

### 공개 엔드포인트

| Method | Path      | 설명   | 상태 코드 |
|--------|-----------|------|-------|
| GET    | `/`       | 루트   | 200   |
| GET    | `/health` | 헬스체크 | 200   |

### 인증 엔드포인트

| Method | Path                 | 설명     | 상태 코드 |
|--------|----------------------|--------|-------|
| POST   | `/api/v1/auth/token` | 토큰 로그인 | 200   |

### 사용자 API (`/api/v1/*`, 인증 필요)

| Method | Path                                     | 설명                 | 상태 코드 |
|--------|------------------------------------------|--------------------|-------|
| GET    | `/api/v1/users/me`                       | 내 정보 조회            | 200   |
| POST   | `/api/v1/github-secrets`                 | GitHub 시크릿 등록      | 201   |
| DELETE | `/api/v1/github-secrets`                 | GitHub 시크릿 삭제      | 204   |
| GET    | `/api/v1/github-events`                  | GitHub 이벤트 조회      | 200   |
| GET    | `/api/v1/jira-users`                     | Jira 사용자 조회        | 200   |
| GET    | `/api/v1/slack-users`                    | Slack 사용자 조회       | 200   |
| GET    | `/api/v1/work-logs`                      | 업무 일지 조회           | 200   |

### 관리자 API (`/admin-api/v1/*`, 관리자 권한 필요)

| Method | Path                             | 설명        | 상태 코드 |
|--------|----------------------------------|-----------|-------|
| GET    | `/admin-api/v1/users`            | 전체 사용자 목록 | 200   |
| POST   | `/admin-api/v1/users`            | 사용자 생성    | 201   |
| DELETE | `/admin-api/v1/users/{user_id}`  | 사용자 삭제    | 204   |

## DTO 상세

### Auth

**`TokenResponseDto`** (Response — `controller/api/dto/token_dto.py`)

| 필드           | 타입  | 설명                 |
|--------------|-----|--------------------|
| access_token | str | JWT 액세스 토큰         |
| token_type   | str | 토큰 타입 (기본: bearer) |

### User (Admin)

**`CreateUserRequestDto`** (Request — `controller/admin/dto/user_dto.py`)

| 필드       | 타입          | 필수 | 설명                                  |
|----------|-------------|:--:|-------------------------------------|
| name     | NotBlankStr | O  | 사용자 이름                              |
| email    | EmailStr    | O  | 이메일                                 |
| password | NotBlankStr | O  | 비밀번호                                |
| timezone | str         | X  | 타임존 (기본: `Asia/Seoul`, ZoneInfo 검증) |

### User (API)

**`UserResponseDto`** (Response — `controller/api/dto/user_dto.py`)

| 필드         | 타입       | 설명     |
|------------|----------|--------|
| id         | int      | 사용자 ID |
| name       | str      | 이름     |
| email      | str      | 이메일    |
| timezone   | str      | 타임존    |
| created_at | datetime | 생성일시   |
| updated_at | datetime | 수정일시   |

**`UserDetailResponseDto`** (Response — `/api/v1/users/me` 응답용)

| 필드                 | 타입                         | 설명            |
|--------------------|----------------------------|---------------|
| id                 | int                        | 사용자 ID        |
| name               | str                        | 이름            |
| email              | str                        | 이메일           |
| timezone           | str                        | 타임존           |
| tz_info            | ZoneInfo                   | 타임존 객체        |
| created_at         | datetime                   | 생성일시          |
| updated_at         | datetime                   | 수정일시          |
| github_user_secret | GitHubSecretResponseDto / null | GitHub 시크릿 정보 |
| jira_user          | JiraUserResponseDto / null | Jira 사용자 정보   |
| slack_user         | SlackUserResponseDto / null | Slack 사용자 정보  |

### GitHub Secret

**`CreateGitHubSecretRequestDto`** (Request)

| 필드                    | 타입          | 필수 | 설명          |
|-----------------------|-------------|:--:|-------------|
| username              | NotBlankStr | O  | GitHub 사용자명 |
| personal_access_token | NotBlankStr | O  | GitHub PAT  |
| user_id               | int         | O  | 사용자 ID      |

**`GitHubSecretResponseDto`** (Response)

| 필드        | 타입   | 설명          |
|-----------|------|-------------|
| id        | int  | 시크릿 ID      |
| username  | str  | GitHub 사용자명 |
| user_id   | int  | 사용자 ID      |
| is_active | bool | 활성 상태       |

### GitHub Event

**`GitHubEventResponseDto`** (Response)

| 필드          | 타입          | 설명            |
|-------------|-------------|---------------|
| id          | int         | 이벤트 ID        |
| event_id    | str         | GitHub 이벤트 ID |
| target_date | date        | 수집 대상 날짜      |
| event       | dict        | 이벤트 원본 데이터    |
| commit      | dict / null | 커밋 상세 데이터     |

**`CollectGitHubRequestDto`** (Request — 수집 API용)

| 필드          | 타입          | 필수 | 설명                     |
|-------------|-------------|:--:|------------------------|
| target_date | date / null | X  | 수집 대상 날짜 (null: 어제 날짜) |

**`MinimumGitHubEventResponseDto`** (Response — 수집 API 응답용)

| 필드          | 타입   | 설명            |
|-------------|------|---------------|
| id          | int  | 이벤트 ID        |
| event_id    | str  | GitHub 이벤트 ID |
| target_date | date | 수집 대상 날짜      |

## 서비스 모델

### UserModel

인증된 사용자 정보를 담는 서비스 계층 모델 (보안 설정에서 사용).

| 필드         | 타입       | 설명       |
|------------|----------|----------|
| id         | int      | 사용자 ID   |
| name       | str      | 이름       |
| email      | str      | 이메일      |
| timezone   | str      | 타임존      |
| tz_info    | ZoneInfo | 타임존 객체   |
| is_admin   | bool     | 관리자 여부   |
| created_at | datetime | 생성일시     |
| updated_at | datetime | 수정일시     |

### UserWithPlatformInfoModel

User 엔티티와 플랫폼 연동 정보를 통합한 서비스 계층 모델.

| 필드                 | 타입                            | 설명            |
|--------------------|-------------------------------|---------------|
| id                 | int                           | 사용자 ID        |
| name               | str                           | 이름            |
| email              | str                           | 이메일           |
| timezone           | str                           | 타임존           |
| tz_info            | ZoneInfo                      | 타임존 객체        |
| created_at         | datetime                      | 생성일시          |
| updated_at         | datetime                      | 수정일시          |
| github_user_secret | GitHubUserSecretModel / null  | GitHub 시크릿 정보 |
| jira_user          | JiraUserModel / null          | Jira 사용자 정보   |
| slack_user         | SlackUserModel / null         | Slack 사용자 정보  |

## 커스텀 타입

| 타입          | 정의                                                                       | 설명               |
|-------------|--------------------------------------------------------------------------|------------------|
| NotBlankStr | `Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]` | 공백 제거 후 최소 1자 이상 |

## 예외 처리

### 예외 계층

```
ServiceException (500)
├── GitHubUserSecretAlreadyExistException
├── GitHubUserSecretNotSetException
├── JiraUserNotAssignedException
├── JiraUserProjectNotAssignedException
├── SlackUserNotAssignedException
├── SlackClientException
├── IdempotentRequestException
│   ├── ConflictRequestException
│   └── CompletedRequestException
├── NoSlackChannelsFound
└── EntityNotFoundException (404)
    ├── UserNotFoundException
    ├── GitHubUserSecretNotFoundException
    ├── JiraUserNotFoundException
    └── SlackUserByIdNotFoundException
```

- `exception_handler.py`에서 FastAPI에 핸들러 등록
- 각 예외는 적절한 HTTP 상태 코드로 변환
- 인증/인가 관련 에러는 FastAPI `HTTPException`으로 처리 (401, 403)

### 에러 응답 형식

```json
{
  "status": "404 NOT_FOUND",
  "error": "Entity Not Found",
  "message": "User not found by 1",
  "path": "/api/v1/users/me",
  "requestedAt": "2025-01-01T00:00:00+00:00"
}
```

| 예외                         | HTTP 상태 | 설명         |
|----------------------------|---------|------------|
| RequestValidationError     | 400     | 요청 검증 실패   |
| HTTPException (인증 실패)      | 401     | 인증 실패      |
| HTTPException (권한 부족)      | 403     | 관리자 권한 필요  |
| EntityNotFoundException    | 404     | 엔티티 미발견    |
| ConflictRequestException   | 409     | 요청 처리 중    |
| CompletedRequestException  | 422     | 이미 처리된 요청  |
| ServiceException           | 500     | 서비스 에러     |
| Exception (기타)             | 500     | 예상치 못한 에러  |
