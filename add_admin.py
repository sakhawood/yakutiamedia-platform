import asyncio
import asyncpg
import os


async def main():

    conn = await asyncpg.connect(
        dsn=os.getenv("DATABASE_URL"),
        ssl="require"
    )

    await conn.execute("""
        INSERT INTO admins (telegram_id, name)
        VALUES ($1,$2)
        ON CONFLICT DO NOTHING
    """, 475955973, "Алексей")

    print("ADMIN ADDED")

    await conn.close()


asyncio.run(main())
