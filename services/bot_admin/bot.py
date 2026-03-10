import os
import asyncpg
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler
)

from .monitor import monitor_events
from .handlers import open_event, send_to_work


_pool = None


async def get_pool():

    global _pool

    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            ssl="require"
        )

    return _pool


def main():

    print("BOT C STARTING", flush=True)

    app = ApplicationBuilder().token(
        os.getenv("BOT_TOKEN")
    ).build()

    import asyncio

    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(get_pool())

    app.bot_data["db_pool"] = pool

    app.add_handler(
        CallbackQueryHandler(open_event, pattern="open_")
    )

    app.add_handler(
        CallbackQueryHandler(send_to_work, pattern="work_")
    )
    
    print("HANDLERS REGISTERED", flush=True)
    
    app.job_queue.run_repeating(
        monitor_events,
        interval=10,
        first=10
    )

    print("MONITOR STARTED", flush=True)

    app.run_polling()


if __name__ == "__main__":
    main()
