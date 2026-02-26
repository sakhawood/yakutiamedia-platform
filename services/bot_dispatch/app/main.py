import asyncio
import logging
from telegram.ext import ApplicationBuilder

from .config import BOT_TOKEN
from .bot_photographers import register_handlers, check_orders


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def main():
    print("BOT B STARTING")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # регистрация кнопок и обработчиков
    register_handlers(application)

    # проверка заказов каждые 30 секунд
    application.job_queue.run_repeating(
        check_orders,
        interval=30,
        first=5
    )

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.idle()


if __name__ == "__main__":
    asyncio.run(main())