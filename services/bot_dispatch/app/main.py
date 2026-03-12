from telegram.ext import ApplicationBuilder
from .config import BOT_TOKEN, CHECK_INTERVAL
from .event_monitor import monitor_events
from .bot_photographers import register_handlers
from core.db.pool import get_pool

import asyncio


def main():

    print("BOT B STARTING", flush=True)

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # создаём подключение к базе
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    pool = loop.run_until_complete(get_pool())

    # кладём пул в bot_data
    application.bot_data["db_pool"] = pool

    print("DB POOL CONNECTED", flush=True)

    register_handlers(application)

    print("HANDLERS REGISTERED", flush=True)

    application.job_queue.run_repeating(
        monitor_events,
        interval=CHECK_INTERVAL,
        first=10
    )

    print("EVENT MONITOR STARTED", flush=True)

    application.run_polling()


if __name__ == "__main__":
    main()
