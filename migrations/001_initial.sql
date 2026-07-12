CREATE TABLE companies (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    notification_email VARCHAR(320),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL,
    company_id VARCHAR(36) REFERENCES companies(id) ON DELETE SET NULL,
    language_preference VARCHAR(10) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ
);

CREATE TABLE email_settings (
    id INTEGER PRIMARY KEY,
    smtp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    smtp_host VARCHAR(255),
    smtp_port INTEGER,
    smtp_username VARCHAR(320),
    smtp_password TEXT,
    smtp_from_address VARCHAR(320),
    smtp_from_name VARCHAR(120),
    smtp_use_tls BOOLEAN NOT NULL DEFAULT TRUE,
    smtp_use_ssl BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE company_variables (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    label VARCHAR(200) NOT NULL,
    field_type VARCHAR(30) NOT NULL,
    options JSON,
    required BOOLEAN NOT NULL DEFAULT FALSE,
    help_text TEXT,
    applies_to VARCHAR(30) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE requests (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_by_user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    process_type VARCHAR(30) NOT NULL,
    employee_name VARCHAR(200) NOT NULL,
    relevant_date DATE NOT NULL,
    notes TEXT,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE request_variable_values (
    id VARCHAR(36) PRIMARY KEY,
    request_id VARCHAR(36) NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    company_variable_id VARCHAR(36) NOT NULL REFERENCES company_variables(id) ON DELETE CASCADE,
    value TEXT,
    CONSTRAINT uq_request_variable UNIQUE (request_id, company_variable_id)
);

CREATE TABLE audit_log (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(120) NOT NULL,
    target_type VARCHAR(80),
    target_id VARCHAR(36),
    created_at TIMESTAMPTZ NOT NULL
);
