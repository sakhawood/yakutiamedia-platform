import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime


print("INIT SHEETS START")


BOOK_EVENTS = "Order_Yakutia.media"
BOOK_PHOTOGRAPHERS = "Order_Photographers"


class SheetsClient:
    def __init__(self):
        credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

        if not credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS_JSON is not set")

        credentials_dict = json.loads(credentials_json)

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes,
        )

        self.client = gspread.authorize(credentials)

        self.events_book = self.client.open(BOOK_EVENTS)
        self.photographers_book = self.client.open(BOOK_PHOTOGRAPHERS)

    # =========================
    # ASSIGNMENTS
    # =========================

    def get_assignments_sheet(self):
        return self.events_book.worksheet("НАЗНАЧЕНИЯ")

    def count_accepted(self, order_id: str):
        sheet = self.get_assignments_sheet()
        records = sheet.get_all_records()

        count = 0
        for row in records:
            if (
                str(row.get("ID события")) == str(order_id)
                and str(row.get("Статус")).lower() in ["принял", "accepted"]
            ):
                count += 1

        return count

    def add_assignment(self, order_id, telegram_id, name, status):
        sheet = self.get_assignments_sheet()
        from datetime import datetime

        sheet.append_row([
            order_id,
            telegram_id,
            name,
            status,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "",
            "",
        ])

    # =========================
    # ORDERS
    # =========================

    def get_orders(self):
        sheet = self.events_book.sheet1
        data = sheet.get_all_records()
        return data

    def update_order_cell(self, row: int, col: int, value):
        sheet = self.events_book.sheet1
        sheet.update_cell(row, col, value)

    # =========================
    # PHOTOGRAPHERS
    # =========================

    def get_photographers(self):
        sheet = self.photographers_book.sheet1
        return sheet.get_all_records()

    # =========================
    # NOTIFICATIONS
    # =========================

    def get_notifications_sheet(self):
        return self.photographers_book.worksheet("NOTIFICATIONS")

    def get_notifications(self):
        sheet = self.get_notifications_sheet()
        return sheet.get_all_records()

    def add_notification(self, event_id: str, telegram_id: str):
        sheet = self.get_notifications_sheet()
        sheet.append_row([
            event_id,
            telegram_id,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        ])