from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from telegram.ext import (
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from core.db.pool import get_pool

ASK_PHOTOGRAPHERS = 1
ASK_DURATION = 2
ASK_ADMIN_COMMENT = 3
CONFIRM_START = 4

async def current_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pool = await get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, event_date, start_time
            FROM events
            WHERE status='waiting'
            AND admin_id IS NULL
            ORDER BY event_date
            """
        )

    if not rows:
        await query.edit_message_text("Нет новых заявок")
        return

    keyboard = []

    for r in rows:
        text = f"{r['id']} | {r['event_date']} {r['start_time']}"
        keyboard.append(
            [InlineKeyboardButton(text, callback_data=f"open_event:{r['id']}")]
        )

    keyboard.append([InlineKeyboardButton("Назад", callback_data="admin_menu")])

    await query.edit_message_text(
        "Новые заявки",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def open_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    event_id = query.data.split(":")[1]

    pool = get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM events
            WHERE id=$1
            """,
            event_id,
        )

    if not row:
        await query.edit_message_text("Заказ не найден")
        return

    text = (
        f"Заказ №{row['id']}\n\n"
        f"Категория: {row['category']}\n"
        f"Дата: {row['event_date']}\n"
        f"Время: {row['start_time']}\n"
        f"Локация: {row['location']}\n\n"
        f"Описание:\n{row['description']}\n\n"
        f"Телефон:\n{row['client_phone']}"
    )

    keyboard = [
        [InlineKeyboardButton("Подтвердить заказ", callback_data=f"confirm_event:{event_id}")],
        [InlineKeyboardButton("Изменить заказ", callback_data=f"edit_event:{event_id}")],
        [InlineKeyboardButton("Удалить заказ", callback_data=f"delete_event:{event_id}")],
        [InlineKeyboardButton("Назад", callback_data="current_events")],
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    event_id = query.data.split(":")[1]

    pool = get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE events
            SET status='cancelled'
            WHERE id=$1
            """,
            event_id,
        )

    await query.edit_message_text("Заказ удалён")

    await current_events(update, context)
    return

    return await current_events(update, context)

async def confirm_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    event_id = query.data.split(":")[1]
    admin_id = query.from_user.id

    pool = get_pool()

    async with pool.acquire() as conn:

        result = await conn.execute(
            """
            UPDATE events
            SET admin_id=$1
            WHERE id=$2
            AND admin_id IS NULL
            """,
            admin_id,
            event_id
        )

    if result == "UPDATE 0":
        await query.edit_message_text(
            "Этот заказ уже взял другой администратор"
        )
        return ConversationHandler.END

    context.user_data["event_id"] = event_id

    await query.edit_message_text(
        "Введите количество фотографов:"
    )

    return ASK_PHOTOGRAPHERS

async def ask_photographers(update: Update, context: ContextTypes.DEFAULT_TYPE):

    photographers = update.message.text.strip()

    if not photographers.isdigit():
        await update.message.reply_text("Введите число фотографов")
        return ASK_PHOTOGRAPHERS

    photographers = int(photographers)

    if photographers < 1 or photographers > 20:
        await update.message.reply_text("Введите число от 1 до 20")
        return ASK_PHOTOGRAPHERS


    pool = get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE events
            SET required_photographers=$1
            WHERE id=$2
            """,
            photographers,
            context.user_data["event_id"]
        )

    context.user_data["photographers"] = photographers

    await update.message.reply_text(
        "Введите длительность мероприятия (часов):"
    )

    return ASK_DURATION

async def ask_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):

    duration = update.message.text.strip()

    if not duration.isdigit():
        await update.message.reply_text("Введите длительность числом")
        return ASK_DURATION

    duration = int(duration)

    pool = get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE events
            SET event_duration=$1
            WHERE id=$2
            """,
            duration,
            context.user_data["event_id"]
        )

    context.user_data["duration"] = duration

    await update.message.reply_text(
        "Введите комментарий администратора:"
    )

    return ASK_ADMIN_COMMENT

async def ask_admin_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    comment = update.message.text

    pool = get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE events
            SET admin_comment=$1
            WHERE id=$2
            """,
            comment,
            context.user_data["event_id"]
        )

    context.user_data["comment"] = comment

    text = (
        f"Проверьте заказ\n\n"
        f"Фотографов: {context.user_data['photographers']}\n"
        f"Длительность: {context.user_data['duration']} часов\n\n"
        f"Комментарий:\n{comment}"
    )

    keyboard = [
        [InlineKeyboardButton(
            "Запустить заказ",
            callback_data="start_event"
        )]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CONFIRM_START

async def start_event(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    event_id = context.user_data.get("event_id")

    if not event_id:
        await query.edit_message_text("Ошибка: заказ не найден")
        return ConversationHandler.END

    pool = get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE events
            SET status='в работу'
            WHERE id=$1
            """,
            event_id
        )

    await query.edit_message_text(
        "Заказ отправлен фотографам"
    )

    return ConversationHandler.END

async def my_events(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id
    pool = get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, event_date, start_time, status
            FROM events
            WHERE admin_id=$1
            AND status!='cancelled'
            ORDER BY event_date
            """,
            admin_id
        )

    if not rows:
        await query.edit_message_text("У вас нет заказов")
        return

    keyboard = []

    for r in rows:

        text = f"{r['id']} | {r['event_date']} {r['start_time']} | {r['status']}"

        keyboard.append([
            InlineKeyboardButton(
                text,
                callback_data=f"open_event:{r['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("Назад", callback_data="admin_menu")
    ])

    await query.edit_message_text(
        "Мои заказы",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
