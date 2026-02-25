from datetime import datetime
from core.sheets_client import get_worksheet
from core.id_service import generate_event_id

BOOK_NAME = "Order_Yakutia.media"
SHEET_NAME = "СОБЫТИЯ"

def create_event(data: dict):

    sheet = get_worksheet(BOOK_NAME, SHEET_NAME)

    event_id = generate_event_id(sheet)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        event_id,
        now,
        "создано",
        data["type"],
        data["category"],
        data["date"],
        data["start_time"],
        data["place"],
        data["people"],
        data["name"],
        data["phone"],
        data["description"]
    ]

    sheet.append_row(row)

    return event_id