# Jira ↔ Task 연동 기능

## 배경

Jira 백로그를 로컬 Task로 자동으로 가져오고,
로컬에서 작업한 내용을 Jira에 수동으로 반영할 수 있는 기능.

## 설계 방향

- **Pull(Jira → App)**: 백로그 상태 이슈만 자동 생성. 기존 Task 업데이트 없음
- **Push(App → Jira)**: 수동 버튼으로만 동작. 의도하지 않은 overwrite 방지
- **미리보기**: Jira 이슈의 현재 상태를 실시간 조회 (로컬 저장 없음)

### Overwrite 문제 해결

양방향 자동 동기화 대신, Pull은 생성만 / Push는 수동으로 분리하여
타인의 수정이 로컬 Task를 덮어쓰는 문제를 원천 차단.

---

## 기능 목록

### 기능 1: Jira 백로그 가져오기 (Pull)

**목적**: Jira에서 나에게 할당된 백로그 이슈를 로컬 Task로 생성

- Jira에서 `statusCategory = "To Do"`, 내가 담당자인 이슈를 조회
- `jira_issue_key`로 이미 가져온 이슈는 skip (멱등성)
- 새 이슈만 `status = BACKLOG`로 Task 생성
- 수동 트리거 (버튼)
- 향후: "가져오기" 버튼으로 특정 이슈를 선택적으로 가져오는 기능 고려

### 기능 2: Jira 미리보기 (Read)

**목적**: Task에 연결된 Jira 이슈의 현재 상태를 확인

- Jira 이슈의 description, 코멘트를 실시간 조회
- 로컬 저장 없이 Jira API 직접 호출 (항상 최신)
- 맥락 파악용 — Jira 웹을 왔다갔다 하지 않아도 됨

### 기능 3: Jira 코멘트 밀어넣기 (Push)

**목적**: 로컬에서 작성한 내용을 Jira에 코멘트로 추가

- 수동 트리거 (버튼)
- 진행상황 공유, 분석 결과 기록 등에 활용

### 기능 4: Jira 상태 변경 (Push)

**목적**: 로컬 Task 상태 변경을 Jira에도 반영

- 수동 트리거 (버튼)
- Jira는 워크플로 기반이므로 transition ID 조회 후 변경 필요

---

## 우선순위

```
Phase 1: 기능 1 (Pull) + Task 엔티티 확장
Phase 2: 기능 2 (미리보기)
Phase 3: 기능 3 (코멘트 Push)
Phase 4: 기능 4 (상태 변경 Push)
```

---

## 사용자 흐름

```
1. Jira 백로그 이슈가 Task로 들어옴         ← 기능 1
2. "이게 뭐지?" → 미리보기로 맥락 파악       ← 기능 2
3. 로컬에서 작업, 메모 작성
4. "진행상황 공유해야지" → 코멘트 밀어넣기    ← 기능 3
5. "상태도 바꾸자" → Jira 상태 변경          ← 기능 4
```

---

## Task 엔티티 변경 (Phase 1)

추가 컬럼:

| 컬럼               | 타입                     | 설명              |
|------------------|------------------------|-----------------|
| `jira_issue_key` | VARCHAR(100), nullable | e.g., `FMP-123` |
| `jira_issue_id`  | VARCHAR(100), nullable | Jira 내부 ID      |
| `jira_synced_at` | TIMESTAMPTZ, nullable  | 마지막 동기화 시각      |

- UNIQUE 제약: `(user_id, jira_issue_key)` — 동일 이슈 중복 생성 방지
- Jira 연결 여부 판단: `jira_issue_key IS NOT NULL` (별도 boolean 불필요)

## 상태 매핑 (Phase 4)

Jira `statusCategory` 기반 매핑 (프로젝트별 커스텀 상태에도 대응):

| Jira statusCategory | TaskStatusEnum |
|---------------------|----------------|
| To Do               | BACKLOG        |
| In Progress         | IN_PROGRESS    |
| Done                | DONE           |

---

## 미결 사항

- [ ] Pull 시 Jira description을 Task.content에 넣을지 (Jira 마크업 변환 이슈)
- [ ] Jira 이슈 삭제/완료 시 로컬 Task 처리 방침
- [ ] Task에서 Jira 연결 해제 기능 필요 여부
- [ ] 미리보기 캐싱 전략 (실시간 vs 짧은 TTL)
- [ ] 자동 Pull 주기 (앱 진입 시 자동 체크 등) 도입 시점
