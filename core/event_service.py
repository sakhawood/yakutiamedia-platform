import asyncpg
import os
import random
import string


def generate_event_id():
    chars = string.digits + string.ascii_uppercase
    return ''.join(random.choices(chars, k=5))


async def create_event(pool, data):

    event_id = generate_event_id()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            INSERT INTO events(
                id,
                event_date,
                start_time,
                location,
                type,
                category,
                description,
                client_name,
                client_phone,
                required_photographers,
                status
            )
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'в работу')
            """,
            event_id,
            data["date"],
            data["start_time"],
            data["place"],
            data["type"],
            data["category"],
            data["description"],
            data["name"],
            data["phone"],
            1
        )

    return event_id
