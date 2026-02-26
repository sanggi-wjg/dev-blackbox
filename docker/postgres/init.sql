CREATE EXTENSION IF NOT EXISTS vector;

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS
$$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- users 테이블
CREATE TABLE IF NOT EXISTS users
(
    id         BIGSERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(255) NOT NULL,
    password   VARCHAR(255) NOT NULL,
    timezone   VARCHAR(50)  NOT NULL DEFAULT 'Asia/Seoul',

    is_admin   BOOLEAN      NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ  NOT NULL DEFAULT '9999-12-31 14:59:59+00',

    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE TRIGGER tr_users_updated_at
    BEFORE UPDATE
    ON users
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_users_001 ON users (email);
CREATE INDEX idx_users_002 ON users (created_at DESC);

COMMENT ON TABLE users IS '사용자 테이블';
COMMENT ON COLUMN users.id IS '사용자 ID';
COMMENT ON COLUMN users.name IS '사용자 이름';
COMMENT ON COLUMN users.email IS '이메일 (UNIQUE)';
COMMENT ON COLUMN users.timezone IS '타임존 (ZoneInfo 검증)';


-- github_user_secret 테이블
CREATE TABLE IF NOT EXISTS github_user_secret
(
    id                    SERIAL PRIMARY KEY,
    user_id               BIGINT       NOT NULL,
    username              VARCHAR(50)  NOT NULL,
    personal_access_token VARCHAR(255) NOT NULL,

    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_github_user_secret_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,

    CONSTRAINT uq_github_user_secret_user_id UNIQUE (user_id)
);

CREATE TRIGGER tr_github_user_secret_updated_at
    BEFORE UPDATE
    ON github_user_secret
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_github_user_secret_001 ON github_user_secret (user_id);
CREATE INDEX idx_github_user_secret_002 ON github_user_secret (created_at DESC);

COMMENT ON TABLE github_user_secret IS 'GitHub 인증 정보 테이블';
COMMENT ON COLUMN github_user_secret.user_id IS '사용자 FK';
COMMENT ON COLUMN github_user_secret.username IS 'GitHub 사용자명';
COMMENT ON COLUMN github_user_secret.personal_access_token IS 'GitHub PAT (AES-256-GCM 암호화 저장)';


-- github_event 테이블 (GitHub 이벤트 + 커밋 수집 데이터)
CREATE TABLE IF NOT EXISTS github_event
(
    id                    BIGSERIAL PRIMARY KEY,
    user_id               BIGINT       NOT NULL,
    github_user_secret_id INT          NOT NULL,
    event_id              VARCHAR(100) NOT NULL,
    event_type            VARCHAR(50)  NOT NULL,
    target_date           DATE         NOT NULL,
    event                 JSONB        NOT NULL,
    commit                JSONB        NULL,

    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_github_event_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_github_event_secret FOREIGN KEY (github_user_secret_id) REFERENCES github_user_secret (id) ON DELETE RESTRICT,

    CONSTRAINT uq_github_event_event_id UNIQUE (event_id)
);

CREATE TRIGGER tr_github_event_updated_at
    BEFORE UPDATE
    ON github_event
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_github_event_001 ON github_event (user_id, target_date, event_type);
CREATE INDEX idx_github_event_002 ON github_event (target_date);
CREATE INDEX idx_github_event_003 ON github_event (created_at DESC);

COMMENT ON TABLE github_event IS 'GitHub 이벤트 + 커밋 수집 데이터';
COMMENT ON COLUMN github_event.user_id IS '사용자 FK';
COMMENT ON COLUMN github_event.github_user_secret_id IS 'GitHub 인증 정보 FK';
COMMENT ON COLUMN github_event.event_id IS 'GitHub 이벤트 ID (UNIQUE)';
COMMENT ON COLUMN github_event.event_type IS 'GitHub 이벤트 타입 (PushEvent, PullRequestEvent 등)';
COMMENT ON COLUMN github_event.target_date IS '수집 대상 날짜';
COMMENT ON COLUMN github_event.event IS '이벤트 원본 데이터 (JSONB)';
COMMENT ON COLUMN github_event.commit IS '커밋 상세 데이터 (JSONB)';


-- platform_work_log 테이블 (플랫폼별 업무 일지 LLM 요약)
CREATE TABLE IF NOT EXISTS platform_work_log
(
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT       NOT NULL,
    target_date DATE         NOT NULL,
    platform    VARCHAR(20)  NOT NULL,
    content     TEXT         NOT NULL DEFAULT '',
    embedding   vector(1024) NULL,
    model_name  VARCHAR(100) NOT NULL,
    prompt      TEXT         NOT NULL,

    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_platform_work_log_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,

    CONSTRAINT uq_platform_work_log_user_date_platform UNIQUE (user_id, target_date, platform)
);

CREATE TRIGGER tr_platform_work_log_updated_at
    BEFORE UPDATE
    ON platform_work_log
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_platform_work_log_001 ON platform_work_log (user_id, target_date);
CREATE INDEX idx_platform_work_log_002 ON platform_work_log (target_date);
CREATE INDEX idx_platform_work_log_003 ON platform_work_log (created_at DESC);

COMMENT ON TABLE platform_work_log IS '플랫폼별 LLM 요약';
COMMENT ON COLUMN platform_work_log.user_id IS '사용자 FK';
COMMENT ON COLUMN platform_work_log.target_date IS '요약 대상 날짜';
COMMENT ON COLUMN platform_work_log.platform IS '플랫폼 구분 (GITHUB, JIRA, SLACK 등)';
COMMENT ON COLUMN platform_work_log.content IS 'LLM 생성 요약 텍스트';
COMMENT ON COLUMN platform_work_log.embedding IS '요약 임베딩 벡터 (1024차원)';
COMMENT ON COLUMN platform_work_log.model_name IS '사용 LLM 모델명';
COMMENT ON COLUMN platform_work_log.prompt IS '요약 생성에 사용된 프롬프트';


-- daily_work_log 테이블 (통합 일일 요약)
CREATE TABLE IF NOT EXISTS daily_work_log
(
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT       NOT NULL,
    target_date DATE         NOT NULL,
    content     TEXT         NOT NULL,
    embedding   vector(1024) NULL,

    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_daily_work_log_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,

    CONSTRAINT uq_daily_work_log_user_date UNIQUE (user_id, target_date)
);

CREATE TRIGGER tr_daily_work_log_updated_at
    BEFORE UPDATE
    ON daily_work_log
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_daily_work_log_001 ON daily_work_log (user_id, target_date);
CREATE INDEX idx_daily_work_log_002 ON daily_work_log (target_date);
CREATE INDEX idx_daily_work_log_004 ON daily_work_log (created_at DESC);

COMMENT ON TABLE daily_work_log IS '통합 일일 업무 요약';
COMMENT ON COLUMN daily_work_log.user_id IS '사용자 FK';
COMMENT ON COLUMN daily_work_log.target_date IS '요약 대상 날짜';
COMMENT ON COLUMN daily_work_log.content IS '통합 요약 텍스트';
COMMENT ON COLUMN daily_work_log.embedding IS '요약 임베딩 벡터 (1024차원)';


-- jira_user 테이블 (Jira 사용자 정보)
CREATE TABLE IF NOT EXISTS jira_user
(
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT       NULL,
    account_id    VARCHAR(128) NOT NULL,
    active        BOOLEAN      NOT NULL DEFAULT TRUE,
    display_name  VARCHAR(255) NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    url           VARCHAR(512) NOT NULL,
    project       VARCHAR(100) NULL,

    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_jira_user_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,

    CONSTRAINT uq_jira_user_account_id UNIQUE (account_id),
    CONSTRAINT uq_jira_user_user_id UNIQUE (user_id)
);

CREATE TRIGGER tr_jira_user_updated_at
    BEFORE UPDATE
    ON jira_user
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_jira_user_001 ON jira_user (user_id);
CREATE INDEX idx_jira_user_002 ON jira_user (account_id);
CREATE INDEX idx_jira_user_003 ON jira_user (created_at DESC);

COMMENT ON TABLE jira_user IS 'Jira 사용자 정보 테이블';
COMMENT ON COLUMN jira_user.account_id IS 'Jira 계정 ID (UNIQUE)';
COMMENT ON COLUMN jira_user.active IS '활성 상태';
COMMENT ON COLUMN jira_user.display_name IS 'Jira 표시 이름';
COMMENT ON COLUMN jira_user.email_address IS 'Jira 이메일';
COMMENT ON COLUMN jira_user.url IS 'Jira 프로필 URL';
COMMENT ON COLUMN jira_user.project IS 'Jira 프로젝트명 (선택적)';
COMMENT ON COLUMN jira_user.user_id IS '사용자 FK';


-- jira_event 테이블 (Jira 이슈 수집 데이터)
CREATE TABLE IF NOT EXISTS jira_event
(
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT       NOT NULL,
    jira_user_id BIGINT       NOT NULL,
    issue_id     VARCHAR(100) NOT NULL,
    issue_key    VARCHAR(100) NOT NULL,
    target_date  DATE         NOT NULL,
    issue        JSONB        NOT NULL,
    changelog    JSONB        NULL,

    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_jira_event_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_jira_event_jira_user FOREIGN KEY (jira_user_id) REFERENCES jira_user (id) ON DELETE RESTRICT,
);

CREATE TRIGGER tr_jira_event_updated_at
    BEFORE UPDATE
    ON jira_event
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_jira_event_001 ON jira_event (user_id, target_date);
CREATE INDEX idx_jira_event_002 ON jira_event (target_date);
CREATE INDEX idx_jira_event_003 ON jira_event (created_at DESC);

COMMENT ON TABLE jira_event IS 'Jira 이슈 수집 데이터';
COMMENT ON COLUMN jira_event.user_id IS '사용자 FK';
COMMENT ON COLUMN jira_event.jira_user_id IS 'Jira 사용자 FK';
COMMENT ON COLUMN jira_event.issue_key IS 'Jira 이슈 키 (FMP-123)';
COMMENT ON COLUMN jira_event.target_date IS '수집 대상 날짜';
COMMENT ON COLUMN jira_event.issue IS '이슈 원본 데이터 (JSONB)';
COMMENT ON COLUMN jira_event.changelog IS '변경 이력 데이터 (JSONB)';


-- slack_user 테이블 (Slack 사용자 정보)
CREATE TABLE IF NOT EXISTS slack_user
(
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT       NULL,
    member_id    VARCHAR(128) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    real_name    VARCHAR(255) NOT NULL,
    email        VARCHAR(255) NULL,

    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_slack_user_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,

    CONSTRAINT uq_slack_user_member_id UNIQUE (member_id),
    CONSTRAINT uq_slack_user_user_id UNIQUE (user_id)
);

CREATE TRIGGER tr_slack_user_updated_at
    BEFORE UPDATE
    ON slack_user
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_slack_user_001 ON slack_user (user_id);
CREATE INDEX idx_slack_user_002 ON slack_user (member_id);
CREATE INDEX idx_slack_user_003 ON slack_user (created_at DESC);

COMMENT ON TABLE slack_user IS 'Slack 사용자 정보 테이블';
COMMENT ON COLUMN slack_user.member_id IS 'Slack 멤버 ID (UNIQUE)';
COMMENT ON COLUMN slack_user.display_name IS 'Slack 표시 이름';
COMMENT ON COLUMN slack_user.real_name IS 'Slack 실제 이름';
COMMENT ON COLUMN slack_user.email IS 'Slack 이메일';
COMMENT ON COLUMN slack_user.user_id IS '사용자 FK';


-- slack_message 테이블 (Slack 메시지 수집 데이터)
CREATE TABLE IF NOT EXISTS slack_message
(
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT       NOT NULL,
    slack_user_id BIGINT       NOT NULL,
    target_date   DATE         NOT NULL,
    channel_id    VARCHAR(100) NOT NULL,
    channel_name  VARCHAR(255) NOT NULL,
    message_ts    VARCHAR(100) NOT NULL,
    message_text  TEXT         NOT NULL DEFAULT '',
    message       JSONB        NOT NULL,
    thread_ts     VARCHAR(100) NULL,

    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_slack_message_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_slack_message_slack_user FOREIGN KEY (slack_user_id) REFERENCES slack_user (id) ON DELETE RESTRICT
);

CREATE TRIGGER tr_slack_message_updated_at
    BEFORE UPDATE
    ON slack_message
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_slack_message_001 ON slack_message (user_id, target_date);
CREATE INDEX idx_slack_message_002 ON slack_message (target_date);
CREATE INDEX idx_slack_message_003 ON slack_message (created_at DESC);

COMMENT ON TABLE slack_message IS 'Slack 메시지 수집 데이터';
COMMENT ON COLUMN slack_message.user_id IS '사용자 FK';
COMMENT ON COLUMN slack_message.slack_user_id IS 'Slack 사용자 FK';
COMMENT ON COLUMN slack_message.target_date IS '수집 대상 날짜';
COMMENT ON COLUMN slack_message.channel_id IS 'Slack 채널 ID';
COMMENT ON COLUMN slack_message.channel_name IS 'Slack 채널 이름';
COMMENT ON COLUMN slack_message.message_ts IS 'Slack 메시지 타임스탬프 (고유 ID)';
COMMENT ON COLUMN slack_message.message_text IS '메시지 본문 (평문)';
COMMENT ON COLUMN slack_message.message IS '메시지 원본 데이터 (JSONB)';
COMMENT ON COLUMN slack_message.thread_ts IS '스레드 부모 타임스탬프';
