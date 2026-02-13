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
    timezone   VARCHAR(50)  NOT NULL DEFAULT 'Asia/Seoul',

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


-- github_user_secret 테이블
CREATE TABLE IF NOT EXISTS github_user_secret
(
    id                    SERIAL PRIMARY KEY,
    user_id               BIGINT       NOT NULL,
    username              VARCHAR(50)  NOT NULL,
    personal_access_token VARCHAR(255) NOT NULL,
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    deactivate_at         TIMESTAMPTZ,

    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    is_deleted            BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_at            TIMESTAMPTZ  NOT NULL DEFAULT '9999-12-31 14:59:59+00',

    CONSTRAINT fk_github_user_secret_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE TRIGGER tr_github_user_secret_updated_at
    BEFORE UPDATE
    ON github_user_secret
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_github_user_secret_001 ON github_user_secret (user_id);
CREATE INDEX idx_github_user_secret_002 ON github_user_secret (created_at DESC);


-- github_event 테이블 (GitHub 이벤트 + 커밋 수집 데이터)
CREATE TABLE IF NOT EXISTS github_event
(
    id                    BIGSERIAL PRIMARY KEY,
    user_id               BIGINT      NOT NULL,
    github_user_secret_id INT         NOT NULL,
    event_id              VARCHAR(100) NOT NULL,
    target_date           DATE        NOT NULL,
    event                 JSONB       NOT NULL,
    commit                JSONB       NULL,

    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_github_event_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_github_event_secret FOREIGN KEY (github_user_secret_id) REFERENCES github_user_secret (id) ON DELETE RESTRICT,

    CONSTRAINT uq_github_event_event_id UNIQUE (event_id)
);

CREATE TRIGGER tr_github_event_updated_at
    BEFORE UPDATE
    ON github_event
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_github_event_001 ON github_event (user_id, target_date);
CREATE INDEX idx_github_event_002 ON github_event (target_date);
CREATE INDEX idx_github_event_003 ON github_event (created_at DESC);
