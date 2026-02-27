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

| Method | Path                                  | 설명                | 상태 코드   |
|--------|---------------------------------------|-------------------|---------|
| GET    | `/api/v1/users/me`                    | 내 정보 조회           | 200     |
| POST   | `/api/v1/github-secrets`              | GitHub 시크릿 등록     | 201     |
| DELETE | `/api/v1/github-secrets`              | GitHub 시크릿 삭제     | 204     |
| GET    | `/api/v1/github-events`               | GitHub 이벤트 조회     | 200     |
| GET    | `/api/v1/jira-secrets`                | Jira 시크릿 목록 조회    | 200     |
| GET    | `/api/v1/jira-users`                  | Jira 사용자 조회       | 200     |
| PATCH  | `/api/v1/jira-users`                  | Jira 사용자 할당       | 204     |
| DELETE | `/api/v1/jira-users/{jira_user_id}`   | Jira 사용자 할당 해제    | 204     |
| GET    | `/api/v1/slack-secrets`               | Slack 시크릿 목록 조회   | 200     |
| GET    | `/api/v1/slack-users`                 | Slack 사용자 조회      | 200     |
| PATCH  | `/api/v1/slack-users/{slack_user_id}` | Slack 사용자 할당      | 204     |
| DELETE | `/api/v1/slack-users/{slack_user_id}` | Slack 사용자 할당 해제   | 204     |
| GET    | `/api/v1/work-logs/platforms`         | 플랫폼별 업무 일지 조회     | 200     |
| GET    | `/api/v1/work-logs/user-content`      | 사용자 직접 입력 조회      | 200/204 |
| PUT    | `/api/v1/work-logs/user-content`      | 사용자 직접 입력 생성/수정   | 200/201 |
| GET    | `/api/v1/work-logs/daily`             | 일일 통합 업무 일지 조회    | 200     |
| POST   | `/api/v1/work-logs/manual-sync`       | 수동 동기화 (멱등성 키 필요) | 202     |

### 관리자 API (`/admin-api/v1/*`, 관리자 권한 필요)

| Method | Path                                               | 설명             | 상태 코드 |
|--------|----------------------------------------------------|----------------|-------|
| GET    | `/admin-api/v1/users`                              | 전체 사용자 목록      | 200   |
| POST   | `/admin-api/v1/users`                              | 사용자 생성         | 201   |
| DELETE | `/admin-api/v1/users/{user_id}`                    | 사용자 삭제         | 204   |
| GET    | `/admin-api/v1/jira-secrets`                       | Jira 시크릿 목록 조회 | 200   |
| POST   | `/admin-api/v1/jira-secrets`                       | Jira 시크릿 등록    | 201   |
| DELETE | `/admin-api/v1/jira-secrets/{jira_secret_id}`      | Jira 시크릿 삭제    | 204   |
| POST   | `/admin-api/v1/jira-secrets/{jira_secret_id}/sync` | Jira 사용자 동기화   | 200   |
| GET    | `/admin-api/v1/slack-secrets`                       | Slack 시크릿 목록 조회 | 200   |
| POST   | `/admin-api/v1/slack-secrets`                       | Slack 시크릿 등록    | 201   |
| DELETE | `/admin-api/v1/slack-secrets/{slack_secret_id}`     | Slack 시크릿 삭제    | 204   |
| POST   | `/admin-api/v1/slack-secrets/{slack_secret_id}/sync` | Slack 사용자 동기화  | 200   |

## DTO

DTO 필드 상세는 `controller/api/dto/`, `controller/admin/dto/` 코드 참고.

### 멱등성 (Idempotency)

`POST /api/v1/work-logs/manual-sync`는 `Idempotency-Key` 헤더가 필수이다.

- 최초 요청: `PROCESSING` 마킹 후 백그라운드 작업 시작 (202)
- 중복 요청 (처리 중): `ConflictRequestException` (409)
- 중복 요청 (완료됨): `CompletedRequestException` (422 + 캐시된 응답)
- TTL: 300초 (5분)

## 예외 처리

### 예외 계층

```
ServiceException (500)
├── GitHubUserSecretAlreadyExistException
├── GitHubUserSecretNotSetException
├── JiraUserSecretMismatchException
├── JiraUserNotAssignedException
├── JiraUserProjectNotAssignedException
├── SlackUserSecretMismatchException
├── SlackUserNotAssignedException
├── SlackClientException
├── NoSlackChannelsFound
├── IdempotentRequestException
│   ├── ConflictRequestException
│   └── CompletedRequestException
└── EntityNotFoundException (404)
    ├── UserNotFoundException
    ├── GitHubUserSecretNotFoundException
    ├── JiraSecretNotFoundException
    ├── JiraUserNotFoundException
    ├── SlackSecretNotFoundException
    └── SlackUserNotFoundException
```

- `controller/config/exception_handler.py`에서 FastAPI에 핸들러 등록
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
