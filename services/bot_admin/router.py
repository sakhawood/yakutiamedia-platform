from .handlers import current_events, my_events, close_session


async def text_router(update, context):

    text = update.message.text

    if text == "Текущие заявки":
        await current_events(update, context)

    elif text == "Мои заказы":
        await my_events(update, context)

    elif text == "Закрыть сессию":
        await close_session(update, context)
