import uuid

def generate_event_id(length: int = 5):
    return uuid.uuid4().hex[:length].upper()