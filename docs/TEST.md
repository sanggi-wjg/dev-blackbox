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

- `python_classes` — `*Test` 패턴의 클래스를 테스트 클래스로 인식 (e.g., `UserRepositoryTest`)

## 테스트 DB 환경

테스트 실행 시 `conftest.py`에서 Testcontainers 기반으로 테스트 DB를 자동 구성:

1. `PostgresContainer(pgvector/pgvector:pg17)` 임시 컨테이너 기동
2. 테스트 DB에 `pgvector` 확장 설치
3. `Base.metadata.create_all()`로 스키마 초기화

세션 격리: `db_session` fixture는 function scope — 테스트마다 새 세션 생성, 종료 시 미커밋 데이터 자동 롤백.

Fixture 상세는 `tests/conftest.py` 코드 참고.

## 작성 컨벤션

- 소스 디렉토리 구조를 미러링하여 테스트 파일 배치
- 파일명: `{모듈명}_test.py`
- 클래스명: `{모듈명}Test` (e.g., `UserRepositoryTest`)
- 함수명: `test_` 접두사 + 테스트 대상 함수명 또는 동작 설명
- 한글 함수명 사용 가능 (e.g., `test_ISO_형식_날짜를_KST로_변환한다`)
- DB 연동 테스트는 `*Test` 클래스로 그룹화
- 모든 테스트는 `# given`, `# when`, `# then` 주석으로 구분
