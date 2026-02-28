---
name: create-task-test
description: Task 레이어의 테스트 코드를 작성합니다. APScheduler 백그라운드 태스크의 로직을 분석하여 테스트 케이스를 생성합니다.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# create-task-test

Task 레이어(`dev_blackbox/task/`)의 테스트 코드를 작성하는 스킬.
APScheduler 백그라운드 태스크의 비즈니스 로직을 분석하여 테스트 케이스를 생성한다.

## 입력

사용자에게 다음 정보를 확인한다:

1. **대상 Task 파일 경로** (예: `dev_blackbox/task/collect_task.py`)
2. **테스트할 함수** (전체 또는 특정 함수 지정)

## 함수 분류

Task 모듈의 함수를 분석하여 다음으로 분류한다:

### 최상위 태스크 함수

스케줄러에 등록되는 진입점 함수. 분산 락 획득 → 내부 로직 호출 구조.

- `distributed_lock`을 mock하여 락 획득 시/실패 시 동작 검증
- 내부 서비스/함수 호출을 mock하여 호출 검증

### 내부 비즈니스 함수

실제 데이터 수집/처리를 수행하는 함수. Service를 조합한다.

- Service 메서드를 mock
- 외부 클라이언트(`GitHubClient`, `JiraClient`, `SlackClient`)를 mock
- `get_db_session()`을 mock하여 DB 세션 격리
- LLM Agent를 mock

### 헬퍼 함수

데이터 변환, 텍스트 추출 등 보조 함수.

- 순수 함수인 경우 직접 테스트
- Service 의존이 있으면 mock

## 생성 산출물

### 테스트 파일 — `tests/task/{태스크명}_test.py`

소스 디렉토리 구조를 미러링하여 배치한다.

```
dev_blackbox/task/collect_task.py
→ tests/task/collect_task_test.py
```

## 테스트 코드 구조

### 클래스/함수 네이밍

```python
class {태스크명_PascalCase}Test:  # 예: CollectTaskTest

    def test_{함수명}(self, ...):  # 정상 케이스

    def test_{함수명}_{조건}_한글설명(self, ...):  # 엣지/예외 케이스
```

### 최상위 태스크 함수 테스트 템플릿

```python
from unittest.mock import patch, MagicMock, call

from dev_blackbox.task.{태스크_모듈} import {태스크_함수}
from tests.fixtures.lock_helper import mock_lock_acquired, mock_lock_not_acquired


class {태스크명}Test:

    def test_{태스크_함수}_락_획득_시_내부_로직을_실행한다(self):
        # given
        mock_service = MagicMock()

        with (
            patch(
                "dev_blackbox.task.{모듈}.distributed_lock",
                return_value=mock_lock_acquired(),
            ),
            patch("dev_blackbox.task.{모듈}.{Service}", return_value=mock_service),
            patch("dev_blackbox.task.{모듈}.get_db_session") as mock_db,
        ):
            mock_db.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            # when
            {태스크_함수}()

        # then
        mock_service.{메서드}.assert_called()

    def test_{태스크_함수}_락_미획득_시_내부_로직을_실행하지_않는다(self):
        # given
        mock_service = MagicMock()

        with (
            patch(
                "dev_blackbox.task.{모듈}.distributed_lock",
                return_value=mock_lock_not_acquired(),
            ),
            patch("dev_blackbox.task.{모듈}.{Service}", return_value=mock_service),
        ):
            # when
            {태스크_함수}()

        # then
        mock_service.{메서드}.assert_not_called()
```

### 내부 비즈니스 함수 테스트 템플릿

```python
def test_{내부_함수}_정상_수집(self):
    # given
    mock_service = MagicMock()
    mock_service.{method}.return_value = [...]

    mock_client = MagicMock(spec={Client})
    mock_client.{api_method}.return_value = [...]

    with (
        patch("dev_blackbox.task.{모듈}.get_db_session") as mock_db,
        patch("dev_blackbox.task.{모듈}.{Client}.create", return_value=mock_client),
    ):
        mock_session = MagicMock()
        mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.return_value.__exit__ = MagicMock(return_value=False)

        # when
        {내부_함수}(user_context, target_date)

    # then
    mock_service.{method}.assert_called_once()
```

### 플랫폼 격리 테스트 템플릿

```python
def test_{함수명}_한_플랫폼_실패가_다른_플랫폼에_영향을_주지_않는다(self):
    # given
    mock_github_service = MagicMock()
    mock_github_service.{method}.side_effect = Exception("GitHub API error")

    mock_jira_service = MagicMock()
    mock_jira_service.{method}.return_value = [...]

    with (
        patch("dev_blackbox.task.{모듈}.{GitHubService}", return_value=mock_github_service),
        patch("dev_blackbox.task.{모듈}.{JiraService}", return_value=mock_jira_service),
        patch("dev_blackbox.task.{모듈}.get_db_session") as mock_db,
    ):
        mock_db.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_db.return_value.__exit__ = MagicMock(return_value=False)

        # when — GitHub 실패에도 예외가 전파되지 않아야 한다
        {함수명}(user_context, target_date)

    # then — Jira는 정상 실행되어야 한다
    mock_jira_service.{method}.assert_called_once()
```

### 공통 Fixture 헬퍼

테스트에서 사용하는 공통 헬퍼는 `tests/fixtures/`에 정의되어 있다. 직접 정의하지 말고 import하여 사용한다.

#### 분산 락 헬퍼 — `tests/fixtures/lock_helper.py`

```python
from tests.fixtures.lock_helper import mock_lock_acquired, mock_lock_not_acquired
```

#### UserContext 헬퍼 — `tests/fixtures/user_context_helper.py`

```python
from tests.fixtures.user_context_helper import create_user_context

# 기본값: id=1, tz_info=Asia/Seoul, 모든 플랫폼 비활성
user_context = create_user_context()

# 특정 플랫폼 활성화
user_context = create_user_context(has_github_user_secret=True, has_jira_user=True)
```

## 테스트 케이스 설계 원칙

### 최상위 태스크 함수

1. **락 획득 성공** — 내부 로직 실행 확인
2. **락 미획득** — 내부 로직 미실행 확인
3. **사용자 목록 조회** — 전체 사용자 순회 확인

### 내부 수집/요약 함수

1. **정상 수집** — 데이터 수집 + 저장 호출 확인
2. **빈 데이터** — 수집 결과 0건 시 빈 업무 일지 저장
3. **플랫폼 격리** — 한 플랫폼 실패가 다른 플랫폼에 영향 없음
4. **플랫폼 미설정** — GitHub secret/Jira user/Slack user 없으면 해당 수집 건너뜀
5. **LLM 요약** — Agent 호출 확인 + 결과 저장 확인

### 동기화 태스크

1. **정상 동기화** — 클라이언트 호출 + 신규 사용자 저장
2. **동기화 대상 없음** — 모두 기존 사용자면 저장 0건
3. **클라이언트 에러** — 예외 처리 확인

## 컨벤션

- `# given`, `# when`, `# then` 주석으로 구분 (mock 설정이 길면 `# mock` 섹션 추가)
- **`then`에서 `given`의 입력 값을 참조**: 검증 시 리터럴 값을 반복하지 않고, `given`에서 생성한 변수를 참조
- 한글 함수명 사용 가능 (예: `test_락_미획득_시_내부_로직을_실행하지_않는다`)
- `MagicMock`에는 반드시 `spec=ClassName` 지정 (외부 클라이언트에 적용)
- `unittest.mock.patch` 경로는 **대상이 import된 모듈** 기준
  - 예: Task에서 `from dev_blackbox.service.github_event_service import GitHubEventService` →
    patch 경로: `"dev_blackbox.task.{모듈}.GitHubEventService"`
- `get_db_session()`은 context manager이므로 `__enter__`/`__exit__`을 mock해야 함
- Task 테스트는 DB를 사용하지 않고 **전부 mock으로 격리** (Task는 Service를 조합하는 레이어)
- `UserContext`는 `tests/fixtures/user_context_helper.py`의 `create_user_context()`로 생성
- 분산 락 mock은 `tests/fixtures/lock_helper.py`의 `mock_lock_acquired()` / `mock_lock_not_acquired()`를 사용
- 테스트 실행 후 `poetry run pytest tests/task/{파일}_test.py -v`로 검증

## 체크리스트

생성 완료 후 다음을 확인한다:

- [ ] 테스트 파일이 `tests/task/{태스크명}_test.py`에 배치되었는가
- [ ] 클래스명이 `{태스크명}Test` 패턴인가
- [ ] 모든 테스트가 `# given`, `# when`, `# then`으로 구분되는가
- [ ] 분산 락 획득/미획득 케이스가 있는가
- [ ] 플랫폼 격리 테스트가 있는가 (수집 태스크의 경우)
- [ ] 빈 데이터 시 빈 업무 일지 저장 케이스가 있는가 (수집 태스크의 경우)
- [ ] 외부 클라이언트 mock에 `spec`이 지정되었는가
- [ ] `get_db_session()` mock이 context manager로 처리되었는가
- [ ] `poetry run pytest`로 전체 테스트가 통과하는가
