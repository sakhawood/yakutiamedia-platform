import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime


print("INIT SHEETS START")


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

        self.events_book = self.client.open("Order_Yakutia.media")
        self.photographers_book = self.client.open("Order_Photographers")

    # =========================
    # EVENTS
    # =========================

    def get_orders_sheet(self):
        return self.events_book.worksheet("СОБЫТИЯ")

    def get_assignments_sheet(self):
        return self.events_book.worksheet("НАЗНАЧЕНИЯ")

    def get_orders(self):
        sheet = self.get_orders_sheet()
        return sheet.get_all_records()

    def count_accepted(self, order_id):
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
    # PHOTOGRAPHERS
    # =========================

    def get_photographers_sheet(self):
        return self.photographers_book.worksheet("ФОТОГРАФЫ")

    def get_notifications_sheet(self):
        return self.photographers_book.worksheet("NOTIFICATIONS")

    def get_active_photographers(self):
        sheet = self.get_photographers_sheet()
        records = sheet.get_all_records()

        active = []

        for row in records:
            if str(row.get("Активен")).lower() in ["true", "да", "1"]:
                active.append({
                    "Telegram ID": row.get("Telegram ID"),
                    "ИМЯ": row.get("ИМЯ"),
                    "Username": row.get("Username"),
                    "Время рассылки (мин)": int(row.get("Время рассылки (мин)") or 0)
                })
        active.sort(key=lambda x: x["Время рассылки (мин)"])
        return active

    # =========================
    # NOTIFICATIONS
    # =========================

    def already_notified(self, order_id, telegram_id):
        sheet = self.get_notifications_sheet()
        records = sheet.get_all_records()

        for row in records:
            if (
                str(row.get("ID события")) == str(order_id)
                and str(row.get("Telegram ID")) == str(telegram_id)
            ):
                return True

        return False

    def add_notification(self, order_id, telegram_id):
        sheet = self.get_notifications_sheet()
        sheet.append_row([
            order_id,
            telegram_id,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        ])
    
    def get_notifications_sheet(self):
        return self.photographers_book.worksheet("NOTIFICATIONS")


    def get_notified_photographers(self, order_id):
        sheet = self.get_notifications_sheet()
        records = sheet.get_all_records()

        notified = set()

        for row in records:
            if str(row.get("ID события")) == str(order_id):
                notified.add(str(row.get("Telegram ID")))

        return notified
    
    def log_notification(self, order_id, telegram_id):
        sheet = self.get_notifications_sheet()
        sheet.append_row([
            order_id,
            telegram_id
        ])