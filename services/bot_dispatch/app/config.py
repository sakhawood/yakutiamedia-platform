import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

BOOK_EVENTS = "Order_Yakutia.media"
BOOK_PHOTOGRAPHERS = "Order_Photographers"

CHECK_INTERVAL = 60  # секунд