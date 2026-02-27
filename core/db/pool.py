import asyncpg
import os

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            ssl="require"
        )
    return _pool