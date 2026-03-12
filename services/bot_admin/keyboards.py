from telegram import ReplyKeyboardMarkup
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def admin_keyboard():

    keyboard = [
        ["📥 Текущие заявки"],
        ["📂 Мои заказы"],
        ["🚪 Закрыть сессию"]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )

def event_keyboard(event_id):

    keyboard = [
        [
            InlineKeyboardButton(
                "Открыть",
                callback_data=f"open_event:{event_id}"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)

def event_manage_keyboard(event_id):

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Подтвердить",
                callback_data=f"confirm_event:{event_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "✏ Изменить",
                callback_data=f"edit_event:{event_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Удалить",
                callback_data=f"delete_event:{event_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅ Назад",
                callback_data="back_events"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)
