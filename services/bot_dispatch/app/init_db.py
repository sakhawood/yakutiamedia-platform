import asyncpg
import asyncio
import os

DATABASE_URL = os.getenv("DATABASE_URL")


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS photographers (
    telegram_id BIGINT PRIMARY KEY,
    name TEXT,
    username TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    client_name TEXT,
    client_phone TEXT,
    description TEXT,
    location TEXT,
    event_date DATE,
    start_time TIME,
    type TEXT,
    category TEXT,
    required_photographers INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'в работу',
    distribution_priority INTEGER,
    distribution_started_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assignments (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT REFERENCES events(id) ON DELETE CASCADE,
    photographer_id BIGINT REFERENCES photographers(telegram_id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    accepted_at TIMESTAMP,
    completed_at TIMESTAMP,
    link TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(event_id, photographer_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT REFERENCES events(id) ON DELETE CASCADE,
    photographer_id BIGINT REFERENCES photographers(telegram_id) ON DELETE CASCADE,
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(event_id, photographer_id)
);

CREATE INDEX IF NOT EXISTS idx_photographers_active_priority
ON photographers(active, priority);

CREATE INDEX IF NOT EXISTS idx_events_status
ON events(status);

CREATE INDEX IF NOT EXISTS idx_assignments_event_status
ON assignments(event_id, status);

CREATE INDEX IF NOT EXISTS idx_notifications_event
ON notifications(event_id);
"""


async def init():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")

    pool = await asyncpg.create_pool(DATABASE_URL)

    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
        print("DATABASE INITIALIZED SUCCESSFULLY")

    await pool.close()


if __name__ == "__main__":
    asyncio.run(init())