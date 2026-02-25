import random
import string

def generate_event_id(sheet, length=5):
    characters = string.ascii_uppercase + string.digits

    existing_ids = set(sheet.col_values(1))

    while True:
        event_id = ''.join(random.choices(characters, k=length))
        if event_id not in existing_ids:
            return event_id