# TODO

## 1. 데이터 수집

### GitHub

- [x] Event 수집 (PushEvent, PullRequestEvent)
- [x] Commit 상세 조회
- [x] 수집 데이터 DB 저장 (GitHubEvent 엔티티 + JSONB)
- [x] 사용자별 GitHub PAT 암호화 저장 (GitHubUserSecret + AES-256-GCM)
- ~~[ ] PullRequestEvent 처리 로직 구현~~

### Jira

- [ ] Jira Client 구현
- [ ] 이슈/작업 로그 수집

### Slack

- [ ] Slack Client 구현
- [ ] 메시지/스레드 활동 수집

### IDE (Wakatime)

- [ ] Wakatime Client 구현
- [ ] 코딩 활동 로그 수집

## 2. LLM 요약

- [x] LLM 연동 (LLMAgent + OllamaConfig + LlamaIndex)
- [x] 프롬프트 설계 (GITHUB_COMMIT_SUMMARY_PROMPT)
- [x] 수집 데이터 → 요약 파이프라인 연결 (collect_task 통합)

## 3. 일일 업무 일지 생성

- [ ] 일지 포맷 정의
- [ ] 최종 리포트 생성 및 출력
