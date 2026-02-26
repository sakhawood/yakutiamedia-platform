import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os


class SheetsClient:

    def __init__(self):

        print("INIT SHEETS START")

        creds_dict = {
            "type": os.getenv("GOOGLE_TYPE"),
            "project_id": os.getenv("GOOGLE_PROJECT_ID"),
            "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
            "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_CERT_URL")
        }

        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

        client = gspread.authorize(credentials)

        self.orders_book = client.open("Order_YakutiaMedia")
        self.photographers_book = client.open("Order_Photographer")

        self.orders_sheet = self.orders_book.sheet1
        self.photographers_sheet = self.photographers_book.worksheet("Photographers")
        self.notifications_sheet = self.photographers_book.worksheet("NOTIFICATIONS")
        self.assignments_sheet = self.orders_book.worksheet("НАЗНАЧЕНИЕ")

    # ---------------- ORDERS ----------------

    def get_orders(self):
        return self.orders_sheet.get_all_records()

    def count_accepted(self, order_id):
        records = self.assignments_sheet.get_all_records()

        count = 0
        for row in records:
            if str(row.get("ID события")) == str(order_id):
                count += 1

        return count

    # ---------------- PHOTOGRAPHERS ----------------

    def get_active_photographers(self):
        records = self.photographers_sheet.get_all_records()

        result = []
        for row in records:
            if str(row.get("Активен")).lower() == "true":
                result.append(row)

        return result

    # ---------------- NOTIFICATIONS ----------------

    def get_notified_photographers(self, order_id):
        records = self.notifications_sheet.get_all_records()

        result = []
        for row in records:
            if str(row.get("ID события")) == str(order_id):
                result.append(str(row.get("Telegram ID")))

        return result

    def log_notification(self, order_id, telegram_id):
        self.notifications_sheet.append_row([
            order_id,
            telegram_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])