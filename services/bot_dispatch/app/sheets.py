import os
import json
import gspread
from google.oauth2.service_account import Credentials


print("INIT SHEETS START")


class SheetsClient:
    def __init__(self):
        credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

        if not credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS_JSON is not set in environment variables")

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

    def open_book(self, book_name: str):
        return self.client.open(book_name)