from core.db.pool import get_pool


async def ensure_indexes():

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_status
        ON events(status)
        """)

        await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_admin
        ON events(admin_id)
        """)

        await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_date
        ON events(event_date)
        """)
