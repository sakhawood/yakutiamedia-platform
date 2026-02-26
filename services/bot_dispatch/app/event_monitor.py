from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


async def monitor_events(context):

    sheets = context.application.bot_data["sheets"]

    try:
        print("=== MONITOR START ===", flush=True)

        events = sheets.get_orders_sheet().get_all_records()
        assignments = sheets.get_assignments_sheet().get_all_records()

        for idx, event in enumerate(events, start=2):

            event_id = str(event.get("ID")).strip()
            status = str(event.get("Статус") or "").strip()

            if status != "в работу":
                continue

            try:
                required = int(event.get("Количество фотографов") or 0)
            except:
                required = 0

            if required <= 0:
                continue

            accepted = [
                a for a in assignments
                if str(a.get("ID события")) == event_id
                and a.get("Статус") == "принял"
            ]

            if len(accepted) >= required:
                print("EVENT FULL → SETTING STATUS", flush=True)
                sheets.sheet_events.update_cell(idx, 3, "укомплектовано")
                continue

            await start_distribution(
                context.application,
                sheets,
                event_id,
                required,
                accepted
            )

        print("=== MONITOR END ===", flush=True)

    except Exception as e:
        print("MONITOR ERROR:", repr(e), flush=True)


async def start_distribution(application, sheets, event_id, required, accepted):

    try:
        accepted_ids = {
            str(a.get("Telegram ID"))
            for a in accepted
        }

        photographers = sheets.get_photographers_sheet().get_all_records()

        active_photographers = [
            p for p in photographers
            if str(p.get("Активен", "")).strip() == "1"
        ]

        notified_ids = sheets.get_notified_photographers(event_id)

        eligible = [
            p for p in active_photographers
            if str(p.get("Telegram ID")) not in accepted_ids
            and str(p.get("Telegram ID")) not in notified_ids
        ]

        if not eligible:
            print("NO ELIGIBLE PHOTOGRAPHERS", flush=True)
            return

        p = eligible[0]

        tg_id = int(str(p.get("Telegram ID")).split(".")[0])

        events = sheets.get_orders()
        event = next(
            (e for e in events if str(e.get("ID")) == str(event_id)),
            {}
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Принять",
                    callback_data=f"accept_{event_id}"
                )
            ]
        ]

        text = (
            f"📌 Новое мероприятие\n\n"
            f"🆔 ID: {event_id}\n"
            f"📂 Тип: {event.get('Тип','')}\n"
            f"🏷 Категория: {event.get('Категория','')}\n\n"
            f"📅 Дата: {event.get('Дата мероприятия','')}\n"
            f"⏰ Время: {event.get('Время начала','')}\n"
            f"📍 Место: {event.get('Место проведения','')}\n\n"
            f"📸 Требуется фотографов: {required}\n"
        )

        await application.bot.send_message(
            chat_id=tg_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        sheets.add_notification(event_id, tg_id)

        print("SENT TO:", tg_id, flush=True)

    except Exception as e:
        print("DISTRIBUTION ERROR:", repr(e), flush=True)