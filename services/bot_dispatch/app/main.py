import asyncio
from telegram.ext import ApplicationBuilder
from .config import BOT_TOKEN, CHECK_INTERVAL
from .event_monitor import monitor_events
from .bot_photographers import register_handlers
from core.db.pool import get_pool


async def main():

    print("BOT B STARTING")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # создаём пул PostgreSQL
    pool = await get_pool()
    application.bot_data["db_pool"] = pool

    register_handlers(application)
    print("HANDLERS REGISTERED", flush=True)

    application.job_queue.run_repeating(
        monitor_events,
        interval=CHECK_INTERVAL,
        first=10
    )

    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())