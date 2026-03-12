from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram import ReplyKeyboardMarkup
from .keyboards import admin_keyboard
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

async def start(update, context):

    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("Открыть сессию", callback_data="activate_admin")]
    ]

    msg = await update.message.reply_text(
        "Панель администратора\n\nСессия закрыта",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    context.user_data["panel_message_id"] = msg.message_id


async def update_panel(update, context, text, keyboard):

    chat_id = update.effective_chat.id
    message_id = context.user_data.get("panel_message_id")

    if not message_id:
        msg = await update.effective_message.reply_text(
            text,
            reply_markup=keyboard
        )
        context.user_data["panel_message_id"] = msg.message_id
        return

    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=keyboard
    )


async def text_router(update, context):

    text = update.message.text

    if text == "Текущие заявки":
        await current_events(update, context)

    elif text == "Мои заказы":
        await my_events(update, context)

    elif text == "Закрыть сессию":
        await close_session(update, context)


async def activate_session(update, context):

    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE admins
            SET active = TRUE
            WHERE telegram_id=$1
            """,
            admin_id
        )

    keyboard = [
        [InlineKeyboardButton("Текущие заявки", callback_data="current_events")],
        [InlineKeyboardButton("Мои заказы", callback_data="my_events")],
        [InlineKeyboardButton("Закрыть сессию", callback_data="close_admin")]
    ]

    await update_panel(
        update,
        context,
        "Сессия администратора открыта",
        InlineKeyboardMarkup(keyboard)
    )


async def close_session(update, context):

    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE admins
            SET active = FALSE
            WHERE telegram_id=$1
            """,
            admin_id
        )

    keyboard = [
        [InlineKeyboardButton("Открыть сессию", callback_data="activate_admin")]
    ]

    await update_panel(
        update,
        context,
        "Сессия закрыта",
        InlineKeyboardMarkup(keyboard)
    )



async def admin_menu(update, context):

    keyboard = [
        [InlineKeyboardButton("Текущие заявки", callback_data="current_events")],
        [InlineKeyboardButton("Мои заказы", callback_data="my_events")],
        [InlineKeyboardButton("Закрыть сессию", callback_data="close_admin")]
    ]

    query = update.callback_query

    if query:
        await query.answer()

    await update_panel(
        update,
        context,
        "Панель администратора",
        InlineKeyboardMarkup(keyboard)
    )
  

async def current_events(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query:
        await query.answer()

    pool = await get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, category, event_date, start_time
            FROM events
            WHERE status='waiting'
            ORDER BY event_date
            """
        )

    if not rows:

        keyboard = [
            [InlineKeyboardButton("Назад", callback_data="admin_menu")]
        ]

        await query.edit_message_text(
            "Нет новых заявок",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("В меню", callback_data="admin_menu")]
            ])
        )

        return

    keyboard = []

    for r in rows:

        date = str(r["event_date"])
        time = str(r["start_time"])[:5]
        category = r["category"]

        text = f"{date} {time} | {category}"

        keyboard.append([
            InlineKeyboardButton(
                text,
                callback_data=f"open_event:{r['id']}:current"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("Назад", callback_data="admin_menu")
    ])

    await update_panel(
        update,
        context,
        "Текущие заявки",
        InlineKeyboardMarkup(keyboard)
    )

async def open_event(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split(":")

    event_id = data[1]
    source = data[2] if len(data) > 2 else "current"

    back = "my_events" if source == "my" else "current_events"

    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM events
            WHERE id=$1
            """,
            event_id
        )

    if not row:

        await query.edit_message_text(
            "Заказ не найден"
        )

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
        [InlineKeyboardButton("Удалить заказ", callback_data=f"delete_confirm:{event_id}")],
        [InlineKeyboardButton("Назад", callback_data=back)],
    ]
    

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def edit_event(update, context):

    query = update.callback_query
    await query.answer()

    event_id = query.data.split(":")[1]

    await query.edit_message_text(
        f"Редактирование заказа {event_id} пока не реализовано"
    )

async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    event_id = query.data.split(":")[1]

    keyboard = [
        [InlineKeyboardButton("Удалить", callback_data=f"delete_event:{event_id}")],
        [InlineKeyboardButton("Отмена", callback_data="admin_menu")]
    ]

    await query.edit_message_text(
        "Вы уверены, что хотите удалить заказ?",
        reply_markup=InlineKeyboardMarkup(keyboard)
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
            event_id
        )

    keyboard = [
        [InlineKeyboardButton("В меню", callback_data="admin_menu")]
    ]

    await query.edit_message_text(
        "Заказ удалён",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("В меню", callback_data="admin_menu")]
        ])
    )



async def confirm_event(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    event_id = query.data.split(":")[1]
    admin_id = query.from_user.id

    pool = await get_pool()

    async with pool.acquire() as conn:

        row = await conn.fetchrow(
            """
            SELECT status, admin_id
            FROM events
            WHERE id=$1
            """,
            event_id
        )

        if not row:
            await query.edit_message_text("Заявка не найдена")
            return ConversationHandler.END


        # если заказ уже в работе
        if row["status"] != "waiting":

            await query.edit_message_text(
                "Эта заявка уже обрабатывается",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("В меню", callback_data="admin_menu")]
                ])
            )

            return ConversationHandler.END


        # закрепляем заявку
        await conn.execute(
            """
            UPDATE events
            SET admin_id=$1,
                status='assigned'
            WHERE id=$2
            """,
            admin_id,
            event_id
        )

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
    admin_id = query.from_user.id

    if not event_id:

        await query.edit_message_text(
            "Ошибка: заказ не найден"
        )

        return ConversationHandler.END

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE events
            SET status='active',
                admin_id=$1
            WHERE id=$2
            """,
            admin_id,
            event_id
        )

    keyboard = [
        [InlineKeyboardButton("В меню", callback_data="admin_menu")]
    ]

    await query.edit_message_text(
        "Заказ отправлен фотографам",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("В меню", callback_data="admin_menu")]
        ])
    )
    context.user_data.clear()

    return ConversationHandler.END



async def my_events(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query:
        await query.answer()

    admin_id = update.effective_user.id
    pool = await get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, category, event_date, start_time, status
            FROM events
            WHERE admin_id=$1
            AND status!='waiting'
            AND status!='cancelled'
            ORDER BY event_date
            """,
            admin_id
        )

    if not rows:

        keyboard = [
            [InlineKeyboardButton("Назад", callback_data="admin_menu")]
        ]

        await query.edit_message_text(
            "У вас нет заказов",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("В меню", callback_data="admin_menu")]
            ])
        )

        return

    keyboard = []

    for r in rows:

        date = str(r["event_date"])
        time = str(r["start_time"])[:5]
        category = r["category"]
        status = r["status"]

        text = f"{date} {time} | {category} | {status}"

        keyboard.append([
            InlineKeyboardButton(
                text,
                callback_data=f"open_event:{r['id']}:my"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("Назад", callback_data="admin_menu")
    ])

    await update_panel(
        update,
        context,
        "Мои заказы",
        InlineKeyboardMarkup(keyboard)
    )

