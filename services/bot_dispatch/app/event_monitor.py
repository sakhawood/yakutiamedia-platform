from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

print("MONITOR TICK", flush=True)
TIMEOUT_MINUTES = 3


async def monitor_events(context):

    pool = context.application.bot_data["db_pool"]
    bot = context.application.bot

    try:
        async with pool.acquire() as conn:

            events = await conn.fetch("""
                SELECT *
                FROM events
                WHERE status='в работу'
            """)

            for event in events:

                event_id = event["id"]
                required = event["required_photographers"]

                if required <= 0:
                    continue

                # Сколько уже приняли
                accepted = await conn.fetchval("""
                    SELECT COUNT(*)
                    FROM assignments
                    WHERE event_id=$1
                    AND status='accepted'
                """, event_id)

                if accepted >= required:

                    await conn.execute("""
                        UPDATE events
                        SET status='укомплектовано',
                            distribution_priority=NULL,
                            distribution_started_at=NULL
                        WHERE id=$1
                    """, event_id)

                    continue

                current_priority = event["distribution_priority"]
                started_at = event["distribution_started_at"]

                # Получаем список активных приоритетов
                priorities = await conn.fetch("""
                    SELECT DISTINCT priority
                    FROM photographers
                    WHERE active=TRUE
                    ORDER BY priority ASC
                """)

                priority_list = [p["priority"] for p in priorities]

                if not priority_list:
                    continue

                # Если первая рассылка
                if current_priority is None:

                    next_priority = priority_list[0]

                else:

                    # Проверяем timeout
                    if started_at is not None:
                        delta = datetime.utcnow() - started_at
                        if delta < timedelta(minutes=TIMEOUT_MINUTES):
                            continue

                    # Переход к следующему приоритету
                    try:
                        idx = priority_list.index(current_priority)
                        next_priority = priority_list[idx + 1]
                    except (ValueError, IndexError):
                        # Больше приоритетов нет
                        continue

                # Получаем группу фотографов текущего приоритета
                photographers = await conn.fetch("""
                    SELECT p.telegram_id
                    FROM photographers p
                    WHERE p.active=TRUE
                    AND p.priority=$1
                    AND NOT EXISTS (
                        SELECT 1 FROM assignments a
                        WHERE a.event_id=$2
                        AND a.photographer_id=p.telegram_id
                        AND a.status IN ('accepted','completed')
                    )
                    AND NOT EXISTS (
                        SELECT 1 FROM notifications n
                        WHERE n.event_id=$2
                        AND n.photographer_id=p.telegram_id
                    )
                """, next_priority, event_id)

                if not photographers:
                    continue

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
                    f"📅 {event['event_date']} {event['start_time']}\n"
                    f"📂 {event['type']} | {event['category']}\n\n"
                    f"📸 Требуется фотографов: {required}\n"
                )

                for p in photographers:
                    try:
                        await bot.send_message(
                            chat_id=p["telegram_id"],
                            text=text,
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )

                        await conn.execute("""
                            INSERT INTO notifications(
                                event_id,
                                photographer_id,
                                sent_at
                            )
                            VALUES($1,$2,NOW())
                            ON CONFLICT DO NOTHING
                        """, event_id, p["telegram_id"])

                    except Exception as e:
                        print("SEND ERROR:", repr(e), flush=True)

                # Сохраняем состояние рассылки
                await conn.execute("""
                    UPDATE events
                    SET distribution_priority=$1,
                        distribution_started_at=NOW()
                    WHERE id=$2
                """, next_priority, event_id)

    async with pool.acquire() as conn:

    events = await conn.fetch("""
        SELECT *
        FROM events
        WHERE status='в работу'
    """)

    print("EVENTS FOUND:", len(events), flush=True)

    except Exception as e:
        print("MONITOR ERROR:", repr(e), flush=True)
        