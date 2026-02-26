from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


async def monitor_events(context):

    sheets = context.application.bot_data["sheets"]

    try:
        print("=== MONITOR START ===", flush=True)

        events = sheets.sheet_events.get_all_records()
        assignments = sheets.sheet_assignments.get_all_records()

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

    print("Distributing event", event_id, flush=True)

    try:
        accepted_ids = {
            str(a.get("Telegram ID"))
            for a in accepted
        }

        photographers = sheets.sheet_photographers.get_all_records()

        active_photographers = [
            p for p in photographers
            if str(p.get("Активен", "")).strip() == "1"
        ]

        notifications_raw = sheets.sheet_notifications.get_all_values()

        if len(notifications_raw) <= 1:
            notifications = []
        else:
            headers = notifications_raw[0]
            notifications = [
                dict(zip(headers, row))
                for row in notifications_raw[1:]
                if len(row) == len(headers)
            ]

        notified_ids = {
            str(n.get("Telegram ID"))
            for n in notifications
            if str(n.get("ID события")) == event_id
        }

        eligible = [
            p for p in active_photographers
            if str(p.get("Telegram ID")) not in accepted_ids
            and str(p.get("Telegram ID")) not in notified_ids
        ]

        if not eligible:
            print("NO ELIGIBLE PHOTOGRAPHERS", flush=True)
            return

        # ВОЛНОВАЯ модель — только один за цикл
        p = eligible[0]

        tg_id = int(str(p.get("Telegram ID")).split(".")[0])

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Принять",
                    callback_data=f"accept_{event_id}"
                )
            ]
        ]

        event = next(
            (e for e in sheets.sheet_events.get_all_records()
            if str(e.get("ID")) == str(event_id)),
            {}
        )

        text = (
            f"📌 *Новое мероприятие*\n\n"
            f"🆔 *ID:* {event_id}\n"
            f"📂 *Тип:* {event.get('Тип','')}\n"
            f"🏷 *Категория:* {event.get('Категория','')}\n\n"
            f"📅 *Дата:* {event.get('Дата мероприятия','')}\n"
            f"⏰ *Время:* {event.get('Время начала','')}\n"
            f"📍 *Место:* {event.get('Место проведения','')}\n\n"
            f"👥 *Ожидаемые гости:* {event.get('Ожидаемые люди','')}\n"
            f"📸 *Требуется фотографов:* {required}\n\n"
            f"📝 *Описание:*\n{event.get('Описание мероприятия','')}"
        )

        await application.bot.send_message(
            chat_id=tg_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        print("SENT TO:", tg_id, flush=True)

        sheets.sheet_notifications.append_row([
            event_id,
            tg_id,
            datetime.utcnow().isoformat()
        ])

    except Exception as e:
        print("DISTRIBUTION ERROR:", repr(e), flush=True)