from telegram import InlineKeyboardMarkup, InlineKeyboardButton


async def monitor_events(context):

    pool = context.application.bot_data["db_pool"]
    bot = context.application.bot

    async with pool.acquire() as conn:

        events = await conn.fetch("""
            SELECT *
            FROM events
            WHERE status='waiting'
            AND admin_id IS NULL
        """)

        if not events:
            return

        admin = await conn.fetchrow("""
            SELECT *
            FROM admins
            WHERE active=TRUE
            ORDER BY last_activity ASC
            LIMIT 1
        """)

        if not admin:
            return

        admin_id = admin["telegram_id"]

        for event in events:

            event_id = event["id"]

            await conn.execute("""
                UPDATE events
                SET admin_id=$1,
                    admin_status='assigned',
                    admin_assigned_at=NOW(),
                    admin_last_activity=NOW()
                WHERE id=$2
            """, admin_id, event_id)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "Открыть заявку",
                        callback_data=f"open_{event_id}"
                    )
                ]
            ]

            text = f"""
Новая заявка

ID: {event_id}

Тип: {event['type']}
Категория: {event['category']}

Дата: {event['event_date']}
Время: {event['start_time']}

Место: {event['location']}
"""

            await bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
