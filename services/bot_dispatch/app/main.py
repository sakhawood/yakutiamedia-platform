import asyncio
from telegram.ext import ApplicationBuilder
from .config import BOT_TOKEN, CHECK_INTERVAL
from .event_monitor import monitor_events

async def main():
    print("BOT B STARTING")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    from .sheets import SheetsClient

    sheets = SheetsClient()
    application.bot_data["sheets"] = sheets

    application.job_queue.run_repeating(
        monitor_events,
        interval=CHECK_INTERVAL,
        first=10
    )

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # держим процесс живым
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())