from telegram.ext import ApplicationBuilder
from .config import BOT_TOKEN, CHECK_INTERVAL
from .event_monitor import monitor_events
from .bot_photographers import register_handlers
from .sheets import SheetsClient


def main():
    print("BOT B STARTING")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    sheets = SheetsClient()
    application.bot_data["sheets"] = sheets

    register_handlers(application)
    print("HANDLERS REGISTERED", flush=True)

    application.job_queue.run_repeating(
        monitor_events,
        interval=CHECK_INTERVAL,
        first=10
    )

    application.run_polling()


if __name__ == "__main__":
    main()