# Pipeline

데이터 수집, LLM 요약, 동기화 파이프라인 상세.

> 아키텍처 개요는 [ARCHITECTURE.md](ARCHITECTURE.md) 참고.
> 인프라 설정(스케줄러, Redis)은 [INFRASTRUCTURE.md](INFRASTRUCTURE.md) 참고.

## 스케줄링 태스크 목록

| 태스크                                            | 스케줄                             | 설명                     |
|------------------------------------------------|---------------------------------|------------------------|
| `health_check_task()`                          | 매 5분 (interval)                 | 헬스 체크                  |
| `collect_events_and_summarize_work_log_task()` | 매일 00:00 UTC / 09:00 KST (cron) | 전체 사용자 데이터 수집 + LLM 요약 |
| `sync_jira_users_task()`                       | 매일 15:00 UTC / 00:00 KST (cron) | Jira 사용자 동기화           |
| `sync_slack_users_task()`                      | 매일 15:10 UTC / 00:10 KST (cron) | Slack 사용자 동기화          |

모든 태스크는 `distributed_lock()`으로 중복 실행을 방지한다.

## 전체 수집 + 요약 파이프라인

### 개요

```
collect_events_and_summarize_work_log_task()
       │
       ├── distributed_lock 획득
       │
       ├── UserService.get_users() → UserContext 변환
       │
       ▼  (사용자별 반복)
  _collect_events_and_summarize(user, target_date)
       │
       ├── target_date 기본값: 유저 타임존 기준 어제
       │
       ├── _collect_and_summarize(user, target_date)
       │       │
       │       ├── GitHub 수집 + 요약  (github_user_secret이 있는 경우)
       │       ├── Jira 수집 + 요약    (jira_user가 있는 경우)
       │       └── Slack 수집 + 요약   (slack_user가 있는 경우)
       │
       └── _save_daily_work_log(user, target_date)  ← 통합 일일 업무 일지
```

각 플랫폼 수집은 독립된 try-except로 감싸져 있어, 한 플랫폼 실패가 다른 플랫폼에 영향을 주지 않는다.

### GitHub 수집 + LLM 요약

```
_collect_github_events(user_id, target_date)
       │
       ├── GitHubEventService.save_github_events()
       │       │
       │       ├── 기존 이벤트 삭제 (target_date 기준)
       │       ├── EncryptService.decrypt()          ← PAT 복호화
       │       ├── GithubClient.fetch_events_by_date()   ← GitHub API v3
       │       ├── 이벤트 필터링 (PushEvent)
       │       ├── GithubClient.fetch_commit()       ← 커밋 상세 조회
       │       └── GitHubEventRepository.save_all()  ← DB 저장
       │
       ├── commit_detail_text 추출 → 텍스트 병합 (최대 50,000자)
       │
       ▼
_summarize_github(user, target_date, commit_message)
       │
       ├── SummaryOllamaConfig (temperature=0.1, context=64k)
       ├── LLMAgent.query(GITHUB_COMMIT_SUMMARY_PROMPT)   ← Ollama 요약
       │
       ▼
  WorkLogService.save_platform_work_log(platform=GITHUB)   ← DB 저장
```

### Jira 수집 + LLM 요약

```
_collect_jira_events(user, target_date)
       │
       ├── JiraEventService.save_jira_events()
       │       │
       │       ├── 기존 이벤트 삭제 (target_date 기준, 멱등성 보장)
       │       ├── IssueJQL 빌드 (프로젝트, 담당자, 상태, 날짜 범위)
       │       ├── JiraClient.fetch_search_issues()  ← Jira REST API
       │       ├── JiraIssueModel.from_raw() 변환
       │       ├── changelog를 target_date + 타임존 기준 필터링
       │       └── JiraEventRepository.save_all()    ← DB 저장
       │
       ├── issue_detail_text(target_date, tz_info) 추출 → 텍스트 병합 (최대 50,000자)
       │
       ▼
_summarize_jira(user, target_date, issue_details)
       │
       ├── SummaryOllamaConfig (temperature=0.1, context=64k)
       ├── LLMAgent.query(JIRA_ISSUE_SUMMARY_PROMPT)      ← Ollama 요약
       │
       ▼
  WorkLogService.save_platform_work_log(platform=JIRA)     ← DB 저장
```

### Slack 수집 + LLM 요약

```
_collect_slack_events(user, target_date)
       │
       ├── SlackMessageService.save_slack_messages()
       │
       ├── "[#{channel_name}] {message_text}" 포맷 → 텍스트 병합 (최대 50,000자)
       │
       ▼
_summarize_slack(user, target_date, message_details)
       │
       ├── SummaryOllamaConfig (temperature=0.1, context=64k)
       ├── LLMAgent.query(SLACK_MESSAGE_SUMMARY_PROMPT)    ← Ollama 요약
       │
       ▼
  WorkLogService.save_platform_work_log(platform=SLACK)    ← DB 저장
```

### 빈 활동 데이터 처리

플랫폼 수집 결과가 없으면(이벤트/메시지 0건) 빈 업무 일지를 저장한다:

```python
_save_empty_work_log(user, target_date, platform, message=EMPTY_ACTIVITY_MESSAGE)
# → content: "이 플랫폼에 대해 수집된 활동 데이터가 없습니다."
# → model_name: "", prompt: ""
```

### 일일 통합 업무 일지

모든 플랫폼 수집/요약 완료 후, 플랫폼별 업무 일지를 병합하여 일일 통합 업무 일지를 생성한다:

```python
_save_daily_work_log(user, target_date)
↓
WorkLogService.save_daily_work_log(user_id, target_date)
↓
# PlatformEnum.platforms() 기준 (USER_CONTENT 제외) PlatformWorkLog 조회
# 각 PlatformWorkLog의 markdown_text ("# {platform}\n\n{content}") 병합
# DailyWorkLog.create() → DB 저장
```

## 수동 동기화 (Per-User)

API를 통해 특정 사용자의 특정 날짜에 대해 수동으로 수집/요약을 트리거할 수 있다.

```
POST /api/v1/work-logs/manual-sync  (Idempotency-Key 헤더 필수)
       │
       ▼
collect_events_and_summarize_work_log_by_user_task(user_id, target_date)
       │
       ├── 사용자별 분산 락 획득
       │   (lock_name: "collect_events_and_summarize_work_log_task:user_id:{id}:target_date:{date}")
       │
       ├── UserService.get_user_by_id_or_throw(user_id)
       │
       └── _collect_events_and_summarize(user, target_date)  ← 스케줄 태스크와 동일 로직
```

- 전체 사용자 태스크와 달리 **사용자+날짜 조합으로 락**이 걸려, 다른 사용자/날짜의 수동 동기화와 동시 실행 가능
- FastAPI `BackgroundTasks`로 비동기 실행 (202 Accepted 즉시 응답)
- 멱등성 키로 중복 요청 방지

## 사용자 동기화 파이프라인

### Jira 사용자 동기화

```
[APScheduler] sync_jira_users_task() (매일 15:00 UTC)
       │
       ├── distributed_lock 획득
       │
       ▼
  JiraUserService.sync_jira_users()
       │
       ├── JiraClient.fetch_assignable_users()    ← Jira API
       ├── 기존 account_id 비교 → 신규 사용자만 필터링
       │
       ▼
  JiraUserRepository.save_all()                  ← DB 저장
```

### Slack 사용자 동기화

```
[APScheduler] sync_slack_users_task() (매일 15:10 UTC)
       │
       ├── distributed_lock 획득
       │
       ▼
  SlackUserService.sync_slack_users()            ← Slack API
       │
       ▼
  DB 저장
```

## 설계 원칙

- **플랫폼 격리**: 각 플랫폼 수집/요약은 독립된 try-except. 한 플랫폼 실패가 다른 플랫폼을 차단하지 않음
- **분산 락**: 스케줄 태스크는 전역 락, 수동 동기화는 사용자+날짜 단위 락
- **세션 격리**: 각 수집/요약 단계마다 별도 `get_db_session()` 사용. 한 단계 커밋이 다른 단계와 무관
- **텍스트 길이 제한**: LLM 입력은 최대 50,000자로 잘라냄 (토큰 한도 보호)
- **타임존 인식**: `target_date` 기본값은 유저 타임존 기준 어제 날짜
- **멱등성 보장**: 수집 시 기존 데이터 삭제 후 재저장 (같은 날짜 재수집 가능)
