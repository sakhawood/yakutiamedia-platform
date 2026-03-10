import asyncio
import asyncpg
import os


async def main():

    conn = await asyncpg.connect(
        dsn=os.getenv("DATABASE_URL"),
        ssl="require"
    )

    rows = await conn.fetch("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'events'
        ORDER BY ordinal_position
    """)

    for r in rows:
        print(r["column_name"], "|", r["data_type"])

    await conn.close()


asyncio.run(main())
