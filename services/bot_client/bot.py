import datetime
import json
import uuid
import string
from datetime import datetime
from telegram.ext import MessageHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters,
    ConversationHandler, ContextTypes
)
import gspread

# ==== ВСТАВЬТЕ СВОЙ ТОКЕН ====
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = -1003824519107 # позже вставим

# ==== Google Sheets ====
google_creds = os.getenv("GOOGLE_CREDENTIALS")

if not google_creds:
    raise ValueError("GOOGLE_CREDENTIALS environment variable is not set")

creds_dict = json.loads(google_creds)
gc = gspread.service_account_from_dict(creds_dict)
sheet = gc.open("Order_Yakutia.media").worksheet("СОБЫТИЯ")

TYPE, CATEGORY, DATE, TIME, PLACE, PEOPLE, NAME, PHONE, DESCRIPTION, CONFIRM = range(10)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [["🚀 Старт заявки"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    text = (
        "Здравствуйте.\n\n"
        "Вы находитесь в официальном боте Yakutia.media.\n\n"
        "Через эту форму вы можете оставить заявку на:\n"
        "— размещение рекламы\n"
        "— освещение мероприятия\n"
        "— партнёрство\n\n"
        "Нажмите «🚀 Старт заявки», чтобы начать."
    )

    await update.message.reply_text(
        text,
        reply_markup=reply_markup
    )

    return ConversationHandler.END

async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [["Личное", "Публичное"]]

    await update.message.reply_text(
        "Шаг 1 из 6\n\nВыберите тип мероприятия:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return TYPE

async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["type"] = update.message.text

    keyboard = [
        ["Спорт", "Культура"],
        ["Бизнес", "Творчество"],
        ["Другое"]
    ]

    await update.message.reply_text(
        "Шаг 2 из 6\n\nВыберите категорию:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return CATEGORY

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text

    await update.message.reply_text(
        "Шаг 3 из 6\n\nВведите дату мероприятия (например: 25.03.2026):"
    )

    return DATE

import re

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return DATE

    user_input = update.message.text

    try:
        event_date = datetime.strptime(user_input, "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат.\nВведите дату в формате ДД.ММ.ГГГГ"
        )
        return DATE

    today = datetime.now()

    if event_date.date() < today.date():
        await update.message.reply_text(
            "❌ Дата не может быть в прошлом.\nВведите корректную дату."
        )
        return DATE

    context.user_data["date"] = user_input

    await update.message.reply_text(
        "Введите время начала мероприятия (например: 14:00)"
    )
    return TIME

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_input = update.message.text.strip()

    try:
        datetime.strptime(user_input, "%H:%M")
    except ValueError:
        await update.message.reply_text(
            "Неверный формат времени. Введите в формате ЧЧ:ММ (например 14:00)"
        )
        return TIME

    context.user_data["start_time"] = user_input

    await update.message.reply_text(
        "Где будет проходить мероприятие?"
    )

    return PLACE

async def get_place(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["place"] = update.message.text

    await update.message.reply_text(
        "Шаг 5 из 8\n\nВведите ваше имя:"
    )

    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text

    keyboard = [[{"text": "Отправить контакт", "request_contact": True}]]

    await update.message.reply_text(
        "Шаг 6 из 6\n\nОтправьте номер телефона:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

    return PHONE

import re

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.contact:
        raw_phone = update.message.contact.phone_number
    else:
        raw_phone = update.message.text

    normalized = normalize_phone(raw_phone)

    if not normalized:
        await update.message.reply_text(
            "Введите корректный российский номер.\n"
            "Пример: +79991234567 или 89991234567"
        )
        return PHONE

    context.user_data["phone"] = normalized

    await update.message.reply_text(
        "Шаг 7 из 8\n\n"
        "Опишите мероприятие:\n"
        "Формат, программа, цель проведения."
    )

    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["description"] = update.message.text

    await update.message.reply_text(
        "Шаг 8 из 8\n\n"
        "Укажите ожидаемое количество человек:"
    )

    return PEOPLE

async def get_people(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text(
            "Введите числовое значение (например: 150)"
        )
        return PEOPLE

    context.user_data["people"] = int(text)

    summary = (
    f"<b>Проверьте данные:</b>\n\n"
    f"<b>Тип:</b> {context.user_data['type']}\n"
    f"<b>Категория:</b> {context.user_data['category']}\n"
    f"<b>Дата:</b> {context.user_data['date']}\n"
    f"<b>Время начала:</b> {context.user_data['start_time']}\n"
    f"<b>Место:</b> {context.user_data['place']}\n"
    f"<b>Имя:</b> {context.user_data['name']}\n"
    f"<b>Телефон:</b> {context.user_data['phone']}\n"
    f"\n"
    f"<b>Описание:</b>\n{context.user_data['description']}\n"
    f"\n"
    f"<b>Ожидаемое количество:</b> {context.user_data['people']}"
)

    keyboard = [
        ["✅ Подтвердить"],
        ["✏ Изменить"]
    ]

    await update.message.reply_text(
        summary,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return CONFIRM

async def confirm_application(update: Update, context: ContextTypes.DEFAULT_TYPE):

    choice = update.message.text

    if choice == "✏ Изменить":
        keyboard = [["🚀 Старт заявки"]]

        await update.message.reply_text(
            "Заполните заявку заново.",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

        return ConversationHandler.END

    if choice != "✅ Подтвердить":
        return CONFIRM

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event_id = generate_event_id(sheet)
    context.user_data["event_id"] = event_id

    sheet.append_row([
    event_id,
    now,
    "создано",
    context.user_data["type"],
    context.user_data["category"],
    context.user_data["date"],
    context.user_data["start_time"],
    context.user_data["place"],
    context.user_data["people"],
    context.user_data["name"],
    context.user_data["phone"],
    context.user_data["description"]
])
    message = (
    f"<b>📥 Новая заявка #{event_id}</b>\n\n"
    f"<b>Тип:</b> {context.user_data['type']}\n"
    f"<b>Категория:</b> {context.user_data['category']}\n"
    f"<b>Дата:</b> {context.user_data['date']}\n"
    f"<b>Время начала:</b> {context.user_data['start_time']}\n"
    f"<b>Место:</b> {context.user_data['place']}\n"
    f"<b>Имя:</b> {context.user_data['name']}\n"
    f"<b>Телефон:</b> {context.user_data['phone']}\n"
    f"<b>Ожидаемое количество:</b> {context.user_data['people']}\n"
    f"<b>Описание:</b>\n{context.user_data['description']}"
)

    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=message,
        parse_mode="HTML"
    )

    keyboard = [["🚀 Старт заявки"]]

    await update.message.reply_text(
        f"✅ Заявка отправлена.\nID события: {event_id}",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

def normalize_phone(raw_phone: str) -> str:

    # Убираем пробелы, скобки, дефисы
    digits = "".join(filter(str.isdigit, raw_phone))

    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]

    if digits.startswith("7") and len(digits) == 11:
        return "+7" + digits[1:]

    if digits.startswith("9") and len(digits) == 10:
        return "+7" + digits

    return None

def generate_event_id(sheet):
    chars = string.digits + string.ascii_uppercase
    existing_ids = set(sheet.col_values(1))

    while True:
        raw = uuid.uuid4().int
        event_id = ""

        while raw > 0 and len(event_id) < 5:
            raw, i = divmod(raw, 36)
            event_id = chars[i] + event_id

        event_id = event_id.zfill(5)

        if event_id not in existing_ids:
            return event_id

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Главное меню
    app.add_handler(CommandHandler("start", start))

    # Conversation Handler
    conv = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex("^🚀 Старт заявки$"),
            start_application
        )
    ],
    states={
        TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_type)],
        CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
        DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
        TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],  # ← ОБЯЗАТЕЛЬНО
        PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_place)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        PHONE: [MessageHandler(filters.TEXT | filters.CONTACT, get_phone)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
        PEOPLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_people)],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_application)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel)
    ],
)

    app.add_handler(conv)

    app.run_polling()


if __name__ == "__main__":
    main()
