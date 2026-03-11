import random
import string

def generate_event_id(length=7):

    characters = string.ascii_uppercase + string.digits

    return "".join(random.choices(characters, k=length))
