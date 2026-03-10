import asyncio
import asyncpg
import os


async def main():

    conn = await asyncpg.connect(
        dsn=os.getenv("DATABASE_URL"),
        ssl="require"
    )

    print("ADDING BOT C FIELDS")

    await conn.execute("""
        ALTER TABLE events
        ADD COLUMN IF NOT EXISTS admin_id BIGINT;
    """)

    await conn.execute("""
        ALTER TABLE events
        ADD COLUMN IF NOT EXISTS admin_assigned_at TIMESTAMP;
    """)

    await conn.execute("""
        ALTER TABLE events
        ADD COLUMN IF NOT EXISTS hours INTEGER;
    """)

    await conn.execute("""
        ALTER TABLE events
        ADD COLUMN IF NOT EXISTS admin_status TEXT DEFAULT 'waiting';
    """)

    await conn.execute("""
        ALTER TABLE events
        ADD COLUMN IF NOT EXISTS admin_last_activity TIMESTAMP;
    """)

    print("EVENTS TABLE UPDATED")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admins(
            telegram_id BIGINT PRIMARY KEY,
            name TEXT,
            active BOOLEAN DEFAULT FALSE,
            last_activity TIMESTAMP
        );
    """)

    print("ADMINS TABLE READY")

    await conn.close()


asyncio.run(main())
