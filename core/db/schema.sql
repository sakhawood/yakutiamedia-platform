-- USERS
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    first_name TEXT,
    username TEXT,
    role TEXT CHECK (role IN ('manager','photographer')),
    is_active BOOLEAN DEFAULT TRUE,
    response_time_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_role_active 
ON users(role, is_active, response_time_minutes);

-- EVENTS
CREATE TABLE events (
    id VARCHAR(20) PRIMARY KEY,
    client_name TEXT,
    phone TEXT,
    description TEXT,
    location TEXT,
    event_date DATE,
    start_time TIME,
    category TEXT,
    type TEXT,
    required_photographers INTEGER DEFAULT 0,
    status TEXT,
    manager_id BIGINT REFERENCES users(telegram_id),
    version INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT NOW(),
    recalculated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_status ON events(status);

-- ASSIGNMENTS
CREATE TABLE assignments (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(20) REFERENCES events(id) ON DELETE CASCADE,
    photographer_id BIGINT REFERENCES users(telegram_id),
    status TEXT CHECK (status IN ('accepted','cancelled','finished')),
    accepted_at TIMESTAMP,
    finished_at TIMESTAMP,
    upload_link TEXT,
    cancel_reason TEXT,
    requeue_priority BOOLEAN DEFAULT FALSE,
    offer_active BOOLEAN DEFAULT FALSE,
    priority_exhausted BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_assignments_event 
ON assignments(event_id);

-- NOTIFICATIONS
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(20),
    user_id BIGINT,
    role TEXT,
    notified_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_event_user 
ON notifications(event_id, user_id);

-- AUDIT
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    entity TEXT,
    entity_id TEXT,
    action TEXT,
    source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);