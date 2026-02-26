import gspread
from google.oauth2.service_account import Credentials
from app.config import GOOGLE_CREDENTIALS


class SheetsClient:

    def __init__(self):
        creds = Credentials.from_service_account_info(
            GOOGLE_CREDENTIALS,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )

        self.gc = gspread.authorize(creds)

        # Книги
        self.book_events = self.gc.open("Order_Yakutia.media")
        self.book_photographers = self.gc.open("Order_Photographers")

        # Листы Order_Yakutia.media
        self.sheet_events = self.book_events.worksheet("СОБЫТИЯ")
        self.sheet_assignments = self.book_events.worksheet("НАЗНАЧЕНИЯ")

        # Листы Order_Photographers
        self.sheet_photographers = self.book_photographers.worksheet("ФОТОГРАФЫ")
        self.sheet_notifications = self.book_photographers.worksheet("NOTIFICATIONS")

    def get_active_events(self):
        rows = self.sheet_events.get_all_records()
        return [
            row for row in rows
            if row.get("Статус") == "в работу"
        ]

    def get_photographers(self):
        return self.sheet_photographers.get_all_records()

    def append_assignment(self, row):
        self.sheet_assignments.append_row(row)

    def mark_distributed(self, order_id):

    def count_accepted(self, order_id):
    records = self.assignments_sheet.get_all_records()

    count = 0
    for row in records:
        if str(row.get("ID события")) == str(order_id):
            count += 1

    return count


    def get_notified_photographers(self, order_id):
        records = self.notifications_sheet.get_all_records()

        result = []
        for row in records:
            if str(row.get("ID события")) == str(order_id):
                result.append(str(row.get("Telegram ID")))

        return result


    def get_active_photographers(self):
        records = self.photographers_sheet.get_all_records()

        return [
            row for row in records
            if str(row.get("Активен")).lower() == "true"
        ]


    def log_notification(self, order_id, telegram_id):
        from datetime import datetime

        self.notifications_sheet.append_row([
            order_id,
            telegram_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])

    # Найти строку по ID
    row = self.find_order_row(order_id)

    # Вписать текущее время в колонку distributed_at
    self.orders_sheet.update_cell(row, 16, "SENT")