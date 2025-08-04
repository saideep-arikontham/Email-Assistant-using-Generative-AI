# --------------------------
# IMPORTING LIBRARIES
# --------------------------

import os
import sys
import base64
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import datetime

# --------------------------
# SETTING UP PATH
# --------------------------

# Getting Path of current file
path = Path(os.path.dirname(os.getcwd()))
path = str(path)
sys.path.insert(1, path)


# --------------------------
# REQUIRED FUNCTIONS
# --------------------------


def get_email_body(payload):
    """Recursively extracts the best plain text body from the email payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            body = get_email_body(part)
            if body and body != "(No content)":
                return body

    mime_type = payload.get('mimeType', '')
    data = payload.get('body', {}).get('data')

    if data:
        decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

        if mime_type == "text/plain":
            return decoded.strip()
        elif mime_type == "text/html":
            soup = BeautifulSoup(decoded, "html.parser")
            return soup.get_text(separator=" ", strip=True)

    return "(No content)"


def extract_header(headers, name):
    """Helper to extract a specific header value from Gmail headers."""
    for header in headers:
        if header.get('name', '').lower() == name.lower():
            return header.get('value', '')
    return f"(No {name})"


def read_emails(max_results = 10):
    creds = Credentials.from_authorized_user_file(f'{path}/config/token.json')
    service = build('gmail', 'v1', credentials=creds)

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(1)
    query = f"after: {yesterday.strftime('%Y/%m/%d')}"

    results = service.users().messages().list(userId='me', q=query).execute()
    
    # results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    
    messages = results.get('messages', [])

    if not messages:
        print("No emails found.")
        return []

    result = []

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data.get('payload', {})
        headers = payload.get('headers', [])

        sender = extract_header(headers, 'from')
        subject = extract_header(headers, 'subject')
        date = extract_header(headers, 'date')

        body = get_email_body(payload)

        result.append({"sender":sender, "date":date, "subject":subject, "body":body})
        

    
    return result

