from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

TIMEOUT_MINUTES = 3

async def monitor_events(context):

    print("MONITOR TICK", flush=True)

    pool = context.application.bot_data["db_pool"]
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

    except Exception as e:
        print("MONITOR ERROR:", repr(e), flush=True)