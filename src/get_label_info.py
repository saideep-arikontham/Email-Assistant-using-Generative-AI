from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

import os
import sys
from pathlib import Path

# Getting path of current file's parent directory
path = Path(os.path.dirname(os.getcwd()))
path = str(path)
sys.path.insert(1, path)


def get_gmail_service():
    creds = Credentials.from_authorized_user_file(f'{path}/config/token.json')
    return build('gmail', 'v1', credentials=creds)

def get_label_id(label_name: str) -> str | None:
    """Return the label ID for a given label name, or None if not found."""
    service = get_gmail_service()
    resp = service.users().labels().list(userId="me").execute()
    for lbl in resp.get("labels", []):
        if lbl["name"] == label_name:
            return lbl["id"]
    return None
