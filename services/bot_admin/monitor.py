from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from core.db.pool import get_pool


async def monitor_events(context):

    print("ADMIN MONITOR TICK", flush=True)

    pool = await get_pool()
    bot = context.application.bot

    async with pool.acquire() as conn:

        events = await conn.fetch("""
            SELECT
                id,
                type,
                category,
                location,
                event_date,
                start_time
            FROM events
            WHERE status='waiting'
            AND admin_id IS NULL
            ORDER BY event_date
        """)

        print("WAITING EVENTS:", len(events), flush=True)

        if not events:
            return

        admin = await conn.fetchrow("""
            SELECT *
            FROM admins
            WHERE active=TRUE
            ORDER BY last_activity ASC
            LIMIT 1
        """)

        print("ADMIN FOUND:", admin, flush=True)

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
                        callback_data=f"open_event:{event_id}"
                    )
                ]
            ]

            text = (
                f"📥 Новая заявка\n\n"
                f"ID: {event_id}\n\n"
                f"Тип: {event['type']}\n"
                f"Категория: {event['category']}\n\n"
                f"Дата: {event['event_date']}\n"
                f"Время: {event['start_time']}\n\n"
                f"Место: {event['location']}"
            )

            await bot.edit_message_text(
                chat_id=admin_id,
                message_id=panel_message_id,
                text=text,
                reply_markup=keyboard
            )
            try:
                await bot.edit_message_text(...)
            except:
                msg = await bot.send_message(...)
                context.user_data["panel_message_id"] = msg.message_id
