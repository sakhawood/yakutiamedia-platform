from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler, filters
from datetime import datetime


GROUP_CHAT_ID = -1003824519107 # ← вставь реальный ID группы заявки_Yakutia.media


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    tg_id = user.id
    pool = context.bot_data["db_pool"]

    async with pool.acquire() as conn:

        photographer = await conn.fetchrow("""
            SELECT *
            FROM photographers
            WHERE telegram_id=$1
        """, tg_id)

        if not photographer:
            await conn.execute("""
                INSERT INTO photographers(
                    telegram_id,
                    name,
                    username,
                    active,
                    priority
                )
                VALUES($1,$2,$3,TRUE,0)
            """, tg_id, user.first_name, user.username)

            status = True
        else:
            status = photographer["active"]

    await show_main_menu(update, context, status)

async def toggle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    tg_id = update.effective_user.id
    pool = context.bot_data["db_pool"]

    async with pool.acquire() as conn:

        current = await conn.fetchval("""
            SELECT active
            FROM photographers
            WHERE telegram_id=$1
        """, tg_id)

        new_status = not current

        await conn.execute("""
            UPDATE photographers
            SET active=$1
            WHERE telegram_id=$2
        """, new_status, tg_id)

    await show_main_menu(update, context, new_status)

async def show_main_menu(update, context, status):

    if status:
        status_text = "🟢 Статус: Активен"
        toggle_text = "⛔ Выключить бота"
    else:
        status_text = "🔴 Статус: Пауза"
        toggle_text = "▶ Включить бота"

    keyboard = [
        ["📂 Мои заказы"],
        [toggle_text]
    ]

    print("MENU BUILT", flush=True)

    await update.message.reply_text(
        status_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pool = context.bot_data["db_pool"]
    tg_id = update.effective_user.id

    async with pool.acquire() as conn:

        rows = await conn.fetch("""
            SELECT e.id,
                   e.type,
                   e.event_date,
                   e.start_time,
                   e.category
            FROM assignments a
            JOIN events e ON a.event_id = e.id
            WHERE a.photographer_id=$1
            AND a.status='accepted'
        """, tg_id)

    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
    else:
        message = update.message

    if not rows:
        await message.reply_text("У вас нет активных заказов.")
        return

    keyboard = []

    for r in rows:

        button_text = (
            f"🆔 {r['id']} | "
            f"{r['type']} | "
            f"{r['event_date']} | "
            f"{r['start_time']} | "
            f"{r['category']}"
        )

        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"order_{r['id']}"
            )
        ])

    await message.reply_text(
        "Ваши заказы:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def open_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    event_id = query.data.split("_")[1]
    pool = context.bot_data["db_pool"]

    async with pool.acquire() as conn:

        event = await conn.fetchrow("""
            SELECT *
            FROM events
            WHERE id=$1
        """, event_id)

    if not event:
        await query.edit_message_text("Событие не найдено.")
        return

    text = (
        f"🆔 ID события: {event_id}\n\n"
        f"👤 Заказчик: {event['client_name']}\n"
        f"📞 Телефон: {event['client_phone']}\n\n"
        f"📝 Описание:\n{event['description']}\n\n"
        f"📍 Место: {event['location']}\n\n"
        f"📅 Дата: {event['event_date']}\n"
        f"⏰ Время: {event['start_time']}\n"
        f"📂 Тип: {event['type']}\n"
        f"🏷 Категория: {event['category']}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📤 Отправить ссылку",
                callback_data=f"upload_{event_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отменить участие",
                callback_data=f"cancel_{event_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Назад",
                callback_data="back_orders"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_to_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await my_orders(update, context)

from datetime import datetime

async def accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    tg_id = query.from_user.id
    event_id = query.data.replace("accept_", "", 1)
    pool = context.bot_data["db_pool"]

    async with pool.acquire() as conn:
        async with conn.transaction():

            event = await conn.fetchrow("""
                SELECT *
                FROM events
                WHERE id=$1
                FOR UPDATE
            """, event_id)

            if not event:
                await query.answer("Событие не найдено.", show_alert=True)
                return

            # Проверка: уже принял?
            already = await conn.fetchval("""
                SELECT 1
                FROM assignments
                WHERE event_id=$1
                AND photographer_id=$2
                AND status='accepted'
            """, event_id, tg_id)

            if already:
                await query.answer(
                    "Вы уже приняли это мероприятие.",
                    show_alert=True
                )
                return

            # Сколько уже принято
            accepted = await conn.fetchval("""
                SELECT COUNT(*)
                FROM assignments
                WHERE event_id=$1
                AND status='accepted'
            """, event_id)

            if accepted >= event["required_photographers"]:
                await query.answer(
                    "Набрано необходимое количество фотографов.",
                    show_alert=True
                )
                return

            # Вставка без ON CONFLICT
            await conn.execute("""
                INSERT INTO assignments(
                    event_id,
                    photographer_id,
                    status,
                    accepted_at
                )
                VALUES($1,$2,'accepted',NOW())
            """, event_id, tg_id)

            # Пересчёт после вставки
            accepted_after = accepted + 1

            if accepted_after >= event["required_photographers"]:
                await conn.execute("""
                    UPDATE events
                    SET status='укомплектовано'
                    WHERE id=$1
                """, event_id)

    await query.edit_message_text(
        f"✅ Вы приняли мероприятие {event_id}"
    )

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    tg_id = query.from_user.id
    event_id = query.data.replace("cancel_", "", 1)
    pool = context.bot_data["db_pool"]

    async with pool.acquire() as conn:
        async with conn.transaction():

            await conn.execute("""
                UPDATE assignments
                SET status='cancelled'
                WHERE event_id=$1
                AND photographer_id=$2
            """, event_id, tg_id)

            await conn.execute("""
                UPDATE events
                SET status='в работу'
                WHERE id=$1
            """, event_id)

    await query.edit_message_text(
        f"❌ Вы отменили участие в мероприятии {event_id}"
    )

async def route_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    print("TEXT RECEIVED:", text, flush=True)

    if "заказы" in text.lower():
        await my_orders(update, context)

    elif "выключить" in text.lower() or "включить" in text.lower():
        await toggle_status(update, context)

async def start_upload_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    event_id = query.data.replace("upload_", "", 1)

    context.user_data["awaiting_link"] = event_id

    await query.edit_message_text(
        f"🆔 ID события: {event_id}\n\n"
        f"Отправьте ссылку на фотографии."
    )

async def handle_link_input(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "awaiting_link" not in context.user_data:
        return

    event_id = context.user_data.pop("awaiting_link")
    link = update.message.text.strip()
    tg_id = update.effective_user.id

    pool = context.bot_data["db_pool"]

    async with pool.acquire() as conn:
        async with conn.transaction():

            await conn.execute("""
                UPDATE assignments
                SET status='completed',
                    completed_at=NOW(),
                    link=$1
                WHERE event_id=$2
                AND photographer_id=$3
            """, link, event_id, tg_id)

            finished = await conn.fetchval("""
                SELECT COUNT(*)
                FROM assignments
                WHERE event_id=$1
                AND status='completed'
            """, event_id)

            required = await conn.fetchval("""
                SELECT required_photographers
                FROM events
                WHERE id=$1
            """, event_id)

            if finished >= required:
                await conn.execute("""
                    UPDATE events
                    SET status='завершено'
                    WHERE id=$1
                """, event_id)

    await update.message.reply_text(
        f"✅ Ссылка сохранена для события {event_id}"
    )


def register_handlers(application):

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex("Мои заказы"),
            my_orders
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex("Выключить бота|Включить бота"),
            toggle_status
        )
    )

    application.add_handler(
        CallbackQueryHandler(open_order, pattern="^order_")
    )

    application.add_handler(
        CallbackQueryHandler(back_to_orders, pattern="^back_orders")
    )

    application.add_handler(
        CallbackQueryHandler(accept_order, pattern="^accept_")
    )

    application.add_handler(
        CallbackQueryHandler(cancel_order, pattern="^cancel_")
    )

    application.add_handler(
        CallbackQueryHandler(start_upload_link, pattern="^upload_")
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link_input)
    )