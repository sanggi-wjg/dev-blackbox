# TODO

## 1. 데이터 수집

### GitHub
- [x] Event 수집 (PushEvent, PullRequestEvent)
- [x] Commit 상세 조회
- [ ] PullRequestEvent 처리 로직 구현
- [ ] 수집 데이터 DB 저장

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
- [ ] LLM 연동 (프롬프트 설계 + API 호출)
- [ ] 수집 데이터 → 요약 파이프라인

## 3. 일일 업무 일지 생성
- [ ] 일지 포맷 정의
- [ ] 최종 리포트 생성 및 출력