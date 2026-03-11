from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from core.db.pool import get_pool

TIMEOUT_MINUTES = 3

async def monitor_events(context):

    print("MONITOR TICK", flush=True)

    pool = await get_pool()
    bot = context.application.bot

    try:
        async with pool.acquire() as conn:

            events = await conn.fetch("""
                SELECT *
                FROM events
                WHERE status='в работу'
            """)

            print("EVENTS FOUND:", len(events), flush=True)

            for event in events:

                event_id = event["id"]
                required = event["required_photographers"]

                if required <= 0:
                    continue

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

                priorities = await conn.fetch("""
                    SELECT DISTINCT priority
                    FROM photographers
                    WHERE active=TRUE
                    ORDER BY priority ASC
                """)

                priority_list = [p["priority"] for p in priorities]

                if not priority_list:
                    print("NO ACTIVE PHOTOGRAPHERS", flush=True)
                    continue

                # определяем следующий приоритет
                if current_priority is None:
                    next_priority = priority_list[0]
                else:
                    if started_at:
                        delta = datetime.now() - started_at
                        if delta < timedelta(minutes=TIMEOUT_MINUTES):
                            print("WAITING TIMEOUT...", flush=True)
                            continue
                    try:
                        idx = priority_list.index(current_priority)
                        next_priority = priority_list[idx + 1]
                    except (ValueError, IndexError):
                        print("NO MORE PRIORITIES", flush=True)
                        continue

                photographers = await conn.fetch("""
                    SELECT telegram_id
                    FROM photographers
                    WHERE active=TRUE
                    AND priority=$1
                """, next_priority)

                if not photographers:
                    print("NO PHOTOGRAPHERS FOR PRIORITY", next_priority, flush=True)
                    continue

                print("SENDING TO PRIORITY:", next_priority, flush=True)
                print("PHOTOGRAPHERS FOUND:", len(photographers), flush=True)

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
                    f"📸 Требуется фотографов: {required}"
                )

                for p in photographers:
                    try:
                        await bot.send_message(
                            chat_id=p["telegram_id"],
                            text=text,
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )

                        await conn.execute("""
                            INSERT INTO notifications(event_id, photographer_id, sent_at)
                            VALUES($1,$2,NOW())
                            ON CONFLICT DO NOTHING
                        """, event_id, p["telegram_id"])

                    except Exception as e:
                        print("SEND ERROR:", repr(e), flush=True)

                await conn.execute("""
                    UPDATE events
                    SET distribution_priority=$1,
                        distribution_started_at=NOW()
                    WHERE id=$2
                """, next_priority, event_id)

    except Exception as e:
        print("MONITOR ERROR:", repr(e), flush=True)