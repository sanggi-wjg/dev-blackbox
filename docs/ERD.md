# ERD (Entity Relationship Diagram)

도메인별 데이터 모델 관계도.

> 컬럼 상세는 [DATABASE.md](DATABASE.md) 또는 `docker/postgres/init.sql` 참고.

## 전체 도메인 관계

```mermaid
erDiagram
    users ||--o| github_user_secret: "1:1"
    users ||--o{ github_event: "1:N"
    users ||--o| jira_user: "1:1"
    users ||--o{ jira_event: "1:N"
    users ||--o| slack_user: "1:1"
    users ||--o{ slack_message: "1:N"
    users ||--o{ platform_work_log: "1:N"
    users ||--o{ daily_work_log: "1:N"
    github_user_secret ||--o{ github_event: "1:N"
    jira_secret ||--o{ jira_user: "1:N"
    jira_user ||--o{ jira_event: "1:N"
    slack_secret ||--o{ slack_user: "1:N"
    slack_user ||--o{ slack_message: "1:N"
```

## 1. 사용자 도메인

```mermaid
erDiagram
    users {
        bigserial id PK
        varchar name
        varchar email UK
        varchar password
        varchar timezone
        boolean is_admin
        boolean is_deleted
    }
```

## 2. GitHub 도메인

```mermaid
erDiagram
    users ||--o| github_user_secret : "1:1"
    users ||--o{ github_event : "1:N"
    github_user_secret ||--o{ github_event : "1:N"

    github_user_secret {
        serial id PK
        bigint user_id FK,UK
        varchar username
        varchar personal_access_token "AES-256-GCM 암호화"
    }

    github_event {
        bigserial id PK
        bigint user_id FK
        int github_user_secret_id FK
        varchar event_id UK
        varchar event_type
        date target_date
        jsonb event
        jsonb commit
    }
```

## 3. Jira 도메인

```mermaid
erDiagram
    jira_secret ||--o{ jira_user : "1:N"
    users ||--o| jira_user : "1:1 (NULLABLE)"
    users ||--o{ jira_event : "1:N"
    jira_user ||--o{ jira_event : "1:N"

    jira_secret {
        bigserial id PK
        varchar name
        varchar url
        varchar username "AES-256-GCM 암호화"
        varchar api_token "AES-256-GCM 암호화"
        boolean is_deleted
    }

    jira_user {
        bigserial id PK
        bigint jira_secret_id FK
        bigint user_id FK,UK "NULLABLE"
        varchar account_id "복합UK(secret+account)"
        boolean is_active
        varchar display_name
        varchar email_address
        varchar project "NULLABLE"
    }

    jira_event {
        bigserial id PK
        bigint user_id FK
        bigint jira_user_id FK
        varchar issue_id
        varchar issue_key
        date target_date
        jsonb issue
        jsonb changelog
    }
```

## 4. Slack 도메인

```mermaid
erDiagram
    slack_secret ||--o{ slack_user : "1:N"
    users ||--o| slack_user : "1:1 (NULLABLE)"
    users ||--o{ slack_message : "1:N"
    slack_user ||--o{ slack_message : "1:N"

    slack_secret {
        bigserial id PK
        varchar name
        varchar bot_token "AES-256-GCM 암호화"
        boolean is_deleted
    }

    slack_user {
        bigserial id PK
        bigint slack_secret_id FK
        bigint user_id FK,UK "NULLABLE"
        varchar member_id "복합UK(secret+member)"
        boolean is_active
        varchar display_name
        varchar real_name
        varchar email
    }

    slack_message {
        bigserial id PK
        bigint user_id FK
        bigint slack_user_id FK
        date target_date
        varchar channel_id
        varchar channel_name
        varchar message_ts
        text message_text
        jsonb message
        varchar thread_ts "NULLABLE"
    }
```

## 5. 업무 일지 도메인

```mermaid
erDiagram
    users ||--o{ platform_work_log : "1:N"
    users ||--o{ daily_work_log : "1:N"

    platform_work_log {
        bigserial id PK
        bigint user_id FK
        date target_date "복합UK(user+date+platform)"
        varchar platform
        text content
        vector embedding "1024차원, NULLABLE"
        varchar model_name
        text prompt
    }

    daily_work_log {
        bigserial id PK
        bigint user_id FK
        date target_date "복합UK(user+date)"
        text content
        vector embedding "1024차원, NULLABLE"
    }
```