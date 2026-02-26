import asyncio
from telegram.ext import ApplicationBuilder
from .config import BOT_TOKEN, CHECK_INTERVAL
from .bot_photographers import check_orders

async def main():
    print("BOT B STARTING")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.job_queue.run_repeating(
        check_orders,
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