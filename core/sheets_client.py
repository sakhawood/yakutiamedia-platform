import os
import json
import gspread

def get_gspread_client():
    google_creds = os.getenv("GOOGLE_CREDENTIALS")

    if not google_creds:
        raise ValueError("GOOGLE_CREDENTIALS not set")

    creds_dict = json.loads(google_creds)
    return gspread.service_account_from_dict(creds_dict)

def get_worksheet(book_name: str, sheet_name: str):
    gc = get_gspread_client()
    return gc.open(book_name).worksheet(sheet_name)