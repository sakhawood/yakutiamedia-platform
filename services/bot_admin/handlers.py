from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram import ReplyKeyboardMarkup
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

def admin_keyboard():

    keyboard = [
        ["Текущие заявки"],
        ["Мои заказы"],
        ["Закрыть сессию"]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )

async def start(update, context):

    await update.message.reply_text(
        "Панель администратора",
        reply_markup=admin_keyboard()
    )

async def text_router(update, context):

    text = update.message.text

    if text == "Текущие заявки":
        return await current_events(update, context)

    if text == "Мои заказы":
        await my_events(update, context)

    if text == "Закрыть сессию":
        await update.message.reply_text("Сессия закрыта")

async def activate_session(update, context):
    query = update.callback_query
    await query.answer()

    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE admins
            SET active=TRUE
            WHERE telegram_id=$1
            """,
            query.from_user.id
        )

    await admin_menu(update, context)

async def close_session(update, context):
    query = update.callback_query
    await query.answer()

    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE admins
            SET active=FALSE
            WHERE telegram_id=$1
            """,
            query.from_user.id
        )

    await query.edit_message_text("Сессия администратора закрыта")

async def admin_menu(update, context):
    query = update.callback_query

    keyboard = [
        [InlineKeyboardButton("Текущие заявки", callback_data="current_events")],
        [InlineKeyboardButton("Мои заказы", callback_data="my_events")],
        [InlineKeyboardButton("Закрыть сессию", callback_data="close_admin")]
    ]

    await query.edit_message_text(
        "Панель администратора",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
  

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
        await query.edit_message_text(
            "Нет новых заявок",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data="admin_menu")]
            ])
        )
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

    data = query.data.split(":")

    if len(data) < 2:
        await query.answer("Ошибка данных", show_alert=True)
        return

    event_id = data[1]

    pool = await get_pool()

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
        [InlineKeyboardButton("Назад", callback_data="my_events")],
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    event_id = query.data.split(":")[1]

    pool = await get_pool()

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

async def edit_event(update, context):

    query = update.callback_query
    await query.answer()

    event_id = query.data.split(":")[1]

    await query.edit_message_text(
        f"Редактирование заказа {event_id} пока не реализовано"
    )


async def confirm_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    event_id = query.data.split(":")[1]
    admin_id = query.from_user.id

    pool = await get_pool()

    row = await conn.fetchrow(
        "SELECT admin_id FROM events WHERE id=$1",
        event_id
    )

    if row["admin_id"] != admin_id:
        await query.edit_message_text("Этот заказ закреплен за другим администратором")
        return ConversationHandler.END

    async with pool.acquire() as conn:

        result = await conn.execute(
            """
            UPDATE events
            SET admin_id=$1
            WHERE id=$2
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


    pool = await get_pool()

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

    pool = await get_pool()

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

    pool = await get_pool()

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

    pool = await get_pool()

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

    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message

    events = get_admin_events()   # ваша функция получения заказов

        if not events:
            await message.reply_text("У вас нет заказов")
            return

        text = "Ваши заказы:\n"

        for e in events:
            text += f"{e['id']} | {e['status']}\n"

        await message.reply_text(text)

    admin_id = query.from_user.id
    pool = await get_pool()

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

        date = str(r["event_date"])
        time = str(r["start_time"])[:5]

        text = f"{date} {time} | {r['status']} | {r['id']}"

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
