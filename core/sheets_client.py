import os
import json
import gspread

def get_worksheet(book_name: str, sheet_name: str):
    google_creds = os.getenv("GOOGLE_CREDENTIALS")

    if not google_creds:
        raise ValueError("GOOGLE_CREDENTIALS environment variable is not set")

    creds_dict = json.loads(google_creds)
    gc = gspread.service_account_from_dict(creds_dict)

    return gc.open(book_name).worksheet(sheet_name)