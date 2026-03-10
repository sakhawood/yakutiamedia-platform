from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler


async def open_event(update, context):

    query = update.callback_query
    await query.answer()

    event_id = query.data.split("_")[1]

    pool = context.application.bot_data["db_pool"]

    async with pool.acquire() as conn:

        event = await conn.fetchrow("""
            SELECT *
            FROM events
            WHERE id=$1
        """, event_id)

    keyboard = [
        [InlineKeyboardButton("Отправить в работу", callback_data=f"work_{event_id}")]
    ]

    text = f"""
Заявка {event_id}

Тип: {event['type']}
Категория: {event['category']}
Дата: {event['event_date']}
Время: {event['start_time']}

Описание:
{event['description']}
"""

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_to_work(update, context):

    query = update.callback_query
    await query.answer()

    event_id = query.data.split("_")[1]

    pool = context.application.bot_data["db_pool"]

    async with pool.acquire() as conn:

        await conn.execute("""
            UPDATE events
            SET status='в работу',
                admin_status='done'
            WHERE id=$1
        """, event_id)

    await query.edit_message_text("Заявка отправлена в работу")
