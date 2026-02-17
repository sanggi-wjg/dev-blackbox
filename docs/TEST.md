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
```

- `testpaths` — 테스트 탐색 루트 디렉토리
- `pythonpath` — 프로젝트 루트를 import 경로에 추가

## 디렉토리 구조

```
tests/
├── conftest.py              # 공통 fixture
├── client/
│   └── model/
│       └── jira_model_test.py   # Jira 모델 테스트
├── core/
│   └── encrypt_test.py      # EncryptService 암복호화 테스트
└── util/
    └── datetime_util_test.py  # 날짜 변환 유틸리티 테스트
```

- 소스 디렉토리 구조를 미러링하여 테스트 파일 배치
- 파일명: `{모듈명}_test.py`

## 작성 컨벤션

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

- 함수명: `test_` 접두사 + 테스트 대상 함수명 또는 동작 설명
- 한글 함수명 사용 가능 (e.g., `test_ISO_형식_날짜를_KST로_변환한다`)

### 외부 의존성 없는 단위 테스트

- DB, 외부 API 연동 없이 순수 로직만 테스트
- `EncryptService`, `datetime_util` 등 인프라 독립적인 모듈 대상

## 테스트 목록

| 파일                                | 테스트                             | 설명                              |
|-----------------------------------|---------------------------------|---------------------------------|
| `client/model/jira_model_test.py` | `test_jira_status_group`        | JiraStatusGroup 상태 그룹 조합 검증     |
| `core/encrypt_test.py`            | `test_encrypt_service`          | AES-256-GCM 암복호화 정합성 검증         |
| `util/datetime_util_test.py`      | `test_get_date_from_iso_format` | ISO 날짜 → 타임존 변환 후 date 반환       |