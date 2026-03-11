import os
from core.db.init_db import ensure_indexes

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)

from .monitor import monitor_events

from .handlers import (
    open_event,
    confirm_event,
    ask_photographers,
    ask_duration,
    ask_admin_comment,
    start_event,
    my_events,
    ASK_PHOTOGRAPHERS,
    ASK_DURATION,
    ASK_ADMIN_COMMENT,
    CONFIRM_START
)


def main():

    print("BOT C STARTING", flush=True)

    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ensure_indexes())

    app = ApplicationBuilder().token(
        os.getenv("BOT_TOKEN")
    ).build()

    conv_confirm_event = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(confirm_event, pattern="^confirm_event:")
        ],
        states={
            ASK_PHOTOGRAPHERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_photographers)
            ],
            ASK_DURATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_duration)
            ],
            ASK_ADMIN_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_admin_comment)
            ],
            CONFIRM_START: [
                CallbackQueryHandler(start_event, pattern="^start_event$")
            ],
        },
        fallbacks=[]
    )

    app.add_handler(CallbackQueryHandler(open_event, pattern="^open_event:"))
    app.add_handler(CallbackQueryHandler(my_events, pattern="^my_events$"))
    app.add_handler(conv_confirm_event)

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
