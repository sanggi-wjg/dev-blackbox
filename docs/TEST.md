# Test

테스트 구성 및 작성 가이드.

> 아키텍처 개요는 [ARCHITECTURE.md](ARCHITECTURE.md) 참고.

## 실행

```bash
# 전체 테스트
poetry run pytest

# 특정 디렉토리
poetry run pytest tests/util/

# 특정 파일
poetry run pytest tests/util/datetime_util_test.py

# verbose 모드
poetry run pytest -v
```

## 설정

`pyproject.toml`에 정의:

```toml
[tool.pytest.ini_options]
testpaths = ['tests']
pythonpath = ['.']
python_classes = ['*Test']
```

- `testpaths` — 테스트 탐색 루트 디렉토리
- `pythonpath` — 프로젝트 루트를 import 경로에 추가
- `python_classes` — `*Test` 패턴의 클래스를 테스트 클래스로 인식 (e.g., `UserRepositoryTest`)

## 디렉토리 구조

```
tests/
├── conftest.py              # 공통 fixture (DB 세션, 엔티티 팩토리 등)
├── client/
│   └── model/
│       └── jira_model_test.py   # Jira 모델 테스트
├── core/
│   └── encrypt_test.py      # EncryptService 암복호화 테스트
├── service/                 # Service 계층 테스트
├── storage/
│   └── rds/
│       └── user_repository_test.py  # UserRepository 테스트
└── util/
    └── datetime_util_test.py  # 날짜 변환 유틸리티 테스트
```

- 소스 디렉토리 구조를 미러링하여 테스트 파일 배치
- 파일명: `{모듈명}_test.py`

## 테스트 DB 환경

### 자동 설정

테스트 실행 시 `conftest.py`에서 테스트 DB를 자동으로 구성:

1. 메인 DB에 연결하여 `{database}_test` DB 존재 여부 확인 → 없으면 생성
2. 테스트 DB에 `pgvector` 확장 설치
3. `Base.metadata.drop_all()` → `create_all()`로 스키마 초기화

테스트 DB 이름과 DSN은 `PostgresDatabaseSecrets`의 `test_database`, `test_dsn` 프로퍼티로 관리.

### 세션 격리

- `autocommit=False` — `commit()`을 호출하지 않으면 `session.close()` 시 자동 rollback
- `db_session` fixture는 function scope — 테스트마다 새 세션 생성 → 종료 시 미커밋 데이터 자동 롤백

### Fixture

| Fixture              | Scope     | 설명                                           |
|----------------------|-----------|----------------------------------------------|
| `test_engine`        | session   | 테스트 DB 생성, 스키마 초기화, Engine 제공                |
| `db_session_factory` | session   | sessionmaker 인스턴스 제공                         |
| `db_session`         | function  | 테스트별 Session 제공 (종료 시 자동 rollback)           |
| `user_fixture`       | function  | `User` 엔티티 팩토리 (`email` → `User` 생성 및 flush) |

### 엔티티 팩토리 fixture 작성 예시

```python
@pytest.fixture()
def user_fixture(
    db_session: Session,
) -> Callable[[str], User]:

    def _create(email: str) -> User:
        user = User.create(name=email, email=email)
        db_session.add(user)
        db_session.flush()
        return user

    return _create
```

## 작성 컨벤션

### 클래스 기반 테스트

Repository, Service 등 DB 연동 테스트는 `*Test` 클래스로 그룹화:

```python
class UserRepositoryTest:

    def test_find_by_id(self, db_session, user_fixture):
        repository = UserRepository(db_session)

        # given
        user = user_fixture("iam@dev.com")

        # when
        result = repository.find_by_id(user.id)

        # then
        assert result == user
```

### Given-When-Then 패턴

모든 테스트는 `# given`, `# when`, `# then` 주석으로 구분:

```python
def test_encrypt_service():
    key = "test_key"
    pepper = "test_pepper"
    encrypt_service = EncryptService(key, pepper)

    # given
    secret_key = "Hello, I am a secret key!"

    # when
    encrypted_text = encrypt_service.encrypt(secret_key)
    decrypted_text = encrypt_service.decrypt(encrypted_text)

    # then
    assert decrypted_text == secret_key
```

### 네이밍 규칙

- 클래스명: `{모듈명}Test` (e.g., `UserRepositoryTest`)
- 함수명: `test_` 접두사 + 테스트 대상 함수명 또는 동작 설명
- 한글 함수명 사용 가능 (e.g., `test_ISO_형식_날짜를_KST로_변환한다`)

### 테스트 분류

- **단위 테스트** — DB, 외부 API 연동 없이 순수 로직만 테스트 (`EncryptService`, `datetime_util` 등)
- **Repository 테스트** — 테스트 DB 연동, `db_session` fixture 사용, 클래스 기반

## 테스트 목록

| 파일                                         | 테스트                             | 설명                              |
|--------------------------------------------|---------------------------------|---------------------------------|
| `client/model/jira_model_test.py`          | `test_jira_status_group`        | JiraStatusGroup 상태 그룹 조합 검증     |
| `core/encrypt_test.py`                     | `test_encrypt_service`          | AES-256-GCM 암복호화 정합성 검증         |
| `storage/rds/user_repository_test.py`      | `test_find_by_id`               | UserRepository ID 조회 검증          |
| `storage/rds/user_repository_test.py`      | `test_find_all`                 | UserRepository 전체 조회 검증          |
| `util/datetime_util_test.py`               | `test_get_date_from_iso_format` | ISO 날짜 → 타임존 변환 후 date 반환       |