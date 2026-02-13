# API

REST API 엔드포인트 명세.

> 아키텍처 개요는 [ARCHITECTURE.md](ARCHITECTURE.md) 참고.

## 엔드포인트 목록

| Method | Path                              | 설명                 | 상태 코드 |
|--------|-----------------------------------|--------------------|-------|
| GET    | `/`                               | 루트                 | 200   |
| GET    | `/health`                         | 헬스체크               | 200   |
| POST   | `/users`                          | 사용자 생성             | 201   |
| GET    | `/users/{user_id}`                | 사용자 조회             | 200   |
| GET    | `/users`                          | 전체 사용자 목록          | 200   |
| POST   | `/github-secrets`                 | GitHub 시크릿 등록      | 201   |
| GET    | `/github-secrets/users/{user_id}` | 사용자별 GitHub 시크릿 조회 | 200   |
| POST   | `/collect/github/users/{user_id}` | GitHub 데이터 수집      | 201   |

## DTO 상세

### User

**`CreateUserRequestDto`** (Request)

| 필드       | 타입          | 필수 | 설명                                  |
|----------|-------------|:--:|-------------------------------------|
| name     | NotBlankStr | O  | 사용자 이름                              |
| email    | EmailStr    | O  | 이메일                                 |
| timezone | str         | X  | 타임존 (기본: `Asia/Seoul`, ZoneInfo 검증) |

**`UserResponseDto`** (Response)

| 필드         | 타입       | 설명     |
|------------|----------|--------|
| id         | int      | 사용자 ID |
| name       | str      | 이름     |
| email      | str      | 이메일    |
| timezone   | str      | 타임존    |
| created_at | datetime | 생성일시   |
| updated_at | datetime | 수정일시   |

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

### GitHub Collect

**`CollectGitHubRequestDto`** (Request)

| 필드          | 타입          | 필수 | 설명                     |
|-------------|-------------|:--:|------------------------|
| user_id     | int         | O  | 사용자 ID                 |
| target_date | date / null | X  | 수집 대상 날짜 (null: 어제 날짜) |

## 커스텀 타입

| 타입          | 정의                                                                       | 설명               |
|-------------|--------------------------------------------------------------------------|------------------|
| NotBlankStr | `Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]` | 공백 제거 후 최소 1자 이상 |

## 예외 처리

### 예외 계층

```
ServiceException (500)
└── EntityNotFoundException (404)
    ├── UserByIdNotFoundException
    ├── UserByNameNotFoundException
    └── GitHubSecretByUserIdNotFoundException
```

- `exception_handler.py`에서 FastAPI에 핸들러 등록
- 각 예외는 적절한 HTTP 상태 코드로 변환

### 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

| 예외                      | HTTP 상태 | 설명        |
|-------------------------|---------|-----------|
| EntityNotFoundException | 404     | 엔티티 미발견   |
| ServiceException        | 500     | 서비스 에러    |
| Exception (기타)          | 500     | 예상치 못한 에러 |
